"""A calibração do revisor sem a API (ADR-0083, parte 3): os casos, a conta e o relatório."""

from campsverso_tools.revisor import Case, load_cases, render, score

PLANTED = Case("x", 9, "t", "", "", "diff", ("cartridges/office/sim/config.py",), "o dia errado")
CLEAN = Case("y", 9, "t", "", "", "diff", (), "")


def test_os_casos_tem_tres_defeitos_plantados_e_um_limpo() -> None:
    cases = load_cases()
    assert [c.name for c in cases] == ["teste-afrouxado", "constituicao", "erro-de-logica", "limpo"]
    assert [bool(c.files) for c in cases] == [True, True, True, False]
    for case in cases:
        assert case.diff.startswith("diff --git")
        for name in case.files:  # o defeito está num arquivo que o diff muda
            assert f"+++ b/{name}" in case.diff


def test_a_conta_acha_pelo_arquivo_e_separa_o_que_e_a_mais() -> None:
    body = (
        "Resumo.\n\n"
        "1. **grave** · cartridges/office/sim/config.py:84 · quinta.\n"
        "2. **média** · services/x.py:3 · outra coisa.\n"
        "3. **leve** · services/y.py:1 · nome."
    )
    assert score(PLANTED, body) == (True, 1)
    assert score(PLANTED, "1. **leve** · cartridges/office/sim/config.py:84 · quinta.") == (
        False,
        0,
    )
    assert score(CLEAN, body) == (None, 2)


def test_o_relatorio_tem_a_tabela_e_as_revisoes() -> None:
    saved = {
        "date": "2026-11-21T12:00:00+00:00",
        "results": [
            {
                "case": "x",
                "model": "google/gemini-4-neon",
                "verdict": "devolver",
                "raw": "Veredito: devolver\n\nAchei.",
                "hit": True,
                "extra": 0,
                "cost_usd": 0.02,
            },
            {"case": "y", "model": "google/gemini-4-neon", "error": "sem resposta"},
        ],
    }
    text = render(saved, [PLANTED, CLEAN])
    assert "| x | devolver | devolver · achou sim · a mais 0 |" in text
    assert "| y | mesclar | sem resposta |" in text
    assert "| `google/gemini-4-neon` | 1 de 1 | 0 | 1 de 1 | US$ 0.020 |" in text
    assert "<summary>x · google/gemini-4-neon · devolver</summary>" in text
