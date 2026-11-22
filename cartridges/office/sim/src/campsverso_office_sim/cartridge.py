"""Cartucho office, o gênero: o escritório em tempo real, com o pedido no quadro (ADR-0078)."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

from campsverso_cartridge_api import (
    AffordanceDef,
    CartridgeManifest,
    ClockDef,
    EventLabelDef,
    KindDef,
    MetricDef,
    Requirement,
    Scalar,
    WorldBuilder,
)
from campsverso_office_sim import config
from campsverso_office_sim.actions import ALL_ACTIONS
from campsverso_office_sim.commands import COMMANDS
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
        KindDef(config.COPA_CHAIR, attributes={"virada": None}),  # um assento, de lado
        KindDef(config.COFFEE_MACHINE, blocking=True),
        KindDef(config.FRIDGE, blocking=True),
        KindDef(config.MICROWAVE, blocking=True),
        KindDef(config.TRASH, blocking=True),
        KindDef(config.RESTROOM_DOOR, attributes={"lado": None}),
        KindDef(config.RESTROOM),
        KindDef(config.FILE_CABINET, blocking=True),
        KindDef(config.PLANT, blocking=True),
        KindDef(config.TV, blocking=True),
        KindDef(config.SOFA, blocking=True),
        KindDef(config.PUFF, blocking=True, attributes={"cor": None}),
        KindDef(config.ROBOT, attributes={"nome": None, "modulo": None, "descricao": None}),
        KindDef(config.LIGHT_SWITCH, attributes={"acesa": None}),  # na parede (ADR-0088)
    )


def labels(data: Mapping[str, Any]) -> tuple[EventLabelDef, ...]:
    """Os rótulos da linha do tempo, dos dados (ADR-0068)."""
    return tuple(
        EventLabelDef(
            event=str(entry["event"]), text=str(entry["text"]), where=dict(entry.get("where", {}))
        )
        for entry in data.get("labels", [])
    )


def affordances(data: Mapping[str, Any]) -> tuple[AffordanceDef, ...]:
    """O menu de quem está no escritório (ADR-0051, ADR-0082): as pausas, pelo `office.yaml`."""
    return tuple(
        AffordanceDef(
            action=str(entry["action"]),
            label=str(entry["label"]),
            on=tuple(str(k) for k in entry["kinds"]),  # `on` no contrato; `kinds` no YAML
            target=bool(entry.get("target", True)),
            note=None if entry.get("note") is None else str(entry["note"]),
            requires=tuple(
                Requirement(
                    hint=str(need["hint"]),
                    attribute=None if need.get("attribute") is None else str(need["attribute"]),
                    values=tuple(cast(list[Scalar | None], need.get("values") or [])),
                )
                for need in cast(list[Mapping[str, Any]], entry.get("requires") or [])
            ),
        )
        for entry in cast(list[Mapping[str, Any]], data.get("affordances", []))
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
        for command in COMMANDS:  # o que vem de fora: o PR do dev (ADR-0083, ADR-0084)
            world.add_command(command)
        for label in labels(data):
            world.add_label(label)
        for metric in metrics(data):
            world.add_metric(metric)
        for affordance in affordances(data):
            world.add_affordance(affordance)

    def rules_file(self) -> Path | None:
        return None  # o escritório não tem regra oculta no M23: a medida é o pedido (ADR-0077)
