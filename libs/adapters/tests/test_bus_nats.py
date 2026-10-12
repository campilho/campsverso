"""NatsBus contra um NATS de verdade, com o nats.conf do repositório (escopo A8; ADR-0017)."""

import asyncio
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import pytest

from campsverso_adapters import NatsBus, load_env
from campsverso_ports import Envelope, PermissionDeniedError
from campsverso_testkit.nats_server import REPO, NatsServer

STREAMS = load_env(REPO / "config" / "env" / "local.yaml", root=REPO).nats.streams


async def _connect(nats: NatsServer, user: str, *, manage: bool = False) -> NatsBus:
    return await NatsBus.connect(
        nats.url,
        user=user,
        password=nats.passwords[user],
        name=f"teste-{user}",
        streams=STREAMS,
        manage_streams=manage,
    )


def _event(event_id: str, seq: int) -> dict[str, Any]:
    return {"id": event_id, "seq": seq, "type": "campsverso.world.teste.v1"}


class Collector:
    def __init__(self) -> None:
        self.received: list[Envelope] = []

    async def __call__(self, batch: Sequence[tuple[str, Envelope]]) -> None:
        self.received += [envelope for _, envelope in batch]

    async def until(self, count: int, timeout: float = 5) -> None:
        async with asyncio.timeout(timeout):
            while len(self.received) < count:
                await asyncio.sleep(0.02)


async def test_republicar_o_mesmo_id_nao_duplica(nats: NatsServer) -> None:
    kernel = await _connect(nats, "kernel", manage=True)
    for _ in range(3):
        await kernel.publish("campsverso.w.world.teste.v1", _event("evento-1", 0))
    await kernel.publish("campsverso.w.world.teste.v1", _event("evento-2", 1))
    operator, seen = await _connect(nats, "operator"), Collector()
    await operator.consume("campsverso.*.world.>", "teste-dedup", seen)
    await seen.until(2)
    await asyncio.sleep(0.3)
    assert [e["id"] for e in seen.received] == ["evento-1", "evento-2"]
    await kernel.close()
    await operator.close()


async def test_consumidor_duravel_retoma_de_onde_parou(nats: NatsServer) -> None:
    kernel = await _connect(nats, "kernel", manage=True)
    archiver = await _connect(nats, "archiver")
    for seq in range(2):
        await kernel.publish("campsverso.w.world.teste.v1", _event(f"a-{seq}", seq))
    first = Collector()
    subscription = await archiver.consume("campsverso.*.world.>", "teste-retoma", first)
    await first.until(2)
    await subscription.unsubscribe()
    for seq in range(2, 4):
        await kernel.publish("campsverso.w.world.teste.v1", _event(f"a-{seq}", seq))
    second = Collector()
    await archiver.consume("campsverso.*.world.>", "teste-retoma", second)
    await second.until(2)
    await asyncio.sleep(0.3)
    assert [e["seq"] for e in second.received] == [2, 3]  # só o que não tinha confirmado
    await kernel.close()
    await archiver.close()


async def test_lote_com_erro_volta_a_ser_entregue(nats: NatsServer) -> None:
    kernel = await _connect(nats, "kernel", manage=True)
    archiver = await _connect(nats, "archiver")
    await kernel.publish("campsverso.w.world.teste.v1", _event("b-0", 0))

    async def fails(_: Sequence[tuple[str, Envelope]]) -> None:
        raise OSError("disco cheio")

    await archiver.consume("campsverso.*.world.>", "teste-erro", fails)
    await asyncio.sleep(0.3)
    await archiver.close()
    archiver, again = await _connect(nats, "archiver"), Collector()
    await archiver.consume("campsverso.*.world.>", "teste-erro", again)
    with pytest.raises(TimeoutError):
        await again.until(1, timeout=1)  # sem confirmação, só volta depois do ack_wait
    await kernel.close()
    await archiver.close()


@pytest.mark.parametrize("pattern", ["campsverso.w.internal.>", "campsverso.w.world.>"])
async def test_a8_controlador_nao_assina_internal_nem_world(nats: NatsServer, pattern: str) -> None:
    controller = await _connect(nats, "controller")
    with pytest.raises(PermissionDeniedError):
        await controller.subscribe(pattern, _ignore)
    allowed = await controller.subscribe("campsverso.w.agent.camps.>", _ignore)
    await allowed.unsubscribe()
    await controller.close()


async def test_a8_controlador_nao_cria_consumidor_no_stream_internal(nats: NatsServer) -> None:
    await (await _connect(nats, "kernel", manage=True)).close()
    controller = await _connect(nats, "controller")
    with pytest.raises(PermissionDeniedError):
        await controller.consume("campsverso.*.internal.>", "espiao", Collector())
    await controller.close()


async def test_gateway_le_os_quatro_streams_do_avatar(nats: NatsServer) -> None:
    await (await _connect(nats, "kernel", manage=True)).close()
    gateway = await _connect(nats, "gateway")
    for pattern, durable in (
        ("campsverso.w.world.>", "g-world"),
        ("campsverso.w.agent.camps.>", "g-agent"),
        ("campsverso.w.internal.>", "g-internal"),
        ("campsverso.w.observer.>", "g-observer"),
    ):
        consumer = await gateway.consume(pattern, durable, Collector())
        await consumer.unsubscribe()
    with pytest.raises(PermissionDeniedError):  # só o avatar da v0.1 (ADR-0022)
        await gateway.consume("campsverso.w.agent.outro.>", "g-outro", Collector())
    await gateway.close()


async def test_gateway_so_publica_comandos_do_relogio(nats: NatsServer) -> None:
    await (await _connect(nats, "kernel", manage=True)).close()
    gateway = await _connect(nats, "gateway")
    await gateway.publish("campsverso.w.cmd.clock.pause.v1", _event(_ID, 0))
    with pytest.raises(PermissionDeniedError):
        await gateway.publish("campsverso.w.cmd.action.propose.v1", _event(_ID2, 1))
    await gateway.close()


_ID = "01a12d2b-6c1d-7670-9f5b-49c93d5575ea"
_ID2 = "01a12d2b-6c1d-7670-9f5b-49c93d5575eb"


async def _ignore(_: str, __: Envelope) -> None:
    return None


def test_streams_do_ambiente_local() -> None:
    names = {s.name: s for s in STREAMS}
    assert set(names) == {"WORLD", "AGENT", "OBSERVER", "INTERNAL", "COMMANDS"}
    assert names["INTERNAL"].max_age_seconds == 90 * 86400
    assert names["COMMANDS"].subjects == ("campsverso.*.cmd.>",)


def test_caminho_do_repo() -> None:
    assert (REPO / "Makefile").exists()
    assert isinstance(REPO, Path)


async def test_consumidor_ocioso_continua_vivo(nats: NatsServer) -> None:
    """Um stream vazio por vários segundos não pode matar o laço de consumo."""
    kernel = await _connect(nats, "kernel", manage=True)
    archiver, seen = await _connect(nats, "archiver"), Collector()
    await archiver.consume("campsverso.*.observer.>", "teste-ocioso", seen)
    await asyncio.sleep(3)  # três fetches sem nada
    await kernel.publish("campsverso.w.observer.teste.v1", _event("tarde", 0))
    await seen.until(1)
    await kernel.close()
    await archiver.close()
