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


def optional(view: WorldView, *path: str) -> Mapping[str, Any] | None:
    """Uma seção que só alguns cenários têm (tools, market, recipes...), ou None."""
    node: Any = farm(view)
    for key in path:
        if not isinstance(node, Mapping) or key not in node:
            return None
        node = cast(Mapping[str, Any], node)[key]
    return cast(Mapping[str, Any], node) if isinstance(node, Mapping) else None


def ticks_per_hour(view: WorldView) -> int:
    return 3600 // int(section(view, "clock")["tick_seconds"])


def season_level(view: WorldView, crop: str, season: str | None) -> str | None:
    """A afinidade da cultura com a estação (boa, fraca, parada), se declarada (ADR-0067)."""
    if season is None:
        return None
    affinity = optional(view, "crops", crop, "seasons")
    level = None if affinity is None else affinity.get(season)
    return None if level is None else str(level)


def season_factor(view: WorldView, crop: str) -> float:
    """O ritmo de crescimento da cultura na estação do dia; 1 sem ano ou sem afinidade declarada."""
    year = optional(view, "year")
    level = season_level(view, crop, view.season(view.day))
    if year is None or level is None:
        return 1.0
    return float(cast(Mapping[str, Any], year["affinity"])[level])
