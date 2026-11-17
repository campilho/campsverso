"""A mente com rotina do dev do escritório (ADR-0080, decisão 18; o plano do M24, §2.5 e §3.4).

Uma versão híbrida do harness: o modelo pensa quando há trabalho, e a rotina conduz o resto, de
graça. Para o kernel é um controlador só, `llm`.

- **A rotina** é o dev-script: anda pela sala, pega o pedido, senta, faz as pausas, almoça e avisa.
  Ela recebe a foto inteira, refeita dos deltas da percepção (`apply_delta`).
- **O trabalho de um pedido** é uma sessão do modelo na oficina (`WorkSession`), em segundo plano:
  quando a rotina propõe trabalhar, a sessão começa, e o dev fica na mesa trabalhando enquanto ela
  corre. No `pronto`, o patch é revisado e a entrega sai na hora, sem esperar um pedido de decisão.
- **Quem fala com o dev** recebe a resposta do modelo, numa chamada curta, com o que ele está
  fazendo.

Se o modelo falha na conversa, a rotina responde. Uma sessão que não chega ao `pronto` vira uma
fala com o motivo, e o pedido fica em "fazendo": o dev não recomeça sozinho.

**A memória** (o plano do M24, §2.2 e §2.3), quando ligada: cada entrega vira episódios, pelo
perfil do escritório; cada sessão na oficina vira uma linha; a ferramenta `anotar` guarda o que o
modelo quer lembrar. Ao chegar, o dev revê os dias de trabalho ainda não revistos, numa chamada em
segundo plano, e a sessão de um pedido espera a revisão acabar. A memória vem antes do pedido, na
sessão, e na conversa.
"""

import asyncio
import contextlib
import json
import time
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, cast

from campsverso_controller_runner.runner import Controller
from campsverso_controller_runner.workshop import WorkshopSession
from campsverso_mind import Clock, Memory, Mind, SessionResult, StepOutcome, WorkSession
from campsverso_ports import Effort, ModelCallError, ModelPort, ModelRequest, Telemetry, Workspace
from campsverso_world_view import apply_delta

type Propose = Callable[[Mapping[str, Any]], Awaitable[None]]

DOING = "fazendo"
# Sem o sinal de vida da guarda por este tempo, a mente desliga (ADR-0080, decisão 16): três sinais
# perdidos, como a tela faz com o pulso do kernel.
GUARD_SILENCE_SECONDS = 15.0
OFF_LINE = "Fiquei sem bateria: não consigo mais programar hoje."
WORK_BLOCK_SECONDS = 60
THINK_SECONDS = 60
SAY_MAX = 280
REVIEW_WAIT_SECONDS = 120.0  # quanto a sessão de um pedido espera a revisão da manhã acabar


def _me(view: Mapping[str, Any]) -> str:
    return str(cast(Mapping[str, Any], view["self"])["entity_id"])


def _entities(view: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    return list(cast(Sequence[Mapping[str, Any]], view.get("entities") or ()))


def doing_ticket(view: Mapping[str, Any]) -> Mapping[str, Any] | None:
    """O pedido em que o dev trabalha: o dele em "fazendo"."""
    mine = _me(view)
    for entity in _entities(view):
        attrs = cast(Mapping[str, Any], entity.get("attributes") or {})
        if (
            entity.get("kind") == "ticket"
            and attrs.get("estado") == DOING
            and attrs.get("dono") == mine
        ):
            return entity
    return None


@dataclass(frozen=True, slots=True)
class Robot:
    """Um robô na bancada (o plano do M24, §4), como a foto o mostra."""

    entity_id: str
    name: str
    module: str
    description: str


def robots_in(view: Mapping[str, Any]) -> list[Robot]:
    """Os robôs da bancada, na ordem dos apoios."""
    found: list[Robot] = []
    for entity in _entities(view):
        attrs = cast(Mapping[str, Any], entity.get("attributes") or {})
        if entity.get("kind") == "robot" and attrs.get("nome") and attrs.get("modulo"):
            found.append(
                Robot(
                    str(entity["entity_id"]),
                    str(attrs["nome"]),
                    str(attrs["modulo"]),
                    str(attrs.get("descricao") or ""),
                )
            )
    return sorted(found, key=lambda r: r.entity_id)


def robot_tool(template: Mapping[str, Any], robots: Sequence[Robot]) -> dict[str, Any]:
    """A ferramenta da bancada com os robôs que estão nela: os nomes em `nome` e o que cada um faz
    na descrição."""
    tool = cast(dict[str, Any], json.loads(json.dumps(template)))
    present = "; ".join(f"{r.name}: {r.description}" if r.description else r.name for r in robots)
    tool["description"] = f"{str(tool['description']).strip()} Na bancada agora: {present}."
    props = cast(dict[str, Any], tool["input_schema"]["properties"])
    props["nome"] = {
        **cast(Mapping[str, Any], props.get("nome") or {}),
        "enum": [r.name for r in robots],
    }
    return tool


def brief(ticket: Mapping[str, Any]) -> str:
    """O pedido como ele chega à sessão: o número, o título, o que fazer, o aceite e a devolução."""
    a = cast(Mapping[str, Any], ticket.get("attributes") or {})
    lines = [
        f"Pedido {a.get('numero')}: {a.get('titulo', '')}",
        "",
        f"O que fazer: {a.get('descricao') or '(sem descrição)'}",
        f"Teste de aceite: {a.get('aceite') or '(nenhum)'}",
    ]
    if a.get("comentario"):
        lines.append(f"O gerente devolveu o pedido, com este comentário: {a['comentario']}")
    return "\n".join(lines)


class OfficeMind:
    controller_type = "llm"

    def __init__(
        self,
        script: Controller,
        mind: Mind,
        port: ModelPort,
        workshop: WorkshopSession,
        *,
        controller_id: str,
        avatar_id: str,
        model: str,
        session_tools: Sequence[Mapping[str, Any]],
        session_instructions: str,
        chat_instructions: str,
        effort: Effort | None = "medium",
        max_steps: int = 60,
        telemetry: Telemetry | None = None,
        memory: Memory | None = None,
    ) -> None:
        self._script = script
        self._port = port
        self._workshop = workshop
        self._controller_id = controller_id
        self._avatar = avatar_id
        self._model = model
        self._memory = memory
        self._robot_tool = mind.robot_tool
        note_tool = None if memory is None else memory.settings.profile.note_tool
        self._note = None if note_tool is None else str(note_tool["name"])
        self._tools = [dict(t) for t in session_tools] + (
            [] if note_tool is None else [dict(note_tool)]
        )
        self._identity = f"{mind.card.strip()}\n\n{mind.notes.strip()}"
        self._session_system = f"{self._identity}\n\n{session_instructions.strip()}"
        self._chat_system = f"{self._identity}\n\n{chat_instructions.strip()}"
        self._effort: Effort | None = effort
        self._max_steps = max_steps
        self._telemetry = telemetry
        self._view: dict[str, Any] | None = None
        self._task: asyncio.Task[None] | None = None
        self._working_on: str | None = None
        self._stop = False
        self.failed: set[str] = set()  # pedidos cuja sessão não chegou ao pronto
        self._thinking: set[str] = set()  # pedidos cujo tempo simulado acabou: o dev pensa sentado
        self.propose: Propose | None = None  # a entrega fora de um pedido de decisão: o runner
        self.sessions = 0
        self.replies = 0
        self.gave_up = False
        # O orçamento (ADR-0080, decisão 15): o teto do dia ou do total desliga a mente, e a rotina
        # conduz o dev; o de um pedido para a sessão dele. Sem sinal da guarda, a mente desliga.
        self.off = False
        self._said_off = False
        self._exceeded: set[str] = set()
        self._guard_at: float | None = None
        # A revisão da manhã: no máximo uma tentativa por dia do mundo, em segundo plano.
        self._review: asyncio.Task[None] | None = None
        self._review_day: int | None = None
        self.reviews = 0

    @property
    def controller_id(self) -> str:
        return self._controller_id

    @property
    def model(self) -> str:
        return self._model

    @property
    def working(self) -> bool:
        return self._task is not None and not self._task.done()

    # ------------------------------------------------------------- a foto

    def _track(self, delivery: Mapping[str, Any]) -> dict[str, Any] | None:
        if "view" in delivery:
            self._view = dict(cast(Mapping[str, Any], delivery["view"]))
        elif self._view is not None:
            self._view = apply_delta(self._view, delivery)
        return self._view

    def observe(self, delivery: Mapping[str, Any]) -> None:
        self._track(delivery)
        if self._memory is not None:
            self._memory.observe(delivery)

    # ------------------------------------------------------------- o orçamento

    def on_budget(self, message: Mapping[str, Any]) -> None:
        """O sinal de vida da guarda (`live.budget.v1`): o que está estourado agora."""
        self._guard_at = time.monotonic()
        self._exceeded = {str(x) for x in cast(Sequence[Any], message.get("exceeded") or ())}
        if self._working_on is not None and self._working_on in self._exceeded:
            self._stop = True  # o teto do pedido: a sessão para entre um passo e outro
        self._update_off()

    def _update_off(self) -> None:
        silent = (
            self._guard_at is not None and time.monotonic() - self._guard_at > GUARD_SILENCE_SECONDS
        )
        off = silent or bool(self._exceeded & {"day", "total"})
        if off and not self.off:
            self._stop = True
            self._warn("mind.off", exceeded=sorted(self._exceeded), silent=silent)
        if not off and self.off:
            self._said_off = False  # o operador subiu o teto: a mente volta e pode avisar de novo
            self._stop = False
        self.off = off

    # ------------------------------------------------------------- a decisão

    async def decide(self, delivery: Mapping[str, Any]) -> dict[str, Any] | None:
        view = self._track(delivery)
        if view is None:
            return {"action": "wait", "params": {"seconds": 5}, "intent": "rotina: esperar a foto"}
        decision = cast(Mapping[str, Any], delivery.get("decision") or {})
        view = {**view, "decision": decision}
        if self._memory is not None:
            self._memory.observe(delivery)
        self._update_off()
        if self.off:
            if not self._said_off:
                self._said_off = True
                return _say(OFF_LINE)
            proposal = dict(self._script.decide(view))
            proposal.pop("workshop", None)
            return proposal
        self._maybe_review()
        mine = _me(view)
        heard = [
            h
            for h in cast(Sequence[Mapping[str, Any]], view.get("heard") or ())
            if h["avatar_id"] != mine and h.get("listener_id") in (None, mine)
        ]
        if heard:
            reply = await self._reply(view, heard)
            if reply is not None:
                return reply
        if self.working:
            return self._keep_working(view, delivery)
        proposal = dict(self._script.decide(view))
        proposal.pop("workshop", None)  # a sessão fixa do script é só da reserva sem modelo
        ticket = doing_ticket(view)
        if proposal.get("action") == "work" and ticket is not None:
            ticket_id = str(ticket["entity_id"])
            if ticket_id not in self.failed:
                self._start(ticket)
                return self._keep_working(view, delivery)
        return proposal

    def _keep_working(self, view: Mapping[str, Any], delivery: Mapping[str, Any]) -> dict[str, Any]:
        """Na mesa, enquanto a sessão corre: o trabalho em blocos e, depois do tamanho simulado do
        pedido, sentado, pensando."""
        number = cast(Mapping[str, Any], (doing_ticket(view) or {}).get("attributes") or {}).get(
            "numero", "?"
        )
        intent = f"pensando no pedido {number} ({self._model})"
        if self._working_on is not None and _rejected_done(delivery):
            self._thinking.add(self._working_on)
        if self._working_on in self._thinking:
            return {"action": "wait", "params": {"seconds": THINK_SECONDS}, "intent": intent}
        return {"action": "work", "params": {"seconds": WORK_BLOCK_SECONDS}, "intent": intent}

    # ------------------------------------------------------------- a sessão

    def _start(self, ticket: Mapping[str, Any]) -> None:
        self._working_on = str(ticket["entity_id"])
        self.sessions += 1
        self._task = asyncio.create_task(self._session(ticket))

    async def _session(self, ticket: Mapping[str, Any]) -> None:
        ticket_id = str(ticket["entity_id"])
        number = cast(Mapping[str, Any], ticket.get("attributes") or {}).get("numero", "?")
        summary = ""
        tests = ""
        steps = 0
        await self._await_review()
        robots = robots_in(self._view or {})
        bench = (
            None if self._robot_tool is None or not robots else robot_tool(self._robot_tool, robots)
        )
        tools = self._tools + ([] if bench is None else [bench])
        try:
            space = await self._workshop.begin(ticket_id)

            async def execute(tool: str, args: Mapping[str, Any]) -> StepOutcome:
                nonlocal summary, tests
                if bench is not None and tool == bench["name"]:
                    return await self._call_robot(space, robots, args)
                if tool == self._note and self._memory is not None:
                    clock = self._memory.clock or Clock(0, 1, "")
                    written = self._memory.write_note(clock, args.get("texto"))
                    if not written:
                        return StepOutcome("nada anotado: o texto veio vazio", False)
                    return StepOutcome("anotado: você vai rever isso de manhã", True)
                if tool == "pronto":
                    summary = str(args.get("resumo") or "")
                    await self._workshop.step(space, tool, args)
                    return StepOutcome("pronto: a entrega vai para a revisão", True, True)
                result = await self._workshop.step(space, tool, args)
                if tool == "rodar_testes":
                    tests = (result.text.splitlines() or [""])[0][:160]
                return StepOutcome(result.text, result.ok)

            session = WorkSession(
                self._port,
                model=self._model,
                system=self._session_system,
                tools=tools,
                avatar_id=self._avatar,
                ticket_id=ticket_id,
                max_steps=self._max_steps,
                effort=self._effort,
            )
            result = await session.run(self._opening(ticket), execute, lambda: self._stop)
            steps = result.steps
            outcome = await self._outcome(space, result, number, summary)
        except Exception as error:  # a oficina caiu: o dev diz, e o pedido fica em fazendo
            self._warn("mind.session_failed", ticket=ticket_id, error=repr(error))
            outcome = _say(f"Não consegui trabalhar no pedido {number}: a oficina falhou.")
        self._remember_session(ticket_id, number, outcome, steps, tests)
        if outcome.get("action") != "deliver":
            self.failed.add(ticket_id)
        if self.propose is not None:
            await self.propose(outcome)

    async def _call_robot(
        self, space: Workspace, robots: Sequence[Robot], args: Mapping[str, Any]
    ) -> StepOutcome:
        """Um robô da bancada no espaço do pedido (o plano do M24, §4)."""
        name = str(args.get("nome", ""))
        found = next((r for r in robots if r.name == name), None)
        if found is None:
            names = ", ".join(r.name for r in robots)
            return StepOutcome(f"não há robô {name!r} na bancada; estão nela: {names}", False)
        given = args.get("argumentos")
        argv = (
            [str(a) for a in cast(Sequence[Any], given)]
            if isinstance(given, list)
            else ([] if given is None else [str(given)])
        )
        result = await self._workshop.robot(space, found.entity_id, found.module, argv)
        return StepOutcome(result.text, result.ok)

    def _opening(self, ticket: Mapping[str, Any]) -> str:
        """O que abre a sessão: a memória, se ligada, e o pedido."""
        if self._memory is None or self._memory.clock is None:
            return brief(ticket)
        return f"{self._memory.block(self._memory.clock)}\n\n{brief(ticket)}"

    def _remember_session(
        self, ticket_id: str, number: object, outcome: Mapping[str, Any], steps: int, tests: str
    ) -> None:
        """A sessão numa linha da memória: o que saiu dela, quantos passos e os últimos testes."""
        memory = self._memory
        if memory is None or memory.clock is None:
            return
        params = cast(Mapping[str, Any], outcome.get("params") or {})
        delivered = outcome.get("action") == "deliver"
        what = (
            f"terminei: {str(outcome.get('intent', '')).split(': ', 1)[-1]}"
            if delivered
            else f"não entreguei: {params.get('text', '')}"
        )
        detail = f"; testes: {tests}" if tests else ""
        memory.record(
            memory.clock,
            f"trabalhei no pedido {number} na oficina, em {steps} passos; {what}{detail}",
            7 if delivered else 8,
            "workshop",
            (ticket_id,),
        )

    async def _outcome(
        self, space: Workspace, result: SessionResult, number: object, summary: str
    ) -> dict[str, Any]:
        if not result.done:
            self._warn("mind.session_unfinished", reason=result.reason, steps=result.steps)
            return _say(f"Não consegui terminar o pedido {number}: {result.reason}.")
        intent = (
            f"entregar o pedido {number}: {summary}" if summary else f"entregar o pedido {number}"
        )
        deliver: dict[str, Any] = {"action": "deliver", "params": {}, "intent": intent[:500]}
        stamp = f"{space.base[:12]}-{self.sessions}"
        return await self._workshop.finish(space, deliver, stamp)

    async def stop(self) -> None:
        """Para a sessão entre um passo e outro, e espera ela acabar; a revisão também."""
        self._stop = True
        for task in (self._task, self._review):
            if task is not None:
                with contextlib.suppress(Exception):
                    await asyncio.wait_for(task, 30)

    # ------------------------------------------------------------- a revisão da manhã

    def _maybe_review(self) -> None:
        """Na primeira decisão de cada dia do mundo (o dev só decide dentro da sala), a revisão dos
        dias de trabalho ainda não revistos, até três, em segundo plano."""
        memory = self._memory
        clock = None if memory is None else memory.clock
        if memory is None or clock is None or self._review_day == clock.day:
            return
        self._review_day = clock.day
        days = memory.pending_days(clock)
        if days:
            self._review = asyncio.create_task(self._run_review(clock, days))

    async def _run_review(self, clock: Clock, days: Sequence[int]) -> None:
        memory = self._memory
        assert memory is not None
        memory.attempted(days[-1])
        request = memory.review_request(self._identity, clock, days, self._model)
        try:
            response = await self._port.complete(request)
        except ModelCallError as error:
            self._warn("mind.review_failed", kind=error.kind, days=list(days))
            return
        if memory.apply_reflection(request, response, clock, days[-1], days) is None:
            self._warn("mind.review_no_tool", days=list(days))
            return
        self.reviews += 1
        if self._telemetry is not None:
            self._telemetry.info("mind.reviewed", days=list(days))

    async def _await_review(self) -> None:
        """A sessão de um pedido começa depois da revisão, para ter o plano do dia."""
        if self._review is not None and not self._review.done():
            with contextlib.suppress(Exception):
                await asyncio.wait_for(asyncio.shield(self._review), REVIEW_WAIT_SECONDS)

    # ------------------------------------------------------------- a conversa

    async def _reply(
        self, view: Mapping[str, Any], heard: Sequence[Mapping[str, Any]]
    ) -> dict[str, Any] | None:
        """A resposta do modelo a quem falou; None (a rotina responde) se o modelo falha."""
        last = heard[-1]
        ticket = doing_ticket(view)
        status = (
            f"Você está trabalhando no pedido {brief(ticket).splitlines()[0]}"
            + (" (a sessão na oficina está correndo)." if self.working else ".")
            if ticket is not None
            else "Você não tem pedido em andamento."
        )
        said = "\n".join(f"{h['avatar_id']}: {h['text']}" for h in heard)
        clock = cast(Mapping[str, Any], view.get("clock") or {})
        user = f"Agora: {str(clock.get('sim_time', ''))[11:16]}. {status}\n\nOuviu:\n{said}"
        if self._memory is not None and self._memory.clock is not None:
            user = f"{self._memory.block(self._memory.clock)}\n\n{user}"
        request = ModelRequest(
            model=self._model,
            messages=[{"role": "user", "content": [{"type": "text", "text": user}]}],
            system=[
                {"type": "text", "text": self._chat_system, "cache_control": {"type": "ephemeral"}}
            ],
            max_tokens=1024,
            effort="low",
            purpose="conversation",
            avatar_id=self._avatar,
            ticket_id=None if ticket is None else str(ticket["entity_id"]),
        )
        try:
            response = await self._port.complete(request)
        except ModelCallError as error:
            self._warn("mind.reply_failed", kind=error.kind)
            return None
        text = " ".join(response.text().split())
        if not text:
            return None
        self.replies += 1
        return {
            "action": "say",
            "params": {"text": text[:SAY_MAX], "to": str(last["avatar_id"])},
            "intent": "responder a quem falou comigo",
        }

    # ------------------------------------------------------------- o resto do contrato

    async def after_proposal(self) -> None:
        return None

    def drain_events(self) -> list[dict[str, Any]]:
        return [] if self._memory is None else self._memory.drain_events()

    def _warn(self, event: str, **fields: Any) -> None:
        if self._telemetry is not None:
            self._telemetry.warning(event, **fields)


def _say(text: str) -> dict[str, Any]:
    return {"action": "say", "params": {"text": text[:SAY_MAX]}, "intent": "avisar sobre o pedido"}


def _rejected_done(delivery: Mapping[str, Any]) -> bool:
    """A última proposta foi recusada porque o trabalho simulado do pedido acabou."""
    decision = cast(Mapping[str, Any], delivery.get("decision") or {})
    if decision.get("reason") != "action_rejected":
        return False
    for event in reversed(cast(Sequence[Mapping[str, Any]], delivery.get("events") or ())):
        if event.get("type") == "campsverso.action.rejected.v1":
            return cast(Mapping[str, Any], event.get("data") or {}).get("reason") == "done"
    return False
