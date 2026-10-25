"""Cartucho farm_morada_do_sol, a Fazenda Morada do Sol (bíblia 3; ADR-0067): estende a Boa Vista.

Herda o Camps, as ferramentas, o fogão, o baú, o mercado e a arte das camadas de baixo, e
troca o mapa (64 por 40 tiles, maior que a tela), o raio da percepção e o que é deste cenário: o
ano de 28 dias com as quatro estações, a afinidade de cada cultura com cada estação, quatro
culturas novas, canteiros sem teto que voltam a ser grama, o espantalho, os corvos (R-002) e a
fadiga do solo (R-003). Tudo isso é dado (`data/morada.yaml`) sobre o código do gênero farm. O
mapa tem variantes (`data/maps/`, ADR-0070), que o arquivo do mundo escolhe.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

import yaml

from campsverso_cartridge_api import CartridgeManifest, WorldBuilder
from campsverso_farm_boavista_sim.cartridge import overlay as boavista
from campsverso_farm_sim import config
from campsverso_farm_sim.extensions import contribute_extensions

DATA = Path(__file__).parent / "data"


def overlay() -> dict[str, Any]:
    return cast(dict[str, Any], yaml.safe_load((DATA / "morada.yaml").read_text(encoding="utf-8")))


@dataclass(frozen=True)
class FarmMoradaDoSolCartridge:
    manifest: CartridgeManifest = field(
        default_factory=lambda: CartridgeManifest(
            "farm_morada_do_sol", "0.1.0", extends=("farm_boavista",)
        )
    )

    def contribute(self, world: WorldBuilder) -> None:
        world.set_map(json.loads((DATA / "map.tmj").read_text(encoding="utf-8")))
        # As variantes (ADR-0070): o mesmo sítio com a água em outro lugar; o mundo escolhe uma.
        for variant in sorted((DATA / "maps").glob("*.tmj")):
            world.add_map_variant(variant.stem, json.loads(variant.read_text(encoding="utf-8")))
        data = overlay()
        world.merge_data(config.NAMESPACE, data)
        # A Boa Vista já ligou o que é dela (o mercado, o quiosque, as ferramentas): aqui só se
        # troca e se acrescenta, com os menus resolvidos pelas três camadas.
        contribute_extensions(world, data, inherited=boavista())

    def rules_file(self) -> Path | None:
        return DATA / "rules.yaml"
