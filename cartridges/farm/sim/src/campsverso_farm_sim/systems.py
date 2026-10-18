"""Sistemas do gênero fazenda (bíblia §9): funções de estado, tick e RNG nomeado (princípio 4)."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from campsverso_cartridge_api import (
    DailyAt,
    OnSessionStart,
    OnThreshold,
    SystemContext,
    Trigger,
    WorldOps,
    WorldView,
)
from campsverso_farm_sim.config import ENERGY, HUNGER, section


@dataclass(frozen=True)
class FarmSystem:
    name: str
    stage: str
    priority: int
    triggers: tuple[Trigger, ...]
    body: Callable[[SystemContext, WorldOps], None]

    def run(self, ctx: SystemContext, ops: WorldOps) -> None:
        self.body(ctx, ops)


def draw_weather(ctx: SystemContext, ops: WorldOps) -> None:
    """No início, sorteia o dia 1; às 05:00, o dia agrícola que começa às 06:00 (ADR-0018)."""
    view = ctx.view
    day = view.day if isinstance(ctx.trigger, OnSessionStart) else view.day + 1
    chance = float(section(view, "weather")["rain_probability"])
    ops.set_weather("rain" if view.rng("weather").random() < chance else "sun", day)


def _stage_for(points: float, required: float, stages: Mapping[str, Any]) -> str:
    if points >= required:
        return "madura"
    if points >= required * float(stages["crescendo_at_fraction"]):
        return "crescendo"
    if points >= float(stages["broto_at_points"]):
        return "broto"
    return "semente"


def grow_crops(ctx: SystemContext, ops: WorldOps) -> None:
    """Às 06:00: soma pontos de quem foi regado no dia anterior, amadurece e murcha (bíblia §6)."""
    view = ctx.view
    stages = section(view, "stages")
    base = float(section(view, "growth")["points_per_watered_day"])
    for plot in view.entities("plot"):
        crop, stage = plot.attributes.get("crop"), plot.attributes.get("stage")
        if crop is None or stage in ("madura", "murcha"):
            continue
        points = float(plot.hidden.get("growth_points") or 0.0)
        dry = int(plot.hidden.get("dry_days") or 0)
        if plot.attributes.get("watered_today"):
            points += ops.apply_rules("growth_points", plot.entity_id, base)  # regras ocultas aqui
            dry = 0
        else:
            dry += 1
        ops.set_attributes(plot.entity_id, hidden={"growth_points": points, "dry_days": dry})
        if dry >= int(stages["wither_after_dry_days"]):
            ops.set_attributes(plot.entity_id, visible={"stage": "murcha"})
            ops.emit(
                "campsverso.farm.crop.withered.v1",
                {"plot_id": plot.entity_id, "crop": crop, "day": view.day, "dry_days": dry},
            )
            continue
        required = float(section(view, "crops", str(crop))["points_to_mature"])
        new_stage = _stage_for(points, required, stages)
        if new_stage == stage:
            continue
        ops.set_attributes(plot.entity_id, visible={"stage": new_stage})
        if new_stage == "madura":
            planted = int(plot.hidden.get("planted_day") or view.day)
            ops.emit(
                "campsverso.farm.crop.matured.v1",
                {
                    "plot_id": plot.entity_id,
                    "crop": crop,
                    "planted_day": planted,
                    "day": view.day,
                    "days": view.day - planted,
                },
            )


def start_new_day(ctx: SystemContext, ops: WorldOps) -> None:
    """Depois do crescimento: zera a rega; com chuva, toda planta já conta como regada."""
    view = ctx.view
    rained = view.weather(view.day) == "rain"
    for plot in view.entities("plot"):
        has_plant = (
            plot.attributes.get("crop") is not None and plot.attributes.get("stage") != "murcha"
        )
        ops.set_attributes(plot.entity_id, visible={"watered_today": rained and has_plant})


def buyer_collect(ctx: SystemContext, ops: WorldOps) -> None:
    """Às 22:00 o comprador esvazia a caixa e anota o que deve (ADR-0039)."""
    for box in ctx.view.entities("sell_box"):
        owed: dict[str, Any] = {}
        for item, qty in ctx.view.items(box.entity_id).items():
            ops.consume_item(item, qty, box.entity_id, "buyer_collect")
            owed[f"owed_{item}"] = int(box.hidden.get(f"owed_{item}") or 0) + qty
        if owed:
            ops.set_attributes(box.entity_id, hidden=owed)


def buyer_pay(ctx: SystemContext, ops: WorldOps) -> None:
    """Às 06:00 o comprador paga o que recolheu, a quem vendeu."""
    view = ctx.view
    for box in view.entities("sell_box"):
        payee = box.hidden.get("payee")
        lines = [
            {"item": key.removeprefix("owed_"), "qty": int(qty or 0)}
            for key, qty in sorted(box.hidden.items())
            if key.startswith("owed_") and qty
        ]
        if not lines or not isinstance(payee, str):
            continue
        for line in lines:
            line["unit_price"] = int(section(view, "items", str(line["item"]))["sale_price"])
        total = sum(int(line["qty"]) * int(line["unit_price"]) for line in lines)
        ops.create_item("moeda", total, payee, "payment")
        ops.set_attributes(box.entity_id, hidden={f"owed_{line['item']}": 0 for line in lines})
        ops.emit(
            "campsverso.farm.buyer.paid.v1",
            {"container_id": payee, "items": lines, "total": total, "day": view.day},
        )


def kiosk_hours(ctx: SystemContext, ops: WorldOps) -> None:
    hours = section(ctx.view, "kiosk")
    is_open = ctx.view.ticks_until(str(hours["closes"])) < ctx.view.ticks_until(str(hours["opens"]))
    for kiosk in ctx.view.entities("kiosk"):
        ops.set_attributes(kiosk.entity_id, visible={"open": is_open})


def _faint(view: WorldView, ops: WorldOps, avatar_id: str, reason: str) -> None:
    rules = section(view, "faint")
    ops.faint(
        avatar_id,
        "late_night" if reason == "late_night" else "exhausted",
        view.ticks_until(str(rules["wake_at"])),
        {ENERGY: float(rules["wake_energy"])},
    )


def faint_late_night(ctx: SystemContext, ops: WorldOps) -> None:
    """Quem ainda está acordado às 02:00 desmaia onde estiver (bíblia §7)."""
    for avatar_id in ctx.view.avatars():
        if not ctx.view.is_asleep(avatar_id):
            _faint(ctx.view, ops, avatar_id, "late_night")


def faint_exhausted(ctx: SystemContext, ops: WorldOps) -> None:
    """Energia 0: desmaio automático, sem decisão do controlador (ADR-0039)."""
    if ctx.avatar_id is not None:
        _faint(ctx.view, ops, ctx.avatar_id, "exhausted")


def starve(ctx: SystemContext, ops: WorldOps) -> None:
    """De hora em hora: com a fome no teto, quem está acordado perde energia até comer (ADR-0056).

    Soma-se ao dobro de energia por ação acima de 80. Um dia inteiro passando fome termina em
    desmaio; a fome não mata.
    """
    view = ctx.view
    rule = section(view, "starving")
    for avatar_id in view.avatars():
        if view.is_asleep(avatar_id) or view.need(avatar_id, HUNGER) < float(rule["at"]):
            continue
        ops.change_need(avatar_id, ENERGY, -float(rule["energy_per_hour"]))


def build_systems(data: Mapping[str, Any]) -> tuple[FarmSystem, ...]:
    """Horários vêm dos dados do gênero no momento da montagem do mundo."""
    buyer, kiosk = data["buyer"], data["kiosk"]
    return (
        FarmSystem(
            "weather",
            "scheduled",
            10,
            (OnSessionStart(), DailyAt((data["weather"]["draw_at"],))),
            draw_weather,
        ),
        FarmSystem(
            "crop_growth",
            "scheduled",
            10,
            (DailyAt((data["clock"]["day_starts_at"],)),),
            grow_crops,
        ),
        FarmSystem("buyer_pay", "scheduled", 20, (DailyAt((buyer["pays"],)),), buyer_pay),
        FarmSystem(
            "new_day", "scheduled", 30, (DailyAt((data["clock"]["day_starts_at"],)),), start_new_day
        ),
        FarmSystem(
            "buyer_collect", "scheduled", 10, (DailyAt((buyer["collects"],)),), buyer_collect
        ),
        FarmSystem(
            "kiosk_hours",
            "scheduled",
            10,
            (DailyAt((kiosk["opens"], kiosk["closes"])),),
            kiosk_hours,
        ),
        FarmSystem(
            "faint_late_night",
            "scheduled",
            10,
            (DailyAt((data["faint"]["late_night_at"],)),),
            faint_late_night,
        ),
        FarmSystem(
            "faint_exhausted", "reactions", 10, (OnThreshold(ENERGY, 0, "down"),), faint_exhausted
        ),
        FarmSystem(
            "starving",
            "scheduled",
            40,
            (DailyAt(tuple(f"{hour:02d}:00" for hour in range(24))),),  # de hora em hora
            starve,
        ),
    )
