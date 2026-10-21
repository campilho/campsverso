"""O que um cenário liga por cima do gênero (ADR-0062): itens com peso e validade, tipos com
capacidade, as ações e os sistemas da Fazenda Boa Vista, as afordâncias e as métricas dele.

O gênero registra o básico a partir do seu `farm.yaml`; um cenário que quer mais chama
`contribute_extensions` com o seu arquivo (mesclado antes no namespace `farm`). O que não está
no arquivo do cenário não é ligado: a fazenda 1 não passa por aqui.
"""

from collections.abc import Mapping
from typing import Any, cast

from campsverso_cartridge_api import ItemDef, KindDef, WorldBuilder
from campsverso_farm_sim import config
from campsverso_farm_sim.actions import ALL_ACTIONS, EXTRA_ACTIONS, INTERRUPTS
from campsverso_farm_sim.cartridge import affordances, metrics
from campsverso_farm_sim.systems import build_extension_systems


def contribute_extensions(world: WorldBuilder, data: Mapping[str, Any]) -> None:
    base = config.load()
    for item, info in cast(Mapping[str, Mapping[str, Any]], data.get("items", {})).items():
        shelf = info.get("shelf_life_days")
        world.define_item(
            ItemDef(
                item,
                str(info["category"]),
                weight=float(info.get("weight", 0.0)),
                shelf_life_days=None if shelf is None else int(shelf),
            ),
            override=item in base["items"],
        )
    base_kinds = {
        "avatar",
        "plot",
        "bed",
        "table",
        "chest",
        "sell_box",
        "well",
        "kiosk",
        "door",
        "watering_can",
    }
    for kind, info in cast(Mapping[str, Mapping[str, Any]], data.get("kinds", {})).items():
        capacity = info.get("capacity")
        world.define_kind(
            KindDef(
                kind,
                blocking=bool(info.get("blocking", False)),
                attributes=dict(info.get("attributes", {})),
                hidden=dict(info.get("hidden", {})),
                capacity=None if capacity is None else float(capacity),
                shelf_life_factor=float(info.get("shelf_life_factor", 1.0)),
                weight=float(info.get("weight", 0.0)),
            ),
            override=kind in base_kinds,
        )
    known = {action.name for action in ALL_ACTIONS}
    for name, numbers in cast(Mapping[str, Mapping[str, Any]], data.get("actions", {})).items():
        if numbers.get("interrupt") not in INTERRUPTS:  # ADR-0052
            raise ValueError(f"{name} precisa de interrupt em {INTERRUPTS}")
        if name in known:
            continue
        action = next((a for a in EXTRA_ACTIONS if a.name == name), None)
        if action is None:
            raise ValueError(f"ação desconhecida no cenário: {name}")
        world.add_action(action)
    for system in build_extension_systems(data):
        world.add_system(system)
    # As afordâncias do gênero resolveram as escolhas (culturas, itens por categoria) com os dados
    # do gênero; o cenário as resolve de novo com as culturas e os itens somados, e troca as que
    # declara. Sem isso, o menu de plantar da Boa Vista só oferecia as três culturas da fazenda 1.
    declared = {str(entry["action"]) for entry in data.get("affordances", [])}
    inherited = [e for e in base.get("affordances", []) if str(e["action"]) not in declared]
    catalog = {
        "crops": {**base.get("crops", {}), **data.get("crops", {})},
        "items": {
            **base.get("items", {}),
            **{
                name: {**base.get("items", {}).get(name, {}), **info}
                for name, info in cast(
                    Mapping[str, Mapping[str, Any]], data.get("items", {})
                ).items()
            },
        },
        "affordances": [*inherited, *data.get("affordances", [])],
    }
    for affordance in affordances(catalog):
        world.add_affordance(affordance, replace=True)  # o cenário troca a do gênero
    base_metrics = {str(m["id"]) for m in base.get("metrics", [])}
    for metric in metrics(data):
        world.add_metric(metric, override=metric.id in base_metrics)  # o cenário troca a do gênero
    movement = cast(Mapping[str, Any], data.get("movement", {}))
    if movement.get("energy_per_tile"):
        world.set_movement_cost(config.ENERGY, float(movement["energy_per_tile"]))
