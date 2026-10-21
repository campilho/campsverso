"""O relatório da arena e os sinais do leste (ADR-0061), com corridas sintéticas."""

import json
from pathlib import Path
from typing import Any

from campsverso_tools.arena import (
    beliefs_at_end,
    east_signals,
    load_runs,
    main,
    notes_east_advantage,
)


def ev(tick: int, kind: str, /, **data: Any) -> dict[str, Any]:
    return {
        "source": "/kernel/w",
        "seq": 0,
        "tick": tick,
        "type": f"campsverso.{kind}",
        "time": "2026-10-12T01:00:00Z",
        "data": data,
    }


def mem(tick: int, kind: str, /, **data: Any) -> dict[str, Any]:
    return {**ev(tick, kind, avatar_id="camps", **data), "source": "/controller-runner/llm/camps"}


def belief(tick: int, kind: str, belief_id: str, statement: str, confidence: Any) -> dict[str, Any]:
    return mem(
        tick,
        f"memory.belief.{kind}.v1",
        belief_id=belief_id,
        statement=statement,
        confidence=confidence,
        evidence=[],
        source={"kind": "observation"},
    )


MEMORY_RUN: list[dict[str, Any]] = [
    ev(0, "world.session.started.v1", tick_seconds=60),
    ev(0, "world.item.created.v1", item="moeda", qty=100, container_id="camps"),
    mem(30, "memory.noted.v1", day=1, text="Plantei rabanete no oeste."),
    mem(200, "memory.noted.v1", day=1, text="O plot-e-01 parece crescer mais rápido."),
    ev(100, "action.completed.v1", action="plant", params={"target": "plot-w-01"}),
    ev(110, "action.completed.v1", action="plant", params={"target": "plot-e-01"}),
    belief(1000, "formed", "bel-0001", "O poço enche o regador até 10.", 0.9),
    belief(1000, "formed", "bel-0002", "Os canteiros do leste amadurecem em 2 dias.", 0.6),
    belief(
        2500,
        "updated",
        "bel-0002",
        "Rabanete no leste amadurece em 2 dias.",
        {"before": 0.6, "after": 0.9},
    ),
    belief(2500, "formed", "bel-0003", "O leste dá azar.", 0.5),
    ev(2880, "world.clock.phase_changed.v1"),
    mem(4000, "memory.belief.retracted.v1", belief_id="bel-0003", statement="O leste dá azar."),
    ev(4400, "action.completed.v1", action="plant", params={"target": "plot-e-02"}),
    ev(4410, "action.completed.v1", action="harvest", params={"target": "plot-e-01"}),
    ev(4420, "action.completed.v1", action="harvest", params={"target": "plot-w-01"}),
    ev(4430, "action.rejected.v1", reason="not_adjacent"),
    {
        "source": "/controller-runner/llm/camps",
        "seq": 9,
        "tick": 4440,
        "type": "campsverso.llm.call.completed.v1",
        "time": "2026-10-12T02:00:00Z",
        "data": {
            "latency_ms": 1500,
            "cost_usd": 0.01,
            "charged": True,
            "usage": {"input_tokens": 1},
        },
    },
    ev(5760, "world.clock.phase_changed.v1"),
]


def test_os_sinais_do_leste_vem_da_memoria() -> None:
    east = east_signals(MEMORY_RUN)
    assert east["first_note"] == {
        "day": 1,
        "hour": "09:20",  # tick 200: 06:00 mais 200 minutos
        "text": "O plot-e-01 parece crescer mais rápido.",
    }
    assert east["first_discovery_note"] == east["first_note"]  # "mais rápido" nota a vantagem
    assert (east["first_belief"]["belief_id"], east["first_belief"]["day"]) == ("bel-0002", 1)
    tracks = {b["belief_id"]: b for b in east["beliefs"]}
    assert set(tracks) == {"bel-0002", "bel-0003"}  # bel-0001 não fala do leste
    assert [s["kind"] for s in tracks["bel-0002"]["steps"]] == ["formada", "revisada"]
    assert tracks["bel-0002"]["confidence"] == 0.9
    assert tracks["bel-0002"]["statement"] == "Rabanete no leste amadurece em 2 dias."
    assert tracks["bel-0002"]["first_statement"] == "Os canteiros do leste amadurecem em 2 dias."
    assert tracks["bel-0003"]["retracted_day"] == 3
    assert east["plantings"]["days_1_3"] == {"oeste": 1, "leste": 1, "east_fraction": 0.5}
    assert east["plantings"]["from_day_4"] == {"oeste": 0, "leste": 1, "east_fraction": 1.0}
    assert east["harvests"]["from_day_4"]["east_fraction"] == 0.5
    assert (east["discovered"], east["discovered_by"]) == (True, "bel-0002")
    assert [b["belief_id"] for b in beliefs_at_end(MEMORY_RUN)] == ["bel-0001", "bel-0002"]


def test_sem_memoria_so_o_comportamento_conta() -> None:
    east = east_signals(
        [
            ev(0, "world.session.started.v1", tick_seconds=60),
            ev(4400, "action.completed.v1", action="plant", params={"target": "plot-e-01"}),
        ]
    )
    assert (east["first_note"], east["first_belief"], east["beliefs"]) == (None, None, [])
    assert east["first_discovery_note"] is None
    assert east["discovered"] is False
    assert east["plantings"]["days_1_3"]["east_fraction"] is None
    assert east["plantings"]["from_day_4"]["east_fraction"] == 1.0


def test_a_vantagem_tem_de_estar_no_trecho_que_fala_do_leste() -> None:
    assert notes_east_advantage("O plot-e-01 parece crescer mais rápido.")
    assert notes_east_advantage("Os canteiros do leste amadurecem em 2 dias; o manual diz 3.")
    assert not notes_east_advantage(
        "Plano: batata e abóbora no leste; rabanete para comida rápida."
    )
    assert not notes_east_advantage("Rabanete madura em 3 dias no leste.")


def test_uma_mencao_sem_descoberta_nao_conta() -> None:
    east = east_signals([belief(1000, "formed", "bel-0001", "Plantei no leste hoje.", 0.9)])
    assert len(east["beliefs"]) == 1
    assert east["discovered"] is False


def _run(arena: Path, name: str, spec: dict[str, Any], envelopes: list[dict[str, Any]]) -> None:
    folder = arena / name
    folder.mkdir(parents=True)
    summary = {
        "spec": spec,
        "days": 2,
        "calls": 1,
        "cost_usd": 0.01,
        "reflections": 1,
        "notes": 2,
        "beliefs": {"formed": 3, "updated": 1, "retracted": 1},
        "real_seconds": 95.0,
        "aborted_day": None,
    }
    (folder / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    (folder / "archive.jsonl").write_text(
        "".join(json.dumps(e) + "\n" for e in envelopes), encoding="utf-8"
    )


def test_o_relatorio_poe_as_corridas_lado_a_lado(tmp_path: Path) -> None:
    arena = tmp_path / "20261019-070000"
    _run(
        arena,
        "haiku-memoria",
        {
            "name": "haiku-memoria",
            "controller": "llm",
            "memory": True,
            "river_bonus": True,
            "seed": 1,
        },
        MEMORY_RUN,
    )
    _run(
        arena,
        "script",
        {"name": "script", "controller": "script", "memory": False, "river_bonus": True, "seed": 1},
        [
            ev(0, "world.session.started.v1", tick_seconds=60),
            ev(0, "world.item.created.v1", item="moeda", qty=100, container_id="camps"),
            ev(10, "world.item.created.v1", item="moeda", qty=20, container_id="camps"),
            ev(2880, "world.clock.phase_changed.v1"),
            ev(5760, "world.clock.phase_changed.v1"),
        ],
    )
    (arena / "vazia").mkdir()  # uma corrida que não terminou não entra
    assert [r.name for r in load_runs(arena)] == ["script", "haiku-memoria"]
    out = tmp_path / "relatorio.md"
    assert main([str(arena), "--out", str(out)]) == 0
    text = out.read_text(encoding="utf-8")
    assert text.startswith("# Arena de 2026-10-19")
    assert "| Métrica | script | haiku-memoria |" in text
    assert "| Moedas ao fim | 120 | 100 |" in text
    assert "| Custo (US$) | - | 0,01 |" in text
    assert "| Primeira anotação que cita o leste | sem memória | dia 1, 09:20 |" in text
    assert "| Primeira anotação que nota a vantagem do leste | sem memória | dia 1, 09:20 |" in text
    assert "## Colheitas por dia" in text
    assert "| 4 | - | 1 / 1 |" in text  # o script sintético não tem fato no dia 4
    assert "| Veredito | só pelo comportamento | descobriu (bel-0002) |" in text
    assert "dia 1 formada 0,60 → dia 2 revisada 0,90" in text
    assert 'Antes: "Os canteiros do leste amadurecem em 2 dias."' in text
    assert "dia 2 a 3, retirada" in text
    assert "## Moedas por dia" in text
    assert "| 3 | 120 | 100 |" in text  # o dia 2 não tem fato em nenhuma das duas: fica "-"
    assert "haiku-memoria/` com `archive.jsonl`, `summary.json`" in text


def test_sem_corridas_avisa(tmp_path: Path) -> None:
    assert main([str(tmp_path)]) == 2
    assert main([str(tmp_path / "nao-existe")]) == 2


# ----------------------------------------------------------------- a Boa Vista (M14, ADR-0063)

BOAVISTA_MAP = {
    "rows": ["GGGGGGRR", "GGGGGGRR"],
    "legend": {
        "G": {"kind": "grass", "properties": {"water": False}},
        "R": {"kind": "river", "properties": {"water": True}},
    },
}


def dug(tick: int, plot_id: str, x: int, y: int) -> dict[str, Any]:
    return ev(
        tick,
        "world.entity.spawned.v1",
        entity_id=plot_id,
        kind="plot",
        position={"x": x, "y": y},
        attributes={},
        action_id=f"act-{plot_id}",
    )


def done(tick: int, action: str, **params: Any) -> dict[str, Any]:
    return ev(tick, "action.completed.v1", action=action, params=params)


DAY5 = 4 * 1440
BOAVISTA_RUN: list[dict[str, Any]] = [
    ev(0, "world.session.started.v1", tick_seconds=60, map=BOAVISTA_MAP),
    ev(0, "world.item.created.v1", item="moeda", qty=100, container_id="camps"),
    dug(30, "plot-01", 1, 0),  # a 5 da água: fora da faixa
    mem(60, "memory.noted.v1", day=1, text="Cavei um canteiro perto da casa e plantei alho."),
    done(70, "plant", target="plot-01", crop="alho"),
    done(80, "water", target="plot-01"),
    done(90, "fertilize", target="plot-01"),
    ev(2880, "world.clock.phase_changed.v1"),
    dug(DAY5 + 100, "plot-02", 2, 1),  # a 4 da água: na faixa do rio
    mem(
        DAY5 + 200,
        "memory.noted.v1",
        day=5,
        text="Os canteiros perto do rio parecem amadurecer antes. O alho cresceu sem rega.",
    ),
    belief(DAY5 + 300, "formed", "bel-0001", "Canteiros perto do rio amadurecem mais rápido.", 0.8),
    belief(DAY5 + 310, "formed", "bel-0002", "O tomate murcha com um dia seco.", 0.7),
    done(DAY5 + 400, "plant", target="plot-02", crop="tomate"),
    ev(DAY5 + 500, "farm.crop.withered.v1", plot_id="plot-02", crop="tomate", day=5, dry_days=1),
    done(DAY5 + 600, "cook", target="stove", recipe="ensopado"),
    done(DAY5 + 610, "deposit", target="chest", item="rabanete", qty=2),
    done(DAY5 + 700, "harvest", target="plot-01"),
    ev(8640, "world.clock.phase_changed.v1"),
]


def test_na_boa_vista_os_sinais_sao_do_rio_e_das_outras_regras() -> None:
    """ADR-0063: o rio pela posição (sem grupo no canteiro), os canteiros cavados na faixa, e
    cada regra oculta pela primeira anotação, a primeira crença e o comportamento."""
    east = east_signals(BOAVISTA_RUN)
    assert (east["river"], east["groups"]) == ("rio", ["rio", "fora"])
    assert east["digs"]["days_1_3"] == {"rio": 0, "fora": 1, "east_fraction": 0.0}
    assert east["digs"]["from_day_4"] == {"rio": 1, "fora": 0, "east_fraction": 1.0}
    assert (east["first_band_dig"]["day"], east["first_band_dig"]["plot"]) == (5, "plot-02")
    assert east["first_note"]["day"] == 5  # "perto da casa" não é o rio
    assert east["first_discovery_note"]["day"] == 5  # "perto do rio ... amadurecer antes"
    assert (east["discovered"], east["discovered_by"]) == (True, "bel-0001")
    assert east["plantings"]["from_day_4"] == {"rio": 1, "fora": 0, "east_fraction": 1.0}
    assert east["harvests"]["from_day_4"] == {"rio": 0, "fora": 1, "east_fraction": 0.0}
    rules = east["rules"]
    assert rules["alho"]["first_note"]["day"] == 5
    assert rules["alho"]["first_belief"] is None
    assert rules["tomate"]["first_note"] is None
    assert rules["tomate"]["first_belief"]["belief_id"] == "bel-0002"
    assert all(
        rules[name] == {"first_note": None, "first_belief": None}
        for name in ("bau", "ensopado", "adubo")
    )
    assert east["behaviour"] == {
        "alho_planted": 1,
        "alho_waterings": 1,
        "deposits": 1,
        "ensopados": 1,
        "fertilized": 1,
        "tomate_planted": 1,
        "tomate_withered": 1,
    }


def test_o_relatorio_da_boa_vista_fala_do_rio_e_das_linhas_novas(tmp_path: Path) -> None:
    arena = tmp_path / "20261021-2000"
    spec = {
        "name": "sonnet-memoria",
        "controller": "llm",
        "memory": True,
        "river_bonus": True,
        "seed": 20261019,
        "cartridge": "farm_boavista",
        "model": "claude-sonnet-5-5",
        "days": 30,
        "limits": {"usd_per_sim_day": 1.5, "usd_total": 25.0},
    }
    _run(arena, "sonnet-memoria", spec, BOAVISTA_RUN)
    out = tmp_path / "relatorio.md"
    assert main([str(arena), "--out", str(out)]) == 0
    text = out.read_text(encoding="utf-8")
    assert "no mesmo mundo (`farm-boavista-01`)" in text
    assert "| Sonnet 5.5 |" in text
    assert "| 1,50 · 25 |" in text
    assert "Colheitas (rio / fora)" in text
    assert "Canteiros cavados (rio / fora)" in text
    assert "## Quem descobriu o rio" in text
    assert "Primeiro canteiro na faixa do rio | dia 5" in text
    alho = "anotação dia 5; nenhuma crença; plantou 1, regou 1 vez(es)"
    assert f"Regra oculta: o alho não precisa de rega | {alho}" in text
    tomate = "nenhuma anotação; crença dia 5 (0,70); plantou 1, murcharam 1"
    assert f"Regra oculta: o tomate murcha com um dia seco | {tomate}" in text
    assert "Parou no teto de orçamento | não" in text


def test_as_heuristicas_da_boa_vista_nao_confundem_lucro_nem_rotina() -> None:
    """Os falsos positivos da arena do M14: a margem de lucro, regar todo dia, guardar comida."""
    east = east_signals(
        [
            ev(0, "world.session.started.v1", tick_seconds=60, map=BOAVISTA_MAP),
            mem(10, "memory.noted.v1", day=1, text="Tomate custa 30 e vende 70: boa margem."),
            mem(20, "memory.noted.v1", day=1, text="Plano: guardar comida no baú."),
            belief(30, "formed", "bel-0001", "Regado todo dia, o tomate amadurece em 4.", 0.9),
            belief(40, "formed", "bel-0002", "No baú a colheita dura mais.", 0.8),
        ]
    )
    assert (east["first_note"], east["beliefs"]) == (None, [])
    assert east["rules"]["tomate"] == {"first_note": None, "first_belief": None}
    assert east["rules"]["bau"]["first_note"] is None
    assert east["rules"]["bau"]["first_belief"]["belief_id"] == "bel-0002"
