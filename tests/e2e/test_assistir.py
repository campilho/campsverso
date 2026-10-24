"""O modo de assistir (ADR-0068): a tela de uma corrida montada do arquivo de eventos dela, seguida
enquanto cresce ou tocada num relógio de reprodução, sem barramento e sem kernel."""

import json
from pathlib import Path
from typing import Any, cast

from campsverso_adapters import JsonTelemetry, Uuid7Ids
from campsverso_gateway.service import NOTEBOOK, PROJECTED, SKIPPED
from campsverso_gateway.state import observer_state
from campsverso_gateway.watch import WatchService
from campsverso_ports import Envelope
from campsverso_testkit.pipeline import Pipeline
from campsverso_world_view import Projection


async def _day() -> list[dict[str, Any]]:
    pipeline = Pipeline()
    await pipeline.start()
    await pipeline.run_days(1)
    return [dict(e) for e in pipeline.envelopes]


def _write(folder: Path, envelopes: list[dict[str, Any]], *, done: bool) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "archive.jsonl").write_text(
        "".join(json.dumps(e) + "\n" for e in envelopes), encoding="utf-8"
    )
    (folder / "estado.json").write_text(json.dumps({"day": 1, "done": done}), encoding="utf-8")


def _service(arena: Path) -> WatchService:
    return WatchService(arena, Uuid7Ids(), JsonTelemetry("teste"))


async def test_a_corrida_gravada_toca_no_relogio_de_reproducao(tmp_path: Path) -> None:
    envelopes = await _day()
    _write(tmp_path / "script", envelopes, done=True)
    service = _service(tmp_path)
    assert service.runs() == [{"name": "script", "day": 1, "done": True}]
    assert service.cartridge() == "farm_camps"
    run = service._runs["script"]  # pyright: ignore[reportPrivateUsage]
    service.advance(run, 30)  # 30 s a um dia por minuto: meio dia, 720 ticks
    first = service._state(run)  # pyright: ignore[reportPrivateUsage]
    assert 0 < first["tick"] <= 720
    assert first["clock"] == {"mode": "continuous", "scale": 1440.0, "paused": False}
    run.paused = True
    service.advance(run, 600)
    assert service._state(run)["tick"] == first["tick"]  # pyright: ignore[reportPrivateUsage]
    run.paused, run.mode = False, "max"
    service.advance(run, 0)
    whole = service._state(run)  # pyright: ignore[reportPrivateUsage]
    kernel = [e for e in envelopes if str(e["source"]).startswith("/kernel/")]
    assert whole["tick"] == max(
        int(e.get("tick") or 0) for e in kernel if e["visibility"] != "internal"
    )
    assert "camps" in whole["entities"]


async def test_a_corrida_em_andamento_e_seguida_enquanto_o_arquivo_cresce(tmp_path: Path) -> None:
    envelopes = await _day()
    half = len(envelopes) // 2
    folder = tmp_path / "haiku"
    _write(folder, envelopes[:half], done=False)
    service = _service(tmp_path)
    run = service._runs["haiku"]  # pyright: ignore[reportPrivateUsage]
    service.advance(run, 0)
    middle = service._state(run)["tick"]  # pyright: ignore[reportPrivateUsage]
    rest = "".join(json.dumps(e) + "\n" for e in envelopes[half:])
    with (folder / "archive.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(rest[: len(rest) // 2])  # uma linha pela metade fica para depois
        handle.flush()
        service.advance(run, 0)
        handle.write(rest[len(rest) // 2 :])
    service.advance(run, 0)
    assert service._state(run)["tick"] > middle  # pyright: ignore[reportPrivateUsage]
    assert run.offset == (folder / "archive.jsonl").stat().st_size


async def test_o_estado_montado_do_arquivo_e_o_mesmo_do_barramento(tmp_path: Path) -> None:
    """Assistir monta do arquivo a mesma tela que o gateway monta do barramento: a projeção do
    gateway ao vivo recebe os streams world e agent (menos a foto da percepção) e o caderno."""
    envelopes = await _day()
    live = Projection()
    for envelope in envelopes:
        stream = str(envelope["visibility"])
        if envelope["type"] in SKIPPED:
            continue
        if stream in PROJECTED or str(envelope["type"]).startswith(NOTEBOOK):
            live.apply(stream, cast(Envelope, envelope))
    _write(tmp_path / "script", envelopes, done=True)
    service = _service(tmp_path)
    run = service._runs["script"]  # pyright: ignore[reportPrivateUsage]
    run.mode = "max"
    service.advance(run, 0)
    watched = service._state(run)  # pyright: ignore[reportPrivateUsage]
    expected = observer_state(live)
    watched.pop("clock")
    expected.pop("clock")
    assert watched == expected
