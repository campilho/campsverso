"""Ações do gênero fazenda (bíblia §8). Duração e custo vêm dos dados; efeitos, das primitivas."""

import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, ClassVar, cast

from campsverso_cartridge_api import (
    Accepted,
    ActionContext,
    EntityView,
    Interrupt,
    Position,
    Rejection,
    SpawnDef,
    Validation,
    WorldOps,
    WorldView,
)
from campsverso_economy import after_delivery, refuse_delivery, refuse_take
from campsverso_farm_sim import helpers
from campsverso_farm_sim.config import ENERGY, HUNGER, optional, section, ticks_per_hour
from campsverso_farm_sim.fair import apply_sale, check_sale, fair_stall
from campsverso_farm_sim.market import buy_from, memory_market, sell_to
from campsverso_farm_sim.orders import (
    as_order,
    in_board,
    order_rules,
    reputation,
    reputation_rules,
    taken_by,
)
from campsverso_farm_sim.processing import busy, ingredients, machine, recipe, start
from campsverso_farm_sim.weather import can_cost, wet

EMPTY_PLOT: dict[str, Any] = {"crop": None, "stage": None, "watered_today": False}
EMPTY_HIDDEN: dict[str, Any] = {"growth_points": 0.0, "planted_day": None, "dry_days": 0}
FULL = 100.0  # energia cheia (bíblia §7)


def find(view: WorldView, kind: str, target: object) -> EntityView | Rejection:
    """O alvo pedido, ou o único/primeiro do tipo quando a ação não pede alvo."""
    candidates = view.entities(kind)
    if target is None:
        return candidates[0] if candidates else Rejection("invalid_params", f"não há {kind}")
    match = next((e for e in candidates if e.entity_id == target), None)
    return match or Rejection("invalid_params", f"{target!r} não é um {kind}")


def adjacent(view: WorldView, avatar_id: str, entity: EntityView) -> bool:
    me = view.entity(avatar_id).position
    return me is not None and entity.position is not None and me.chebyshev(entity.position) <= 1


def quantity(params: Mapping[str, Any]) -> int | Rejection:
    qty = params.get("qty", 1)
    return qty if isinstance(qty, int) and qty >= 1 else Rejection("invalid_params", "qty >= 1")


def held(view: WorldView, avatar_id: str, kind: str) -> EntityView | None:
    """A primeira entidade deste tipo no inventário do avatar (uma ferramenta)."""
    return next((e for e in view.entities(kind) if e.container_id == avatar_id), None)


def can_kinds(view: WorldView) -> tuple[str, ...]:
    """Os tipos de regador, na ordem de preferência do cenário (ADR-0062); só um na v0.1."""
    tools = optional(view, "tools")
    kinds = tools.get("watering_cans") if tools else None
    return tuple(str(k) for k in cast(list[Any], kinds)) if kinds else ("watering_can",)


def watering_cans(view: WorldView, avatar_id: str) -> list[EntityView]:
    return [
        e for kind in can_kinds(view) for e in view.entities(kind) if e.container_id == avatar_id
    ]


def watering_can(view: WorldView, avatar_id: str) -> EntityView | None:
    """O regador para regar: o primeiro, na ordem do cenário, que tenha carga; senão, o primeiro."""
    cans = watering_cans(view, avatar_id)
    with_charge = [c for c in cans if int(c.attributes.get("charges") or 0) > 0]
    return (with_charge or cans)[0] if cans else None


def tool_weight(view: WorldView, tool: EntityView) -> float:
    """O peso de uma ferramenta, pelo tipo dela nos dados do cenário."""
    kinds = optional(view, "kinds") or {}
    info = cast(Mapping[str, Any], kinds.get(tool.kind) or {})
    return float(info.get("weight", 0.0))


def has_plow(view: WorldView, avatar_id: str) -> bool:
    tools = optional(view, "tools")
    kind = tools.get("plow_kind") if tools else None
    return kind is not None and held(view, avatar_id, str(kind)) is not None


def storable_kinds(view: WorldView) -> tuple[str, ...]:
    tools = optional(view, "tools")
    kinds = tools.get("storable") if tools else None
    return tuple(str(k) for k in cast(list[Any], kinds)) if kinds else ()


def tool_in(view: WorldView, container_id: str, entity_id: object) -> EntityView | None:
    """A ferramenta com este id dentro do contêiner, se for de um tipo que se guarda."""
    if not isinstance(entity_id, str):
        return None
    return next(
        (
            e
            for kind in storable_kinds(view)
            for e in view.entities(kind)
            if e.entity_id == entity_id and e.container_id == container_id
        ),
        None,
    )


def item_info(view: WorldView, item: object) -> Mapping[str, Any] | None:
    items = section(view, "items")
    return items.get(item) if isinstance(item, str) else None


INTERRUPTS: tuple[Interrupt, ...] = ("never", "cancel", "partial")


@dataclass(frozen=True)
class FarmAction:
    name: str = ""
    # O que outro avatar pode desfazer no meio da ação (o canteiro, o baú, o lugar de cavar): a
    # conferência se repete na conclusão (ADR-0072). O que muda com a hora (o quiosque que fecha,
    # a feira) fica de fora: com um avatar só, a ação conclui como sempre concluiu.
    shared: ClassVar[bool] = False

    def check(self, ctx: ActionContext) -> Rejection | None:
        raise NotImplementedError

    def recheck(self, ctx: ActionContext) -> Rejection | None:
        return self.check(ctx) if self.shared else None

    def apply(self, ctx: ActionContext, ops: WorldOps) -> None:
        raise NotImplementedError

    def numbers(self, ctx: ActionContext) -> Mapping[str, Any]:
        """Duração, energia e política da ação; com o arado no inventário, a variante `with_plow`
        dos dados substitui o que declarar (ADR-0062)."""
        base = section(ctx.view, "actions", self.name)
        plowed = base.get("with_plow")
        if isinstance(plowed, Mapping) and has_plow(ctx.view, ctx.avatar_id):
            return {**base, **cast(Mapping[str, Any], plowed)}
        return base

    def validate(self, ctx: ActionContext) -> Validation:
        rejection = self.check(ctx)
        if rejection is not None:
            return rejection
        numbers = self.numbers(ctx)
        # `interrupt` é obrigatório nos dados e conferido ao montar o mundo (ADR-0052)
        return Accepted(int(numbers["duration"]), cast(Interrupt, numbers["interrupt"]))

    def complete(self, ctx: ActionContext, ops: WorldOps) -> None:
        self.apply(ctx, ops)
        energy = float(self.numbers(ctx)["energy"])
        if energy:
            hungry = ctx.view.need(ctx.avatar_id, HUNGER) >= float(
                section(ctx.view)["hunger_doubles_energy_at"]
            )
            ops.change_need(ctx.avatar_id, ENERGY, -(energy * 2 if hungry else energy))

    def interrupted(self, ctx: ActionContext, ops: WorldOps, elapsed_ticks: int) -> None:
        pass  # nenhuma ação da fazenda é `partial` na v0.1 (ADR-0052)


def empty_hidden(view: WorldView, target: str) -> dict[str, Any]:
    """O estado oculto de um canteiro vazio; os campos da fazenda 2 só onde já existiam."""
    hidden = dict(EMPTY_HIDDEN)
    plot = view.entity(target)
    current = plot.hidden
    for key in ("bonus_points", "ripe_days", "empty_days"):
        if key in current:
            hidden[key] = 0.0 if key == "bonus_points" else 0
    if "last_crop" in current:  # a cultura que saiu, para a fadiga do solo (ADR-0067)
        hidden["last_crop"] = plot.attributes.get("crop")
    return hidden


def _plot(ctx: ActionContext) -> EntityView | Rejection:
    plot = find(ctx.view, "plot", ctx.params.get("target"))
    if isinstance(plot, Rejection):
        return plot
    if not adjacent(ctx.view, ctx.avatar_id, plot):
        return Rejection("not_adjacent")
    return plot


@dataclass(frozen=True)
class Plant(FarmAction):
    name: str = "plant"
    shared: ClassVar[bool] = True

    def check(self, ctx: ActionContext) -> Rejection | None:
        plot = _plot(ctx)
        if isinstance(plot, Rejection):
            return plot
        if plot.attributes.get("crop") is not None:
            return Rejection("plot_occupied")
        crops = section(ctx.view, "crops")
        crop = ctx.params.get("crop")
        if not isinstance(crop, str) or crop not in crops:
            return Rejection("invalid_params", "cultura desconhecida")
        if ctx.view.items(ctx.avatar_id).get(str(crops[crop]["seed"]), 0) < 1:
            return Rejection("missing_item")
        return None

    def apply(self, ctx: ActionContext, ops: WorldOps) -> None:
        crop = str(ctx.params["crop"])
        target = str(ctx.params["target"])
        seed = str(section(ctx.view, "crops", crop)["seed"])
        ops.consume_item(seed, 1, ctx.avatar_id, "plant")
        loss = ctx.view.entity(ctx.avatar_id).hidden.get("perde_semente")  # a ficha (ADR-0072)
        if (
            isinstance(loss, int | float)
            and ctx.view.items(ctx.avatar_id).get(seed, 0) >= 1
            and ctx.view.rng("helpers").random() < float(loss)
        ):
            ops.consume_item(seed, 1, ctx.avatar_id, "seed_lost")
        rained = wet(ctx.view, ctx.view.day)  # chuva conta como rega (ADR-0039)
        visible: dict[str, Any] = {"crop": crop, "stage": "semente", "watered_today": rained}
        hidden: dict[str, Any] = {"growth_points": 0.0, "planted_day": ctx.view.day, "dry_days": 0}
        plot = ctx.view.entity(target)
        if plot.attributes.get("adubado"):  # o adubo vale para este plantio (ADR-0062)
            fertilizer = optional(ctx.view, "fertilizer") or {}
            visible["adubado"] = False
            hidden["bonus_points"] = float(fertilizer.get("bonus_points", 0.0))
            hidden["ripe_days"] = 0
        elif "bonus_points" in plot.hidden:
            hidden["bonus_points"] = 0.0
            hidden["ripe_days"] = 0
        ops.set_attributes(target, visible=visible, hidden=hidden)


@dataclass(frozen=True)
class Water(FarmAction):
    name: str = "water"
    shared: ClassVar[bool] = True

    def check(self, ctx: ActionContext) -> Rejection | None:
        plot = _plot(ctx)
        if isinstance(plot, Rejection):
            return plot
        if plot.attributes.get("crop") is None or plot.attributes.get("stage") == "murcha":
            return Rejection("no_plant")
        can = watering_can(ctx.view, ctx.avatar_id)
        if can is None:
            return Rejection("missing_item", "sem regador")
        if int(can.attributes.get("charges") or 0) < can_cost(ctx.view):  # a seca gasta mais
            return Rejection("can_empty")
        return None

    def apply(self, ctx: ActionContext, ops: WorldOps) -> None:
        can = watering_can(ctx.view, ctx.avatar_id)
        assert can is not None
        charges = int(can.attributes["charges"] or 0) - can_cost(ctx.view)
        ops.set_attributes(can.entity_id, visible={"charges": charges})
        ops.set_attributes(str(ctx.params["target"]), visible={"watered_today": True})


@dataclass(frozen=True)
class Refill(FarmAction):
    name: str = "refill"

    def check(self, ctx: ActionContext) -> Rejection | None:
        well = find(ctx.view, "well", ctx.params.get("target"))
        if isinstance(well, Rejection):
            return well
        if not adjacent(ctx.view, ctx.avatar_id, well):
            return Rejection("not_adjacent")
        return (
            None
            if watering_can(ctx.view, ctx.avatar_id)
            else Rejection("missing_item", "sem regador")
        )

    def apply(self, ctx: ActionContext, ops: WorldOps) -> None:
        for can in watering_cans(ctx.view, ctx.avatar_id):  # com dois regadores, enche os dois
            ops.set_attributes(can.entity_id, visible={"charges": can.attributes["capacity"]})


@dataclass(frozen=True)
class Harvest(FarmAction):
    name: str = "harvest"
    shared: ClassVar[bool] = True

    def check(self, ctx: ActionContext) -> Rejection | None:
        plot = _plot(ctx)
        if isinstance(plot, Rejection):
            return plot
        if plot.attributes.get("stage") != "madura":
            return Rejection("not_ripe")
        crop = str(plot.attributes.get("crop"))
        return None if ctx.view.fits(crop, 1, ctx.avatar_id) else Rejection("too_heavy")

    def apply(self, ctx: ActionContext, ops: WorldOps) -> None:
        target = str(ctx.params["target"])
        crop = str(ctx.view.entity(target).attributes["crop"])
        ops.create_item(crop, 1, ctx.avatar_id, "harvest")
        ops.set_attributes(target, visible=EMPTY_PLOT, hidden=empty_hidden(ctx.view, target))
        ops.explain_effects(target)  # regras (inclusive ocultas) que ajudaram a planta (internal)


@dataclass(frozen=True)
class Clear(FarmAction):
    name: str = "clear"
    shared: ClassVar[bool] = True

    def check(self, ctx: ActionContext) -> Rejection | None:
        plot = _plot(ctx)
        if isinstance(plot, Rejection):
            return plot
        return None if plot.attributes.get("stage") == "murcha" else Rejection("not_withered")

    def apply(self, ctx: ActionContext, ops: WorldOps) -> None:
        target = str(ctx.params["target"])
        ops.set_attributes(target, visible=EMPTY_PLOT, hidden=empty_hidden(ctx.view, target))
        rest = optional(ctx.view, "clear_yields")  # os restos da planta murcha (ADR-0069)
        if rest is not None and ctx.view.fits(str(rest["item"]), int(rest["qty"]), ctx.avatar_id):
            ops.create_item(str(rest["item"]), int(rest["qty"]), ctx.avatar_id, "clear")


@dataclass(frozen=True)
class Eat(FarmAction):
    name: str = "eat"

    def check(self, ctx: ActionContext) -> Rejection | None:
        info = item_info(ctx.view, ctx.params.get("item"))
        if info is None or not info.get("hunger"):
            return Rejection("not_edible")
        if ctx.view.items(ctx.avatar_id).get(str(ctx.params["item"]), 0) < 1:
            return Rejection("missing_item")
        return None

    def apply(self, ctx: ActionContext, ops: WorldOps) -> None:
        item = str(ctx.params["item"])
        info = section(ctx.view, "items", item)
        ops.consume_item(item, 1, ctx.avatar_id, "eat")
        ops.change_need(ctx.avatar_id, HUNGER, -float(info["hunger"]))
        satiety = info.get("satiety")
        if isinstance(satiety, Mapping):  # a fome sobe mais devagar por umas horas (ADR-0062)
            satiety = cast(Mapping[str, Any], satiety)
            ticks = int(float(satiety["hours"]) * ticks_per_hour(ctx.view))
            ops.add_need_modifier(
                ctx.avatar_id, HUNGER, float(satiety["factor"]), ticks, "satisfeito_ate"
            )


@dataclass(frozen=True)
class MoveItems(FarmAction):
    """Base de depositar, retirar e vender: transfere itens entre o avatar e um contêiner."""

    shared: ClassVar[bool] = True  # o baú é de todos: o item pode ter saído, o espaço acabado
    kind: str = ""
    to_container: bool = True
    reason: str = ""
    only_category: str | None = None

    def categories(self, ctx: ActionContext) -> tuple[str, ...] | None:
        """As categorias de item que esta ação move; nada é qualquer uma."""
        del ctx
        return None if self.only_category is None else (self.only_category,)

    def _container(self, ctx: ActionContext) -> EntityView | Rejection:
        container = find(ctx.view, self.kind, ctx.params.get("target"))
        if isinstance(container, Rejection):
            return container
        return (
            container if adjacent(ctx.view, ctx.avatar_id, container) else Rejection("not_adjacent")
        )

    def _ends(self, ctx: ActionContext, container: EntityView) -> tuple[str, str]:
        if self.to_container:
            return ctx.avatar_id, container.entity_id
        return container.entity_id, ctx.avatar_id

    def check(self, ctx: ActionContext) -> Rejection | None:
        container = self._container(ctx)
        if isinstance(container, Rejection):
            return container
        source, target = self._ends(ctx, container)
        tool = tool_in(ctx.view, source, ctx.params.get("item"))
        if tool is not None and self.only_category is None:  # uma ferramenta, pelo id (ADR-0062)
            limit = ctx.view.entity(ctx.avatar_id).hidden.get("peso_max_ferramenta")  # ADR-0072
            heavy = isinstance(limit, int | float) and tool_weight(ctx.view, tool) > float(limit)
            if target == ctx.avatar_id and heavy:
                return Rejection("too_heavy")
            return None if ctx.view.fits_entity(tool.kind, target) else Rejection("too_heavy")
        qty = quantity(ctx.params)
        if isinstance(qty, Rejection):
            return qty
        info = item_info(ctx.view, ctx.params.get("item"))
        if info is None:
            return Rejection("invalid_params", "item desconhecido")
        allowed = self.categories(ctx)
        if allowed is not None and info.get("category") not in allowed:
            return Rejection("invalid_params", f"só {', '.join(allowed)}")
        item = str(ctx.params["item"])
        if ctx.view.items(source).get(item, 0) < qty:
            return Rejection("missing_item")
        return None if ctx.view.fits(item, qty, target) else Rejection("too_heavy")

    def apply(self, ctx: ActionContext, ops: WorldOps) -> None:
        container = self._container(ctx)
        assert not isinstance(container, Rejection)
        source, target = self._ends(ctx, container)
        tool = tool_in(ctx.view, source, ctx.params.get("item"))
        if tool is not None and self.only_category is None:
            ops.move_entity(tool.entity_id, target)
            return
        item, qty = str(ctx.params["item"]), int(ctx.params.get("qty", 1))
        ops.transfer_item(item, qty, source, target, self.reason)
        if self.reason == "sell":  # quem recebe o pagamento às 06:00 (ADR-0039)
            # O que o ajudante vende é do patrão (ADR-0072).
            hidden: dict[str, Any] = {"payee": helpers.payee(ctx.view, ctx.avatar_id)}
            if memory_market(ctx.view) is not None:  # a caixa que lembra (ADR-0069)
                trade = sell_to(ctx.view, container, item, qty)
                owed = float(container.hidden.get(f"value_{item}") or 0.0) + trade.total
                hidden[f"factor_{item}"] = trade.factor
                hidden[f"value_{item}"] = round(owed, 2)
                visible = {f"preco_{item}": trade.next_price}
                ops.set_attributes(container.entity_id, visible=visible, hidden=hidden)
                return
            market = optional(ctx.view, "market")
            if market is not None:  # o preço do dia cai a cada `step` unidades (ADR-0062)
                base = int(section(ctx.view, "items", item)["sale_price"])
                sold = int(container.hidden.get(f"sold_{item}") or 0)
                value = float(container.hidden.get(f"value_{item}") or 0.0)
                for _ in range(qty):
                    value += market_price(market, base, sold)
                    sold += 1
                hidden[f"sold_{item}"] = sold
                hidden[f"value_{item}"] = round(value, 2)
                ops.set_attributes(
                    container.entity_id,
                    visible={f"preco_{item}": market_price(market, base, sold)},
                    hidden=hidden,
                )
                return
            ops.set_attributes(container.entity_id, hidden=hidden)


def market_price(market: Mapping[str, Any], base: int, sold_today: int) -> int:
    """O preço da próxima unidade: `drop` a cada `step` vendidas hoje, até `floor` (ADR-0062)."""
    steps = sold_today // int(market["step"])
    fraction = max(float(market["floor"]), 1.0 - float(market["drop"]) * steps)
    return int(base * fraction + 0.5)  # meio para cima, sem o arredondamento bancário


def _for_sale(view: WorldView, name: object) -> Mapping[str, Any] | None:
    """Uma ferramenta à venda no quiosque (nasce como entidade), se o cenário vende."""
    tools = optional(view, "tools")
    for_sale = tools.get("for_sale") if tools else None
    if not isinstance(name, str) or not isinstance(for_sale, Mapping):
        return None
    entry = cast(Mapping[str, Any], for_sale).get(name)
    return cast(Mapping[str, Any], entry) if isinstance(entry, Mapping) else None


@dataclass(frozen=True)
class Buy(FarmAction):
    name: str = "buy"

    def check(self, ctx: ActionContext) -> Rejection | None:
        kiosk = find(ctx.view, "kiosk", ctx.params.get("target"))
        if isinstance(kiosk, Rejection):
            return kiosk
        if not adjacent(ctx.view, ctx.avatar_id, kiosk):
            return Rejection("not_adjacent")
        if not kiosk.attributes.get("open"):
            return Rejection("closed")
        qty = quantity(ctx.params)
        if isinstance(qty, Rejection):
            return qty
        coins = ctx.view.items(ctx.avatar_id).get("moeda", 0)
        name = ctx.params.get("item")
        tool = _for_sale(ctx.view, name)
        if tool is not None:  # uma ferramenta: uma por vez, e tem de caber (ADR-0062)
            if qty != 1:
                return Rejection("invalid_params", "uma ferramenta por vez")
            if coins < int(tool["price"]):
                return Rejection("insufficient_funds")
            if not ctx.view.fits_entity(str(name), ctx.avatar_id):
                return Rejection("too_heavy")
            return None
        info = item_info(ctx.view, name)
        if info is None or "price" not in info:
            return Rejection("invalid_params", "o quiosque não vende isso")
        item = str(name)
        cycle = optional(ctx.view, "kiosk_cycle")
        if cycle is not None and info.get("category") == "semente":
            stock = str(kiosk.attributes.get("estoque_hoje") or "")
            if item not in stock.split(", "):
                return Rejection("out_of_stock")
        if coins < _cost(ctx.view, kiosk, item, qty):
            return Rejection("insufficient_funds")
        return None if ctx.view.fits(item, qty, ctx.avatar_id) else Rejection("too_heavy")

    def apply(self, ctx: ActionContext, ops: WorldOps) -> None:
        name, qty = str(ctx.params["item"]), int(ctx.params.get("qty", 1))
        tool = _for_sale(ctx.view, name)
        if tool is not None:
            ops.consume_item("moeda", int(tool["price"]), ctx.avatar_id, "buy_payment")
            number = len(ctx.view.entities(name)) + 1
            entity_id = f"{name.replace('_', '-')}-{number}"  # ids não levam sublinhado
            ops.spawn(SpawnDef(entity_id, name, container_id=ctx.avatar_id))
            return
        kiosk = find(ctx.view, "kiosk", ctx.params.get("target"))
        assert not isinstance(kiosk, Rejection)
        cost = _cost(ctx.view, kiosk, name, qty)
        if _rises(ctx.view, name):  # a semente que sobe com a compra (ADR-0069)
            trade = buy_from(ctx.view, kiosk, name, qty)
            ops.set_attributes(
                kiosk.entity_id,
                visible={f"preco_{name}": trade.next_price},
                hidden={f"factor_{name}": trade.factor},
            )
        ops.consume_item("moeda", cost, ctx.avatar_id, "buy_payment")
        ops.create_item(name, qty, ctx.avatar_id, "buy")


def _rises(view: WorldView, item: str) -> bool:
    """A semente, num cenário com o mercado que lembra, sobe de preço com a compra."""
    info = item_info(view, item)
    seed = info is not None and info.get("category") == "semente"
    return seed and memory_market(view) is not None


def _cost(view: WorldView, kiosk: EntityView, item: str, qty: int) -> int:
    """O que `qty` unidades custam agora: a tabela, ou o preço que sobe a cada unidade."""
    if _rises(view, item):
        return buy_from(view, kiosk, item, qty).total
    return int(section(view, "items", item)["price"]) * qty


def _bed(ctx: ActionContext) -> EntityView | Rejection | None:
    """Sem alvo, dorme onde está; com alvo, uma cama ou análogo adjacente (ADR-0041)."""
    target = ctx.params.get("target")
    if target is None:
        return None
    beds = section(ctx.view, "sleep", "beds")
    match = next(
        (e for kind in sorted(beds) for e in ctx.view.entities(kind) if e.entity_id == target),
        None,
    )
    if match is None:
        return Rejection("invalid_params", f"{target!r} não é lugar de dormir")
    return match if adjacent(ctx.view, ctx.avatar_id, match) else Rejection("not_adjacent")


def _night(view: WorldView) -> bool:
    """Entre o começo da noite e a hora de acordar (atravessa a meia-noite)."""
    rules = section(view, "sleep")
    return view.ticks_until(str(rules["wake_at"])) < view.ticks_until(str(rules["night_from"]))


def _sleep_ticks(ctx: ActionContext, bed: EntityView | None) -> int:
    """À noite, dorme até a hora de acordar. De dia é um cochilo: acorda com a energia cheia, na
    taxa do lugar, ou na hora de acordar, o que vier antes (ADR-0049)."""
    until_wake = ctx.view.ticks_until(str(section(ctx.view, "sleep")["wake_at"]))
    if _night(ctx.view):
        return until_wake
    if bed is None:
        rate = float(section(ctx.view, "needs", ENERGY, "rates_per_hour")["asleep"])
    else:
        rate = float(section(ctx.view, "sleep", "beds", bed.kind)[ENERGY])
    ticks_per_hour = 3600 / int(section(ctx.view, "clock")["tick_seconds"])
    missing = FULL - ctx.view.need(ctx.avatar_id, ENERGY)
    ticks = round(missing * ticks_per_hour / rate, 6)
    # Com a energia quase cheia (acordado, ela nunca está em 100 exatos: ADR-0056), menos de um
    # tick de sono não é cochilo: `not_tired`.
    return 0 if ticks < 1 else min(until_wake, math.ceil(ticks))


@dataclass(frozen=True)
class Sleep(FarmAction):
    """Dorme a qualquer hora, onde está ou numa cama ao lado (ADR-0041 e ADR-0049)."""

    name: str = "sleep"

    def check(self, ctx: ActionContext) -> Rejection | None:
        bed = _bed(ctx)
        if isinstance(bed, Rejection):
            return bed
        return Rejection("not_tired") if _sleep_ticks(ctx, bed) == 0 else None

    def apply(self, ctx: ActionContext, ops: WorldOps) -> None:
        bed = _bed(ctx)
        assert not isinstance(bed, Rejection)
        rates = None if bed is None else dict(section(ctx.view, "sleep", "beds", bed.kind))
        ops.start_sleep(
            ctx.avatar_id,
            "voluntary",
            _sleep_ticks(ctx, bed),
            rates_per_hour=rates,
            bed_id=None if bed is None else bed.entity_id,
        )


@dataclass(frozen=True)
class Dig(FarmAction):
    """Cava um canteiro num tile de grama ao lado do avatar, ou no dele, com a pá (ADR-0062)."""

    name: str = "dig"
    shared: ClassVar[bool] = True

    def check(self, ctx: ActionContext) -> Rejection | None:
        digging = optional(ctx.view, "digging")
        tools = optional(ctx.view, "tools")
        if digging is None or tools is None:
            return Rejection("invalid_params", "aqui não se cava")
        if held(ctx.view, ctx.avatar_id, str(tools["spade_kind"])) is None:
            return Rejection("missing_item", "sem pá")
        spot = _dig_spot(ctx)
        if isinstance(spot, Rejection):
            return spot
        if ctx.view.tile_kind(spot) != str(digging["tile_kind"]):
            return Rejection("not_grass")
        if any(e.position == spot and e.entity_id != ctx.avatar_id for e in ctx.view.entities()):
            return Rejection("occupied")
        if len(ctx.view.entities("plot")) >= int(digging["max_plots"]):
            return Rejection("no_room")
        return None

    def apply(self, ctx: ActionContext, ops: WorldOps) -> None:
        spot = _dig_spot(ctx)
        assert not isinstance(spot, Rejection)
        digging = section(ctx.view, "digging")
        sequence = digging.get("id_sequence")
        if sequence is None:  # a Boa Vista: o número é a contagem, e nenhum canteiro some
            plot_id = f"plot-{len(ctx.view.entities('plot')) + 1:02d}"
        else:  # um contador que nunca repete, porque o canteiro volta a ser grama (ADR-0067)
            plot_id = f"plot-{ops.next_seq(str(sequence)):03d}"
        # Sem grupo nem rótulo: o terreno não dá pista; a faixa do rio é do analista (bíblia 2 §13).
        hidden: dict[str, Any] = {"bonus_points": 0.0, "ripe_days": 0}
        hidden.update(cast(Mapping[str, Any], digging.get("plot_hidden", {})))
        ops.spawn(SpawnDef(plot_id, "plot", position=spot, hidden=hidden))


def _dig_spot(ctx: ActionContext) -> Position | Rejection:
    """O tile a cavar: `target: {x, y}` ao lado do avatar (um dos 8 ao redor, ou o dele), como se
    rega; sem alvo, o tile em que ele está, que é o que o menu do humano manda."""
    me = ctx.view.entity(ctx.avatar_id).position
    assert me is not None
    raw = ctx.params.get("target")
    if raw is None:
        return me
    if not isinstance(raw, Mapping) or not all(
        isinstance(cast(Mapping[str, Any], raw).get(k), int) for k in ("x", "y")
    ):
        return Rejection("invalid_params", "dig exige target {x, y}, ou nada para cavar aqui")
    target = cast(Mapping[str, int], raw)
    spot = Position(int(target["x"]), int(target["y"]))
    return spot if me.chebyshev(spot) <= 1 else Rejection("not_adjacent")


@dataclass(frozen=True)
class Fertilize(FarmAction):
    """Aduba um canteiro vazio: o próximo plantio cresce mais (ADR-0062)."""

    name: str = "fertilize"
    shared: ClassVar[bool] = True

    def check(self, ctx: ActionContext) -> Rejection | None:
        fertilizer = optional(ctx.view, "fertilizer")
        if fertilizer is None:
            return Rejection("invalid_params", "sem adubo neste mundo")
        plot = _plot(ctx)
        if isinstance(plot, Rejection):
            return plot
        if plot.attributes.get("crop") is not None:
            return Rejection("plot_occupied")
        if plot.attributes.get("adubado"):
            return Rejection("already_fertilized")
        if ctx.view.items(ctx.avatar_id).get(str(fertilizer["item"]), 0) < 1:
            return Rejection("missing_item")
        return None

    def apply(self, ctx: ActionContext, ops: WorldOps) -> None:
        fertilizer = section(ctx.view, "fertilizer")
        ops.consume_item(str(fertilizer["item"]), 1, ctx.avatar_id, "fertilize")
        ops.set_attributes(str(ctx.params["target"]), visible={"adubado": True})


@dataclass(frozen=True)
class Cook(FarmAction):
    """Cozinha uma receita no fogão: os ingredientes viram um prato (ADR-0062)."""

    name: str = "cook"

    def _recipe(self, ctx: ActionContext) -> Mapping[str, Any] | Rejection:
        recipes = optional(ctx.view, "recipes")
        name = ctx.params.get("recipe")
        if recipes is None or not isinstance(name, str) or name not in recipes:
            return Rejection("invalid_params", "receita desconhecida")
        return cast(Mapping[str, Any], recipes[name])

    def numbers(self, ctx: ActionContext) -> Mapping[str, Any]:
        base = section(ctx.view, "actions", self.name)
        recipe = self._recipe(ctx)
        if isinstance(recipe, Rejection):
            return base
        return {
            **base,
            "duration": recipe["duration"],
            "energy": recipe.get("energy", base["energy"]),
        }

    def check(self, ctx: ActionContext) -> Rejection | None:
        cooking = optional(ctx.view, "cooking")
        if cooking is None:
            return Rejection("invalid_params", "sem fogão neste mundo")
        stove = find(ctx.view, str(cooking["stove_kind"]), ctx.params.get("target"))
        if isinstance(stove, Rejection):
            return stove
        if not adjacent(ctx.view, ctx.avatar_id, stove):
            return Rejection("not_adjacent")
        recipe = self._recipe(ctx)
        if isinstance(recipe, Rejection):
            return recipe
        mine = ctx.view.items(ctx.avatar_id)
        ingredients = cast(Mapping[str, Any], recipe["ingredients"])
        if any(mine.get(item, 0) < int(qty) for item, qty in ingredients.items()):
            return Rejection("missing_ingredients")
        dish = str(recipe["dish"])
        return None if ctx.view.fits(dish, 1, ctx.avatar_id) else Rejection("too_heavy")

    def apply(self, ctx: ActionContext, ops: WorldOps) -> None:
        recipe = self._recipe(ctx)
        assert not isinstance(recipe, Rejection)
        for item, qty in sorted(cast(Mapping[str, Any], recipe["ingredients"]).items()):
            ops.consume_item(item, int(qty), ctx.avatar_id, "cook")
        ops.create_item(str(recipe["dish"]), 1, ctx.avatar_id, "cook")


@dataclass(frozen=True)
class Place(FarmAction):
    """Finca no chão, ao lado do avatar (ou onde ele está), um item que vira entidade: o
    espantalho (ADR-0067). O cenário diz em `placeables` o tipo de entidade de cada item."""

    name: str = "place"
    shared: ClassVar[bool] = True

    def check(self, ctx: ActionContext) -> Rejection | None:
        placeables = optional(ctx.view, "placeables")
        item = ctx.params.get("item")
        if placeables is None or not isinstance(item, str) or item not in placeables:
            return Rejection("invalid_params", "isso não se finca")
        if ctx.view.items(ctx.avatar_id).get(item, 0) < 1:
            return Rejection("missing_item")
        spot = _dig_spot(ctx)
        if isinstance(spot, Rejection):
            return spot
        allowed = cast(list[str], section(ctx.view, "placeables", item).get("on", ["grass"]))
        if ctx.view.tile_kind(spot) not in allowed:
            return Rejection("not_grass")
        if any(e.position == spot and e.entity_id != ctx.avatar_id for e in ctx.view.entities()):
            return Rejection("occupied")
        return None

    def apply(self, ctx: ActionContext, ops: WorldOps) -> None:
        spot = _dig_spot(ctx)
        assert not isinstance(spot, Rejection)
        item = str(ctx.params["item"])
        kind = str(section(ctx.view, "placeables", item)["kind"])
        ops.consume_item(item, 1, ctx.avatar_id, "place")
        ops.spawn(SpawnDef(f"{kind}-{ops.next_seq(kind):02d}", kind, position=spot))


@dataclass(frozen=True)
class Withdraw(MoveItems):
    """Pegar do baú e, num cenário com máquinas, o produto que espera numa delas (ADR-0069)."""

    def _container(self, ctx: ActionContext) -> EntityView | Rejection:
        found = machine(ctx.view, ctx.params.get("target"))
        if found is None:
            return super()._container(ctx)
        return found if adjacent(ctx.view, ctx.avatar_id, found) else Rejection("not_adjacent")


@dataclass(frozen=True)
class Process(FarmAction):
    """Carrega uma máquina com os ingredientes de uma receita: ela trabalha sozinha e o produto
    espera dentro dela (ADR-0069)."""

    name: str = "process"
    shared: ClassVar[bool] = True

    def _found(
        self, ctx: ActionContext
    ) -> tuple[EntityView, str, dict[str, int], Mapping[str, Any]] | Rejection:
        entity = machine(ctx.view, ctx.params.get("target"))
        if entity is None:
            return Rejection("invalid_params", "o alvo não é uma máquina")
        if not adjacent(ctx.view, ctx.avatar_id, entity):
            return Rejection("not_adjacent")
        name = ctx.params.get("recipe")
        chosen = recipe(ctx.view, entity.kind, name)
        if chosen is None:
            return Rejection("invalid_params", "receita desconhecida nesta máquina")
        needs = ingredients(ctx.view, chosen, ctx.params.get("item"))
        if isinstance(needs, Rejection):
            return needs
        return entity, str(name), needs, chosen

    def check(self, ctx: ActionContext) -> Rejection | None:
        found = self._found(ctx)
        if isinstance(found, Rejection):
            return found
        entity, _, needs, _ = found
        if busy(entity):
            return Rejection("machine_busy")
        mine = ctx.view.items(ctx.avatar_id)
        if any(mine.get(item, 0) < qty for item, qty in needs.items()):
            return Rejection("missing_ingredients")
        return None

    def apply(self, ctx: ActionContext, ops: WorldOps) -> None:
        found = self._found(ctx)
        assert not isinstance(found, Rejection)
        entity, name, needs, chosen = found
        for item, qty in sorted(needs.items()):
            ops.consume_item(item, qty, ctx.avatar_id, "process")
        start(ctx.view, ops, entity, name, float(chosen["hours"]))


@dataclass(frozen=True)
class Sell(MoveItems):
    """Vender: na caixa de vendas, que o comprador paga de manhã, ou, num cenário com feira, na
    barraca aberta, que paga na hora (ADR-0069)."""

    shared: ClassVar[bool] = False  # vende o que carrega; a barraca da feira fecha com a hora

    def categories(self, ctx: ActionContext) -> tuple[str, ...] | None:
        """O que o comprador da caixa leva: as colheitas e, num cenário com o tacho, os produtos."""
        buyer = optional(ctx.view, "buyer")
        wanted = None if buyer is None else buyer.get("categories")
        return super().categories(ctx) if wanted is None else tuple(cast(list[str], wanted))

    def check(self, ctx: ActionContext) -> Rejection | None:
        stall = fair_stall(ctx.view, ctx.params.get("target"))
        return super().check(ctx) if stall is None else check_sale(ctx, stall)

    def apply(self, ctx: ActionContext, ops: WorldOps) -> None:
        stall = fair_stall(ctx.view, ctx.params.get("target"))
        if stall is None:
            super().apply(ctx, ops)
        else:
            apply_sale(ctx, ops, stall)


def _board_order(ctx: ActionContext) -> tuple[EntityView, EntityView] | Rejection:
    """O quadro ao lado do avatar e o pedido dentro dele (ADR-0069)."""
    data = optional(ctx.view, "orders")
    if data is None:
        return Rejection("invalid_params", "não há encomendas neste mundo")
    board = find(ctx.view, str(data["board_kind"]), ctx.params.get("target"))
    if isinstance(board, Rejection):
        return board
    if not adjacent(ctx.view, ctx.avatar_id, board):
        return Rejection("not_adjacent")
    wanted = ctx.params.get("order")
    order = next((e for e in in_board(ctx.view, board) if e.entity_id == wanted), None)
    return (board, order) if order is not None else Rejection("no_order")


@dataclass(frozen=True)
class AcceptOrder(FarmAction):
    """Aceita um pedido do quadro: ele fica com o avatar até a entrega ou o prazo (ADR-0069)."""

    name: str = "accept_order"

    def check(self, ctx: ActionContext) -> Rejection | None:
        found = _board_order(ctx)
        if isinstance(found, Rejection):
            return found
        board, entity = found
        rules = order_rules(section(ctx.view, "orders"))
        taken = taken_by(ctx.view, board, ctx.avatar_id)
        reason = refuse_take(as_order(entity), ctx.avatar_id, taken, rules)
        return None if reason is None else Rejection(reason)

    def apply(self, ctx: ActionContext, ops: WorldOps) -> None:
        found = _board_order(ctx)
        assert not isinstance(found, Rejection)
        _, entity = found
        ops.set_attributes(entity.entity_id, visible={"aceita_por": ctx.avatar_id})
        ops.emit(
            "campsverso.economy.order.accepted.v1",
            {"order_id": entity.entity_id, "taker": ctx.avatar_id, "day": ctx.view.day},
        )


@dataclass(frozen=True)
class DeliverOrder(FarmAction):
    """Entrega um pedido aceito: os itens saem do inventário, o pagamento entra na hora, e a
    reputação de quem entregou sobe (ADR-0069)."""

    name: str = "deliver_order"

    def check(self, ctx: ActionContext) -> Rejection | None:
        found = _board_order(ctx)
        if isinstance(found, Rejection):
            return found
        _, entity = found
        order = as_order(entity)
        reason = refuse_delivery(order, ctx.avatar_id, ctx.view.day)
        if reason is not None:
            return Rejection(reason)
        if ctx.view.items(ctx.avatar_id).get(order.item, 0) < order.qty:
            return Rejection("missing_item")
        return None

    def apply(self, ctx: ActionContext, ops: WorldOps) -> None:
        found = _board_order(ctx)
        assert not isinstance(found, Rejection)
        board, entity = found
        order = as_order(entity)
        rules = reputation_rules(section(ctx.view, "orders"))
        ops.consume_item(order.item, order.qty, ctx.avatar_id, "order")
        ops.create_item("moeda", order.reward, ctx.avatar_id, "order_payment")
        raised = after_delivery(reputation(board, ctx.avatar_id, rules), rules)
        ops.set_attributes(board.entity_id, hidden={f"reputation_{ctx.avatar_id}": raised})
        ops.despawn(entity.entity_id, "delivered")
        ops.emit(
            "campsverso.economy.order.delivered.v1",
            {
                "order_id": order.order_id,
                "client": order.client,
                "item": order.item,
                "qty": order.qty,
                "reward": order.reward,
                "taker": ctx.avatar_id,
                "day": ctx.view.day,
            },
        )


def _helper_target(ctx: ActionContext) -> EntityView | Rejection:
    """O ajudante pedido (ADR-0072), à vista e na fazenda."""
    target = ctx.params.get("target")
    if not isinstance(target, str) or not helpers.is_helper(ctx.view, target):
        return Rejection("invalid_params", "o alvo não é um ajudante")
    if not ctx.view.present(target):
        return Rejection("absent", "o ajudante não está na fazenda")
    return ctx.view.entity(target)


@dataclass(frozen=True)
class HireHelper(FarmAction):
    """Contrata um ajudante no quadro, por alguns dias, pago adiantado; ele chega na manhã
    seguinte (ADR-0072)."""

    name: str = "hire_helper"
    shared: ClassVar[bool] = True

    def _found(self, ctx: ActionContext) -> tuple[EntityView, str, int, int] | Rejection:
        data = helpers.config(ctx.view)
        if data is None:
            return Rejection("invalid_params", "não há ajudantes neste mundo")
        found = helpers.board(ctx.view, ctx.params.get("target"))
        if found is None:
            return Rejection("invalid_params", "o alvo não é o quadro de ajudantes")
        if not adjacent(ctx.view, ctx.avatar_id, found):
            return Rejection("not_adjacent")
        helper, days = ctx.params.get("helper"), ctx.params.get("days")
        if not isinstance(helper, str) or helper not in helpers.roster(data):
            return Rejection("invalid_params", "ajudante desconhecido")
        if days not in cast(list[int], data["contract_days"]) or not isinstance(days, int):
            return Rejection("invalid_params", f"dias em {data['contract_days']}")
        wage = int(cast(int, ctx.view.entity(helper).attributes["diaria"]))
        return found, helper, days, wage

    def check(self, ctx: ActionContext) -> Rejection | None:
        found = self._found(ctx)
        if isinstance(found, Rejection):
            return found
        _, helper, days, wage = found
        if helpers.is_helper(ctx.view, ctx.avatar_id):
            return Rejection("invalid_params", "um ajudante não contrata")
        if helpers.employer(ctx.view, helper) is not None:
            return Rejection("helper_busy")
        if ctx.view.items(ctx.avatar_id).get(helpers.COIN, 0) < wage * days:
            return Rejection("insufficient_funds")
        return None

    def apply(self, ctx: ActionContext, ops: WorldOps) -> None:
        found = self._found(ctx)
        assert not isinstance(found, Rejection)
        _, helper, days, wage = found
        first = ctx.view.day + 1
        ops.consume_item(helpers.COIN, wage * days, ctx.avatar_id, "wage")
        ops.set_attributes(
            helper,
            visible={"patrao": ctx.avatar_id, "dias": days, "ordem": "cuidar"},
            hidden={"primeiro_dia": first, "ultimo_dia": first + days - 1},
        )
        helpers.show_on_board(ctx.view, ops, [helper])
        ops.emit(
            "campsverso.economy.labor.hired.v1",
            {
                "helper": helper,
                "employer": ctx.avatar_id,
                "days": days,
                "wage": wage,
                "total": wage * days,
                "first_day": first,
                "day": ctx.view.day,
            },
        )


@dataclass(frozen=True)
class OrderHelper(FarmAction):
    """Dá uma ordem ao ajudante, ao lado dele; a ordem fica até ser trocada (ADR-0072)."""

    name: str = "order_helper"

    def check(self, ctx: ActionContext) -> Rejection | None:
        helper = _helper_target(ctx)
        if isinstance(helper, Rejection):
            return helper
        if helpers.employer(ctx.view, helper.entity_id) != ctx.avatar_id:
            return Rejection("not_employer")
        if not adjacent(ctx.view, ctx.avatar_id, helper):
            return Rejection("not_adjacent")
        data = section(ctx.view, helpers.HELPERS)
        task = ctx.params.get("task")
        if task not in cast(list[str], data["tasks"]):
            return Rejection("invalid_params", f"ordem em {data['tasks']}")
        if task == "plantar" and ctx.params.get("crop") not in section(ctx.view, "crops"):
            return Rejection("invalid_params", "plantar pede a cultura")
        if task == "vender" and item_info(ctx.view, ctx.params.get("item")) is None:
            return Rejection("invalid_params", "vender pede o item")
        n = ctx.params.get("n")
        if task == "cavar" and (not isinstance(n, int) or not 1 <= n <= int(data["max_dig"])):
            return Rejection("invalid_params", f"cavar pede n de 1 a {data['max_dig']}")
        return None

    def apply(self, ctx: ActionContext, ops: WorldOps) -> None:
        task = str(ctx.params["task"])
        here = ctx.view.entity(ctx.avatar_id).position
        digging = task == "cavar" and here is not None  # em volta de onde o patrão deu a ordem
        visible: dict[str, Any] = {
            "ordem": task,
            "ordem_cultura": ctx.params.get("crop") if task == "plantar" else None,
            "ordem_item": ctx.params.get("item") if task == "vender" else None,
            "ordem_n": ctx.params.get("n") if task == "cavar" else None,
            "ordem_x": here.x if digging and here is not None else None,
            "ordem_y": here.y if digging and here is not None else None,
        }
        ops.set_attributes(str(ctx.params["target"]), visible=visible)


@dataclass(frozen=True)
class DismissHelper(FarmAction):
    """Dispensa o ajudante, ao lado dele ou no quadro: ele vai embora, e os dias pagos não voltam
    (ADR-0072)."""

    name: str = "dismiss_helper"

    def _helper(self, ctx: ActionContext) -> str | Rejection:
        target = ctx.params.get("target")
        found = helpers.board(ctx.view, target)
        if found is not None:
            helper = ctx.params.get("helper")
            if not isinstance(helper, str) or not helpers.is_helper(ctx.view, helper):
                return Rejection("invalid_params", "ajudante desconhecido")
            return helper if adjacent(ctx.view, ctx.avatar_id, found) else Rejection("not_adjacent")
        entity = _helper_target(ctx)
        if isinstance(entity, Rejection):
            return entity
        if not adjacent(ctx.view, ctx.avatar_id, entity):
            return Rejection("not_adjacent")
        return entity.entity_id

    def check(self, ctx: ActionContext) -> Rejection | None:
        helper = self._helper(ctx)
        if isinstance(helper, Rejection):
            return helper
        if helpers.employer(ctx.view, helper) != ctx.avatar_id:
            return Rejection("not_employer")
        return None

    def apply(self, ctx: ActionContext, ops: WorldOps) -> None:
        helper = self._helper(ctx)
        assert not isinstance(helper, Rejection)
        left = int(cast(int, ctx.view.entity(helper).attributes.get("dias") or 0))
        if ctx.view.present(helper):
            helpers.leave_farm(ctx.view, ops, helper, "dismissed")
        helpers.end_contract(ctx.view, ops, helper)
        helpers.show_on_board(ctx.view, ops, [helper])
        ops.emit(
            "campsverso.economy.labor.dismissed.v1",
            {"helper": helper, "employer": ctx.avatar_id, "days_left": left, "day": ctx.view.day},
        )


@dataclass(frozen=True)
class GoHome(FarmAction):
    """O ajudante vai embora mais cedo (sem comida no baú, por exemplo); o dia conta (ADR-0072)."""

    name: str = "go_home"

    def check(self, ctx: ActionContext) -> Rejection | None:
        if not helpers.is_helper(ctx.view, ctx.avatar_id):
            return Rejection("invalid_params", "só um ajudante vai para casa no meio do dia")
        return None

    def apply(self, ctx: ActionContext, ops: WorldOps) -> None:
        helpers.leave_farm(ctx.view, ops, ctx.avatar_id, "went_home")


EXTRA_ACTIONS: tuple[FarmAction, ...] = (  # só com dados do cenário
    Dig(),
    Fertilize(),
    Cook(),
    Place(),
    AcceptOrder(),
    DeliverOrder(),
    Process(),
    HireHelper(),
    OrderHelper(),
    DismissHelper(),
    GoHome(),
)

ALL_ACTIONS: tuple[FarmAction, ...] = (
    Plant(),
    Water(),
    Refill(),
    Harvest(),
    Clear(),
    Eat(),
    MoveItems(name="deposit", kind="chest", to_container=True, reason="deposit"),
    Withdraw(name="withdraw", kind="chest", to_container=False, reason="withdraw"),
    Sell(name="sell", kind="sell_box", to_container=True, reason="sell", only_category="colheita"),
    Buy(),
    Sleep(),
)
