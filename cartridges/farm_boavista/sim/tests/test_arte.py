"""A arte da Fazenda Boa Vista (ADR-0062, decisão 14; ADR-0063, decisão 7): toda cultura do
cenário e todo tipo com posição no mapa têm desenho nas folhas do gênero, em quadros que existem."""

import json
import struct
from pathlib import Path
from typing import Any, cast

import yaml

from campsverso_farm_boavista_sim.cartridge import DATA

ART = Path(__file__).resolve().parents[3] / "farm" / "art"
STAGES = ("broto", "crescendo", "madura", "murcha")


def _png_size(path: Path) -> tuple[int, int]:
    """Largura e altura do PNG, lidas do cabeçalho IHDR."""
    width, height = struct.unpack(">II", path.read_bytes()[16:24])
    return int(width), int(height)


def _art() -> dict[str, Any]:
    return cast(dict[str, Any], json.loads((ART / "art.json").read_text(encoding="utf-8")))


def _frames(art: dict[str, Any], sheet: str) -> int:
    info = art["sheets"][sheet]
    width, height = _png_size(ART / str(info["image"]))
    return (width // int(info["frame_width"])) * (height // int(info["frame_height"]))


def test_toda_cultura_tem_os_quatro_estagios_desenhados() -> None:
    crops = yaml.safe_load((DATA / "boavista.yaml").read_text(encoding="utf-8"))["crops"]
    art = _art()
    looks = {
        (v["when"].get("crop"), v["when"]["stage"]): v["look"]
        for v in art["kinds"]["plot"]["variants"]
    }
    total = _frames(art, "crops")
    for crop in crops:
        for stage in STAGES:
            look = looks[(crop, stage)]
            assert look["sheet"] == "crops"
            assert 0 <= int(look["frame"]) < total, (crop, stage)
    assert int(looks[(None, "semente")]["frame"]) < total
    # Só a murcha é tingida: as culturas novas têm desenho próprio, não a cor de reserva.
    assert {crop for (crop, _), look in looks.items() if "tint" in look} == set(crops)
    assert all(stage == "murcha" for (_, stage), look in looks.items() if "tint" in look)


def test_o_fogao_tem_desenho() -> None:
    art = _art()
    stove = art["kinds"]["stove"]
    assert stove["sheet"] == "objects"
    assert 0 <= int(stove["frame"]) < _frames(art, "objects")
