"""Cartucho farm_boavista, a Fazenda Boa Vista (bíblia 2; ADR-0062): estende farm_camps.

Herda o Camps, o cartão, a arte e os itens iniciais do cenário da v0.1 e troca o mapa (sem
canteiros, com o fogão), os números e as mecânicas ligadas: as sete culturas, as ferramentas
com peso, o mercado que satura, o ciclo do quiosque, o adubo, as receitas, a validade e o custo
de andar. Tudo isso é dado deste cenário (`data/boavista.yaml`) sobre o código do gênero farm.
"""

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
from campsverso_farm_sim import config
from campsverso_farm_sim.extensions import contribute_extensions

DATA = Path(__file__).parent / "data"


def overlay() -> dict[str, Any]:
    return cast(
        dict[str, Any], yaml.safe_load((DATA / "boavista.yaml").read_text(encoding="utf-8"))
    )


@dataclass(frozen=True)
class FarmBoaVistaCartridge:
    manifest: CartridgeManifest = field(
        default_factory=lambda: CartridgeManifest("farm_boavista", "0.1.0", extends=("farm_camps",))
    )

    def contribute(self, world: WorldBuilder) -> None:
        world.set_map(json.loads((DATA / "map.tmj").read_text(encoding="utf-8")))
        state = cast(
            dict[str, Any], yaml.safe_load((DATA / "world.yaml").read_text(encoding="utf-8"))
        )
        data = overlay()
        world.merge_data(config.NAMESPACE, data)
        contribute_extensions(world, data)
        avatar = state["avatar"]  # troca o controlador padrão herdado (ADR-0062)
        controller = avatar["default_controller"]
        world.add_avatar(
            AvatarDef(str(avatar["id"]), ControllerRef(controller["type"], controller["id"])),
            override=True,
        )
        for entity_id, spawn in state.get("tools", {}).items():  # a pá nasce com o Camps
            world.spawn(SpawnDef(entity_id, str(spawn["kind"]), container_id=str(spawn["holder"])))

    def rules_file(self) -> Path | None:
        return DATA / "rules.yaml"
