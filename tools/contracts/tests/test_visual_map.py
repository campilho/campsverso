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
                expected = "hedge-" if kind == "tree" else "dirt-edge-"
                assert kind in ("tree", "grass")
                assert names[gid].startswith(expected)


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
