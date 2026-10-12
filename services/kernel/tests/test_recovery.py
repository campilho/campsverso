"""Snapshot completo e recuperação com o diário de entradas (plano do M2 §1, §4)."""

import json
from collections.abc import Mapping, Sequence
from typing import Any

import pytest

from campsverso_adapters import (
    ContractValidator,
    FakeWallClock,
    InMemoryBus,
    MemoryBlobStore,
    MemoryTelemetry,
    SequentialUuid7Ids,
    SqliteWorldStore,
)
from campsverso_kernel import Engine, KernelService, RecoveryError, open_world, run_version
from campsverso_kernel.core import KernelCore, WorldConfig
from campsverso_kernel.snapshot import SnapshotError, decode, document, encode, restore
from campsverso_kernel.testing import RULES, START, LabCartridge, command, make_core
from campsverso_kernel.version import RunVersion
from campsverso_ports import BusUnavailableError, Envelope, EnvelopeValidator, EventBus

VERSION = run_version("lab", 60, {"lab": LabCartridge()})


def _facts(core: KernelCore, ticks: int) -> list[tuple[int, int, str, str]]:
    out: list[tuple[int, int, str, str]] = []
    for _ in range(ticks):
        core.step()
        out += [(f.seq, f.tick, f.type, json.dumps(f.data, sort_keys=True)) for f in core.drain()]
    return out


def _doc(core: KernelCore) -> dict[str, Any]:
    return document(core, VERSION.as_dict(), core.log.next_seq)


def _busy_core() -> KernelCore:
    """Laboratório com ação em curso, trajeto pela metade, regra contribuindo e fome alta."""
    core = make_core()
    core.start()
    core.step()
    core.submit(command("move", {"target": {"x": 3, "y": 1}}))
    core.step()  # o trajeto começa; o snapshot cai no meio dele
    core.drain()
    return core


def test_snapshot_de_ida_e_volta_continua_igual() -> None:
    original = _busy_core()
    doc = decode(encode(_doc(original)))
    copy = restore(original.definition, original.config, doc)
    assert copy.export_state() == original.export_state()
    copy.submit(command("touch"))
    original.submit(command("touch"))
    assert _facts(copy, 1500) == _facts(original, 1500)  # passa pela noite, sono e manhã
    assert copy.export_state() == original.export_state()


def test_snapshot_recusa_mundo_com_outra_seed() -> None:
    core = _busy_core()
    other = WorldConfig("lab-01", 8, START)
    with pytest.raises(SnapshotError, match="seed"):
        restore(core.definition, other, decode(encode(_doc(core))))


# ----------------------------------------------------------------- serviço e recuperação


class Lab:
    """Um mundo de laboratório com estado durável em memória, que pode "cair" a qualquer hora."""

    def __init__(
        self,
        bus: EventBus | None = None,
        version: RunVersion = VERSION,
        validator: EnvelopeValidator | None = None,
    ) -> None:
        self.validator = validator
        self.store = SqliteWorldStore(":memory:")
        self.blobs = MemoryBlobStore()
        self.bus = InMemoryBus()
        self.telemetry = MemoryTelemetry()
        self.ids = SequentialUuid7Ids()  # UUIDv7 de verdade nunca se repetem entre processos
        self.service = self._open(bus or self.bus, version)

    def _open(self, bus: EventBus, version: RunVersion) -> KernelService:
        lab = make_core()
        engine, self.recovery = open_world(
            lab.definition,
            lab.config,
            RULES,
            version,
            self.store,
            self.blobs,
            rules_source="test",
            validator=self.validator,
        )
        return KernelService(
            engine,
            bus,
            FakeWallClock(),
            self.ids,
            self.store,
            self.blobs,
            self.telemetry,
            keep_full=3,
        )

    def crash_and_reopen(self, version: RunVersion = VERSION) -> KernelService:
        """O processo morre sem parar com elegância; o que estava só na memória se perde."""
        self.service = self._open(self.bus, version)
        return self.service

    @property
    def events(self) -> list[Envelope]:
        return [e for _, e in self.bus.published]


def _canonical(events: Sequence[Mapping[str, Any]]) -> list[tuple[Any, ...]]:
    return [(e["seq"], e["tick"], e["type"], json.dumps(e["data"], sort_keys=True)) for e in events]


async def _script(service: KernelService, ticks: int) -> None:
    """Move, toca a caixa depois do snapshot do tick 60 e segue até `ticks`."""
    await service.run_ticks(5)
    service.submit(command("move", {"target": {"x": 3, "y": 1}}))
    await service.run_ticks(75)
    service.submit(command("touch"))
    await service.run_ticks(ticks - 80)


async def test_queda_no_meio_nao_perde_nem_duplica() -> None:
    lab = Lab()
    await lab.service.start()
    await _script(lab.service, 100)
    service = lab.crash_and_reopen()
    assert lab.recovery is not None
    assert lab.recovery.snapshot_tick == 60
    assert lab.recovery.inputs == 1  # o touch, gravado no diário depois do snapshot
    assert lab.recovery.tick >= 82  # última gravação: o fim do touch (os ticks quietos não gravam)
    assert lab.recovery.facts > 0
    await service.start()
    await service.run_ticks(1000 - service.core.tick)

    reference = Lab()
    await reference.service.start()
    await _script(reference.service, 1000)
    assert _canonical(lab.events) == _canonical(reference.events)
    assert lab.service.core.export_state() == reference.service.core.export_state()


async def test_comando_ja_gravado_e_entregue_de_novo_e_ignorado() -> None:
    lab = Lab()
    await lab.service.start()
    move = command("move", {"target": {"x": 3, "y": 1}})
    assert lab.service.submit(move) is True
    service = lab.crash_and_reopen()
    await service.start()
    assert service.submit(move) is False  # o JetStream reentregou o que não foi confirmado


async def test_recuperacao_denuncia_fato_adulterado() -> None:
    lab = Lab()
    await lab.service.start()
    await lab.service.run_ticks(90)
    row = lab.store.outbox_from(lab.store.snapshots()[-1].next_seq)[0]
    tampered = {**row.envelope, "data": {**row.envelope["data"], "value": 99.0}}
    lab.store._db.execute(  # pyright: ignore[reportPrivateUsage]
        "UPDATE outbox SET envelope = ? WHERE seq = ?", (json.dumps(tampered), row.seq)
    )
    with pytest.raises(RecoveryError, match="determinismo quebrado"):
        lab.crash_and_reopen()


async def test_recuperacao_recusa_incrementais_de_outra_versao() -> None:
    lab = Lab()
    await lab.service.start()
    await lab.service.run_ticks(90)
    other = RunVersion("outro-codigo", VERSION.cartridges, VERSION.snapshot_every)
    with pytest.raises(RecoveryError, match="outra versão"):
        lab.crash_and_reopen(other)


async def test_parar_com_elegancia_permite_trocar_a_versao() -> None:
    lab = Lab()
    await lab.service.start()
    await lab.service.run_ticks(90)
    await lab.service.stop()  # snapshot no tick 90, sem incrementais depois
    other = RunVersion("outro-codigo", VERSION.cartridges, VERSION.snapshot_every)
    service = lab.crash_and_reopen(other)
    assert service.core.tick == 90
    kinds = [e["type"] for e in lab.events]
    assert kinds.count("campsverso.world.snapshot.created.v1") == 3  # 0, 60 e a parada


async def test_snapshots_antigos_saem_mas_o_inicial_fica() -> None:
    lab = Lab()
    await lab.service.start()
    await lab.service.run_ticks(60 * 6)
    ticks = [s.tick for s in lab.store.snapshots()]
    assert ticks == [0, 240, 300, 360]  # keep_full=3 mais o inicial
    assert len(lab.blobs.blobs) == 4


class FlakyBus(InMemoryBus):
    """Cai depois de `limit` publicações, até alguém religar."""

    def __init__(self, limit: int) -> None:
        super().__init__()
        self.limit = limit

    async def publish(self, subject: str, envelope: Envelope) -> None:
        if self.limit <= 0:
            raise BusUnavailableError("barramento fora")
        self.limit -= 1
        await super().publish(subject, envelope)


async def test_barramento_fora_o_mundo_segue_e_o_outbox_alcanca_depois() -> None:
    bus = FlakyBus(limit=10)
    lab = Lab(bus)
    await lab.service.start()
    await lab.service.run_ticks(200)
    assert len(bus.published) == 10
    assert "kernel.publish_failed" in lab.telemetry.events("warning")
    assert len(lab.store.unpublished(1000)) > 0
    bus.limit = 10_000
    lab.service._retry_at = 0  # pyright: ignore[reportPrivateUsage]
    await lab.service.publish_pending()
    assert lab.store.unpublished(1000) == []
    seqs = [e["seq"] for _, e in bus.published]
    assert seqs == list(range(len(seqs)))  # em ordem, sem buraco nem repetição


async def test_republicar_depois_da_queda_usa_os_mesmos_ids() -> None:
    bus = FlakyBus(limit=0)  # grava tudo, publica nada
    lab = Lab(bus)
    await lab.service.start()
    await lab.service.run_ticks(30)
    recorded = {row.seq: row.envelope["id"] for row in lab.store.unpublished(1000)}
    lab.crash_and_reopen()
    await lab.service.start()
    published = {e["seq"]: e["id"] for e in lab.events}
    assert {seq: published[seq] for seq in recorded} == recorded  # o JetStream deduplica pelo id


def test_motor_agenda_snapshot_a_cada_bloco() -> None:
    engine = Engine(make_core(), VERSION)
    engine.core.start()
    engine.core.drain()
    snapshots = [s for s in (engine.step() for _ in range(130)) if s is not None]
    assert [s.tick for s in snapshots] == [60, 120]
    assert snapshots[0].ref == f"lab-01/snapshots/{snapshots[0].snapshot_id}.json"
    restored = restore(engine.core.definition, engine.core.config, decode(snapshots[1].data))
    assert restored.log.next_seq == snapshots[1].next_seq


def _set_scale(command_id: str, reason: str) -> dict[str, Any]:
    return {
        "specversion": "1.0",
        "id": command_id,
        "source": "/operator/teste",
        "type": "campsverso.cmd.clock.set_scale.v1",
        "time": "2026-10-12T01:00:00Z",
        "datacontenttype": "application/json",
        "dataschema": "contracts://commands/clock/set_scale.v1",
        "worldid": "lab-01",
        "cartridge": "lab",
        "seq": 0,
        "actor": "human/operator",
        "provenance": "simulated",
        "visibility": "observer",
        "data": {"scale": 500, "reason": reason},
    }


async def test_comando_fora_do_contrato_e_recusado_e_reexecutado_igual() -> None:
    lab = Lab(validator=ContractValidator())
    await lab.service.start()
    ids = SequentialUuid7Ids()
    lab.service.submit(_set_scale(ids.new_id(), "porque sim"))  # reason fora do enum
    lab.service.submit({"type": "lixo"})  # sem id nem tipo de comando: só o diário guarda
    lab.service.submit(_set_scale(ids.new_id(), "operator"))
    await lab.service.run_ticks(10)
    rejected = [e["data"] for e in lab.events if e["type"].endswith("command.rejected.v1")]
    assert [r["reason"] for r in rejected] == ["invalid_command"]
    assert "reason" in rejected[0]["detail"]
    assert lab.service.core.scale == 500  # só o comando válido mudou a escala
    service = lab.crash_and_reopen()
    assert lab.recovery is not None
    assert lab.recovery.inputs == 3  # as três entradas reexecutadas, com os mesmos fatos
    assert service.core.scale == 500
