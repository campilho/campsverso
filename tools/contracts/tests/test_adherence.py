"""A aderência ao procedimento (ADR-0074, decisão 35), com corridas sintéticas."""

import json
from pathlib import Path
from typing import Any

from campsverso_tools.adherence import adhere, suspect_of, verdict_of
from campsverso_tools.arena import experiments_of, main

DAY = 1440


def ev(tick: int, kind: str, /, **data: Any) -> dict[str, Any]:
    return {
        "source": "/kernel/w",
        "seq": 0,
        "tick": tick,
        "type": f"campsverso.{kind}",
        "time": "2026-11-08T01:00:00Z",
        "data": data,
    }


def act(tick: int, action: str, avatar: str = "camps", **params: Any) -> dict[str, Any]:
    return ev(tick, "action.completed.v1", avatar_id=avatar, action=action, params=params)


def note(day: int, text: str) -> dict[str, Any]:
    return ev((day - 1) * DAY + 100, "memory.noted.v1", avatar_id="camps", day=day, text=text)


def night(day: int, **data: Any) -> dict[str, Any]:
    return ev(day * DAY - 10, "memory.reflected.v1", avatar_id="camps", day=day, **data)


def trial(suspect: str, a: str, b: str) -> dict[str, str]:
    return {
        "hypothesis": f"[{suspect}] rabanete leva menos dias quando perto.",
        "test": f"Par: {a} (com) e {b} (sem), rabanete, plantio no dia 2. Veredito quando...",
        "prediction": f"{a} amadurece pelo menos 2 dias antes de {b}.",
    }


def test_a_suspeita_sai_dos_colchetes_do_comeco() -> None:
    assert suspect_of("[adubo] o rabanete adubado leva menos.") == "adubo"
    assert suspect_of("  [antes] depois de cenoura leva mais.") == "antes"
    assert suspect_of("[cultura anterior] leva mais.") == "antes"
    assert suspect_of("[estação] no verão leva o dobro.") == "estação"
    assert suspect_of("[lugar do canteiro] perto do poço leva menos.") == "lugar"
    assert suspect_of("[perto da água] leva menos.") == "lugar"
    assert suspect_of("[período] leva menos.") == "outra"  # "rio" só como palavra
    assert suspect_of("[sorte] leva menos.") == "outra"
    assert suspect_of("O rabanete [adubo] leva menos.") is None  # só no começo
    assert suspect_of("Sem colchetes.") is None


def test_o_veredito_pela_primeira_palavra() -> None:
    assert verdict_of("cumpriu") == "cumpriu"
    assert verdict_of("Falhou: os dois levaram 3 dias") == "falhou"
    assert verdict_of("inconclusivo") == "inconclusivo"
    assert verdict_of("talvez") == "outra"


def test_o_par_e_os_formatos_contados_do_arquivo() -> None:
    """Três experimentos: um par certo e com veredito, um par com a rega diferente, e um com
    os canteiros plantados em dias diferentes; as anotações HOJE: e VI: por dia."""
    envelopes = [
        note(1, "HOJE: plantar rabanete. PAR: nenhum."),
        night(1, summary="s", beliefs=[], experiment=trial("adubo", "plot-001", "plot-002")),
        note(2, "HOJE: o par. PAR: plot-001 e plot-002."),
        note(2, "HOJE: de novo, no mesmo dia."),
        act(DAY + 10, "plant", target="plot-001", crop="rabanete"),
        act(DAY + 20, "plant", target="plot-002", crop="rabanete"),
        act(DAY + 30, "water", target="plot-001"),
        act(DAY + 40, "water", target="plot-002"),
        act(DAY + 50, "water", target="plot-009", avatar="tiao"),  # outro avatar não conta
        act(2 * DAY + 30, "water", target="plot-001"),
        act(2 * DAY + 40, "water", target="plot-002"),
        ev(3 * DAY + 5, "farm.crop.matured.v1", plot_id="plot-001", day=4),
        act(3 * DAY + 30, "water", target="plot-002"),  # depois do fim do primeiro: não conta
        note(4, "VI: plot-001 amadureceu no dia 4, esperado 3."),
        night(2, summary="s", beliefs=[]),  # o par crescendo: o mesmo experimento, sem registro
        night(
            4,
            summary="s",
            beliefs=[],
            experiment_result="cumpriu",
            experiment=trial("lugar", "plot-003", "plot-004"),
        ),
        act(4 * DAY + 10, "plant", target="plot-003", crop="rabanete"),
        act(4 * DAY + 20, "plant", target="plot-004", crop="rabanete"),
        act(4 * DAY + 30, "water", target="plot-003"),
        night(
            5,
            summary="s",
            beliefs=[],
            experiment_result="Inconclusivo, a rega foi diferente",
            experiment={"hypothesis": "Sem colchetes.", "test": "Par: plot-005 e plot-006"},
        ),
        act(5 * DAY + 10, "plant", target="plot-005", crop="rabanete"),
        act(6 * DAY + 10, "plant", target="plot-006", crop="rabanete"),
    ]
    experiments = experiments_of(envelopes)
    found = adhere(envelopes, experiments, days=7)
    assert (found.experiments, found.bracketed, found.others) == (3, 2, 0)
    assert found.suspects == ("lugar", "adubo")  # na ordem da lista
    assert (found.planted, found.pairs) == (3, 1)
    assert found.verdicts == {"cumpriu": 1, "inconclusivo": 1}
    assert found.given == 2
    assert (found.today_days, found.saw, found.days) == (2, 1, 7)


def test_o_par_precisa_de_dois_canteiros_plantados_depois_da_noite() -> None:
    envelopes = [
        act(10, "plant", target="plot-001", crop="rabanete"),  # antes da noite: não é o par
        act(20, "plant", target="plot-002", crop="rabanete"),
        night(1, summary="s", beliefs=[], experiment=trial("antes", "plot-001", "plot-002")),
        night(2, summary="s", beliefs=[], experiment={"hypothesis": "[adubo] x", "test": "plot-7"}),
    ]
    found = adhere(envelopes, experiments_of(envelopes), days=2)
    assert (found.planted, found.pairs, found.given) == (0, 0, 0)


def _run(arena: Path, name: str, spec: dict[str, Any], envelopes: list[dict[str, Any]]) -> None:
    folder = arena / name
    folder.mkdir(parents=True)
    summary = {"spec": spec, "days": 2, "calls": 1, "cost_usd": 0.01, "aborted_day": None}
    (folder / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    (folder / "archive.jsonl").write_text(
        "".join(json.dumps(e) + "\n" for e in envelopes), encoding="utf-8"
    )


def test_o_relatorio_mostra_a_aderencia_so_quando_ha_procedimento(tmp_path: Path) -> None:
    base = {"cartridge": "farm_morada_do_sol", "seed": 1, "map": "d", "controller": "llm"}
    start = ev(0, "world.session.started.v1", tick_seconds=60)
    run = [
        start,
        note(1, "HOJE: plantar."),
        night(1, summary="s", beliefs=[], experiment=trial("adubo", "plot-001", "plot-002")),
    ]
    arena = tmp_path / "sem"
    _run(arena, "haiku", {**base, "name": "haiku", "memory": True}, run)
    out = tmp_path / "sem.md"
    assert main([str(arena), "--out", str(out)]) == 0
    assert "## A aderência ao procedimento" not in out.read_text(encoding="utf-8")
    spec = {**base, "memory": True, "playbook": 4}
    _run(arena, "haiku-procedimento", {**spec, "name": "haiku-procedimento"}, run)
    _run(arena, "script3-d", {**base, "name": "script3-d", "controller": "script"}, [start])
    out = tmp_path / "com.md"
    assert main([str(arena), "--out", str(out)]) == 0
    text = out.read_text(encoding="utf-8")
    assert "## A aderência ao procedimento" in text
    section = text.split("## A aderência ao procedimento")[1].split("\n## ")[0]
    assert "script3-d" not in section  # sem memória, sem medida
    assert "| Procedimento | não | sim |" in section
    assert "| Hipóteses com a [suspeita] no começo | 1 de 1 | 1 de 1 |" in section
    assert "| Suspeitas da lista testadas | 1 de 4 (adubo) | 1 de 4 (adubo) |" in section
    assert "| Dias com a anotação HOJE: | 1 de 2 | 1 de 2 |" in section
