"""Gateway sobre o ciclo inteiro em memória: welcome, updates, visões e comandos (ADR-0050)."""

import asyncio
from collections.abc import AsyncIterator, Mapping
from pathlib import Path
from typing import Any

import pytest

from campsverso_adapters import MemoryBlobStore, MemoryClient, MemoryRealtime, MemoryTelemetry
from campsverso_gateway.service import GatewayService
from campsverso_gateway.state import apply_merge_patch, observer_state
from campsverso_testkit.farm import WORLD
from campsverso_testkit.pipeline import DAY, Pipeline
from campsverso_tools.contracts import catalog
from campsverso_tools.contracts.validation import MessageValidator

CONTRACTS = catalog.find_contracts_dir(Path(__file__).resolve().parent)
MESSAGES = MessageValidator(catalog.load(CONTRACTS))


class Rig:
    def __init__(self, pipeline: Pipeline, blobs: MemoryBlobStore | None = None) -> None:
        self.pipeline = pipeline
        self.blobs = blobs or MemoryBlobStore()
        self.gateway = self.new_gateway()
        self.realtime = MemoryRealtime()

    def new_gateway(self) -> GatewayService:
        p = self.pipeline
        return GatewayService(
            WORLD,
            "camps",
            "farm_camps",
            p.bus,
            self.blobs,
            p.clock,
            p.ids,
            MemoryTelemetry(),
            p.validator,
            flush_seconds=3600,  # os testes chamam flush() na hora certa
        )

    async def connect(self, view: str) -> tuple[MemoryClient, dict[str, Any]]:
        client = await self.realtime.connect(view)  # pyright: ignore[reportArgumentType]
        welcome = dict(await client.receive())
        assert MESSAGES.validate(welcome) == []
        return client, welcome


@pytest.fixture
async def rig() -> AsyncIterator[Rig]:
    pipeline = Pipeline()
    rig = Rig(pipeline)
    await rig.gateway.start()
    serving = asyncio.create_task(rig.realtime.serve(rig.gateway.handle))
    await pipeline.start()
    yield rig
    await rig.realtime.stop()
    await rig.gateway.stop()
    serving.cancel()


async def _drain(client: MemoryClient) -> list[Mapping[str, Any]]:
    """Tudo o que já chegou ou chega logo: o gateway escreve por uma tarefa à parte."""
    received: list[Mapping[str, Any]] = []
    while True:
        try:
            received.append(await client.receive(timeout=0.2))
        except TimeoutError:
            return received


def _types(message: Mapping[str, Any]) -> set[str]:
    return {str(e["type"]).removeprefix("campsverso.") for e in message["events"]}


async def test_welcome_traz_o_estado_e_o_mapa(rig: Rig) -> None:
    await rig.pipeline.run_until(30)
    rig.gateway.flush()
    _, welcome = await rig.connect("player")
    state = welcome["state"]
    assert state["session"]["map"] == {"id": "farm_camps", "width": 32, "height": 18}
    assert state["clock"] == {"mode": "max", "scale": 72.0, "paused": False}
    assert state["entities"]["bed"]["kind"] == "bed"
    assert state["controllers"]["camps"] == {"type": "script", "id": "script/farmer-v1"}
    assert welcome["commands"] == []
    assert "world.session.started.v1" in _types(welcome)
    assert "perception.delivered.v1" not in _types(welcome)  # as fotos ficam com os controladores


async def test_updates_levam_ao_mesmo_estado_da_projecao(rig: Rig) -> None:
    client, welcome = await rig.connect("operator")
    state = welcome["state"]
    for _ in range(12):
        await rig.pipeline.run_until(rig.pipeline.core.tick + 10)
        rig.gateway.flush()
    updates = await _drain(client)
    assert len(updates) == 12
    for update in updates:
        assert MESSAGES.validate(dict(update)) == []
        state = apply_merge_patch(state, update["patch"])
    assert state == observer_state(rig.gateway.projection)
    # O tick é o do último evento: tick quieto não gera evento, e a UI estima o relógio entre eles.
    assert 100 < state["tick"] <= rig.pipeline.core.tick


async def test_jogador_nunca_recebe_internal_nem_observer(rig: Rig) -> None:
    player, _ = await rig.connect("player")
    operator, _ = await rig.connect("operator")
    await rig.pipeline.run_until(DAY + 60)  # a virada do dia aplica a regra oculta (internal)
    rig.gateway.flush()
    seen_by_player = {e["visibility"] for e in (await player.receive())["events"]}
    seen_by_operator = {e["visibility"] for e in (await operator.receive())["events"]}
    assert seen_by_player <= {"world", "agent"}
    assert "internal" in seen_by_operator


async def test_operador_pausa_e_o_kernel_responde(rig: Rig) -> None:
    rig.gateway.flush()  # o welcome já sai com a sessão; o update traz só a pausa
    operator, welcome = await rig.connect("operator")
    assert "campsverso.cmd.clock.pause.v1" in welcome["commands"]
    await operator.send(
        {
            "type": "campsverso.realtime.command.v1",
            "request_id": "ui-1",
            "command": "campsverso.cmd.clock.pause.v1",
            "data": {"reason": "debug"},
        }
    )
    reply = await operator.receive_until("reply")
    assert MESSAGES.validate(dict(reply)) == []
    assert (reply["request_id"], reply["ok"]) == ("ui-1", True)
    await rig.pipeline.kernel.run_ticks(1)
    rig.gateway.flush()
    update = await operator.receive_until("update")
    assert update["patch"]["clock"] == {"paused": True}
    assert "world.clock.paused.v1" in _types(update)


async def test_comandos_recusados_pelo_gateway(rig: Rig) -> None:
    player, _ = await rig.connect("player")
    operator, _ = await rig.connect("operator")
    step = {"type": "campsverso.realtime.command.v1", "request_id": "ui-2"}
    await player.send(
        {**step, "command": "campsverso.cmd.clock.pause.v1", "data": {"reason": "debug"}}
    )
    assert (await player.receive_until("reply"))["error"]["code"] == "not_allowed"
    await operator.send({**step, "command": "campsverso.cmd.clock.step.v1", "data": {"ticks": 0}})
    assert (await operator.receive_until("reply"))["error"]["code"] == "invalid_command"
    await operator.send({"type": "campsverso.realtime.hello.v1"})
    reply = await operator.receive_until("reply")
    assert (reply["request_id"], reply["error"]["code"]) == ("desconhecido", "invalid_message")
    published = [e for e in rig.pipeline.envelopes if str(e["source"]).startswith("/gateway/")]
    assert published == []


async def test_gateway_volta_do_arquivo_sem_repetir_eventos(rig: Rig) -> None:
    await rig.pipeline.run_until(120)
    rig.gateway.flush()
    before = observer_state(rig.gateway.projection)
    again = Rig(rig.pipeline, rig.blobs).new_gateway()
    assert observer_state(again.projection) == before
    replayed = [e for _, e in rig.pipeline.inner.published if e["visibility"] == "world"]
    await again._on_batch("world", [("x", e) for e in replayed])  # pyright: ignore[reportPrivateUsage]
    assert observer_state(again.projection) == before  # reentrega não muda nada


async def test_pulso_do_kernel_e_sem_sinal(rig: Rig) -> None:
    """O pulso entra no estado; sem pulso por 3 intervalos, o kernel fica sem sinal (ADR-0051)."""
    rig.gateway.flush()
    operator, _ = await rig.connect("operator")
    pulse = {
        "type": "campsverso.live.kernel.v1",
        "worldid": WORLD,
        "tick": 42,
        "sim_time": "2026-10-10T06:42:00-03:00",
        "mode": "continuous",
        "scale": 72,
        "paused": False,
        "pulse_seconds": 1,
        "sent_at": "2026-10-12T15:00:00.000Z",
    }
    await rig.pipeline.inner.announce(f"campsverso.{WORLD}.live.kernel", pulse)
    rig.gateway.flush()
    update = await operator.receive_until("update")
    assert MESSAGES.validate(dict(update)) == []
    assert update["patch"]["pulse"] == {
        "tick": 42,
        "sim_time": "2026-10-10T06:42:00-03:00",
        "alive": True,
    }
    rig.pipeline.clock.advance(3.5)
    rig.gateway.flush()
    assert (await operator.receive_until("update"))["patch"] == {"pulse": {"alive": False}}
    assert rig.pipeline.inner.announced[-1][1] is pulse  # nada do pulso em `published`
