"""Gateway sobre o ciclo inteiro em memória: welcome, updates, visões e comandos (ADR-0050)."""

import asyncio
from collections.abc import AsyncIterator, Mapping
from pathlib import Path
from typing import Any

import pytest

from campsverso_adapters import MemoryBlobStore, MemoryClient, MemoryRealtime, MemoryTelemetry
from campsverso_gateway.service import (
    HUMAN_ID,
    PLAY_COMMANDS,
    POSSESS,
    PROPOSE,
    RELEASE,
    GatewayService,
)
from campsverso_gateway.state import apply_merge_patch, observer_state
from campsverso_testkit.farm import WORLD
from campsverso_testkit.pipeline import DAY, Pipeline
from campsverso_tools.contracts import catalog
from campsverso_tools.contracts.validation import MessageValidator

CONTRACTS = catalog.find_contracts_dir(Path(__file__).resolve().parent)
MESSAGES = MessageValidator(catalog.load(CONTRACTS))


class Rig:
    def __init__(
        self,
        pipeline: Pipeline,
        blobs: MemoryBlobStore | None = None,
        *,
        player_clock: bool = False,
    ) -> None:
        self.pipeline = pipeline
        self.blobs = blobs or MemoryBlobStore()
        self.player_clock = player_clock
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
            player_clock=self.player_clock,
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
    session_map = state["session"]["map"]
    assert (session_map["id"], session_map["width"], session_map["height"]) == (
        "farm_camps",
        32,
        18,
    )
    assert len(session_map["rows"]) == 18  # o terreno vem no session.started (ADR-0056)
    assert session_map["legend"]["G"]["kind"] == "grass"
    assert state["clock"] == {"mode": "max", "scale": 72.0, "paused": False}
    assert state["entities"]["bed"]["kind"] == "bed"
    assert state["controllers"]["camps"] == {"type": "script", "id": "script/farmer-v1"}
    assert welcome["commands"] == list(PLAY_COMMANDS)  # joga, mas não mexe no relógio
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


async def test_no_sandbox_o_jogador_pausa_e_muda_a_velocidade() -> None:
    """ADR-0074, decisão 16: quem joga o sandbox também opera o relógio, menos o passo a passo."""
    pipeline = Pipeline()
    rig = Rig(pipeline, player_clock=True)
    await rig.gateway.start()
    serving = asyncio.create_task(rig.realtime.serve(rig.gateway.handle))
    await pipeline.start()
    try:
        player, welcome = await rig.connect("player")
        clock = {c for c in welcome["commands"] if ".clock." in c}
        assert clock == {
            "campsverso.cmd.clock.pause.v1",
            "campsverso.cmd.clock.resume.v1",
            "campsverso.cmd.clock.set_scale.v1",
        }
        base = {"type": "campsverso.realtime.command.v1", "request_id": "ui-1"}
        pause = {"command": "campsverso.cmd.clock.pause.v1", "data": {"reason": "debug"}}
        await player.send({**base, **pause})
        assert (await player.receive_until("reply"))["ok"] is True
        step = {"command": "campsverso.cmd.clock.step.v1", "data": {"ticks": 1}}
        await player.send({**base, "request_id": "ui-2", **step})
        assert (await player.receive_until("reply"))["error"]["code"] == "not_allowed"
    finally:
        await rig.realtime.stop()
        await rig.gateway.stop()
        serving.cancel()


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


async def _ask(client: MemoryClient, command: str, data: Mapping[str, Any]) -> Mapping[str, Any]:
    await client.send(
        {
            "type": "campsverso.realtime.command.v1",
            "request_id": command[-24:],
            "command": command,
            "data": dict(data),
        }
    )
    return await client.receive_until("reply")


async def test_jogador_assume_joga_e_devolve(rig: Rig) -> None:
    """A9 pelo gateway (ADR-0051): o humano é sempre o mesmo, e quem diz isso é o gateway."""
    pipeline = rig.pipeline
    rig.gateway.flush()
    player, _ = await rig.connect("player")
    operator, _ = await rig.connect("operator")
    mode = {"mode": "continuous", "reason": "jogar"}
    assert (await _ask(operator, "campsverso.cmd.clock.set_mode.v1", mode))["ok"]
    await pipeline.kernel.run_ticks(1)
    fake = {"avatar_id": "camps", "controller": {"type": "script", "id": "script/farmer-v1"}}
    assert (await _ask(player, POSSESS, fake))["ok"]  # a UI não escolhe quem é
    await pipeline.kernel.run_ticks(1)
    possessed = pipeline.of_type("avatar.possessed.v1")[-1]
    assert possessed["controller"] == {"type": "human", "id": HUMAN_ID}
    move = {"avatar_id": "camps", "action": "move", "params": {"near": "well"}}
    assert (await _ask(player, PROPOSE, move))["ok"]
    await pipeline.kernel.run_ticks(1)
    assert pipeline.of_type("action.accepted.v1")[-1]["action"] == "move"
    sent = [
        e for e in pipeline.envelopes if e["type"] == PROPOSE and e["source"] == f"/gateway/{WORLD}"
    ]
    assert (sent[-1]["controllerid"], sent[-1]["actor"]) == (HUMAN_ID, "human/jogador")
    assert (await _ask(player, RELEASE, {"avatar_id": "camps"}))["ok"]
    await pipeline.kernel.run_ticks(1)
    released = pipeline.of_type("avatar.released.v1")[-1]
    assert released["controller"] == {"type": "script", "id": "script/farmer-v1"}


async def test_jogador_ve_a_recusa_do_proprio_comando(rig: Rig) -> None:
    """Com o mundo no modo máximo, o kernel recusa o humano; o jogador vê o motivo (ADR-0051)."""
    rig.gateway.flush()
    player, _ = await rig.connect("player")
    other, _ = await rig.connect("player")
    fake = {"avatar_id": "camps", "controller": {"type": "human", "id": "x"}}
    reply = await _ask(player, POSSESS, fake)
    await rig.pipeline.kernel.run_ticks(1)
    rig.gateway.flush()
    update = await player.receive_until("update")
    (rejected,) = [
        e for e in update["events"] if e["type"] == "campsverso.world.command.rejected.v1"
    ]
    assert rejected["data"]["command_id"] == reply["command_id"]
    assert rejected["data"]["reason"] == "mode_not_allowed"
    seen_by_other = await other.receive_until("update")
    assert all(e["visibility"] in {"world", "agent"} for e in seen_by_other["events"])
