"""A sessão de trabalho do dev na oficina (ADR-0080; o plano do M24, §3.4): uma conversa própria
com o modelo, com as ferramentas da oficina, até o `pronto` ou um limite.

É separada da janela das decisões do mundo: enquanto a sessão corre, o mundo vê o dev trabalhando
na mesa, e quem responde a uma fala é outra chamada, curta. A mente só conhece a porta de modelo;
quem executa as ferramentas é quem roda a sessão (`execute`), pela porta da oficina.
"""

from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, cast

from campsverso_ports import Effort, ModelCallError, ModelPort, ModelRequest

CACHE = {"type": "ephemeral"}
NUDGE = "Use uma ferramenta da oficina. Quando o pedido estiver pronto, chame `pronto`."
MAX_RESULT_CHARS = 20_000


@dataclass(frozen=True, slots=True)
class StepOutcome:
    """O que uma ferramenta devolveu à sessão; `done` encerra (o `pronto`)."""

    text: str
    ok: bool
    done: bool = False


@dataclass(frozen=True, slots=True)
class SessionResult:
    done: bool  # chegou ao `pronto`
    steps: int  # chamadas ao modelo
    reason: str  # pronto, parada, limite de passos, falhas do modelo, sem ferramenta


type Execute = Callable[[str, Mapping[str, Any]], Awaitable[StepOutcome]]


class WorkSession:
    def __init__(
        self,
        port: ModelPort,
        *,
        model: str,
        system: str,
        tools: Sequence[Mapping[str, Any]],
        avatar_id: str,
        ticket_id: str,
        max_steps: int = 60,
        max_tokens: int = 8192,
        effort: Effort | None = "medium",
        max_failures: int = 3,
    ) -> None:
        self._port = port
        self._model = model
        self._system = [{"type": "text", "text": system, "cache_control": dict(CACHE)}]
        self._tools = [dict(t) for t in tools]
        self._avatar = avatar_id
        self._ticket = ticket_id
        self._max_steps = max_steps
        self._max_tokens = max_tokens
        self._effort: Effort | None = effort
        self._max_failures = max_failures
        self.messages: list[dict[str, Any]] = []
        # O texto da resposta que pediu a ferramenta em curso (ADR-0093, decisão 12): só a primeira
        # ferramenta de cada resposta o leva; a tela o mostra como um comentário.
        self.said = ""

    def _request(self) -> ModelRequest:
        messages = [dict(m) for m in self.messages]
        last = dict(messages[-1])
        blocks = [dict(b) for b in cast(Sequence[Mapping[str, Any]], last["content"])]
        # O prefixo cresce, e o marcador do cache anda com ele.
        blocks[-1] = {**blocks[-1], "cache_control": dict(CACHE)}
        messages[-1] = {**last, "content": blocks}
        return ModelRequest(
            model=self._model,
            messages=messages,
            system=self._system,
            tools=self._tools,
            max_tokens=self._max_tokens,
            effort=self._effort,
            purpose="workshop",
            avatar_id=self._avatar,
            ticket_id=self._ticket,
        )

    async def run(
        self, brief: str, execute: Execute, should_stop: Callable[[], bool] = lambda: False
    ) -> SessionResult:
        """Do pedido (`brief`) ao `pronto`: cada resposta com ferramentas vira os resultados delas
        no turno seguinte; sem ferramenta, um lembrete. Para entre um passo e outro, quando
        `should_stop` diz (o teto do pedido, a mente desligada)."""
        self.messages = [{"role": "user", "content": [{"type": "text", "text": brief}]}]
        failures = no_tool = 0
        for step in range(self._max_steps):
            if should_stop():
                return SessionResult(False, step, "parada")
            try:
                response = await self._port.complete(self._request())
            except ModelCallError:
                failures += 1
                if failures >= self._max_failures:
                    return SessionResult(False, step + 1, "falhas do modelo")
                continue
            failures = 0
            answer = [dict(b) for b in response.content]
            self.messages.append({"role": "assistant", "content": answer})
            uses = response.tool_uses()
            if not uses:
                no_tool += 1
                if no_tool >= self._max_failures or response.stop_reason == "refusal":
                    return SessionResult(False, step + 1, "sem ferramenta")
                self.messages.append({"role": "user", "content": [{"type": "text", "text": NUDGE}]})
                continue
            no_tool = 0
            results: list[dict[str, Any]] = []
            done = False
            said = " ".join(str(b.get("text") or "") for b in answer if b.get("type") == "text")
            for use in uses:
                if done:  # depois do pronto, nada mais roda
                    results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": str(use["id"]),
                            "content": "Ignorada: a sessão já acabou no pronto.",
                            "is_error": True,
                        }
                    )
                    continue
                given = cast(Mapping[str, Any], use.get("input") or {})
                self.said, said = said.strip(), ""
                outcome = await execute(str(use["name"]), given)
                block: dict[str, Any] = {
                    "type": "tool_result",
                    "tool_use_id": str(use["id"]),
                    "content": outcome.text[:MAX_RESULT_CHARS] or "(vazio)",
                }
                if not outcome.ok:
                    block["is_error"] = True
                results.append(block)
                done = done or outcome.done
            self.messages.append({"role": "user", "content": results})
            if done:
                return SessionResult(True, step + 1, "pronto")
        return SessionResult(False, self._max_steps, "limite de passos")
