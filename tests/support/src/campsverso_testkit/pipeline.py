"""O ciclo de decisão inteiro num processo só: kernel, percepção e controlador (escopo §5).

Tudo passa pelo barramento em memória com validação de contrato, como passaria pelo NATS: os
serviços não se conhecem, só trocam envelopes. Serve aos testes rápidos do M3; os processos de
verdade ficam para os testes com NATS e para o `make soak`.
"""

from collections.abc import Sequence
from typing import Any, Literal

from campsverso_adapters import (
    ContractValidator,
    FakeWallClock,
    InMemoryBus,
    MemoryBlobStore,
    MemoryTelemetry,
    SequentialUuid7Ids,
    SqliteWorldStore,
    ValidatingBus,
)
from campsverso_cartridge_api import ControllerRef
from campsverso_controller_runner.replay import Recorded, ReplayRunner
from campsverso_controller_runner.runner import ControllerRunner, load_controller
from campsverso_kernel.engine import Engine
from campsverso_kernel.service import KernelService
from campsverso_kernel.version import run_version
from campsverso_perception.service import PerceptionService
from campsverso_ports import Envelope
from campsverso_testkit.farm import WORLD, make_core

DAY = 1440
REPLAY_ID = "replay/teste"


class DeadlockError(Exception):
    """O lockstep esperou um controlador que não respondeu."""


class Pipeline:
    def __init__(
        self,
        seed: int = 20261010,
        *,
        controller: Literal["script", "replay", "none"] = "script",
        recording: Sequence[Recorded] = (),
        river_bonus: bool = True,
    ) -> None:
        self.inner = InMemoryBus()
        self.bus = ValidatingBus(self.inner)
        self.ids = SequentialUuid7Ids()
        self.clock = FakeWallClock()
        self.telemetry = MemoryTelemetry()
        validator = ContractValidator()
        core = make_core(seed, river_bonus=river_bonus)
        if controller == "replay":
            core.configure_controllers({"camps": ControllerRef("replay", REPLAY_ID)})
        core.configure_clock("max", None, False)
        self.validator = validator
        self.version = run_version("farm_camps", 60)
        self.store, self.blobs = SqliteWorldStore(":memory:"), MemoryBlobStore()
        engine = Engine(core, self.version, validator)
        self.kernel = KernelService(
            engine, self.bus, self.clock, self.ids, self.store, self.blobs, self.telemetry
        )
        self.core = core
        self.perception = PerceptionService(
            WORLD, self.bus, MemoryBlobStore(), self.clock, self.ids, self.telemetry
        )
        self.runner: ControllerRunner | ReplayRunner | None = None
        if controller == "script":
            self.runner = ControllerRunner(
                WORLD,
                "camps",
                load_controller("farmer"),
                self.bus,
                self.ids,
                self.clock,
                self.telemetry,
            )
        elif controller == "replay":
            self.runner = ReplayRunner(
                WORLD, "camps", REPLAY_ID, recording, self.bus, self.ids, self.clock, self.telemetry
            )

    async def start(self) -> None:
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
