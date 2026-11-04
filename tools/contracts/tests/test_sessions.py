"""`make sessoes`: turnos, tempo ativo e tokens, sem nada do texto das conversas (ADR-0051)."""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from campsverso_tools.sessions import Turn, credits, main, merge, read_csv, turns


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


def test_turno_gravado_nao_encolhe_quando_a_transcricao_compacta() -> None:
    """Compactar a sessão tira as chamadas antigas do arquivo: o turno volta com zero e não pode
    apagar os números gravados; um turno que cresceu de verdade continua a ser atualizado."""

    def turn(calls: int, marco: str = "") -> Turn:
        start, end = "2026-10-18T20:00-03:00", "2026-10-18T20:09-03:00"
        return Turn("s1", start, end, 9.0, calls, 1, 2, 3, 4, marco)

    saved = [turn(11, "M10+M11")]
    (kept,) = merge(saved, [turn(0)], "M13")
    assert (kept.chamadas, kept.marco) == (11, "M10+M11")
    (grown,) = merge(saved, [turn(12)], "M13")
    assert (grown.chamadas, grown.marco) == (12, "M10+M11")
    (fresh,) = merge([], [turn(0)], "M13")
    assert fresh.marco == "M13"  # um turno novo entra mesmo sem chamada (um pedido só de texto)


def test_ignora_o_contexto_reinserido_com_carimbo_anterior_ao_turno(tmp_path: Path) -> None:
    """Ao compactar, o app regrava a transcrição com mensagens antigas depois do pedido novo,
    com os carimbos originais: elas não contam no turno nem puxam o fim dele para trás."""
    path = tmp_path / "abcdef12-sessao.jsonl"
    path.write_text(
        "\n".join(
            [
                _prompt("10:00:00", "continuando a sessão"),
                _call("09:00:00", "msg-velha", 999),  # reinserida: de antes do turno
                _call("10:01:00", "msg-nova", 10),
            ]
        ),
        encoding="utf-8",
    )
    (turn,) = turns(path)
    assert (turn.chamadas, turn.saida) == (1, 10)
    # O fim é 10:01Z no fuso de quem roda (o CI roda em UTC), não as 09:00Z da reinserida.
    assert datetime.fromisoformat(turn.fim) == datetime(2026, 10, 12, 10, 1, tzinfo=UTC)


def test_creditos_somam_o_que_entrou_o_cartao_e_o_gasto(tmp_path: Path) -> None:
    path = tmp_path / "creditos.csv"
    path.write_text(
        "data,provedor,movimento,usd,brl,iof_brl,saldo_usd,nota\n"
        "2026-10-07,Anthropic,assinatura,,588.42,19.93,,mensal\n"
        "2026-10-18,Anthropic,plano,100.00,,,100.00,da assinatura\n"
        "2026-10-29,OpenRouter,compra,50.00,290.10,10.10,50.00,\n"
        "2026-11-02,Anthropic,compra,30.00,,,58.73,\n"
        "2026-11-02,OpenRouter,saldo,,,,12.50,\n"
        "2026-11-03,Anthropic,compra,1000.00,5800.00,200.00,1040.00,\n",
        encoding="utf-8",
    )
    lines = credits(path)
    # A assinatura não entra na conta da API: só a compra de 1.000 tem o real, a de 30 falta.
    anthropic = "| Anthropic | 1.130,00 | 5.800,00 (faltam 1) | 200,00 | 5.600,00 | 5,60 |"
    assert anthropic + " 1.040,00 | 90,00 |" in lines
    assert "| OpenRouter | 50,00 | 290,10 | 10,10 | 280,00 | 5,60 | 12,50 | 37,50 |" in lines
    assert (
        "| Total | 1.180,00 | 6.090,10 (faltam 1) | 210,10 | 5.880,00 | 5,60 | 1.052,50 | 127,50 |"
        in lines
    )
    assert any("1 pagamento," in line for line in lines)
    assert "R$ 588,42 no cartão, R$ 19,93 de IOF devolvido, R$ 568,49 líquidos." in lines
    assert credits(tmp_path / "nenhum.csv") == []
