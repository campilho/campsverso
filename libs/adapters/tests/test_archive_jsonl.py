"""Arquivo JSONL por mundo e por data simulada, com compressão dos dias antigos (ADR-0043)."""

import gzip
import json
from pathlib import Path
from typing import Any

from campsverso_adapters import JsonlArchive, MemoryTelemetry


def _event(event_id: str, simtime: str | None, world: str = "w") -> dict[str, Any]:
    envelope: dict[str, Any] = {"id": event_id, "worldid": world, "time": "2026-10-12T01:00:00Z"}
    if simtime is not None:
        envelope["simtime"] = simtime
    return envelope


def _ids(path: Path) -> list[str]:
    data = gzip.decompress(path.read_bytes()) if path.suffix == ".gz" else path.read_bytes()
    return [json.loads(line)["id"] for line in data.splitlines()]


def test_um_arquivo_por_mundo_e_data_simulada(tmp_path: Path) -> None:
    archive = JsonlArchive(tmp_path, compress_after_days=7)
    assert archive.append(_event("a", "2026-10-10T23:59:00-03:00"))
    assert archive.append(_event("b", "2026-10-11T00:00:00-03:00"))
    assert archive.append(_event("cmd", None))  # comando: vai para o dia mais recente
    assert archive.append(_event("c", "2026-10-10T08:00:00-03:00", world="outro"))
    archive.close()
    assert _ids(tmp_path / "w" / "2026-10-10.jsonl") == ["a"]
    assert _ids(tmp_path / "w" / "2026-10-11.jsonl") == ["b", "cmd"]
    assert _ids(tmp_path / "outro" / "2026-10-10.jsonl") == ["c"]


def test_entrega_repetida_e_descartada_mesmo_depois_de_reabrir(tmp_path: Path) -> None:
    archive = JsonlArchive(tmp_path, compress_after_days=7)
    archive.append(_event("a", "2026-10-10T08:00:00-03:00"))
    assert not archive.append(_event("a", "2026-10-10T08:00:00-03:00"))
    archive.close()
    again = JsonlArchive(tmp_path, compress_after_days=7)
    assert not again.append(_event("a", "2026-10-10T08:00:00-03:00"))
    again.close()
    assert _ids(tmp_path / "w" / "2026-10-10.jsonl") == ["a"]


def test_linha_cortada_pela_queda_e_removida_ao_abrir(tmp_path: Path) -> None:
    day = tmp_path / "w" / "2026-10-10.jsonl"
    day.parent.mkdir(parents=True)
    day.write_bytes(b'{"id":"a","worldid":"w"}\n{"id":"b","wor')
    telemetry = MemoryTelemetry()
    archive = JsonlArchive(tmp_path, compress_after_days=7, telemetry=telemetry)
    archive.append(_event("b", "2026-10-10T09:00:00-03:00"))  # reentregue: não fora confirmado
    archive.close()
    assert _ids(day) == ["a", "b"]
    assert telemetry.events("warning") == ["archive.torn_line_removed"]


def test_dias_antigos_sao_comprimidos_sem_perder_nada(tmp_path: Path) -> None:
    archive = JsonlArchive(tmp_path, compress_after_days=2)
    for day in range(10, 15):
        archive.append(_event(f"e{day}", f"2026-10-{day}T08:00:00-03:00"))
    archive.flush()
    files = sorted(p.name for p in (tmp_path / "w").iterdir())
    assert files == [
        "2026-10-10.jsonl.gz",
        "2026-10-11.jsonl.gz",
        "2026-10-12.jsonl",
        "2026-10-13.jsonl",
        "2026-10-14.jsonl",
    ]
    archive.append(_event("atrasado", "2026-10-10T09:00:00-03:00"))  # novo membro gzip
    archive.close()
    assert _ids(tmp_path / "w" / "2026-10-10.jsonl.gz") == ["e10", "atrasado"]
