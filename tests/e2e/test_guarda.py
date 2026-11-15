"""A guarda de orçamento num NATS de verdade (ADR-0080), com o usuário dela: consome os tetos novos
do operador no stream COMMANDS, publica o fato em `observer` e dá sinal de vida em `live`, que
nenhum stream guarda. As permissões do `nats.conf` são parte do que se testa."""

import asyncio
from collections.abc import Sequence
from typing import Any

from campsverso_adapters import (
    FakeWallClock,
    JsonTelemetry,
    MemoryBlobStore,
    NatsBus,
    Uuid7Ids,
    load_env,
)
from campsverso_budget.ledger import BudgetLimits
from campsverso_budget.service import LIMITS_CHANGED, PULSE, SET, BudgetService
from campsverso_contracts import subject
from campsverso_ports import Envelope
from campsverso_testkit.nats_server import REPO, NatsServer

ENV = REPO / "config" / "env" / "local.yaml"
WORLD = "office-campsverso-teste"


async def _bus(nats: NatsServer, user: str, *, manage: bool = False) -> NatsBus:
    return await NatsBus.connect(
        nats.url,
        user=user,
        password=nats.passwords[user],
        name=f"teste-{user}",
        streams=load_env(ENV, root=REPO).nats.streams,
        manage_streams=manage,
    )


def _command(ids: Uuid7Ids) -> dict[str, Any]:
    return {
        "specversion": "1.0",
        "id": ids.new_id(),
        "source": f"/gateway/{WORLD}",
        "type": SET,
        "time": "2026-11-16T12:00:00Z",
        "datacontenttype": "application/json",
        "dataschema": "contracts://commands/ops/budget.set.v1",
        "worldid": WORLD,
        "cartridge": "office_campsverso",
        "tick": 16230,
        "simtime": "2026-11-16T09:01:00-03:00",
        "seq": 0,
        "provenance": "simulated",
        "visibility": "observer",
        "actor": "human/operador",
        "data": {"usd_per_ticket": 2.0, "reason": "o pedido do testador é maior"},
    }


async def test_a_guarda_recebe_os_tetos_e_da_sinal_de_vida(nats: NatsServer) -> None:
    operator = await _bus(nats, "operator", manage=True)
    budget = await _bus(nats, "budget")
    gateway = await _bus(nats, "gateway")
    facts: list[Envelope] = []
    pulses: list[dict[str, Any]] = []

    async def observed(batch: Sequence[tuple[str, Envelope]]) -> None:
        facts.extend(envelope for _, envelope in batch)

    async def heard(_: str, message: Any) -> None:
        pulses.append(dict(message))

    watch = await operator.consume(f"campsverso.{WORLD}.observer.ops.>", "teste-ops", observed)
    live = await gateway.subscribe(f"campsverso.{WORLD}.live.budget", heard)
    ids = Uuid7Ids()
    guard = BudgetService(
        WORLD,
        BudgetLimits(usd_per_sim_day=3.0, usd_total=30.0, usd_per_ticket=1.0),
        budget,
        MemoryBlobStore(),
        FakeWallClock(),
        ids,
        JsonTelemetry("budget"),
        on_exceeded="mind_off",
    )
    try:
        await guard.start()
        await guard.announce_pulse(5.0)  # o laço da raiz de composição, uma vez
        await gateway.publish(subject(SET, WORLD), _command(ids))  # o gateway pode mandar
        for _ in range(100):
            if facts:
                break
            await asyncio.sleep(0.05)
        (changed,) = [e for e in facts if e["type"] == LIMITS_CHANGED]
        assert changed["data"] == {
            "usd_per_sim_day": 3.0,
            "usd_per_ticket": 2.0,
            "usd_total": 30.0,
            "reason": "o pedido do testador é maior",
        }
        for _ in range(100):
            if len(pulses) >= 2:  # o da raiz e o que sai logo depois dos tetos novos
                break
            await asyncio.sleep(0.05)
        assert pulses[0]["limits"]["usd_per_ticket"] == 1.0
        assert pulses[-1]["type"] == PULSE
        assert pulses[-1]["limits"]["usd_per_ticket"] == 2.0
        assert guard.failure is None
    finally:
        await guard.stop()
        await watch.unsubscribe()
        await live.unsubscribe()
        for bus in (gateway, budget, operator):
            await bus.close()
