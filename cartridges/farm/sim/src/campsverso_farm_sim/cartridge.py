"""Cartucho farm, o gênero: mecânicas genéricas de fazenda (ADR-0031)."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

from campsverso_cartridge_api import (
    AffordanceDef,
    AffordanceParam,
    CartridgeManifest,
    ClockDef,
    EventLabelDef,
    ItemDef,
    KindDef,
    MetricDef,
    NeedDef,
    ThresholdDef,
    WorldBuilder,
)
from campsverso_farm_sim import config
from campsverso_farm_sim.actions import ALL_ACTIONS, EMPTY_HIDDEN, EMPTY_PLOT, INTERRUPTS
from campsverso_farm_sim.rules import SoilFatigue, WaterProximityBonus
from campsverso_farm_sim.systems import build_systems


def _kinds(data: dict[str, Any]) -> tuple[KindDef, ...]:
    capacity = int(data["watering_can"]["capacity"])
    return (
        KindDef("avatar"),
        KindDef("plot", attributes=EMPTY_PLOT, hidden=EMPTY_HIDDEN),
        KindDef("bed", blocking=True),
        KindDef("table", blocking=True),
        KindDef("chest", blocking=True),
        KindDef("sell_box", blocking=True),
        KindDef("well", blocking=True),
        KindDef("kiosk", blocking=True, attributes={"open": False}),
        KindDef("door"),
        KindDef("watering_can", attributes={"charges": capacity, "capacity": capacity}),
    )


def _choices(raw: Any, data: dict[str, Any]) -> tuple[str, ...]:
    """Escolhas de um parâmetro: lista, `crops` ou `{category: [...]}` (ADR-0051)."""
    if raw is None:
        return ()
    if raw == "crops":
        return tuple(data["crops"])
    if isinstance(raw, dict):
        wanted = cast(dict[str, list[str]], raw)["category"]
        return tuple(i for i, info in data["items"].items() if info["category"] in wanted)
    return tuple(str(c) for c in cast(list[Any], raw))


def affordances(data: dict[str, Any]) -> tuple[AffordanceDef, ...]:
    """O catálogo de ações do `farm.yaml`, com as escolhas resolvidas pelos dados do gênero."""
    return tuple(
        AffordanceDef(
            action=str(entry["action"]),
            label=str(entry["label"]),
            on=tuple(entry["kinds"]),  # `on` no contrato; no YAML 1.1, `on` vira booleano
            target=bool(entry.get("target", True)),
            params=tuple(
                AffordanceParam(
                    name=str(p["name"]),
                    label=str(p["label"]),
                    choices=_choices(p.get("choices"), data),
                    source=p.get("source", "any"),
                    minimum=p.get("minimum"),
                    default=p.get("default"),
                    entities=bool(p.get("entities", False)),
                )
                for p in entry.get("params", [])
            ),
        )
        for entry in data.get("affordances", [])
    )


def metrics(data: Mapping[str, Any]) -> tuple[MetricDef, ...]:
    """O catálogo de métricas do dia, dos dados (ADR-0054)."""
    return tuple(
        MetricDef(
            id=str(entry["id"]),
            label=str(entry["label"]),
            kind=entry["kind"],
            event=entry.get("event"),
            where=dict(entry.get("where", {})),
            by_field=entry.get("by", {}).get("field"),
            by_attribute=entry.get("by", {}).get("attribute"),
            need=entry.get("need"),
            item=entry.get("item"),
            field=entry.get("field"),
        )
        for entry in data.get("metrics", [])
    )


def labels(data: Mapping[str, Any]) -> tuple[EventLabelDef, ...]:
    """Os rótulos da linha do tempo, dos dados (ADR-0068)."""
    return tuple(
        EventLabelDef(
            event=str(entry["event"]), text=str(entry["text"]), where=dict(entry.get("where", {}))
        )
        for entry in data.get("labels", [])
    )


@dataclass(frozen=True)
class FarmCartridge:
    manifest: CartridgeManifest = field(default_factory=lambda: CartridgeManifest("farm", "0.2.0"))

    def contribute(self, world: WorldBuilder) -> None:
        data = config.load()
        clock = data["clock"]
        world.configure_clock(
            ClockDef(
                tick_seconds=int(clock["tick_seconds"]),
                day_starts_at=str(clock["day_starts_at"]),
                phases=tuple((name, str(hhmm)) for name, hhmm in clock["phases"].items()),
                default_scale=float(clock["default_scale"]),
            )
        )
        world.set_tiles_per_minute(float(data["movement"]["tiles_per_minute"]))
        radius = data["perception"]["radius"]
        world.set_perception_radius(None if radius is None else int(radius))
        world.merge_data(config.NAMESPACE, data)
        for kind in _kinds(data):
            world.define_kind(kind)
        for item, info in data["items"].items():
            world.define_item(ItemDef(item, str(info["category"])))
        for need, info in data["needs"].items():
            world.define_need(
                NeedDef(
                    need,
                    float(info["initial"]),
                    dict(info["rates_per_hour"]),
                    role=info.get("role"),
                )
            )
        for threshold in data["thresholds"]:
            world.add_threshold(
                ThresholdDef(
                    threshold["need"],
                    float(threshold["value"]),
                    threshold["direction"],
                    bool(threshold["requests_decision"]),
                )
            )
        for action in ALL_ACTIONS:
            interrupt = data["actions"][action.name].get("interrupt")
            if interrupt not in INTERRUPTS:  # ADR-0052
                raise ValueError(f"farm.yaml: {action.name} precisa de interrupt em {INTERRUPTS}")
            world.add_action(action)
        for system in build_systems(data):
            world.add_system(system)
        world.add_rule_impl(WaterProximityBonus())
        world.add_rule_impl(SoilFatigue())
        for affordance in affordances(data):
            world.add_affordance(affordance)
        for metric in metrics(data):
            world.add_metric(metric)
        for label in labels(data):
            world.add_label(label)

    def rules_file(self) -> Path | None:
        return None  # o gênero não liga nenhuma regra; o cenário decide (ADR-0039)
