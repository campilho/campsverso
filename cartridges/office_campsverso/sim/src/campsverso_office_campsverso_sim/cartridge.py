"""Cartucho office_campsverso, o escritório do Campsverso: estende o gênero office (ADR-0078)."""

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

import yaml

from campsverso_cartridge_api import (
    AvatarDef,
    CartridgeManifest,
    ControllerRef,
    ControllerType,
    Position,
    SpawnDef,
    WorldBuilder,
)

DATA = Path(__file__).parent / "data"


@dataclass(frozen=True)
class OfficeCampsversoCartridge:
    manifest: CartridgeManifest = field(
        default_factory=lambda: CartridgeManifest("office_campsverso", "0.1.0", extends=("office",))
    )

    def contribute(self, world: WorldBuilder) -> None:
        world.set_map(json.loads((DATA / "map.tmj").read_text(encoding="utf-8")))
        state = cast(
            dict[str, Any], yaml.safe_load((DATA / "escritorio.yaml").read_text(encoding="utf-8"))
        )
        office = cast(Mapping[str, Any], state["office"])
        world.merge_data("office", office)
        door = Position(int(office["door"]["x"]), int(office["door"]["y"]))
        for member in cast(list[Mapping[str, Any]], state["cast"]):
            controller = cast(Mapping[str, str], member["controller"])
            avatar_id = str(member["id"])
            # Todos começam fora: o expediente põe o dev e o vigia; o gerente entra ao ser assumido.
            world.spawn(
                SpawnDef(
                    avatar_id,
                    "avatar",
                    display_name=str(member["name"]),
                    attributes={"papel": str(member["role"])},
                )
            )
            world.add_avatar(
                AvatarDef(
                    avatar_id,
                    ControllerRef(cast(ControllerType, controller["type"]), controller["id"]),
                    present=False,
                    controllers=frozenset(str(kind) for kind in member["accepts"]),
                    enters_at=door if member.get("enters_at_door") else None,
                )
            )

    def rules_file(self) -> Path | None:
        return None
