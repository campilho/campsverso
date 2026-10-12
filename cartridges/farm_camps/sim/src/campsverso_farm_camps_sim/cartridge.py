"""Cartucho farm_camps, o cenário da v0.1: estende o gênero farm (ADR-0031)."""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

import yaml

from campsverso_cartridge_api import (
    AvatarDef,
    CartridgeManifest,
    ControllerRef,
    SpawnDef,
    WorldBuilder,
)

DATA = Path(__file__).parent / "data"


@dataclass(frozen=True)
class FarmCampsCartridge:
    manifest: CartridgeManifest = field(
        default_factory=lambda: CartridgeManifest("farm_camps", "0.1.0", extends=("farm",))
    )

    def contribute(self, world: WorldBuilder) -> None:
        world.set_map(json.loads((DATA / "map.tmj").read_text(encoding="utf-8")))
        state = cast(
            dict[str, Any], yaml.safe_load((DATA / "world.yaml").read_text(encoding="utf-8"))
        )
        avatar = state["avatar"]
        controller = avatar["default_controller"]
        world.add_avatar(
            AvatarDef(avatar["id"], ControllerRef(controller["type"], controller["id"]))
        )
        world.spawn(SpawnDef(state["watering_can"], "watering_can", container_id=avatar["id"]))
        for container, items in state["initial_items"].items():
            for item, qty in items.items():
                world.add_items(container, item, int(qty))

    def rules_file(self) -> Path | None:
        return DATA / "rules.yaml"
