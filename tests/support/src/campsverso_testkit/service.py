"""Fazenda do Camps rodando pelo serviço do kernel e pelo barramento validador (critério A2)."""

from typing import Any

from campsverso_adapters import FakeWallClock, InMemoryBus, SequentialUuid7Ids, ValidatingBus
from campsverso_kernel.service import KernelService
from campsverso_ports import Envelope
from campsverso_testkit.farm import SCRIPT_ID, WORLD, make_core


class ServiceFarmer:
    """Controlador roteirizado que só fala pelo barramento, como os controladores de verdade."""

    def __init__(self, seed: int = 20261010) -> None:
        self.inner = InMemoryBus()
        self.bus = ValidatingBus(self.inner)
        self.ids = SequentialUuid7Ids()
        self.service = KernelService(make_core(seed), self.bus, FakeWallClock(), self.ids)
        self.core = self.service.core
        self._seq = 0
        self.correlation: str | None = None

    async def start(self) -> None:
        async def remember(_: str, envelope: Envelope) -> None:
            self.correlation = str(envelope["correlationid"])

        await self.bus.subscribe(
            f"campsverso.{WORLD}.agent.camps.avatar.decision_requested.v1", remember
        )
        await self.service.start()

    @property
    def events(self) -> list[Envelope]:
        return [e for s, e in self.inner.published if ".cmd." not in s]

    def of_type(self, event: str) -> list[dict[str, Any]]:
        return [dict(e["data"]) for e in self.events if e["type"] == f"campsverso.{event}.v1"]

    async def run(self, ticks: int) -> None:
        await self.service.run_ticks(ticks)

    async def until(self, hhmm: str) -> None:
        minute = int(hhmm[:2]) * 60 + int(hhmm[3:])
        await self.run(self.core.calendar.ticks_until(self.core.tick, minute))

    async def do(self, action: str, **params: Any) -> None:
        self._seq += 1
        envelope: dict[str, Any] = {
            "specversion": "1.0",
            "id": self.ids.new_id(),
            "source": "/controller-runner/script/farmer-v1",
            "type": "campsverso.cmd.action.propose.v1",
            "time": "2026-10-10T09:00:00Z",
            "datacontenttype": "application/json",
            "dataschema": "contracts://commands/action/propose.v1",
            "worldid": WORLD,
            "cartridge": "farm_camps",
            "seq": self._seq,
            "controller": "script",
            "controllerid": SCRIPT_ID,
            "provenance": "simulated",
            "visibility": "observer",
            "data": {"avatar_id": "camps", "action": action, "params": params},
        }
        if self.correlation:
            envelope["correlationid"] = self.correlation
        await self.bus.publish(f"campsverso.{WORLD}.cmd.action.propose.v1", envelope)
        await self.run(1)
        while self.core.world.avatar_map["camps"].action is not None:
            await self.run(1)
