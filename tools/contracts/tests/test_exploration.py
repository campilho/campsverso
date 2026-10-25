"""As métricas de exploração (ADR-0070), numa corrida sintética com o resultado conhecido."""

import json
from pathlib import Path
from typing import Any

from campsverso_tools import arena
from campsverso_tools.exploration import explore, lines

LEGEND = {
    "G": {"kind": "grass", "properties": {"passable": True, "water": False}},
    "~": {"kind": "river", "properties": {"passable": False, "water": True}},
}
# 40 x 5: grama, e água nas duas últimas colunas. A porta fica em (1, 2): a várzea começa na
# coluna 34 (até 4 tiles da água), e "longe" passa da coluna 19 (mais de 18 tiles da porta).
ROWS = ["G" * 38 + "~~"] * 5


def ev(tick: int, kind: str, /, **data: Any) -> dict[str, Any]:
    minutes = (6 * 60 + tick) % 1440  # o dia simulado começa às 06:00
    clock = f"2026-09-22T{minutes // 60:02d}:{minutes % 60:02d}:00-03:00"
    return {
        "seq": tick,
        "tick": tick,
        "time": "2026-10-25T12:00:00Z",
        "simtime": clock,
        "type": f"campsverso.{kind}",
        "data": data,
    }


def photo(tick: int, x0: int, width: int) -> dict[str, Any]:
    """Uma foto do avatar, com o recorte de `width` colunas a partir de `x0` e a porta."""
    door = {"entity_id": "door", "kind": "door", "position": {"x": 1, "y": 2}}
    view = {
        "entities": [door],
        "map": {"origin": {"x": x0, "y": 0}, "rows": [r[x0 : x0 + width] for r in ROWS]},
    }
    return ev(tick, "perception.delivered.v1", avatar_id="camps", view=view)


def step(tick: int, x: int, phase: str) -> dict[str, Any]:
    """Um delta: o avatar em (x, 2), na fase do dia."""
    me = {"entity_id": "camps", "position": {"x": x, "y": 2}}
    return ev(tick, "perception.updated.v1", avatar_id="camps", self=me, clock={"phase": phase})


def dig(tick: int, plot: str, x: int) -> dict[str, Any]:
    position = {"x": x, "y": 2}
    return ev(
        tick,
        "world.entity.spawned.v1",
        entity_id=plot,
        kind="plot",
        position=position,
        action_id="a",
    )


def plant(tick: int, plot: str, crop: str) -> dict[str, Any]:
    return ev(tick, "action.completed.v1", action="plant", params={"target": plot, "crop": crop})


SESSION = ev(
    0,
    "world.session.started.v1",
    tick_seconds=60,
    map={"id": "teste", "width": 40, "height": 5, "rows": ROWS, "legend": LEGEND},
    perception={"radius": 3, "by_phase": {"dia": 3, "noite": 1}, "lights": {"lanterna": 2}},
)
RUN = [
    SESSION,
    photo(0, 0, 4),  # vê as colunas 0 a 3
    dig(10, "plot-001", 2),
    plant(11, "plot-001", "rabanete"),
    plant(20, "plot-001", "rabanete"),  # repete a cultura do canteiro
    step(30, 20, "noite"),  # à noite vê 1 tile para cada lado: (19..21, 1..3)
    ev(40, "world.item.created.v1", item="lanterna", qty=1, container_id="camps"),
    step(50, 30, "noite"),  # com a lanterna, 2: (28..32, 0..4)
    dig(60, "plot-002", 30),  # longe, sem espantalho
    plant(61, "plot-002", "milho"),
    step(1500, 36, "dia"),  # no dia 2, 3 tiles: colunas 33 a 39, com a água
    dig(1510, "plot-003", 35),  # a várzea, e longe
    ev(
        1511,
        "world.entity.spawned.v1",
        entity_id="scarecrow-1",
        kind="scarecrow",
        position={"x": 36, "y": 2},
    ),
    plant(1512, "plot-003", "milho"),  # longe, mas com espantalho
    plant(1513, "plot-001", "couve"),  # troca a cultura
]


def test_a_exploracao_de_uma_corrida_conhecida() -> None:
    found = explore(RUN)
    assert found is not None
    assert found.limited_view
    # a foto: 4 colunas x 5 linhas; à noite, 3 x 3; com a lanterna, 5 x 5; de dia, 7 x 5
    assert found.seen_by_day == {1: 20 + 9 + 25, 2: 20 + 9 + 25 + 35}
    assert found.seen_tiles == 89
    assert found.seen_most_day is None  # nunca viu 90% do mapa
    assert found.first_water == "dia 2, 07:00"
    assert found.plots_by_zone == {"resto": 1, "longe": 1, "várzea longe": 1}
    assert found.plantings_by_zone == {"resto": 3, "longe": 1, "várzea longe": 1}
    assert found.fertile_after_water == (1, 2)  # dos 2 plantios depois de ver a água, 1 na várzea
    assert found.exposed == 1
    assert found.door_distance == round((1 + 29 + 34) / 3, 1)
    assert found.repeats == (1, 2)
    text = "\n".join(lines(found))
    assert "tiles vistos: 89 de 200 (44%)" in text
    assert "plantios que repetiram a cultura do canteiro: 1 de 2" in text


def test_sem_mapa_nao_ha_exploracao_e_sem_raio_tudo_e_visto() -> None:
    assert explore([ev(0, "world.session.started.v1", tick_seconds=60)]) is None
    whole = {**SESSION["data"], "perception": {"radius": None}}
    found = explore([{**SESSION, "data": whole}, photo(0, 0, 40)])
    assert found is not None
    assert not found.limited_view
    assert (found.seen_tiles, found.seen_most_day) == (200, 1)


def test_o_relatorio_da_arena_mostra_a_exploracao(tmp_path: Path) -> None:
    folder = tmp_path / "20261025-120000" / "script3"
    folder.mkdir(parents=True)
    spec = {"name": "script3", "controller": "script", "cartridge": "farm_morada_do_sol"}
    (folder / "summary.json").write_text(json.dumps({"spec": spec}), encoding="utf-8")
    (folder / "archive.jsonl").write_text(
        "".join(json.dumps({**e, "source": "/kernel/w"}) + "\n" for e in RUN), encoding="utf-8"
    )
    out = tmp_path / "relatorio.md"
    assert arena.main([str(folder.parent), "--out", str(out)]) == 0
    text = out.read_text(encoding="utf-8")
    assert "## A exploração" in text
    assert "| Tiles vistos | 89 (44%) |" in text
    assert "| A primeira água à vista | dia 2, 07:00 |" in text
    assert "| Plantios (várzea / várzea longe / longe / resto) | 0 / 1 / 1 / 3 |" in text
