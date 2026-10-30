"""Cartucho farm, o gênero: mecânicas genéricas de fazenda (ADR-0031)."""

import re
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
    Requirement,
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


_FIELD = re.compile(r"\{(?!target\.)([a-z_][a-z0-9_.]*)\}")  # `{target.x}` a tela resolve


def _note(raw: Any, data: Mapping[str, Any]) -> str | None:
    """A nota do menu (M21), com valores dos dados entre chaves: `aberto das {kiosk.opens}`."""
    if raw is None:
        return None

    def value(match: re.Match[str]) -> str:
        found: Any = data
        for key in match[1].split("."):
            found = cast(Mapping[str, Any], found)[key]
        return str(found)

    return _FIELD.sub(value, str(raw))


def _cost(
    action: str, entry: Mapping[str, Any], data: Mapping[str, Any]
) -> tuple[float, int] | None:
    """A energia e os minutos da ação pela tabela `actions`, para o menu (M21)."""
    numbers = cast(Mapping[str, Mapping[str, Any]], data.get("actions", {})).get(action)
    if numbers is None or entry.get("cost") is False:
        return None
    return float(numbers.get("energy", 0)), int(numbers.get("duration", 0))


def _prices(
    choices: tuple[str, ...], field: str, data: Mapping[str, Any]
) -> tuple[tuple[str, float], ...]:
    """O preço de tabela de cada escolha: o campo `field` do item, ou o da ferramenta à venda."""
    items = cast(Mapping[str, Mapping[str, Any]], data.get("items", {}))
    tools = cast(Mapping[str, Any], data.get("tools", {}))
    for_sale = cast(Mapping[str, Mapping[str, Any]], tools.get("for_sale", {}))
    found: list[tuple[str, float]] = []
    for choice in choices:
        price = items.get(choice, {}).get(field, for_sale.get(choice, {}).get(field))
        if price is not None:
            found.append((choice, float(price)))
    return tuple(found)


def _notes(
    raw: Any, choices: tuple[str, ...], data: Mapping[str, Any]
) -> tuple[tuple[str, str], ...]:
    """Uma nota de cada escolha (M21): `{from: helpers.roster, text: "{nome}, {bom}"}` formata o
    texto com os campos da ficha de cada escolha."""
    if raw is None:
        return ()
    spec = cast(Mapping[str, str], raw)
    found: Any = data
    for key in spec["from"].split("."):
        found = cast(Mapping[str, Any], found)[key]
    sheets = cast(Mapping[str, Mapping[str, Any]], found)
    return tuple(
        (choice, _FIELD.sub(lambda m, s=sheets[choice]: str(s[m[1]]), spec["text"]))
        for choice in choices
        if choice in sheets
    )


def _requires(raw: Any) -> tuple[Requirement, ...]:
    """O que precisa valer para a ação fazer sentido agora (M21), pelo YAML: `{attribute, in,
    hint}` sobre o alvo ou `{item, hint}` no inventário."""
    return tuple(
        Requirement(
            hint=str(r["hint"]),
            attribute=r.get("attribute"),
            values=tuple(cast(list[Any], r.get("in", []))),
            item=r.get("item"),
        )
        for r in cast(list[Mapping[str, Any]], raw or [])
    )


def _param(p: Mapping[str, Any], data: Mapping[str, Any]) -> AffordanceParam:
    choices = _choices(p.get("choices"), cast(dict[str, Any], data))
    return AffordanceParam(
        name=str(p["name"]),
        label=str(p["label"]),
        choices=choices,
        source=p.get("source", "any"),
        minimum=p.get("minimum"),
        default=p.get("default"),
        entities=bool(p.get("entities", False)),
        prices=_prices(choices, str(p["price"]), data) if p.get("price") else (),
        price_attribute=p.get("price_attribute"),
        stock_attribute=p.get("stock_attribute"),
        held_prefix=p.get("held_prefix"),
        option_notes=_notes(p.get("notes"), choices, data),
    )


def affordances(data: Mapping[str, Any]) -> tuple[AffordanceDef, ...]:
    """O catálogo de ações do `farm.yaml`, com as escolhas resolvidas pelos dados do gênero. Para o
    menu (M21): o custo de cada ação pela tabela `actions`, a nota (o horário) e o preço de tabela
    das escolhas de um parâmetro com `price` (o campo do item: `price` ou `sale_price`)."""
    return tuple(
        AffordanceDef(
            action=str(entry["action"]),
            label=str(entry["label"]),
            on=tuple(entry["kinds"]),  # `on` no contrato; no YAML 1.1, `on` vira booleano
            target=bool(entry.get("target", True)),
            params=tuple(_param(p, data) for p in entry.get("params", [])),
            cost=_cost(str(entry["action"]), entry, data),
            note=_note(entry.get("note"), data),
            requires=_requires(entry.get("requires")),
        )
        for entry in cast(list[Mapping[str, Any]], data.get("affordances", []))
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
