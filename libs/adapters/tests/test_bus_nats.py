"""NatsBus contra um NATS de verdade, com o nats.conf do repositório (escopo A8; ADR-0017)."""

import asyncio
import random
import sys
import time
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
    await again.until(1, timeout=2)  # quem retoma recebe na hora, sem esperar o ack_wait
    assert [e["id"] for e in again.received] == ["b-0"]
    await kernel.close()
    await archiver.close()


# O processo que cai: consome, recebe o lote com o seq 1 e nunca confirma, até o SIGKILL.
_STUCK = """
import asyncio, sys
from campsverso_adapters import NatsBus, load_env
from campsverso_testkit.nats_server import REPO

async def main(url, user, password, durable):
    streams = load_env(REPO / "config" / "env" / "local.yaml", root=REPO).nats.streams
    bus = await NatsBus.connect(url, user=user, password=password, name="caido", streams=streams)

    async def stuck(batch):
        if any(e["seq"] == 1 for _, e in batch):
            print("recebi", flush=True)
            await asyncio.Event().wait()

    await bus.consume("campsverso.*.world.>", durable, stuck)
    await asyncio.Event().wait()

asyncio.run(main(*sys.argv[1:]))
"""


@pytest.mark.parametrize("user", ["gateway", "perception", "budget", "codehost"])
async def test_o_lote_em_voo_de_quem_caiu_volta_na_hora_e_em_ordem(
    nats: NatsServer, user: str
) -> None:
    """ADR-0085: o processo cai (SIGKILL) com um lote recebido e sem confirmar; o mundo segue
    publicando; o processo que volta recebe o lote antes do que é novo, e não 30 s depois."""
    kernel = await _connect(nats, "kernel", manage=True)
    for seq in range(3):
        await kernel.publish("campsverso.w.world.teste.v1", _event(f"v-{seq}", seq))
    durable = f"teste-voo-{user}"
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        "-c",
        _STUCK,
        nats.url,
        user,
        nats.passwords[user],
        durable,
        stdout=asyncio.subprocess.PIPE,
    )
    assert process.stdout is not None
    async with asyncio.timeout(15):
        assert (await process.stdout.readline()).strip() == b"recebi"
    process.kill()
    await process.wait()
    for seq in range(3, 5):
        await kernel.publish("campsverso.w.world.teste.v1", _event(f"v-{seq}", seq))
    back, seen = await _connect(nats, user), Collector()
    started = time.monotonic()
    await back.consume("campsverso.*.world.>", durable, seen)
    await seen.until(4, timeout=5)
    assert time.monotonic() - started < 5  # bem antes do ack_wait de 30 s
    seqs = [e["seq"] for e in seen.received]
    assert seqs == sorted(seqs)
    assert seqs[-2:] == [3, 4]
    assert 1 in seqs  # o lote em voo voltou
    await kernel.close()
    await back.close()


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
    helper = await gateway.consume("campsverso.w.agent.dita.>", "g-dita", Collector())
    await helper.unsubscribe()  # o operador vê todos os avatares (ADR-0072)
    await gateway.close()


async def test_os_ajudantes_so_leem_o_que_e_de_cada_um(nats: NatsServer) -> None:
    """ADR-0072: o runner dos ajudantes lê a percepção deles, e nunca a do Camps."""
    await (await _connect(nats, "kernel", manage=True)).close()
    helpers = await _connect(nats, "helpers")
    for avatar in ("dita", "ze-graudo", "nina", "seu-bento", "tiao"):
        consumer = await helpers.consume(
            f"campsverso.w.agent.{avatar}.>", f"h-{avatar}", Collector()
        )
        await consumer.unsubscribe()
    for pattern in (
        "campsverso.w.agent.camps.>",
        "campsverso.w.world.>",
        "campsverso.w.internal.>",
    ):
        with pytest.raises(PermissionDeniedError):
            await helpers.subscribe(pattern, _ignore)
    with pytest.raises(PermissionDeniedError):
        await helpers.consume("campsverso.w.agent.camps.>", "h-espiao", Collector())
    await helpers.close()


async def test_gateway_so_publica_relogio_e_comandos_do_humano(nats: NatsServer) -> None:
    await (await _connect(nats, "kernel", manage=True)).close()
    gateway = await _connect(nats, "gateway")
    await gateway.publish("campsverso.w.cmd.clock.pause.v1", _event(_ID, 0))
    await gateway.publish("campsverso.w.cmd.action.propose.v1", _event(_ID2, 1))
    with pytest.raises(PermissionDeniedError):  # regras ocultas: nunca pela UI
        await gateway.publish("campsverso.w.cmd.rules.toggle.v1", _event(_ID3, 2))
    await gateway.close()


_ID = "01a12d2b-6c1d-7670-9f5b-49c93d5575ea"
_ID2 = "01a12d2b-6c1d-7670-9f5b-49c93d5575eb"
_ID3 = "01a12d2b-6c1d-7670-9f5b-49c93d5575ec"


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


async def test_rajada_chega_inteira_e_na_hora(nats: NatsServer) -> None:
    """Dois fatos do mesmo tick (o `accepted` e o `moved` de um andar) chegam juntos e logo.

    Com o fetch de 100 e prazo de 1 s, o segundo ia para um pedido que o nats-py já tinha largado,
    e o fetch seguinte o pegava e ficava esperando completar o lote: o trajeto do gerente chegava à
    tela até 1 s depois, junto com a chegada (o clique a 1x no escritório, 20/nov)."""
    kernel = await _connect(nats, "kernel", manage=True)
    gateway = await _connect(nats, "operator")
    arrived: dict[int, float] = {}

    async def note(batch: Sequence[tuple[str, Envelope]]) -> None:
        for _, envelope in batch:
            arrived[int(envelope["seq"])] = time.monotonic()

    await gateway.consume("campsverso.*.world.>", "teste-rajada", note)
    rng = random.Random(3)
    sent: dict[int, float] = {}
    for burst in range(12):
        await asyncio.sleep(rng.uniform(0.3, 1.3))  # às vezes depois do prazo do fetch
        for seq in (2 * burst, 2 * burst + 1):
            sent[seq] = time.monotonic()
            await kernel.publish("campsverso.w.world.teste.v1", _event(f"rajada-{seq}", seq))
            await asyncio.sleep(0.001)
    async with asyncio.timeout(5):
        while len(arrived) < len(sent):
            await asyncio.sleep(0.01)
    delays = {seq: round(arrived[seq] - sent[seq], 3) for seq in sent}
    late = {seq: delay for seq, delay in delays.items() if delay > 0.25}
    assert late == {}  # o seq e o atraso, em segundos, de quem chegou tarde
    await kernel.close()
    await gateway.close()
