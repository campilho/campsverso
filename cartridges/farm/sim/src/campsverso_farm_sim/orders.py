"""As encomendas da fazenda sobre a biblioteca de economia (ADR-0069).

O cenário liga as encomendas com a seção `orders`. O quadro é uma entidade do mapa, e cada pedido
é uma entidade dentro dele (`order-003`), com o que se pede nos atributos visíveis:
- `cliente`, `item`, `quantidade`, `pagamento` (o total, na entrega) e `prazo` (o último dia);
- `aceita_por`: o avatar que aceitou, ou nada.

A reputação de cada avatar mora nos atributos ocultos do quadro (`reputation_camps`). Na Morada do
Sol ela é a regra oculta R-004: quem cumpre o prazo vê mais pedidos e prêmios maiores.
"""

from collections.abc import Mapping
from typing import Any, cast

from campsverso_cartridge_api import EntityView, SpawnDef, SystemContext, WorldOps, WorldView
from campsverso_economy import (
    Order,
    OrderRules,
    ReputationRules,
    after_expiry,
    draw,
    expired,
)
from campsverso_farm_sim.config import optional, season_level, section
from campsverso_farm_sim.market import crop_reference, memory_market

ORDER_KIND = "order"


def order_rules(data: Mapping[str, Any]) -> OrderRules:
    qty = cast(list[int], data["qty"])
    days = cast(list[int], data["days"])
    return OrderRules(
        max_open=int(data["max_open"]),
        max_taken=int(data["max_taken"]),
        new_per_day=int(data["new_per_day"]),
        chance=float(data["chance"]),
        qty=(int(qty[0]), int(qty[1])),
        days=(int(days[0]), int(days[1])),
        premium=float(data["premium"]),
    )


def reputation_rules(data: Mapping[str, Any]) -> ReputationRules:
    rep = cast(Mapping[str, Any], data.get("reputation") or {})
    return ReputationRules(
        start=float(rep.get("start", 0.5)),
        gain=float(rep.get("gain", 0.1)),
        loss=float(rep.get("loss", 0.2)),
        spread=float(rep.get("spread", 0.5)),
    )


def boards(view: WorldView) -> list[EntityView]:
    data = optional(view, "orders")
    return [] if data is None else list(view.entities(str(data["board_kind"])))


def in_board(view: WorldView, board: EntityView) -> list[EntityView]:
    """Os pedidos do quadro, em ordem de id."""
    found = [e for e in view.entities(ORDER_KIND) if e.container_id == board.entity_id]
    return sorted(found, key=lambda e: e.entity_id)


def as_order(entity: EntityView) -> Order:
    a = entity.attributes
    taker = a.get("aceita_por")
    return Order(
        order_id=entity.entity_id,
        client=str(a["cliente"]),
        item=str(a["item"]),
        qty=int(cast(int, a["quantidade"])),
        reward=int(cast(int, a["pagamento"])),
        posted_day=int(cast(int, entity.hidden.get("posted_day") or 0)),
        due_day=int(cast(int, a["prazo"])),
        taker=None if taker is None else str(taker),
    )


def reputation(board: EntityView, taker: str, rules: ReputationRules) -> float:
    raw = board.hidden.get(f"reputation_{taker}")
    return rules.start if raw is None else float(cast(float, raw))


def board_reputation(board: EntityView, rules: ReputationRules) -> float:
    """A reputação que pesa no quadro: a média de quem já negociou com ele, ou a inicial."""
    known = [float(cast(float, v)) for k, v in board.hidden.items() if k.startswith("reputation_")]
    return sum(known) / len(known) if known else rules.start


def taken_by(view: WorldView, board: EntityView, taker: str) -> int:
    return sum(1 for e in in_board(view, board) if e.attributes.get("aceita_por") == taker)


def label(order: Order) -> str:
    """Como o pedido aparece no quadro e no menu."""
    item = order.item.replace("_", " ")
    return f"{order.client}: {order.qty} {item} até o dia {order.due_day}, paga {order.reward}"


def _candidates(view: WorldView) -> list[tuple[str, float]]:
    """O que se pede hoje: as colheitas fora da estação parada, pela referência do mercado (ou da
    tabela, num cenário sem o mercado que lembra), e os produtos do tacho, se houver."""
    data = section(view, "orders")
    items = section(view, "items")
    season = view.season(view.day)
    box = next(iter(view.entities("sell_box")), None)
    found: list[tuple[str, float]] = []
    for item, info in sorted(items.items()):
        category = info.get("category")
        if category not in cast(list[str], data.get("categories", ["colheita"])):
            continue
        if category == "colheita" and season_level(view, item, season) == "parada":
            continue
        if box is not None and memory_market(view) is not None:
            found.append((item, crop_reference(view, box, item)))
        else:
            found.append((item, float(info["sale_price"])))
    return found


def orders_daily(ctx: SystemContext, ops: WorldOps) -> None:
    """Na virada do dia: os pedidos vencidos saem do quadro (o aceito pesa na reputação de quem
    aceitou), e os novos aparecem, sorteados pelo RNG `orders`."""
    view = ctx.view
    data = section(view, "orders")
    rules, rep_rules = order_rules(data), reputation_rules(data)
    clients = [str(c) for c in cast(list[Any], data["clients"])]
    for board in boards(view):
        if int(cast(int, board.hidden.get("orders_day") or 0)) == view.day:
            continue  # a sessão que começa numa virada não sorteia duas vezes
        ops.set_attributes(board.entity_id, hidden={"orders_day": view.day})
        for entity in in_board(view, board):
            order = as_order(entity)
            if not expired(order, view.day):
                continue
            ops.despawn(entity.entity_id, "expired")
            payload: dict[str, Any] = {
                "order_id": order.order_id,
                "client": order.client,
                "item": order.item,
                "qty": order.qty,
                "due_day": order.due_day,
                "day": view.day,
            }
            if order.taker is not None:
                payload["taker"] = order.taker
                lowered = after_expiry(reputation(board, order.taker, rep_rules), rep_rules)
                ops.set_attributes(board.entity_id, hidden={f"reputation_{order.taker}": lowered})
            ops.emit("campsverso.economy.order.expired.v1", payload)
        board = view.entity(board.entity_id)
        fresh = draw(
            view.rng("orders"),
            view.day,
            len(in_board(view, board)),
            _candidates(view),
            clients,
            rules,
            board_reputation(board, rep_rules),
            rep_rules,
            lambda: f"order-{ops.next_seq(ORDER_KIND):03d}",
        )
        for order in fresh:
            ops.spawn(
                SpawnDef(
                    order.order_id,
                    ORDER_KIND,
                    container_id=board.entity_id,
                    display_name=label(order),
                    attributes={
                        "cliente": order.client,
                        "item": order.item,
                        "quantidade": order.qty,
                        "pagamento": order.reward,
                        "prazo": order.due_day,
                        "aceita_por": None,
                    },
                    hidden={"posted_day": order.posted_day},
                )
            )
            ops.emit(
                "campsverso.economy.order.posted.v1",
                {
                    "order_id": order.order_id,
                    "board_id": board.entity_id,
                    "client": order.client,
                    "item": order.item,
                    "qty": order.qty,
                    "reward": order.reward,
                    "posted_day": order.posted_day,
                    "due_day": order.due_day,
                },
            )
