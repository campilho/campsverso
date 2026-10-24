"""A feira da fazenda sobre a biblioteca de economia (ADR-0069): uma barraca que abre pela agenda (a
cada 7 dias na Morada do Sol), compra colheitas e produtos acima da referência, com pressão própria,
e paga na hora.

O cenário liga a feira com a seção `fair`. A barraca é uma entidade do mapa, com atributos visíveis:
`open`, `proxima_feira` (o dia da próxima, ou de hoje enquanto está aberta) e o preço de agora de
cada item (`preco_milho`). O fator de cada item fica oculto e volta a 1 a cada feira.
"""

from collections.abc import Mapping
from typing import Any, cast

from campsverso_cartridge_api import (
    ActionContext,
    EntityView,
    Rejection,
    SystemContext,
    WorldOps,
    WorldView,
)
from campsverso_economy import Recurring, Trade, sell, unit_price
from campsverso_farm_sim.config import optional, section
from campsverso_farm_sim.market import crop_reference, factor, memory_market, rules


def schedule(data: Mapping[str, Any]) -> Recurring:
    return Recurring(every=int(data["every"]), first=int(data["first"]))


def fair_stall(view: WorldView, target: object) -> EntityView | None:
    """A barraca da feira, se é ela o alvo pedido."""
    data = optional(view, "fair")
    if data is None or not isinstance(target, str):
        return None
    stall = next((e for e in view.entities(str(data["kind"])) if e.entity_id == target), None)
    return stall


def _items(view: WorldView) -> list[str]:
    data = section(view, "fair")
    wanted = set(cast(list[str], data.get("categories", ["colheita"])))
    items = section(view, "items")
    return sorted(i for i, info in items.items() if info.get("category") in wanted)


def fair_reference(view: WorldView, item: str) -> float:
    """O preço de referência na feira: a referência do mercado (a tabela, num cenário sem o mercado
    que lembra), mais o prêmio da feira."""
    premium = float(section(view, "fair")["premium"])
    info = section(view, "items", item)
    box = next(iter(view.entities("sell_box")), None)
    if info.get("category") == "colheita" and box is not None and memory_market(view) is not None:
        base = crop_reference(view, box, item)
    else:
        base = float(info["sale_price"])
    return base * (1.0 + premium)


def fair_hours(ctx: SystemContext, ops: WorldOps) -> None:
    """Abre a barraca no dia de feira e fecha na hora; na abertura, os preços partem da referência
    do dia, sem a pressão da feira anterior."""
    view = ctx.view
    data = section(view, "fair")
    when = schedule(data)
    opens, closes = str(data["opens"]), str(data["closes"])
    in_hours = view.ticks_until(closes) < view.ticks_until(opens)
    is_open = when.happens(view.day) and in_hours
    upcoming = when.next_on(view.day if is_open else view.day + 1)
    for stall in view.entities(str(data["kind"])):
        visible: dict[str, Any] = {"open": is_open, "proxima_feira": upcoming}
        hidden: dict[str, Any] = {}
        if is_open and int(cast(int, stall.hidden.get("fair_day") or 0)) != view.day:
            hidden["fair_day"] = view.day
            for item in _items(view):
                hidden[f"factor_{item}"] = 1.0
                visible[f"preco_{item}"] = unit_price(fair_reference(view, item), 1.0)
        ops.set_attributes(stall.entity_id, visible=visible, hidden=hidden)


def check_sale(ctx: ActionContext, stall: EntityView) -> Rejection | None:
    me = ctx.view.entity(ctx.avatar_id).position
    if me is None or stall.position is None or me.chebyshev(stall.position) > 1:
        return Rejection("not_adjacent")
    if not stall.attributes.get("open"):
        return Rejection("closed")
    qty = ctx.params.get("qty", 1)
    if not isinstance(qty, int) or qty < 1:
        return Rejection("invalid_params", "qty >= 1")
    item = ctx.params.get("item")
    if not isinstance(item, str) or item not in _items(ctx.view):
        return Rejection("invalid_params", "a feira não compra isso")
    if ctx.view.items(ctx.avatar_id).get(item, 0) < qty:
        return Rejection("missing_item")
    return None


def _trade(view: WorldView, stall: EntityView, item: str, qty: int) -> Trade:
    side = cast(Mapping[str, Any], section(view, "fair")["sell"])
    return sell(fair_reference(view, item), factor(stall, item), qty, rules(side))


def apply_sale(ctx: ActionContext, ops: WorldOps, stall: EntityView) -> None:
    """Vende na barraca: o item sai, as moedas entram na hora, e o preço daquele item cai."""
    item, qty = str(ctx.params["item"]), int(ctx.params.get("qty", 1))
    trade = _trade(ctx.view, stall, item, qty)
    ops.consume_item(item, qty, ctx.avatar_id, "fair_sale")
    ops.create_item("moeda", trade.total, ctx.avatar_id, "fair_payment")
    ops.set_attributes(
        stall.entity_id,
        visible={f"preco_{item}": trade.next_price},
        hidden={f"factor_{item}": trade.factor},
    )
