"""Mapa visual e manifestos de arte (ADR-0053): coerentes com o mapa lógico e com os arquivos."""

import json
import struct
from pathlib import Path
from typing import Any

from campsverso_tools import visual_map
from campsverso_tools.visual_map import (
    GROUND,
    LOGIC,
    OUT,
    REPO,
    TILESET,
    build,
    logical_types,
    render,
)

ART = {"farm": REPO / "cartridges/farm/art", "farm_camps": REPO / "cartridges/farm_camps/art"}


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _png_size(path: Path) -> tuple[int, int]:
    width, height = struct.unpack(">II", path.read_bytes()[16:24])
    return width, height


def test_o_mapa_visual_gravado_esta_em_dia() -> None:
    assert OUT.read_text(encoding="utf-8") == render(build(_json(LOGIC), _json(TILESET)))
    assert visual_map.main(["--check"]) == 0


def test_cada_tile_desenhado_combina_com_o_tipo_logico() -> None:
    logic = logical_types(_json(LOGIC))
    visual = _json(OUT)
    names = {t["id"] + 1: t["type"] for t in visual["tilesets"][0]["tiles"]}
    assert (visual["width"], visual["height"]) == (len(logic[0]), len(logic))
    ground, *over = visual["layers"]
    width = int(visual["width"])
    for i, gid in enumerate(ground["data"]):
        kind = logic[i // width][i % width]
        assert names[gid].startswith(GROUND[kind]), (i % width, i // width, kind, names[gid])
    for layer in over:
        for i, gid in enumerate(layer["data"]):
            kind = logic[i // width][i % width]
            if gid:
                expected = {"tree": "hedge-", "grass": "dirt-edge-", "wall": "wall-"}
                assert kind in expected
                assert names[gid].startswith(expected[kind])


def test_manifestos_apontam_para_arquivos_e_quadros_que_existem() -> None:
    sheets: dict[str, tuple[Path, int, int]] = {}
    for layer, folder in ART.items():
        manifest = _json(folder / "art.json")
        assert manifest["version"] == 1, layer
        assert (folder / manifest["credits"]).is_file(), layer
        if "visual_map" in manifest:
            assert (folder / manifest["visual_map"]).is_file()
        for name, sheet in manifest.get("sheets", {}).items():
            width, height = _png_size(folder / sheet["image"])
            columns, rows = width // sheet["frame_width"], height // sheet["frame_height"]
            sheets[name] = (folder / sheet["image"], columns, rows)
    terrain = _json(TILESET)
    assert (TILESET.parent / terrain["image"]).is_file()
    farm = _json(ART["farm"] / "art.json")
    for kind, art in farm["kinds"].items():
        for look in [art, *(v["look"] for v in art.get("variants", []))]:
            if "sheet" in look:
                _, columns, rows = sheets[look["sheet"]]
                assert look["frame"] < columns * rows, (kind, look)
    camps = _json(ART["farm_camps"] / "art.json")["avatars"]["camps"]
    _, columns, rows = sheets[camps["sheet"]]
    for name, animation in camps["animations"].items():
        last_row = animation["row"] + (0 if animation.get("single") else 3)
        assert last_row < rows, name
        assert max(animation["frames"]) < columns, name
    for target in [camps["idle"], camps["asleep"], *camps["actions"].values()]:
        assert target in camps["animations"]


def test_toda_cultura_e_estagio_da_fazenda_tem_arte() -> None:
    import yaml

    data = yaml.safe_load(
        (REPO / "cartridges/farm/sim/src/campsverso_farm_sim/data/farm.yaml").read_text()
    )
    farm = _json(ART["farm"] / "art.json")
    variants = farm["kinds"]["plot"]["variants"]
    stages = ("broto", "crescendo", "madura", "murcha")
    for crop in data["crops"]:
        for stage in stages:
            assert any(v["when"] == {"crop": crop, "stage": stage} for v in variants), (crop, stage)
    assert any(v["when"] == {"stage": "semente"} for v in variants)


OFFICE_ART = {
    "office": REPO / "cartridges/office/art",
    "office_campsverso": REPO / "cartridges/office_campsverso/art",
}


def test_o_mapa_visual_do_escritorio_combina_com_o_mapa_logico() -> None:
    """O escritório (ADR-0078): cada tile do chão cabe no tipo lógico, a parede do fundo tem duas
    linhas de face sobre a sala, e a decoração fica na parede do fundo ou num tile de móvel."""
    scenario = "office_campsverso"
    logic = _json(visual_map.logic_map(scenario))
    tileset = _json(visual_map.OFFICE_TILESET)
    decor = _json(visual_map.decor_file(scenario))
    out = visual_map.visual_map(scenario)
    assert out.read_text(encoding="utf-8") == render(visual_map.build_office(logic, tileset, decor))
    assert (visual_map.OFFICE_TILESET.parent / tileset["image"]).is_file()
    types = logical_types(logic)
    visual = _json(out)
    names = {t["id"] + 1: t["type"] for t in tileset["tiles"]}
    ground, over = visual["layers"]
    width = int(visual["width"])
    for i, gid in enumerate(ground["data"]):
        x, y = i % width, i // width
        assert names[gid] in visual_map.OFFICE_GROUND[types[y][x]], (x, y, names[gid])
        if names[gid] == "north-b":
            assert types[y + 1][x] in visual_map.ROOM
    for i, gid in enumerate(over["data"]):
        x, y = i % width, i // width
        if gid:
            under = names[ground["data"][i]]
            assert under.startswith("north-") or types[y][x] == "furniture", (x, y, under)


def test_os_manifestos_do_escritorio_apontam_para_quadros_que_existem() -> None:
    sheets: dict[str, tuple[int, int]] = {}
    manifests = {layer: _json(folder / "art.json") for layer, folder in OFFICE_ART.items()}
    for layer, manifest in manifests.items():
        folder = OFFICE_ART[layer]
        assert (folder / manifest["credits"]).is_file(), layer
        for name, sheet in manifest.get("sheets", {}).items():
            width, height = _png_size(folder / sheet["image"])
            sheets[name] = (width // sheet["frame_width"], height // sheet["frame_height"])
    scenario = manifests["office_campsverso"]
    assert (OFFICE_ART["office_campsverso"] / scenario["visual_map"]).is_file()
    # O tileset do mapa visual é desenhado pela folha de mesmo nome (a tela procura assim).
    assert _json(visual_map.OFFICE_TILESET)["name"] in manifests["office"]["sheets"]
    for kind, art in manifests["office"]["kinds"].items():
        if "sheet" in art:
            columns, rows = sheets[art["sheet"]]
            assert art["frame"] < columns * rows, kind
    assert manifests["office"]["kinds"]["chair"]["seat"] == "up"
    cast = scenario["avatars"]
    assert set(cast) == {"camps", "gerente", "vigia"}
    for name, avatar in cast.items():
        columns, rows = sheets[avatar["sheet"]]
        for animation in avatar["animations"].values():
            last_row = animation["row"] + (0 if animation.get("single") else 3)
            assert last_row < rows, name
            assert max(animation["frames"]) < columns, name
        targets = [avatar["idle"], avatar["asleep"], avatar["seated"], *avatar["actions"].values()]
        assert all(target in avatar["animations"] for target in targets), name
