"""Sistemas do gênero fazenda (bíblia §9): funções de estado, tick e RNG nomeado (princípio 4)."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, cast

from campsverso_cartridge_api import (
    DailyAt,
    OnSessionStart,
    OnThreshold,
    SystemContext,
    Trigger,
    WorldOps,
    WorldView,
)
from campsverso_climate import ClimateRules, draw
from campsverso_farm_sim.actions import EMPTY_PLOT, empty_hidden
from campsverso_farm_sim.config import (
    ENERGY,
    HUNGER,
    optional,
    season_factor,
    season_level,
    section,
)
from campsverso_farm_sim.fair import fair_hours
from campsverso_farm_sim.helpers import helpers_arrive, helpers_board, helpers_leave
from campsverso_farm_sim.helpers import times as helper_times
from campsverso_farm_sim.market import memory_market, turnover
from campsverso_farm_sim.orders import orders_daily
from campsverso_farm_sim.processing import HOURS, machines_hourly
from campsverso_farm_sim.weather import drought_noon, knocked_down, market_shock, wet


@dataclass(frozen=True)
class FarmSystem:
    name: str
    stage: str
    priority: int
    triggers: tuple[Trigger, ...]
    body: Callable[[SystemContext, WorldOps], None]

    def run(self, ctx: SystemContext, ops: WorldOps) -> None:
        self.body(ctx, ops)


def climate_rules(weather: Mapping[str, Any]) -> ClimateRules:
    """As chances do tempo, dos dados: só `rain_probability` nas fazendas 1 e 2; `chances` e
    `by_season` num cenário com tempestade e seca (ADR-0069)."""
    default = weather.get("chances") or {"rain": float(weather["rain_probability"])}
    by_season = cast(Mapping[str, Mapping[str, float]], weather.get("by_season") or {})
    return ClimateRules(
        default={str(k): float(v) for k, v in cast(Mapping[str, Any], default).items()},
        by_season={s: {str(k): float(v) for k, v in c.items()} for s, c in by_season.items()},
    )


def draw_weather(ctx: SystemContext, ops: WorldOps) -> None:
    """No início, sorteia o dia 1; às 05:00, o dia agrícola que começa às 06:00 (ADR-0018). O
    sorteio é o da biblioteca do clima, pela estação do dia (ADR-0069)."""
    view = ctx.view
    day = view.day if isinstance(ctx.trigger, OnSessionStart) else view.day + 1
    weather = section(view, "weather")
    rules = climate_rules(weather)
    forecast = "forecast_at" in weather and day > view.day  # a previsão da véspera (ADR-0069)
    ops.set_weather(draw(view.rng("weather"), rules, view.season(day)), day, forecast=forecast)


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
    ripe_limit = stages.get("harvest_withers_after_days")  # a madura murcha sem colher (ADR-0062)
    for plot in view.entities("plot"):
        crop, stage = plot.attributes.get("crop"), plot.attributes.get("stage")
        if crop is None or stage == "murcha":
            continue
        if stage == "madura":
            if ripe_limit is None:
                continue
            ripe = int(plot.hidden.get("ripe_days") or 0) + 1
            if ripe < int(ripe_limit):
                ops.set_attributes(plot.entity_id, hidden={"ripe_days": ripe})
                continue
            ops.set_attributes(
                plot.entity_id, visible={"stage": "murcha"}, hidden={"ripe_days": ripe}
            )
            ops.emit(
                "campsverso.farm.crop.withered.v1",
                {"plot_id": plot.entity_id, "crop": crop, "day": view.day, "dry_days": 0},
            )
            continue
        info = section(view, "crops", str(crop))
        needs_water = bool(info.get("needs_water", True))  # o alho cresce sem rega (oculto)
        dry_limit = int(info.get("wither_after_dry_days", stages["wither_after_dry_days"]))
        points = float(plot.hidden.get("growth_points") or 0.0)
        dry = int(plot.hidden.get("dry_days") or 0)
        watered = plot.attributes.get("watered_today") and not plot.hidden.get("parched")
        if watered or not needs_water:
            # A estação dá o ritmo (ADR-0067); as regras ocultas entram por cima.
            pace = base * season_factor(view, str(crop))
            points += ops.apply_rules("growth_points", plot.entity_id, pace)
            points += float(plot.hidden.get("bonus_points") or 0.0)  # o adubo deste plantio
            dry = 0
        else:
            dry += 1
        ops.set_attributes(plot.entity_id, hidden={"growth_points": points, "dry_days": dry})
        if dry >= dry_limit:
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
    """Depois do crescimento: zera a rega; com chuva (ou tempestade), toda planta já conta como
    regada. Num cenário com seca, a marca da seca de ontem sai."""
    view = ctx.view
    rained = wet(view, view.day)
    dry_season = optional(view, "weather", "drought") is not None
    for plot in view.entities("plot"):
        has_plant = (
            plot.attributes.get("crop") is not None and plot.attributes.get("stage") != "murcha"
        )
        hidden = {"parched": False} if dry_season else None
        ops.set_attributes(
            plot.entity_id, visible={"watered_today": rained and has_plant}, hidden=hidden
        )


def weather_effects(ctx: SystemContext, ops: WorldOps) -> None:
    """Na manhã do dia, antes do crescimento: a tempestade derruba plantas maduras, e depois de uma
    tempestade ou de uma seca o mercado sobe (ADR-0069)."""
    view = ctx.view
    for plot_id, crop in knocked_down(view):
        ops.set_attributes(plot_id, visible=EMPTY_PLOT, hidden=empty_hidden(view, plot_id))
        ops.emit(
            "campsverso.farm.crop.knocked_down.v1",
            {"plot_id": plot_id, "crop": crop, "day": view.day},
        )
    market_shock(view, ops)


def buyer_collect(ctx: SystemContext, ops: WorldOps) -> None:
    """Às 22:00 o comprador esvazia a caixa e anota o que deve (ADR-0039). Com mercado, o valor
    de cada venda já foi calculado na hora, pelo preço do dia (ADR-0062)."""
    market = optional(ctx.view, "market")
    for box in ctx.view.entities("sell_box"):
        owed: dict[str, Any] = {}
        for item, qty in ctx.view.items(box.entity_id).items():
            ops.consume_item(item, qty, box.entity_id, "buyer_collect")
            owed[f"owed_{item}"] = int(box.hidden.get(f"owed_{item}") or 0) + qty
            if market is not None:
                value = float(box.hidden.get(f"value_{item}") or 0.0)
                owed[f"due_{item}"] = round(float(box.hidden.get(f"due_{item}") or 0.0) + value, 2)
                owed[f"value_{item}"] = 0.0
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
        market = optional(view, "market")
        cleared: dict[str, Any] = {}
        total = 0
        for line in lines:
            item = str(line["item"])
            base = int(section(view, "items", item)["sale_price"])
            if market is None:
                line["unit_price"] = base
                total += int(line["qty"]) * base
            else:  # o que cada venda valeu no dia, pelo preço que caía (ADR-0062)
                value = round(float(box.hidden.get(f"due_{item}") or 0.0))
                line["unit_price"] = max(1, round(value / int(line["qty"])))
                total += value
                cleared[f"due_{item}"] = 0.0
            cleared[f"owed_{item}"] = 0
        if total:
            ops.create_item("moeda", total, payee, "payment")
        ops.set_attributes(box.entity_id, hidden=cleared)
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


def kiosk_stock(ctx: SystemContext, ops: WorldOps) -> None:
    """O estoque de sementes do dia, pelo ciclo do cenário (ADR-0062); o ciclo não é dito."""
    view = ctx.view
    cycle = section(view, "kiosk_cycle")
    today = ((view.day - 1) % int(cycle["days"])) + 1
    season = view.season(view.day)
    items = section(view, "items")

    def in_season(seed: str) -> bool:  # a semente parada na estação não é vendida (ADR-0067)
        crop = items.get(seed, {}).get("crop")
        return crop is None or season_level(view, str(crop), season) != "parada"

    seeds = sorted(
        str(seed)
        for seed, days in cast(Mapping[str, Any], cycle["seeds"]).items()
        if today in cast(list[int], days) and in_season(str(seed))
    )
    always = sorted(str(item) for item in cast(list[Any], cycle.get("always", [])))
    stock = ", ".join(seeds + always)
    for kiosk in view.entities("kiosk"):
        ops.set_attributes(kiosk.entity_id, visible={"estoque_hoje": stock})


def crows(ctx: SystemContext, ops: WorldOps) -> None:
    """Na virada do dia, depois do crescimento: a planta madura longe da casa, sem espantalho por
    perto, pode amanhecer comida por um corvo (R-002, oculta; ADR-0067). O canteiro fica vazio e
    o efeito é visível; a distância, o raio do espantalho e a chance não são ditos."""
    view = ctx.view
    rule = section(view, "crows")
    anchor = view.entity(str(rule["anchor"])).position
    if anchor is None:
        return
    guards = [
        e.position for e in view.entities(str(rule["scarecrow_kind"])) if e.position is not None
    ]
    far, radius = int(rule["min_distance"]), int(rule["scarecrow_radius"])
    chance = float(rule["chance"])
    for plot in view.entities("plot"):
        spot = plot.position
        if plot.attributes.get("stage") != "madura" or spot is None:
            continue
        if spot.chebyshev(anchor) <= far or any(spot.chebyshev(g) <= radius for g in guards):
            continue
        if view.rng("crows").random() >= chance:
            continue
        crop = str(plot.attributes["crop"])
        ops.set_attributes(
            plot.entity_id, visible=EMPTY_PLOT, hidden=empty_hidden(view, plot.entity_id)
        )
        ops.emit(
            "campsverso.farm.crop.eaten.v1",
            {"plot_id": plot.entity_id, "crop": crop, "day": view.day, "by": "corvo"},
        )


def revert_plots(ctx: SystemContext, ops: WorldOps) -> None:
    """Na virada do dia, o canteiro cavado que passou `revert_after_days` manhãs vazio volta a ser
    grama (ADR-0067). Só os que guardam `empty_days` (os cavados do cenário que liga isto); o
    canteiro com planta, mesmo murcha, não conta, e o alvo de uma ação em andamento espera."""
    view = ctx.view
    limit = int(section(view, "digging")["revert_after_days"])
    for plot in view.entities("plot"):
        if "empty_days" not in plot.hidden:
            continue
        if plot.attributes.get("crop") is not None:
            if plot.hidden.get("empty_days"):
                ops.set_attributes(plot.entity_id, hidden={"empty_days": 0})
            continue
        days = int(plot.hidden.get("empty_days") or 0) + 1
        if days >= limit and not view.targeted(plot.entity_id):
            ops.despawn(plot.entity_id, "reverted_to_grass")
        else:
            ops.set_attributes(plot.entity_id, hidden={"empty_days": days})


def market_reset(ctx: SystemContext, ops: WorldOps) -> None:
    """Na virada do dia, os preços voltam à tabela e a contagem do dia zera (ADR-0062). Com o
    mercado que lembra, o preço só recupera parte do caminho (ADR-0069)."""
    view = ctx.view
    if memory_market(view) is not None:
        turnover(view, ops)
        return
    items = section(view, "items")
    for box in view.entities("sell_box"):
        visible: dict[str, Any] = {}
        hidden: dict[str, Any] = {}
        for item, info in sorted(items.items()):
            if info.get("category") != "colheita":
                continue
            visible[f"preco_{item}"] = int(info["sale_price"])
            hidden[f"sold_{item}"] = 0
        ops.set_attributes(box.entity_id, visible=visible, hidden=hidden)


def build_extension_systems(data: Mapping[str, Any]) -> tuple[FarmSystem, ...]:
    """Os sistemas que um cenário liga com as suas seções (ADR-0062)."""
    day_start = str(data.get("clock", {}).get("day_starts_at", "06:00"))
    systems: list[FarmSystem] = []
    if "kiosk_cycle" in data:
        systems.append(
            FarmSystem(
                "kiosk_stock",
                "scheduled",
                15,
                (OnSessionStart(), DailyAt((day_start,))),
                kiosk_stock,
            )
        )
    if "crows" in data:
        systems.append(
            FarmSystem(
                "crows",
                "scheduled",
                11,  # depois do crescimento (10): a planta que amadureceu hoje já pode ser comida
                (DailyAt((day_start,)),),
                crows,
            )
        )
    if "revert_after_days" in data.get("digging", {}):
        systems.append(
            FarmSystem(
                "revert_plots",
                "scheduled",
                12,  # depois do crescimento (10): o canteiro colhido hoje ainda conta como vazio
                (DailyAt((day_start,)),),
                revert_plots,
            )
        )
    if "orders" in data:
        systems.append(
            FarmSystem(
                "orders_daily",
                "scheduled",
                26,  # depois do mercado (25): o pedido sai pela referência de hoje
                (OnSessionStart(), DailyAt((day_start,))),
                orders_daily,
            )
        )
    weather = cast(Mapping[str, Any], data.get("weather") or {})
    if "forecast_at" in weather:  # o tempo de amanhã sai na véspera (ADR-0069): troca o do gênero
        systems.append(
            FarmSystem(
                "weather",
                "scheduled",
                10,
                (OnSessionStart(), DailyAt((str(weather["forecast_at"]),))),
                draw_weather,
            )
        )
    if "storm" in weather or "shock" in weather:
        systems.append(
            FarmSystem(
                "weather_effects",
                "scheduled",
                9,  # antes do crescimento (10): a planta que amadureceu hoje ainda não cai
                (DailyAt((day_start,)),),
                weather_effects,
            )
        )
    if "drought" in weather:
        water_by = str(cast(Mapping[str, Any], weather["drought"])["water_by"])
        systems.append(
            FarmSystem("drought_noon", "scheduled", 10, (DailyAt((water_by,)),), drought_noon)
        )
    if "processing" in data:
        systems.append(
            FarmSystem("machines_hourly", "scheduled", 18, (DailyAt(HOURS),), machines_hourly)
        )
    if "helpers" in data:  # os ajudantes (ADR-0072): a chegada e a saída no horário de cada ficha
        arrivals, departures = helper_times(cast(Mapping[str, Any], data["helpers"]))
        systems.append(
            FarmSystem("helpers_board", "scheduled", 30, (OnSessionStart(),), helpers_board)
        )
        systems.append(
            FarmSystem("helpers_arrive", "scheduled", 31, (DailyAt(arrivals),), helpers_arrive)
        )
        systems.append(
            FarmSystem("helpers_leave", "scheduled", 32, (DailyAt(departures),), helpers_leave)
        )
    if "fair" in data:
        fair = data["fair"]
        systems.append(
            FarmSystem(
                "fair_hours",
                "scheduled",
                27,  # depois do mercado (25) e das encomendas (26): a referência de hoje
                (OnSessionStart(), DailyAt((str(fair["opens"]), str(fair["closes"])))),
                fair_hours,
            )
        )
    if "market" in data:
        systems.append(
            FarmSystem(
                "market_reset",
                "scheduled",
                25,  # depois do pagamento (20), antes do dia novo (30)
                (OnSessionStart(), DailyAt((day_start,))),
                market_reset,
            )
        )
    return tuple(systems)


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
