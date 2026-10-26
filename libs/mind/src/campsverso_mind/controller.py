"""O controlador LLM (ADR-0059): uma entrega da percepção entra, uma proposta de ação sai.

Assíncrono, porque a chamada ao modelo leva segundos. Resposta sem ferramenta, recusa do modelo e
falha da porta viram `wait`, com o motivo na intenção; na terceira falha seguida a mente desiste
(`gave_up`), e quem a roda devolve o avatar ao controlador padrão do cartucho.
"""

from collections.abc import Mapping
from typing import Any, cast

from campsverso_mind.memory import Clock, Memory, clock_of
from campsverso_mind.mind import Mind, ToolDef
from campsverso_mind.playbook import playbook
from campsverso_mind.tools import INTENT, NOTE, intent_text, proposal_from, tool_specs
from campsverso_mind.window import CACHE, Window, is_snapshot
from campsverso_ports import Effort, ModelCallError, ModelPort, ModelRequest, Telemetry

INSTRUCTIONS = """\
## Como você recebe o mundo

A cada pedido de decisão você recebe uma foto (tudo o que você vê, em JSON) ou um delta: o que \
mudou desde a última entrega (seu estado, o que apareceu, mudou ou sumiu) e os eventos do \
meio-tempo, na ordem. O relógio anda em ticks de um minuto. O mundo não espera você: o tick da \
entrega diz quando ela foi feita, e o tempo passa enquanto você pensa.

## Como você age

Escolha exatamente uma ferramenta por resposta, e diga no campo `intent`, em uma frase, em \
português, o que pretende. Não escreva texto fora da ferramenta. O resultado da ferramenta é o \
que o mundo fez com ela: se a ação foi recusada, o resultado traz o motivo; leia e escolha outra \
coisa, em vez de repetir."""


class _Nobody:
    def info(self, event: str, **fields: Any) -> None: ...

    def warning(self, event: str, **fields: Any) -> None: ...

    def error(self, event: str, **fields: Any) -> None: ...


class LlmController:
    controller_type = "llm"

    def __init__(
        self,
        mind: Mind,
        port: ModelPort,
        *,
        controller_id: str,
        avatar_id: str,
        model: str,
        effort: Effort | None = "low",
        max_tokens: int = 1024,
        wait_ticks: int = 15,
        max_failures: int = 3,
        telemetry: Telemetry | None = None,
        memory: Memory | None = None,
        with_playbook: bool = False,
    ) -> None:
        self.mind = mind
        self.memory = memory
        if memory is not None:
            memory.adopt(mind)  # o caderno de campo e o experimento, se a mente os usa (ADR-0070)
        self._port = port
        self._controller_id = controller_id
        self._avatar = avatar_id
        self._model = model
        self._effort: Effort | None = effort
        self._max_tokens = max_tokens
        self._wait_ticks = wait_ticks
        self._max_failures = max_failures
        self._telemetry: Telemetry = telemetry if telemetry is not None else _Nobody()
        self.window = Window()
        self._tools: dict[str, ToolDef] = {t.name: t for t in mind.tools}
        self._specs = tool_specs(mind.tools, with_note=memory is not None)
        self._identity = f"{mind.card.strip()}\n\n{mind.notes.strip()}"
        if with_playbook:  # o método e o ofício, depois do manual (ADR-0071)
            self._identity += f"\n\n{playbook(mind)}"
        self._system = [
            {
                "type": "text",
                "text": f"{self._identity}\n\n{INSTRUCTIONS}",
                "cache_control": dict(CACHE),
            }
        ]
        self.reflections = 0
        self.calls = 0  # chamadas respondidas
        self.failures = 0  # falhas seguidas
        self.no_tool = 0  # respostas sem ferramenta
        self.gave_up = False

    @property
    def controller_id(self) -> str:
        return self._controller_id

    @property
    def system(self) -> list[dict[str, Any]]:
        return [dict(b) for b in self._system]

    @property
    def model(self) -> str:
        return self._model

    @property
    def identity(self) -> str:
        """O cartão e as notas do mundo, sem as instruções do jogo (a prova, ADR-0070)."""
        return self._identity

    def observe(self, delivery: Mapping[str, Any]) -> None:
        """Uma entrega que não pede chamada (pedido superado): só entra na janela."""
        self.window.observe(delivery)

    def request(self) -> ModelRequest:
        return ModelRequest(
            model=self._model,
            messages=self.window.request_messages(),
            system=self.system,
            tools=self._specs,
            max_tokens=self._max_tokens,
            effort=self._effort,
            purpose="decision",
            avatar_id=self._avatar,
        )

    async def decide(self, delivery: Mapping[str, Any]) -> dict[str, Any] | None:
        """A entrega entra na janela (e na memória) e o modelo é chamado; `None` quando a mente
        desistiu."""
        clock = clock_of(delivery)
        preface: str | None = None
        if self.memory is not None:
            self.memory.observe(delivery)
            pending = self.memory.pending_day(clock)
            if pending is not None and not self.gave_up:
                await self._reflect(clock, pending)  # a noite passou sem dormir: reflete agora
            if is_snapshot(delivery) or self.memory.fresh:
                # A janela abre com o bloco; e a manhã depois da reflexão o recebe mesmo numa
                # janela que continua, senão o resumo e o plano só chegariam na próxima foto.
                preface = self.memory.block(clock)
                self.memory.fresh = False
        self.window.observe(delivery, preface=preface)
        if self.gave_up:
            return None
        try:
            response = await self._port.complete(self.request())
        except ModelCallError as error:
            self.failures += 1
            self._telemetry.warning(
                "mind.call_failed", kind=error.kind, failures=self.failures, message=error.message
            )
            if self.failures >= self._max_failures:
                self.gave_up = True
                self._telemetry.error("mind.gave_up", failures=self.failures)
            return self._remember(clock, self._wait(f"sem resposta do modelo ({error.kind})"))
        self.failures = 0
        self.calls += 1
        self.window.answered(response.content)
        tool_uses = response.tool_uses()
        if not tool_uses or response.stop_reason == "refusal":
            self.no_tool += 1
            self._telemetry.info("mind.no_tool", stop_reason=response.stop_reason)
            fallback = f"sem ação escolhida ({response.stop_reason})"
            return self._remember(clock, self._wait(intent_text(response.text(), fallback)))
        chosen = tool_uses[0]
        tool = self._tools.get(str(chosen.get("name")))
        if tool is None:
            self.no_tool += 1
            self._telemetry.warning("mind.unknown_tool", name=chosen.get("name"))
            return self._remember(
                clock, self._wait(f"ferramenta desconhecida ({chosen.get('name')})")
            )
        given = cast(Mapping[str, Any], chosen.get("input") or {})
        return self._remember(clock, proposal_from(tool, given), given.get(NOTE))

    def _remember(
        self, clock: Clock, proposal: dict[str, Any], note: object = None
    ) -> dict[str, Any]:
        if self.memory is not None:
            self.memory.proposed(clock, proposal, note)
        return proposal

    async def after_proposal(self) -> None:
        """Depois de a proposta sair: a reflexão da noite, se a mente acabou de propor dormir."""
        if self.memory is None or self.memory.reflect_due is None or self.gave_up:
            return
        clock = self.memory.reflect_due
        await self._reflect(clock, clock.day)

    def drain_events(self) -> list[dict[str, Any]]:
        """Os eventos de memória (anotações, reflexão, crenças) para quem publica."""
        return [] if self.memory is None else self.memory.drain_events()

    async def _reflect(self, clock: Clock, day: int) -> None:
        assert self.memory is not None
        memory = self.memory
        if memory.port.has_reflection(day):
            memory.reflect_due = None
            return
        memory.attempted(day)
        request = memory.reflect_request(self._identity, clock, day, self._model)
        try:
            response = await self._port.complete(request)
        except ModelCallError as error:
            self._telemetry.warning("mind.reflection_failed", kind=error.kind, day=day)
            memory.reflect_due = None
            return
        reflection = memory.apply_reflection(request, response, clock, day)
        if reflection is None:
            self._telemetry.warning("mind.reflection_no_tool", day=day)
            memory.reflect_due = None
            return
        self.reflections += 1
        self._telemetry.info("mind.reflected", day=day, beliefs=len(reflection.beliefs))

    def _wait(self, intent: str) -> dict[str, Any]:
        return {"action": "wait", "params": {"ticks": self._wait_ticks}, INTENT: intent}
