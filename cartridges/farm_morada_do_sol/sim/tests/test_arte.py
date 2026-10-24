"""A arte da Fazenda Morada do Sol (ADR-0067): as culturas novas na folha crops2 do gênero, o
espantalho, as árvores do mapa visual e as folhas que trocam com a estação."""

import json
import struct
from pathlib import Path
from typing import Any, cast

import yaml

from campsverso_farm_morada_do_sol_sim.cartridge import DATA

CARTRIDGES = Path(__file__).resolve().parents[3]
GENRE = CARTRIDGES / "farm" / "art"
LAYER = CARTRIDGES / "farm_morada_do_sol" / "art"
STAGES = ("broto", "crescendo", "madura", "murcha")


def _png_size(path: Path) -> tuple[int, int]:
    """Largura e altura do PNG, lidas do cabeçalho IHDR."""
    width, height = struct.unpack(">II", path.read_bytes()[16:24])
    return int(width), int(height)


def _art(folder: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads((folder / "art.json").read_text(encoding="utf-8")))


def _frames(folder: Path, art: dict[str, Any], sheet: str) -> int:
    info = art["sheets"][sheet]
    width, height = _png_size(folder / str(info["image"]))
    return (width // int(info["frame_width"])) * (height // int(info["frame_height"]))


def test_as_culturas_novas_tem_os_quatro_estagios_na_folha_crops2() -> None:
    data = yaml.safe_load((DATA / "morada.yaml").read_text(encoding="utf-8"))
    new = [crop for crop, info in data["crops"].items() if "seed" in info]
    assert new == ["milho", "melancia", "mandioca", "couve"]
    art = _art(GENRE)
    looks = {
        (v["when"].get("crop"), v["when"]["stage"]): v["look"]
        for v in art["kinds"]["plot"]["variants"]
    }
    total = _frames(GENRE, art, "crops2")
    assert total == 4 * 5  # quatro culturas, cinco quadros do pacote LPC
    for crop in new:
        for stage in STAGES:
            look = looks[(crop, stage)]
            assert look["sheet"] == "crops2"
            assert 0 <= int(look["frame"]) < total, (crop, stage)
        assert "tint" in looks[(crop, "murcha")]


def test_o_espantalho_tem_desenho() -> None:
    art = _art(LAYER)
    scarecrow = art["kinds"]["scarecrow"]
    assert 0 <= int(scarecrow["frame"]) < _frames(LAYER, art, str(scarecrow["sheet"]))


def test_as_arvores_trocam_com_a_estacao() -> None:
    art = _art(LAYER)
    sizes = {_png_size(LAYER / str(art["sheets"][name]["image"])) for name in art["sheets"]}
    assert (384, 128) in sizes  # quatro árvores de 3 x 4 tiles
    for season, look in art["seasons"].items():
        for tileset, sheet in look.get("tilesets", {}).items():
            assert tileset == "trees", season
            assert _png_size(LAYER / str(art["sheets"][sheet]["image"])) == (384, 128)
    visual = json.loads((LAYER / "map-visual.tmj").read_text(encoding="utf-8"))
    assert [t["name"] for t in visual["tilesets"]] == ["terrain", "trees"]
    trees = next(layer for layer in visual["layers"] if layer["name"] == "trees")
    assert sum(1 for gid in trees["data"] if gid) >= 12 * 30  # dezenas de árvores na mata
