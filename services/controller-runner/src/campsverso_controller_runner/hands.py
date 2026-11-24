"""As mãos do dev, do lado do controlador (ADR-0089).

- **`OfficeHandsWorld`** é o que o escritório oferece a qualquer mão, num pedido: os robôs da
  bancada (que animam na tela pelos fatos da oficina), a memória do dev e o sinal de parar.
- **`ApiHands`** é o nosso harness atrás da porta das mãos: a `WorkSession` da mente, com as oito
  ferramentas da oficina pela porta de modelo. É o que o M24 e o M25 fizeram, só mudado de lugar: os
  passos, os textos e as chamadas ao modelo são os mesmos, e a fita do escritório continua valendo.
"""

import json
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, cast

from campsverso_controller_runner.workshop import WorkshopSession
from campsverso_mind import Clock, Memory, StepOutcome, WorkSession
from campsverso_ports import (
    HandsJob,
    HandsResult,
    HandsStep,
    HandsWorld,
    ModelPort,
    Robot,
    ToolResult,
    Workspace,
)

NOTED = "anotado: você vai rever isso de manhã"
NOT_NOTED = "nada anotado: o texto veio vazio"


@dataclass(frozen=True, slots=True)
class BenchRobot:
    """Um robô na bancada (o plano do M24, §4), como a foto o mostra."""

    entity_id: str
    name: str
    module: str
    description: str


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


def robot_args(given: object) -> list[str]:
    """Os argumentos de um robô como o modelo os deu: uma lista, um texto só, ou nada."""
    if isinstance(given, list):
        return [str(a) for a in cast(list[Any], given)]
    return [] if given is None else [str(given)]


class OfficeHandsWorld:
    """O mundo de um pedido, para as mãos: a bancada, a memória, os passos na tela (o
    `workshop.step.v2`, com as mãos e o modelo) e o sinal de parar."""

    def __init__(
        self,
        workshop: WorkshopSession,
        space: Workspace,
        robots: Sequence[BenchRobot],
        memory: Memory | None,
        should_stop: Callable[[], bool],
        *,
        harness: str,
        model: str,
    ) -> None:
        self._workshop = workshop
        self._space = space
        self._bench = list(robots)
        self._memory = memory
        self._should_stop = should_stop
        self._harness = harness
        self._model = model

    @property
    def robots(self) -> Sequence[Robot]:
        return [Robot(r.name, r.description) for r in self._bench]

    async def robot(self, name: str, args: Sequence[str]) -> ToolResult:
        found = next((r for r in self._bench if r.name == name), None)
        if found is None:
            names = ", ".join(r.name for r in self._bench)
            text = f"não há robô {name!r} na bancada; estão nela: {names}"
            return ToolResult(False, text, f"robô {name}: não está na bancada")
        return await self._workshop.robot(self._space, found.entity_id, found.module, list(args))

    async def note(self, text: str) -> ToolResult:
        memory = self._memory
        if memory is None:
            return ToolResult(False, "a memória não está ligada", "anotar: sem memória")
        clock = memory.clock or Clock(0, 1, "")
        if not memory.write_note(clock, text):
            return ToolResult(False, NOT_NOTED, "anotar: vazio")
        return ToolResult(True, NOTED, "anotado")

    async def step(self, step: HandsStep) -> None:
        await self._workshop.shown(self._space, step, harness=self._harness, model=self._model)

    def should_stop(self) -> bool:
        return self._should_stop()


class ApiHands:
    """O nosso harness: a sessão da mente pela porta de modelo, com as ferramentas da oficina, a da
    bancada (quando há robôs) e a de anotar (quando há memória)."""

    def __init__(
        self,
        port: ModelPort,
        workshop: WorkshopSession,
        *,
        tools: Sequence[Mapping[str, Any]],
        robot_tool: Mapping[str, Any] | None,
        note_tool: str | None,
    ) -> None:
        self._port = port
        self._workshop = workshop
        self._tools = [dict(t) for t in tools]
        self._robot_tool = robot_tool
        self._note = note_tool

    @property
    def harness(self) -> str:
        return "api"

    async def run(self, space: Workspace, job: HandsJob, world: HandsWorld) -> HandsResult:
        robots = list(world.robots)
        bench = (
            None if self._robot_tool is None or not robots else robot_tool(self._robot_tool, robots)
        )
        tools = self._tools + ([] if bench is None else [bench])
        summary = ""
        tests = ""
        steps = 0

        async def execute(tool: str, args: Mapping[str, Any]) -> StepOutcome:
            nonlocal summary, tests, steps
            steps += 1
            if bench is not None and tool == bench["name"]:
                result = await world.robot(
                    str(args.get("nome", "")), robot_args(args.get("argumentos"))
                )
                return StepOutcome(result.text, result.ok)
            if tool == self._note:
                texto = args.get("texto")
                result = await world.note("" if texto is None else str(texto))
                return StepOutcome(result.text, result.ok)
            # O que o modelo escreveu antes da ferramenta (ADR-0093, decisão 12).
            note = session.said
            if tool == "pronto":
                summary = str(args.get("resumo") or "")
                await self._workshop.step(
                    space, tool, args, harness="api", model=job.model, note=note
                )
                return StepOutcome("pronto: a entrega vai para a revisão", True, True)
            result = await self._workshop.step(
                space, tool, args, harness="api", model=job.model, note=note
            )
            if tool == "rodar_testes":
                tests = (result.text.splitlines() or [""])[0][:160]
            return StepOutcome(result.text, result.ok)

        session = WorkSession(
            self._port,
            model=job.model,
            system=job.system,
            tools=tools,
            avatar_id=job.avatar_id,
            ticket_id=job.ticket_id,
            max_steps=job.limits.max_turns,
            effort=job.effort,
        )
        result = await session.run(job.opening, execute, world.should_stop)
        return HandsResult(result.done, summary, result.steps, steps, result.reason, None, tests)
