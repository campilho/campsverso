"""Leitura dos dados do gênero (data/farm.yaml)."""

from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

import yaml

from campsverso_cartridge_api import WorldView

DATA_FILE = Path(__file__).parent / "data" / "farm.yaml"
NAMESPACE = "farm"
ENERGY = "energia"
HUNGER = "fome"


def load() -> dict[str, Any]:
    return cast(dict[str, Any], yaml.safe_load(DATA_FILE.read_text(encoding="utf-8")))


def farm(view: WorldView) -> Mapping[str, Any]:
    return view.data(NAMESPACE)


def section(view: WorldView, *path: str) -> Mapping[str, Any]:
    node: Any = farm(view)
    for key in path:
        node = node[key]
    return cast(Mapping[str, Any], node)
