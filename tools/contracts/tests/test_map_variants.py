"""As variantes do mapa da Morada do Sol (ADR-0070): receitas sobre o mapa de hoje, conferidas."""

import json
from pathlib import Path
from typing import Any

from campsverso_tools import map_variants, visual_map
from campsverso_tools.map_variants import (
    BASE,
    MAPS,
    apply,
    fertile,
    grid_of,
    objects_of,
    problems,
    recipes,
    rules,
)
from campsverso_tools.visual_map import GROUND, logical_types, maps_of

ART = BASE.parents[4] / "art"


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _far(path: Path) -> list[int]:
    """A distância à porta de cada tile de terra boa do mapa."""
    doc = _json(path)
    door = objects_of(doc)["door"]
    good = fertile(grid_of(doc), rules().water_radius)
    return [max(abs(x - door[0]), abs(y - door[1])) for x, y in good]


def test_as_variantes_gravadas_estao_em_dia_e_cumprem_o_que_prometem() -> None:
    assert map_variants.main(["--check"]) == 0
    assert sorted(recipes()) == ["b", "c"]  # a d fica para o M21, sem receita no repositório


def test_a_variante_muda_so_a_agua_e_a_mata() -> None:
    base = _json(BASE)
    for name in recipes():
        doc = _json(MAPS / f"{name}.tmj")
        assert (doc["width"], doc["height"]) == (base["width"], base["height"])
        assert objects_of(doc) == objects_of(base)
        changed = {
            (a, b)
            for row_a, row_b in zip(grid_of(base), grid_of(doc), strict=True)
            for a, b in zip(row_a, row_b, strict=True)
            if a != b
        }
        kinds = {kind for pair in changed for kind in pair}
        assert kinds <= {"grass", "tree", "river", "path"}, (name, kinds)


def test_cada_mapa_poe_a_terra_boa_num_lugar() -> None:
    crows = rules().crow_distance
    today, creek, ponds = _far(BASE), _far(MAPS / "b.tmj"), _far(MAPS / "c.tmj")
    # a: a lagoa na linha dos corvos e o rio longe
    assert min(today) < crows < max(today)
    # b: perto da casa, a maior parte a salvo dos corvos
    assert max(creek) <= 22
    assert sum(d <= crows for d in creek) / len(creek) >= 0.6
    # c: só longe, toda além da linha dos corvos
    assert min(ponds) > crows


def test_uma_receita_que_estraga_o_mapa_e_recusada() -> None:
    base = _json(BASE)
    door = objects_of(base)["door"]
    well = objects_of(base)["well"]
    drown = {"fill": [well[0], well[1], well[0], well[1]], "tile": "river"}
    shut = {"fill": [door[0] - 1, door[1] + 1, door[0] + 1, door[1] + 1], "tile": "tree"}
    ops = [drown, shut]  # afoga o poço e fecha a porta
    found = problems(base, apply(grid_of(base), ops), {"fertil_da_porta": {"max": 10}}, rules())
    assert any("o tile de well" in p for p in found)
    assert any("não se alcança a partir da porta" in p for p in found)
    assert any("mais que 10" in p for p in found)


def test_o_mapa_visual_de_cada_variante_combina_com_o_logico() -> None:
    pairs = maps_of("farm_morada_do_sol")
    assert [out.name for _, out in pairs] == [
        "map-visual.tmj",
        "map-visual-b.tmj",
        "map-visual-c.tmj",
    ]
    for logic_path, visual_path in pairs:
        logic = logical_types(_json(logic_path))
        visual = _json(visual_path)
        names = {t["id"] + 1: t["type"] for t in visual["tilesets"][0]["tiles"]}
        width = int(visual["width"])
        for i, gid in enumerate(visual["layers"][0]["data"]):
            kind = logic[i // width][i % width]
            assert names[gid].startswith(GROUND[kind]), (visual_path.name, i % width, i // width)
    assert visual_map.main(["--check", "--scenario", "farm_morada_do_sol"]) == 0


def test_a_arte_aponta_o_mapa_visual_de_cada_variante_pelo_id_do_mapa() -> None:
    manifest = _json(ART / "art.json")
    assert manifest["visual_maps"] == {
        f"farm_morada_do_sol-{name}": f"map-visual-{name}.tmj" for name in recipes()
    }
    for path in manifest["visual_maps"].values():
        assert (ART / path).is_file()
