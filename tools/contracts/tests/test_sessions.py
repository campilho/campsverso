"""`make sessoes`: turnos, tempo ativo e tokens, sem nada do texto das conversas (ADR-0051)."""

import json
from pathlib import Path
from typing import Any

from campsverso_tools.sessions import main, read_csv, turns


def _line(kind: str, stamp: str, **extra: Any) -> str:
    return json.dumps({"type": kind, "timestamp": f"2026-10-12T{stamp}Z", **extra})


def _prompt(stamp: str, text: str) -> str:
    return _line("user", stamp, message={"role": "user", "content": text})


def _call(stamp: str, call: str, out: int) -> str:
    usage = {
        "input_tokens": 2,
        "output_tokens": out,
        "cache_read_input_tokens": 1000,
        "cache_creation_input_tokens": 10,
    }
    return _line("assistant", stamp, message={"id": call, "usage": usage})


def _tool_result(stamp: str) -> str:
    content = [{"type": "tool_result", "content": "ok"}]
    return _line("user", stamp, message={"role": "user", "content": content})


SESSION = [
    _prompt("10:00:00", "segredo da conversa: plantar abóbora"),
    _call("10:00:30", "msg-1", 100),
    _call("10:00:31", "msg-1", 100),  # o mesmo pedido, outro bloco: conta uma vez
    _tool_result("10:01:00"),
    _call("10:02:00", "msg-2", 50),
    _tool_result("10:20:00"),  # 18 min esperando uma aprovação: fora do tempo ativo
    _call("10:21:00", "msg-3", 25),
    _line("user", "10:30:00", isMeta=True, message={"content": "aviso"}),
    _prompt("10:30:00", "<command-name>/compact</command-name>"),
    _prompt("11:00:00", "segundo pedido"),
    _call("11:03:00", "msg-4", 10),
]


def _write(folder: Path, lines: list[str]) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "abcdef12-0000.jsonl"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def test_turnos_tempo_ativo_e_tokens(tmp_path: Path) -> None:
    first, second = turns(_write(tmp_path, SESSION))
    assert first.sessao == "abcdef12"
    assert (first.chamadas, first.saida, first.cache_lido) == (3, 175, 3000)
    assert first.minutos_ativos == 3.0  # 10:00 a 10:02, mais 10:20 a 10:21
    assert (second.chamadas, second.minutos_ativos) == (1, 3.0)


def test_grava_so_numeros_e_nao_duplica(tmp_path: Path) -> None:
    folder, out = tmp_path / "sessoes", tmp_path / "custos"
    _write(folder, SESSION)
    main(["--dir", str(folder), "--out", str(out), "--marco", "M5"])
    _write(folder, [*SESSION, _call("11:04:00", "msg-5", 5)])  # o turno em andamento cresceu
    main(["--dir", str(folder), "--out", str(out), "--marco", "M6"])
    rows = read_csv(out / "sessoes.csv")
    assert [(r.chamadas, r.marco) for r in rows] == [(3, "M5"), (2, "M5")]  # o marco gravado fica
    written = (out / "sessoes.csv").read_text(encoding="utf-8") + (out / "README.md").read_text(
        encoding="utf-8"
    )
    assert "segredo" not in written
    assert "abóbora" not in written
    assert "| M5 | 2 |" in (out / "README.md").read_text(encoding="utf-8")
