"""WorldStore em SQLite e BlobStore em disco (plano do M2 §1)."""

from pathlib import Path

import pytest

from campsverso_adapters import DiskBlobStore, SqliteWorldStore
from campsverso_ports import Commit, InputRow, OutboxRow, SnapshotRef


def _row(seq: int) -> OutboxRow:
    return OutboxRow(seq, "campsverso.w.world.x.v1", {"id": f"id-{seq}", "seq": seq})


def _snapshot(tick: int, next_seq: int) -> SnapshotRef:
    return SnapshotRef(f"w/snapshots/t{tick}.json", tick, "0" * 64, next_seq, 1, "v1")


def test_mundo_novo_nao_tem_estado(tmp_path: Path) -> None:
    store = SqliteWorldStore(tmp_path / "w" / "world.sqlite")
    assert store.state() is None
    assert store.snapshots() == []


def test_commit_grava_tudo_junto_e_sobrevive_a_reabrir(tmp_path: Path) -> None:
    path = tmp_path / "world.sqlite"
    store = SqliteWorldStore(path)
    command = {"id": "cmd-1", "type": "campsverso.cmd.action.propose.v1"}
    store.commit(Commit(0, "v1", outbox=[_row(0), _row(1)], snapshot=_snapshot(0, 2)))
    store.commit(
        Commit(5, "v1", inputs=[InputRow(1, 5, "command", "cmd-1", command)], outbox=[_row(2)])
    )
    store.close()
    store = SqliteWorldStore(path)
    state = store.state()
    assert state is not None
    assert (state.tick, state.version, state.next_seq, state.next_input) == (5, "v1", 3, 2)
    assert store.has_command("cmd-1")
    assert not store.has_command("cmd-2")
    assert store.inputs_from(1)[0].envelope == command
    assert [r.seq for r in store.outbox_from(1)] == [1, 2]


def test_commit_com_erro_nao_grava_nada(tmp_path: Path) -> None:
    store = SqliteWorldStore(tmp_path / "world.sqlite")
    store.commit(Commit(0, "v1", outbox=[_row(0)]))
    with pytest.raises(Exception, match="UNIQUE"):
        store.commit(Commit(1, "v1", outbox=[_row(1), _row(0)]))
    state = store.state()
    assert state is not None
    assert (state.tick, state.next_seq) == (0, 1)


def test_publicacao_e_poda_do_outbox() -> None:
    store = SqliteWorldStore(":memory:")
    store.commit(Commit(0, "v1", outbox=[_row(s) for s in range(5)], snapshot=_snapshot(0, 5)))
    store.mark_published(2)
    assert [r.seq for r in store.unpublished(10)] == [3, 4]
    store.prune_outbox(before_seq=4)
    assert [r.seq for r in store.outbox_from(0)] == [3, 4]  # não publicados nunca saem
    assert store.recent_ids(1) == [(4, "id-4")]
    store.commit(Commit(9, "v1", snapshot=_snapshot(9, 5)))
    store.forget_snapshot("w/snapshots/t0.json")
    assert [s.tick for s in store.snapshots()] == [9]


def test_blobs_no_disco_gravam_inteiros_e_nao_saem_da_raiz(tmp_path: Path) -> None:
    blobs = DiskBlobStore(tmp_path)
    blobs.put("w/snapshots/t1.json", b"{}")
    assert (tmp_path / "w" / "snapshots" / "t1.json").read_bytes() == b"{}"
    assert blobs.get("w/snapshots/t1.json") == b"{}"
    assert list((tmp_path / "w" / "snapshots").iterdir()) == [tmp_path / "w/snapshots/t1.json"]
    blobs.delete("w/snapshots/t1.json")
    blobs.delete("w/snapshots/t1.json")  # apagar de novo não é erro
    with pytest.raises(ValueError, match="fora da raiz"):
        blobs.put("../fora.json", b"x")
