"""O mercado da fazenda sobre a biblioteca de economia (ADR-0069): a caixa de vendas que lembra o
que se vendeu e o quiosque cuja semente sobe quando se compra muito.

O cenário liga este mercado declarando `sell` e `buy` na seção `market`; sem eles, vale o mercado
do dia da Boa Vista (ADR-0062), que volta à tabela de manhã. O estado mora nos atributos:
- na caixa, o fator de cada colheita (`factor_milho`), a oscilação (`drift_milho`) e o choque do
  clima (`shock`, `shock_until`), ocultos; o preço de agora (`preco_milho`), visível;
- no quiosque, o fator de cada semente, oculto, e o preço de agora, visível.
"""

from collections.abc import Mapping
from typing import Any, cast

from campsverso_cartridge_api import EntityView, WorldOps, WorldView
from campsverso_economy import MarketRules, Trade, buy, drift, recover, reference, sell, unit_price
from campsverso_farm_sim.config import optional, season_level, section


def memory_market(view: WorldView) -> Mapping[str, Any] | None:
    """A seção `market` de um cenário com o mercado que lembra, ou nada."""
    market = optional(view, "market")
    return market if market is not None and "sell" in market else None


def rules(side: Mapping[str, Any]) -> MarketRules:
    return MarketRules(
        step=float(side["step"]),
        floor=float(side.get("floor", 0.0)),
        ceiling=float(side.get("ceiling", float("inf"))),
        recovery=float(side.get("recovery", 1.0)),
    )


def crop_reference(view: WorldView, box: EntityView, item: str) -> float:
    """A referência de hoje de uma colheita: a tabela, a estação (o que está fora dela é raro), a
    oscilação do dia e o choque do clima, se ainda vale."""
    market = section(view, "market")
    base = float(section(view, "items", item)["sale_price"])
    level = season_level(view, item, view.season(view.day))
    seasons = cast(Mapping[str, Any], market.get("season") or {})
    season = float(seasons.get(level, 1.0)) if level is not None else 1.0
    shocked = view.day <= int(box.hidden.get("shock_until") or 0)
    shock = float(box.hidden.get("shock") or 0.0) if shocked else 0.0
    return reference(base, season, float(box.hidden.get(f"drift_{item}") or 0.0), shock)


def factor(entity: EntityView, item: str) -> float:
    raw = entity.hidden.get(f"factor_{item}")
    return 1.0 if raw is None else float(raw)


def sell_to(view: WorldView, box: EntityView, item: str, qty: int) -> Trade:
    """Quanto valem `qty` unidades postas agora na caixa, e como fica o preço."""
    market = section(view, "market")
    return sell(crop_reference(view, box, item), factor(box, item), qty, rules(market["sell"]))


def buy_from(view: WorldView, kiosk: EntityView, item: str, qty: int) -> Trade:
    """Quanto custam `qty` sementes agora no quiosque, e como fica o preço."""
    market = section(view, "market")
    base = float(section(view, "items", item)["price"])
    return buy(base, factor(kiosk, item), qty, rules(market["buy"]))


def turnover(view: WorldView, ops: WorldOps) -> None:
    """A virada do dia: o fator de cada colheita recupera parte do caminho até a referência, a
    oscilação anda, e as sementes voltam à tabela. Uma vez por dia, mesmo que a sessão comece
    numa virada."""
    market = section(view, "market")
    sell_rules, buy_rules = rules(market["sell"]), rules(market["buy"])
    moves = cast(Mapping[str, Any], market.get("drift") or {"step": 0.0, "limit": 0.0})
    items = section(view, "items")
    crops = sorted(i for i, info in items.items() if info.get("category") == "colheita")
    rng = view.rng("market")
    for box in view.entities("sell_box"):
        if int(box.hidden.get("market_day") or 0) == view.day:
            continue
        hidden: dict[str, Any] = {"market_day": view.day}
        for item in crops:
            hidden[f"factor_{item}"] = recover(factor(box, item), sell_rules)
            previous = float(box.hidden.get(f"drift_{item}") or 0.0)
            hidden[f"drift_{item}"] = drift(
                previous, rng, float(moves["step"]), float(moves["limit"])
            )
        ops.set_attributes(box.entity_id, hidden=hidden)
        moved = view.entity(box.entity_id)  # com a oscilação de hoje
        visible = {
            f"preco_{item}": unit_price(crop_reference(view, moved, item), factor(moved, item))
            for item in crops
        }
        ops.set_attributes(box.entity_id, visible=visible)
    seeds = sorted(i for i, info in items.items() if info.get("category") == "semente")
    for kiosk in view.entities("kiosk"):
        stock = set(str(kiosk.attributes.get("estoque_hoje") or "").split(", "))
        hidden = {f"factor_{item}": recover(factor(kiosk, item), buy_rules) for item in seeds}
        visible: dict[str, Any] = {  # só a semente do estoque de hoje tem preço na vitrine
            f"preco_{item}": unit_price(float(items[item]["price"]), hidden[f"factor_{item}"])
            if item in stock
            else None
            for item in seeds
        }
        ops.set_attributes(kiosk.entity_id, visible=visible, hidden=hidden)
