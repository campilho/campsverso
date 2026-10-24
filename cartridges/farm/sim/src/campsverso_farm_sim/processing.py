"""O processamento (ADR-0069): máquinas que transformam ingredientes num produto, trabalhando
sozinhas por horas enquanto o avatar segue a vida. Na Morada do Sol, o tacho faz o que vale mais e
dura mais (geleia, molho de tomate, farinha), e a composteira faz adubo do que ia se perder.

O cenário liga as máquinas com `processing.machines`, uma receita por vez em cada máquina:
- os ingredientes são itens com quantidade, ou `any` (as categorias aceitas) com `qty`, e então
  quem carrega escolhe o item;
- a máquina guarda a receita em andamento nos atributos ocultos, e mostra `fazendo` e
  `faltam_horas`;
- o produto aparece dentro dela e espera ser pego (`withdraw`).
"""

import math
from collections.abc import Mapping
from typing import Any, cast

from campsverso_cartridge_api import EntityView, Rejection, SystemContext, WorldOps, WorldView
from campsverso_farm_sim.config import optional, section, ticks_per_hour

HOURS = tuple(f"{hour:02d}:00" for hour in range(24))


def machine(view: WorldView, target: object) -> EntityView | None:
    """A máquina pedida, se o alvo é uma."""
    kinds = optional(view, "processing", "machines")
    if kinds is None or not isinstance(target, str):
        return None
    found = next((e for e in view.entities() if e.entity_id == target), None)
    return found if found is not None and found.kind in kinds else None


def recipe(view: WorldView, kind: str, name: object) -> Mapping[str, Any] | None:
    recipes = optional(view, "processing", "machines", kind, "recipes")
    if recipes is None or not isinstance(name, str) or name not in recipes:
        return None
    return cast(Mapping[str, Any], recipes[name])


def ingredients(
    view: WorldView, chosen: Mapping[str, Any], item: object
) -> dict[str, int] | Rejection:
    """O que a receita consome: os itens fixos, ou o item escolhido de uma das categorias."""
    raw = cast(Mapping[str, Any], chosen["ingredients"])
    if "any" not in raw:
        return {str(k): int(v) for k, v in sorted(raw.items())}
    info = section(view, "items").get(item) if isinstance(item, str) else None
    if info is None or info.get("category") not in cast(list[str], raw["any"]):
        return Rejection("invalid_params", "escolha um item que a receita aceita")
    return {str(item): int(raw["qty"])}


def busy(entity: EntityView) -> bool:
    return entity.hidden.get("batch") is not None


def start(view: WorldView, ops: WorldOps, entity: EntityView, name: str, hours: float) -> None:
    done = view.tick + int(hours * ticks_per_hour(view))
    ops.set_attributes(
        entity.entity_id,
        visible={"fazendo": name, "faltam_horas": math.ceil(hours)},
        hidden={"batch": name, "done_tick": done},
    )


def machines_hourly(ctx: SystemContext, ops: WorldOps) -> None:
    """De hora em hora: a receita que terminou vira produto dentro da máquina."""
    view = ctx.view
    kinds = section(view, "processing", "machines")
    for kind in sorted(kinds):
        for entity in view.entities(kind):
            name = entity.hidden.get("batch")
            if name is None:
                continue
            done = int(cast(int, entity.hidden["done_tick"]))
            if view.tick < done:
                left = math.ceil((done - view.tick) / ticks_per_hour(view))
                ops.set_attributes(entity.entity_id, visible={"faltam_horas": left})
                continue
            chosen = recipe(view, kind, name)
            assert chosen is not None
            makes = chosen["makes"]
            ops.create_item(str(makes), int(chosen.get("qty", 1)), entity.entity_id, "process")
            ops.set_attributes(
                entity.entity_id,
                visible={"fazendo": None, "faltam_horas": None},
                hidden={"batch": None, "done_tick": None},
            )
