"""Cartucho office, o gênero: o escritório em tempo real, com o pedido no quadro (ADR-0078)."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from campsverso_cartridge_api import (
    CartridgeManifest,
    ClockDef,
    EventLabelDef,
    KindDef,
    MetricDef,
    WorldBuilder,
)
from campsverso_office_sim import config
from campsverso_office_sim.actions import ALL_ACTIONS
from campsverso_office_sim.systems import build_systems

INTERRUPTS = ("never", "cancel", "partial")


def _kinds() -> tuple[KindDef, ...]:
    return (
        KindDef(config.AVATAR),
        KindDef(config.DESK, blocking=True, attributes={"dono": None}),
        KindDef(config.CHAIR),
        KindDef(config.BOARD, blocking=True),
        KindDef(config.BENCH, blocking=True),
        KindDef(config.DOOR),
        KindDef(config.TICKET),
        KindDef(config.WATER_COOLER, blocking=True),
        KindDef(config.COPA_COUNTER, blocking=True),
        KindDef(config.COPA_TABLE, blocking=True),
        KindDef(config.RESTROOM_DOOR),
    )


def labels(data: Mapping[str, Any]) -> tuple[EventLabelDef, ...]:
    """Os rótulos da linha do tempo, dos dados (ADR-0068)."""
    return tuple(
        EventLabelDef(
            event=str(entry["event"]), text=str(entry["text"]), where=dict(entry.get("where", {}))
        )
        for entry in data.get("labels", [])
    )


def metrics(data: Mapping[str, Any]) -> tuple[MetricDef, ...]:
    """As métricas do dia, dos dados (ADR-0054)."""
    return tuple(
        MetricDef(
            id=str(entry["id"]),
            label=str(entry["label"]),
            kind=entry["kind"],
            event=entry.get("event"),
            where=dict(entry.get("where", {})),
            field=entry.get("field"),
        )
        for entry in data.get("metrics", [])
    )


@dataclass(frozen=True)
class OfficeCartridge:
    manifest: CartridgeManifest = field(
        default_factory=lambda: CartridgeManifest(config.NAMESPACE, "0.1.0")
    )

    def contribute(self, world: WorldBuilder) -> None:
        data = config.load()
        clock = data["clock"]
        world.configure_clock(
            ClockDef(
                tick_seconds=float(clock["tick_seconds"]),  # 0,25 s (ADR-0081)
                day_starts_at=str(clock["day_starts_at"]),
                phases=tuple((name, str(hhmm)) for name, hhmm in clock["phases"].items()),
                default_scale=float(clock["default_scale"]),
            )
        )
        world.set_screen_tiles_per_second(float(data["movement"]["screen_tiles_per_second"]))
        radius = data["perception"]["radius"]
        world.set_perception_radius(None if radius is None else int(radius))
        world.set_interrupt_on_speech(bool(data["speech"]["interrupts"]))
        world.merge_data(config.NAMESPACE, data)
        for kind in _kinds():
            world.define_kind(kind)
        for action in ALL_ACTIONS:
            if data["actions"][action.name].get("interrupt") not in INTERRUPTS:  # ADR-0052
                raise ValueError(f"office.yaml: {action.name} precisa de interrupt em {INTERRUPTS}")
            world.add_action(action)
        for system in build_systems(data):
            world.add_system(system)
        for label in labels(data):
            world.add_label(label)
        for metric in metrics(data):
            world.add_metric(metric)

    def rules_file(self) -> Path | None:
        return None  # o escritório não tem regra oculta no M23: a medida é o pedido (ADR-0077)
