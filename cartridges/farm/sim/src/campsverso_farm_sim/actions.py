"""Ações do gênero fazenda (bíblia §8). Duração e custo vêm dos dados; efeitos, das primitivas."""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from campsverso_cartridge_api import (
    Accepted,
    ActionContext,
    EntityView,
    Rejection,
    Validation,
    WorldOps,
    WorldView,
)
from campsverso_farm_sim.config import ENERGY, HUNGER, section

EMPTY_PLOT: dict[str, Any] = {"crop": None, "stage": None, "watered_today": False}
EMPTY_HIDDEN: dict[str, Any] = {"growth_points": 0.0, "planted_day": None, "dry_days": 0}


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


def watering_can(view: WorldView, avatar_id: str) -> EntityView | None:
    return next((e for e in view.entities("watering_can") if e.container_id == avatar_id), None)


def item_info(view: WorldView, item: object) -> Mapping[str, Any] | None:
    items = section(view, "items")
    return items.get(item) if isinstance(item, str) else None


@dataclass(frozen=True)
class FarmAction:
    name: str = ""
    cancellable: bool = True

    def check(self, ctx: ActionContext) -> Rejection | None:
        raise NotImplementedError

    def apply(self, ctx: ActionContext, ops: WorldOps) -> None:
        raise NotImplementedError

    def validate(self, ctx: ActionContext) -> Validation:
        rejection = self.check(ctx)
        if rejection is not None:
            return rejection
        return Accepted(int(section(ctx.view, "actions", self.name)["duration"]))

    def complete(self, ctx: ActionContext, ops: WorldOps) -> None:
        self.apply(ctx, ops)
        energy = float(section(ctx.view, "actions", self.name)["energy"])
        if energy:
            hungry = ctx.view.need(ctx.avatar_id, HUNGER) >= float(
                section(ctx.view)["hunger_doubles_energy_at"]
            )
            ops.change_need(ctx.avatar_id, ENERGY, -(energy * 2 if hungry else energy))


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
        ops.set_attributes(
            target,
            visible={"crop": crop, "stage": "semente", "watered_today": rained},
            hidden={"growth_points": 0.0, "planted_day": ctx.view.day, "dry_days": 0},
        )


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
        can = watering_can(ctx.view, ctx.avatar_id)
        assert can is not None
        ops.set_attributes(can.entity_id, visible={"charges": can.attributes["capacity"]})


@dataclass(frozen=True)
class Harvest(FarmAction):
    name: str = "harvest"

    def check(self, ctx: ActionContext) -> Rejection | None:
        plot = _plot(ctx)
        if isinstance(plot, Rejection):
            return plot
        return None if plot.attributes.get("stage") == "madura" else Rejection("not_ripe")

    def apply(self, ctx: ActionContext, ops: WorldOps) -> None:
        target = str(ctx.params["target"])
        crop = str(ctx.view.entity(target).attributes["crop"])
        ops.create_item(crop, 1, ctx.avatar_id, "harvest")
        ops.set_attributes(target, visible=EMPTY_PLOT, hidden=EMPTY_HIDDEN)
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
        ops.set_attributes(str(ctx.params["target"]), visible=EMPTY_PLOT, hidden=EMPTY_HIDDEN)


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
        ops.consume_item(item, 1, ctx.avatar_id, "eat")
        ops.change_need(ctx.avatar_id, HUNGER, -float(section(ctx.view, "items", item)["hunger"]))


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

    def check(self, ctx: ActionContext) -> Rejection | None:
        container = self._container(ctx)
        if isinstance(container, Rejection):
            return container
        qty = quantity(ctx.params)
        if isinstance(qty, Rejection):
            return qty
        info = item_info(ctx.view, ctx.params.get("item"))
        if info is None:
            return Rejection("invalid_params", "item desconhecido")
        if self.only_category is not None and info.get("category") != self.only_category:
            return Rejection("invalid_params", f"só {self.only_category}")
        source = ctx.avatar_id if self.to_container else container.entity_id
        if ctx.view.items(source).get(str(ctx.params["item"]), 0) < qty:
            return Rejection("missing_item")
        return None

    def apply(self, ctx: ActionContext, ops: WorldOps) -> None:
        container = self._container(ctx)
        assert not isinstance(container, Rejection)
        item, qty = str(ctx.params["item"]), int(ctx.params.get("qty", 1))
        if self.to_container:
            ops.transfer_item(item, qty, ctx.avatar_id, container.entity_id, self.reason)
        else:
            ops.transfer_item(item, qty, container.entity_id, ctx.avatar_id, self.reason)
        if self.reason == "sell":  # quem recebe o pagamento às 06:00 (ADR-0039)
            ops.set_attributes(container.entity_id, hidden={"payee": ctx.avatar_id})


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
        info = item_info(ctx.view, ctx.params.get("item"))
        if info is None or info.get("category") != "semente":
            return Rejection("invalid_params", "o quiosque só vende sementes")
        if ctx.view.items(ctx.avatar_id).get("moeda", 0) < int(info["price"]) * qty:
            return Rejection("insufficient_funds")
        return None

    def apply(self, ctx: ActionContext, ops: WorldOps) -> None:
        item, qty = str(ctx.params["item"]), int(ctx.params.get("qty", 1))
        price = int(section(ctx.view, "items", item)["price"])
        ops.consume_item("moeda", price * qty, ctx.avatar_id, "buy_payment")
        ops.create_item(item, qty, ctx.avatar_id, "buy")


@dataclass(frozen=True)
class Sleep(FarmAction):
    name: str = "sleep"
    cancellable: bool = False

    def check(self, ctx: ActionContext) -> Rejection | None:
        bed = find(ctx.view, "bed", ctx.params.get("target"))
        if isinstance(bed, Rejection):
            return bed
        if not adjacent(ctx.view, ctx.avatar_id, bed):
            return Rejection("not_adjacent")
        rules = section(ctx.view, "sleep")
        # Pode dormir a partir de allowed_from e até a hora de acordar (atravessa a meia-noite).
        until_allowed = ctx.view.ticks_until(str(rules["allowed_from"]))
        until_wake = ctx.view.ticks_until(str(rules["wake_at"]))
        return None if until_wake < until_allowed else Rejection("too_early_to_sleep")

    def apply(self, ctx: ActionContext, ops: WorldOps) -> None:
        ops.start_sleep(
            ctx.avatar_id, "bed", ctx.view.ticks_until(str(section(ctx.view, "sleep")["wake_at"]))
        )


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
