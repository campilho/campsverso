"""Ações do gênero fazenda (bíblia §8). Duração e custo vêm dos dados; efeitos, das primitivas."""

import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, cast

from campsverso_cartridge_api import (
    Accepted,
    ActionContext,
    EntityView,
    Interrupt,
    Rejection,
    SpawnDef,
    Validation,
    WorldOps,
    WorldView,
)
from campsverso_farm_sim.config import ENERGY, HUNGER, optional, section, ticks_per_hour

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

    def check(self, ctx: ActionContext) -> Rejection | None:
        raise NotImplementedError

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


def _empty_hidden(view: WorldView, target: str) -> dict[str, Any]:
    """O estado oculto de um canteiro vazio; os campos da fazenda 2 só onde já existiam."""
    hidden = dict(EMPTY_HIDDEN)
    current = view.entity(target).hidden
    for key in ("bonus_points", "ripe_days"):
        if key in current:
            hidden[key] = 0.0 if key == "bonus_points" else 0
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
        ops.consume_item(str(section(ctx.view, "crops", crop)["seed"]), 1, ctx.avatar_id, "plant")
        rained = ctx.view.weather(ctx.view.day) == "rain"  # chuva conta como rega (ADR-0039)
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

    def check(self, ctx: ActionContext) -> Rejection | None:
        plot = _plot(ctx)
        if isinstance(plot, Rejection):
            return plot
        if plot.attributes.get("crop") is None or plot.attributes.get("stage") == "murcha":
            return Rejection("no_plant")
        can = watering_can(ctx.view, ctx.avatar_id)
        if can is None:
            return Rejection("missing_item", "sem regador")
        if int(can.attributes.get("charges") or 0) < 1:
            return Rejection("can_empty")
        return None

    def apply(self, ctx: ActionContext, ops: WorldOps) -> None:
        can = watering_can(ctx.view, ctx.avatar_id)
        assert can is not None
        ops.set_attributes(
            can.entity_id, visible={"charges": int(can.attributes["charges"] or 0) - 1}
        )
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
        ops.set_attributes(target, visible=EMPTY_PLOT, hidden=_empty_hidden(ctx.view, target))
        ops.explain_effects(target)  # regras (inclusive ocultas) que ajudaram a planta (internal)


@dataclass(frozen=True)
class Clear(FarmAction):
    name: str = "clear"

    def check(self, ctx: ActionContext) -> Rejection | None:
        plot = _plot(ctx)
        if isinstance(plot, Rejection):
            return plot
        return None if plot.attributes.get("stage") == "murcha" else Rejection("not_withered")

    def apply(self, ctx: ActionContext, ops: WorldOps) -> None:
        target = str(ctx.params["target"])
        ops.set_attributes(target, visible=EMPTY_PLOT, hidden=_empty_hidden(ctx.view, target))


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

    kind: str = ""
    to_container: bool = True
    reason: str = ""
    only_category: str | None = None

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
            return None if ctx.view.fits_entity(tool.kind, target) else Rejection("too_heavy")
        qty = quantity(ctx.params)
        if isinstance(qty, Rejection):
            return qty
        info = item_info(ctx.view, ctx.params.get("item"))
        if info is None:
            return Rejection("invalid_params", "item desconhecido")
        if self.only_category is not None and info.get("category") != self.only_category:
            return Rejection("invalid_params", f"só {self.only_category}")
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
            hidden: dict[str, Any] = {"payee": ctx.avatar_id}
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
        if coins < int(info["price"]) * qty:
            return Rejection("insufficient_funds")
        return None if ctx.view.fits(item, qty, ctx.avatar_id) else Rejection("too_heavy")

    def apply(self, ctx: ActionContext, ops: WorldOps) -> None:
        name, qty = str(ctx.params["item"]), int(ctx.params.get("qty", 1))
        tool = _for_sale(ctx.view, name)
        if tool is not None:
            ops.consume_item("moeda", int(tool["price"]), ctx.avatar_id, "buy_payment")
            number = len(ctx.view.entities(name)) + 1
            ops.spawn(SpawnDef(f"{name}-{number}", name, container_id=ctx.avatar_id))
            return
        price = int(section(ctx.view, "items", name)["price"])
        ops.consume_item("moeda", price * qty, ctx.avatar_id, "buy_payment")
        ops.create_item(name, qty, ctx.avatar_id, "buy")


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
    """Cava um canteiro no tile onde o avatar está, com a pá (ADR-0062)."""

    name: str = "dig"

    def check(self, ctx: ActionContext) -> Rejection | None:
        digging = optional(ctx.view, "digging")
        tools = optional(ctx.view, "tools")
        if digging is None or tools is None:
            return Rejection("invalid_params", "aqui não se cava")
        if held(ctx.view, ctx.avatar_id, str(tools["spade_kind"])) is None:
            return Rejection("missing_item", "sem pá")
        me = ctx.view.entity(ctx.avatar_id).position
        assert me is not None
        if ctx.view.tile_kind(me) != str(digging["tile_kind"]):
            return Rejection("not_grass")
        if any(e.position == me and e.entity_id != ctx.avatar_id for e in ctx.view.entities()):
            return Rejection("occupied")
        if len(ctx.view.entities("plot")) >= int(digging["max_plots"]):
            return Rejection("no_room")
        return None

    def apply(self, ctx: ActionContext, ops: WorldOps) -> None:
        digging = section(ctx.view, "digging")
        me = ctx.view.entity(ctx.avatar_id).position
        assert me is not None
        number = len(ctx.view.entities("plot")) + 1
        group = "leste" if me.x >= int(digging["east_from_x"]) else "oeste"
        ops.spawn(
            SpawnDef(
                f"plot-{number:02d}",
                "plot",
                position=me,
                attributes={"group": group},
                hidden={"bonus_points": 0.0, "ripe_days": 0},
            )
        )


@dataclass(frozen=True)
class Fertilize(FarmAction):
    """Aduba um canteiro vazio: o próximo plantio cresce mais (ADR-0062)."""

    name: str = "fertilize"

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


EXTRA_ACTIONS: tuple[FarmAction, ...] = (Dig(), Fertilize(), Cook())  # só com dados do cenário

ALL_ACTIONS: tuple[FarmAction, ...] = (
    Plant(),
    Water(),
    Refill(),
    Harvest(),
    Clear(),
    Eat(),
    MoveItems(name="deposit", kind="chest", to_container=True, reason="deposit"),
    MoveItems(name="withdraw", kind="chest", to_container=False, reason="withdraw"),
    MoveItems(
        name="sell", kind="sell_box", to_container=True, reason="sell", only_category="colheita"
    ),
    Buy(),
    Sleep(),
)
