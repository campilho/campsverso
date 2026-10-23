"""O ciclo de decisão inteiro num processo só: kernel, percepção e controlador (escopo §5).

Tudo passa pelo barramento em memória com validação de contrato, como passaria pelo NATS: os
serviços não se conhecem, só trocam envelopes. Serve aos testes rápidos do M3; os processos de
verdade ficam para os testes com NATS e para o `make soak`.

Com `controller="llm"` entra a mente (ADR-0059) sobre uma porta de modelo dada pelo teste (uma
porta falsa, ou a fita em `replay`), medida pelo `MeteredModel`, e opcionalmente a guarda de
orçamento. O relógio fica no modo contínuo, porque o máximo é só de script e replay (princípio 7);
em memória não faz diferença: o barramento entrega e espera a resposta antes do próximo tick.
"""

from collections.abc import Sequence
from typing import Any, Literal

from campsverso_adapters import (
    ContractValidator,
    FakeWallClock,
    InMemoryBus,
    MemoryBlobStore,
    MemoryTelemetry,
    MeteredModel,
    SequentialUuid7Ids,
    SqliteMemory,
    SqliteWorldStore,
    ValidatingBus,
    load_env,
)
from campsverso_budget.ledger import BudgetLimits
from campsverso_budget.service import BudgetService
from campsverso_cartridge_api import ControllerRef
from campsverso_controller_runner.replay import Recorded, ReplayRunner
from campsverso_controller_runner.runner import (
    ControllerRunner,
    SimTime,
    load_controller,
    load_mind,
)
from campsverso_kernel.engine import Engine
from campsverso_kernel.service import KernelService
from campsverso_kernel.version import run_version
from campsverso_mind import LlmController, Memory, MemorySettings
from campsverso_perception.service import PerceptionService
from campsverso_ports import Envelope, MemoryPort, ModelPort
from campsverso_testkit.farm import WORLD, make_core
from campsverso_testkit.nats_server import REPO

DAY = 1440
REPLAY_ID = "replay/teste"
LLM_ID = "llm/camps"
MODEL = "claude-haiku-5-5"
ENV = REPO / "config" / "env" / "local.yaml"
# Os mundos de teste por cartucho (ADR-0062): o id do mundo, o fazendeiro-script e a mente.
WORLDS: dict[str, tuple[str, str, str]] = {
    "farm_camps": (WORLD, "farmer", "camps"),
    "farm_boavista": ("farm-boavista-01", "farmer2", "camps_boavista"),
    "farm_morada_do_sol": ("farm-morada-do-sol-01", "farmer2", "camps_morada"),
}

type ControllerKind = Literal["script", "replay", "none", "llm"]


class DeadlockError(Exception):
    """O lockstep esperou um controlador que não respondeu."""


class Pipeline:
    def __init__(
        self,
        seed: int = 20261010,
        *,
        controller: ControllerKind = "script",
        recording: Sequence[Recorded] = (),
        river_bonus: bool = True,
        port: ModelPort | None = None,
        mind: str | None = None,
        budget: BudgetLimits | None = None,
        memory: MemoryPort | bool = True,
        cartridge: str = "farm_camps",
        model: str = MODEL,
    ) -> None:
        """`memory=True` dá à mente um caderno SQLite em memória (ADR-0060); `False` é o M10;
        uma porta pronta (um arquivo) serve ao teste de reinício. `cartridge` escolhe o mundo
        (a Fazenda do Camps ou a Boa Vista), com o script e a mente de cada um (ADR-0062)."""
        worldid, script, default_mind = WORLDS[cartridge]
        self.worldid, self.cartridge = worldid, cartridge
        mind = mind or default_mind
        self.inner = InMemoryBus()
        self.bus = ValidatingBus(self.inner)
        self.ids = SequentialUuid7Ids()
        self.clock = FakeWallClock()
        self.telemetry = MemoryTelemetry()
        validator = ContractValidator()
        core = make_core(seed, river_bonus=river_bonus, cartridge=cartridge)
        if controller == "replay":
            core.configure_controllers({"camps": ControllerRef("replay", REPLAY_ID)})
        if controller == "llm":
            core.configure_controllers({"camps": ControllerRef("llm", LLM_ID)})
            core.configure_clock("continuous", None, False)
        else:
            core.configure_clock("max", None, False)
        self.validator = validator
        self.version = run_version(cartridge, 60)
        self.store, self.blobs = SqliteWorldStore(":memory:"), MemoryBlobStore()
        engine = Engine(core, self.version, validator)
        self.kernel = KernelService(
            engine, self.bus, self.clock, self.ids, self.store, self.blobs, self.telemetry
        )
        self.core = core
        self.perception = PerceptionService(
            worldid, self.bus, MemoryBlobStore(), self.clock, self.ids, self.telemetry
        )
        self.runner: ControllerRunner | ReplayRunner | None = None
        self.mind: LlmController | None = None
        self.guard: BudgetService | None = None
        if controller == "script":
            self.runner = ControllerRunner(
                worldid,
                "camps",
                load_controller(script),
                self.bus,
                self.ids,
                self.clock,
                self.telemetry,
            )
        elif controller == "replay":
            self.runner = ReplayRunner(
                worldid,
                "camps",
                REPLAY_ID,
                recording,
                self.bus,
                self.ids,
                self.clock,
                self.telemetry,
            )
        elif controller == "llm":
            if port is None:
                raise ValueError("o controlador llm precisa de uma porta de modelo (port=...)")
            sim_time = SimTime()
            metered = MeteredModel(
                port,
                bus=self.bus,
                worldid=worldid,
                cartridge=cartridge,
                controller={"type": "llm", "id": LLM_ID},
                prices=load_env(ENV).models,
                clock=self.clock,
                ids=self.ids,
                sim_clock=sim_time,
            )
            notebook: Memory | None = None
            store: MemoryPort | None
            if isinstance(memory, bool):
                store = SqliteMemory(":memory:") if memory else None
            else:
                store = memory
            if store is not None:
                notebook = Memory(store, "camps", MemorySettings())
            self.mind = LlmController(
                load_mind(mind),
                metered,
                controller_id=LLM_ID,
                avatar_id="camps",
                model=model,
                telemetry=self.telemetry,
                memory=notebook,
            )
            self.runner = ControllerRunner(
                worldid,
                "camps",
                self.mind,
                self.bus,
                self.ids,
                self.clock,
                self.telemetry,
                cartridge=cartridge,
                sim_time=sim_time,
            )
        if budget is not None:
            self.guard = BudgetService(
                worldid, budget, self.bus, MemoryBlobStore(), self.clock, self.ids, self.telemetry
            )

    async def start(self) -> None:
        if self.guard is not None:
            await self.guard.start()
        await self.perception.start()
        if self.runner is not None:
            await self.runner.start()
        await self.kernel.start()

    async def run_until(self, tick: int) -> None:
        while self.core.tick < tick:
            if await self.kernel.run_ticks(min(60, tick - self.core.tick)) == 0:
                raise DeadlockError(f"o lockstep parou no tick {self.core.tick}")

    async def run_days(self, days: int) -> None:
        await self.run_until(self.core.tick + days * DAY)

    @property
    def envelopes(self) -> list[Envelope]:
        return [envelope for _, envelope in self.inner.published]

    def kernel_events(self) -> list[Envelope]:
        return [e for e in self.envelopes if str(e["source"]).startswith("/kernel/")]

    def of_type(self, event: str) -> list[dict[str, Any]]:
        return [dict(e["data"]) for e in self.envelopes if e["type"] == f"campsverso.{event}"]
