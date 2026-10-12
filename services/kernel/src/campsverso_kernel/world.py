"""Estado do mundo, com a visão de leitura e as operações primitivas dos cartuchos (ADR-0025).

Toda mudança de estado vira um fato genérico. Iterações que afetam o resultado são sempre em
ordem de id (princípio 4).
"""

import math
from collections.abc import Generator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Literal

from campsverso_cartridge_api import (
    Attributes,
    ControllerRef,
    EntityView,
    Position,
    Scalar,
    SleepCause,
    ThresholdDef,
)
from campsverso_contracts import CONTRACT_TYPES
from campsverso_kernel.calendar import Calendar, parse_hhmm
from campsverso_kernel.definition import WorldDefinition
from campsverso_kernel.errors import WorldRuleError
from campsverso_kernel.facts import FactLog
from campsverso_kernel.rng import RngStreams, SplitMix64
from campsverso_kernel.rules import Contribution, RulesEngine

SCALE = 120  # unidades por ponto de necessidade (ADR-0038)
MAX_UNITS = 100 * SCALE


def to_units(points: float) -> int:
    units = points * SCALE
    rounded = round(units)
    if abs(units - rounded) > 1e-9:
        raise WorldRuleError(f"{points} pontos não é múltiplo de 1/{SCALE} (ADR-0038)")
    return rounded


def to_points(units: int) -> float:
    return units / SCALE


def position_data(position: Position) -> dict[str, int]:
    return {"x": position.x, "y": position.y}


def controller_data(controller: ControllerRef) -> dict[str, str]:
    return {"type": controller.type, "id": controller.id}


@dataclass
class Entity:
    entity_id: str
    kind: str
    position: Position | None
    container_id: str | None
    blocking: bool
    display_name: str | None
    attributes: dict[str, Scalar]
    hidden: dict[str, Scalar]


@dataclass(frozen=True, slots=True)
class Trajectory:
    origin: Position
    path: tuple[Position, ...]  # origem incluída
    depart_tick: int
    tiles_per_tick: float

    def position_at(self, tick: int) -> Position:
        steps = math.floor((tick - self.depart_tick) * self.tiles_per_tick + 1e-9)
        return self.path[max(0, min(len(self.path) - 1, steps))]


@dataclass
class RunningAction:
    action_id: str
    name: str
    params: dict[str, Any]
    applied_tick: int
    end_tick: int
    command_id: str | None
    correlation: str | None
    trajectory: Trajectory | None = None


@dataclass
class Avatar:
    avatar_id: str
    controller: ControllerRef
    default_controller: ControllerRef
    action: RunningAction | None = None
    asleep: bool = False
    sleep_cause: SleepCause | None = None
    wake_tick: int | None = None
    wake_needs: dict[str, float] = field(default_factory=dict[str, float])
    pending: list[str] = field(default_factory=list[str])

    @property
    def idle(self) -> bool:
        return self.action is None and not self.asleep

    def add_pending(self, reason: str) -> None:
        if reason not in self.pending:
            self.pending.append(reason)


@dataclass(frozen=True, slots=True)
class _Context:
    action: RunningAction | None = None
    cause: str | None = None
    caused_by: int | str | None = None
    correlation: str | None = None


class World:
    """Implementa WorldView e WorldOps (campsverso_cartridge_api)."""

    def __init__(
        self,
        definition: WorldDefinition,
        calendar: Calendar,
        rng: RngStreams,
        rules: RulesEngine,
        log: FactLog,
    ) -> None:
        self.definition = definition
        self.calendar = calendar
        self.rules = rules
        self.log = log
        self._rng = rng
        self.tick = 0
        self.entity_map: dict[str, Entity] = {}
        self.containers: dict[str, dict[str, int]] = {}
        self.needs: dict[str, dict[str, int]] = {}
        self.reported_needs: dict[str, dict[str, int]] = {}
        self.avatar_map: dict[str, Avatar] = {}
        self.weather_by_day: dict[int, str] = {}
        self.contributions: dict[str, dict[str, Contribution]] = {}
        self.crossings: list[
            tuple[str, ThresholdDef]
        ] = []  # deste tick, para os sistemas de reação
        self.blocked: frozenset[Position] = frozenset()
        self._context = _Context()
        self.rates = self._unit_rates()

    # ------------------------------------------------------------- montagem

    def _unit_rates(self) -> dict[str, dict[str, int]]:
        rates: dict[str, dict[str, int]] = {}
        for need in self.definition.needs.values():
            rates[need.need] = {}
            for state, per_hour in need.rates_per_hour.items():
                exact = per_hour * SCALE * self.calendar.tick_seconds / 3600
                if abs(exact - round(exact)) > 1e-9:
                    raise WorldRuleError(
                        f"taxa de {need.need} ({per_hour}/h) não vira unidade inteira por tick"
                    )
                rates[need.need][state] = round(exact)
        return rates

    def spawn_all(self) -> None:
        """Cria entidades, itens iniciais, necessidades e avatares, publicando os fatos."""
        spawns = sorted(
            self.definition.spawns.values(), key=lambda s: (s.position is None, s.entity_id)
        )
        for spawn in spawns:
            kind = self.definition.kinds[spawn.kind]
            entity = Entity(
                entity_id=spawn.entity_id,
                kind=spawn.kind,
                position=spawn.position,
                container_id=spawn.container_id,
                blocking=spawn.blocking or kind.blocking,
                display_name=spawn.display_name,
                attributes={**kind.attributes, **spawn.attributes},
                hidden={**kind.hidden, **spawn.hidden},
            )
            self.entity_map[entity.entity_id] = entity
            data: dict[str, Any] = {
                "entity_id": entity.entity_id,
                "kind": entity.kind,
                "blocking": entity.blocking,
            }
            if entity.position is not None:
                data["position"] = position_data(entity.position)
            if entity.container_id is not None:
                data["container_id"] = entity.container_id
            if entity.display_name is not None:
                data["display_name"] = entity.display_name
            if entity.attributes:
                data["attributes"] = dict(entity.attributes)
            self.emit_fact("campsverso.world.entity.spawned.v1", data)
        self.blocked = frozenset(
            e.position for e in self.entity_map.values() if e.blocking and e.position is not None
        )
        for container, item, qty in sorted(self.definition.initial_items):
            self.create_item(item, qty, container, "initial")
        for avatar in self.definition.avatars.values():
            self.avatar_map[avatar.entity_id] = Avatar(
                avatar.entity_id, avatar.default_controller, avatar.default_controller
            )
            units = {n.need: to_units(n.initial) for n in self.definition.needs.values()}
            self.needs[avatar.entity_id] = dict(sorted(units.items()))
            self.reported_needs[avatar.entity_id] = dict(sorted(units.items()))

    # ------------------------------------------------------------- contexto e fatos

    @contextmanager
    def context(
        self,
        *,
        action: RunningAction | None = None,
        cause: str | None = None,
        caused_by: int | str | None = None,
        correlation: str | None = None,
    ) -> Generator[None]:
        previous = self._context
        self._context = _Context(action, cause, caused_by, correlation)
        try:
            yield
        finally:
            self._context = previous

    def emit_fact(self, event_type: str, data: Mapping[str, Any], **extra: Any) -> None:
        self.log.emit(
            self.tick,
            event_type,
            data,
            caused_by=extra.get("caused_by", self._context.caused_by),
            correlation=extra.get("correlation", self._context.correlation),
            opens_correlation=bool(extra.get("opens_correlation", False)),
        )

    def _with_action(self, data: dict[str, Any]) -> dict[str, Any]:
        if self._context.action is not None:
            data["action_id"] = self._context.action.action_id
        return data

    # ------------------------------------------------------------- WorldView

    @property
    def day(self) -> int:
        return self.calendar.day(self.tick)

    @property
    def minute_of_day(self) -> int:
        return self.calendar.minute_of_day(self.tick)

    def ticks_until(self, hhmm: str) -> int:
        return self.calendar.ticks_until(self.tick, parse_hhmm(hhmm))

    def weather(self, day: int) -> str | None:
        return self.weather_by_day.get(day)

    def data(self, namespace: str) -> Mapping[str, Any]:
        return MappingProxyType(dict(self.definition.data.get(namespace, {})))

    def position_of(self, entity_id: str) -> Position | None:
        avatar = self.avatar_map.get(entity_id)
        if (
            avatar is not None
            and avatar.action is not None
            and avatar.action.trajectory is not None
        ):
            return avatar.action.trajectory.position_at(self.tick)
        return self.entity_map[entity_id].position

    def entity(self, entity_id: str) -> EntityView:
        if entity_id not in self.entity_map:
            raise WorldRuleError(f"entidade inexistente: {entity_id}")
        e = self.entity_map[entity_id]
        return EntityView(
            entity_id=e.entity_id,
            kind=e.kind,
            position=self.position_of(entity_id),
            container_id=e.container_id,
            blocking=e.blocking,
            display_name=e.display_name,
            attributes=MappingProxyType(dict(e.attributes)),
            hidden=MappingProxyType(dict(e.hidden)),
        )

    def entities(self, kind: str | None = None) -> Sequence[EntityView]:
        return [
            self.entity(i)
            for i in sorted(self.entity_map)
            if kind is None or self.entity_map[i].kind == kind
        ]

    def items(self, container_id: str) -> Mapping[str, int]:
        return MappingProxyType(dict(sorted(self.containers.get(container_id, {}).items())))

    def need(self, avatar_id: str, need: str) -> float:
        return to_points(self.needs[avatar_id][need])

    def is_asleep(self, avatar_id: str) -> bool:
        return self.avatar_map[avatar_id].asleep

    def avatars(self) -> Sequence[str]:
        return sorted(self.avatar_map)

    def tiles_with(self, tile_property: str) -> Sequence[Position]:
        return self.definition.grid.tiles_with(tile_property)

    def rng(self, stream: str) -> SplitMix64:
        return self._rng.get(stream)

    def walkable(self, position: Position) -> bool:
        grid = self.definition.grid
        return (
            grid.in_bounds(position)
            and grid.tile_property(position, "passable") is True
            and position not in self.blocked
        )

    # ------------------------------------------------------------- WorldOps: atributos e itens

    def set_attributes(
        self,
        entity_id: str,
        *,
        visible: Attributes | None = None,
        hidden: Attributes | None = None,
        cause: str | None = None,
    ) -> None:
        entity = self.entity_map[entity_id]
        entity.hidden.update(hidden or {})
        changes = {
            k: v for k, v in sorted((visible or {}).items()) if entity.attributes.get(k, ...) != v
        }
        if not changes:
            return
        entity.attributes.update(changes)
        data = self._with_action({"entity_id": entity_id, "changes": changes})
        reason = cause or self._context.cause
        if reason is not None:
            data["cause"] = reason
        self.emit_fact("campsverso.world.entity.state_changed.v1", data)

    def _check_item(self, item: str, qty: int, container_id: str) -> None:
        if item not in self.definition.items:
            raise WorldRuleError(f"item indefinido: {item}")
        if qty < 1:
            raise WorldRuleError(f"quantidade inválida de {item}: {qty}")
        if container_id not in self.entity_map:
            raise WorldRuleError(f"contêiner inexistente: {container_id}")

    def _take(self, item: str, qty: int, container_id: str) -> None:
        stock = self.containers.get(container_id, {})
        if stock.get(item, 0) < qty:
            raise WorldRuleError(f"{container_id} não tem {qty} {item}")
        stock[item] -= qty
        if stock[item] == 0:
            del stock[item]

    def create_item(self, item: str, qty: int, container_id: str, reason: str) -> None:
        self._check_item(item, qty, container_id)
        stock = self.containers.setdefault(container_id, {})
        stock[item] = stock.get(item, 0) + qty
        data = {"item": item, "qty": qty, "container_id": container_id, "reason": reason}
        self.emit_fact("campsverso.world.item.created.v1", self._with_action(data))

    def transfer_item(
        self, item: str, qty: int, from_container: str, to_container: str, reason: str
    ) -> None:
        self._check_item(item, qty, from_container)
        self._check_item(item, qty, to_container)
        self._take(item, qty, from_container)
        stock = self.containers.setdefault(to_container, {})
        stock[item] = stock.get(item, 0) + qty
        data = {
            "item": item,
            "qty": qty,
            "from_container": from_container,
            "to_container": to_container,
            "reason": reason,
        }
        self.emit_fact("campsverso.world.item.transferred.v1", self._with_action(data))

    def consume_item(self, item: str, qty: int, container_id: str, reason: str) -> None:
        self._check_item(item, qty, container_id)
        self._take(item, qty, container_id)
        data = {"item": item, "qty": qty, "container_id": container_id, "reason": reason}
        self.emit_fact("campsverso.world.item.consumed.v1", self._with_action(data))

    # ------------------------------------------------------------- WorldOps: necessidades

    def change_need(self, avatar_id: str, need: str, delta: float) -> None:
        self.set_need_units(avatar_id, need, self.needs[avatar_id][need] + to_units(delta))

    def set_need_units(self, avatar_id: str, need: str, units: int) -> None:
        units = max(0, min(MAX_UNITS, units))
        previous = self.needs[avatar_id][need]
        self.needs[avatar_id][need] = units
        for threshold in self.definition.thresholds:
            if threshold.need != need:
                continue
            level = to_units(threshold.value)
            up = threshold.direction == "up" and previous < level <= units
            down = threshold.direction == "down" and previous > level >= units
            if not (up or down):
                continue
            self.emit_fact(
                "campsverso.world.need.threshold_crossed.v1",
                {
                    "avatar_id": avatar_id,
                    "need": need,
                    "threshold": threshold.value,
                    "direction": threshold.direction,
                    "value": to_points(units),
                },
            )
            self.crossings.append((avatar_id, threshold))
            if threshold.requests_decision:
                self.avatar_map[avatar_id].add_pending("need_threshold")

    def integrate_needs(self, ticks: int) -> None:
        for avatar_id in sorted(self.avatar_map):
            state = "asleep" if self.avatar_map[avatar_id].asleep else "awake"
            for need in sorted(self.needs[avatar_id]):
                rate = self.rates[need].get(state, 0)
                if rate:
                    self.set_need_units(avatar_id, need, self.needs[avatar_id][need] + rate * ticks)

    def report_needs(self) -> None:
        """No máximo um need.changed por hora simulada e por necessidade (contratos §14.3)."""
        for avatar_id in sorted(self.avatar_map):
            for need, units in sorted(self.needs[avatar_id].items()):
                previous = self.reported_needs[avatar_id][need]
                if units == previous:
                    continue
                self.reported_needs[avatar_id][need] = units
                self.emit_fact(
                    "campsverso.world.need.changed.v1",
                    {
                        "avatar_id": avatar_id,
                        "need": need,
                        "previous_value": to_points(previous),
                        "value": to_points(units),
                    },
                )

    def needs_points(self, avatar_id: str) -> dict[str, float]:
        return {need: to_points(units) for need, units in sorted(self.needs[avatar_id].items())}

    # ------------------------------------------------------------- WorldOps: clima, sono, desmaio

    def set_weather(self, condition: str, day: int) -> None:
        self.weather_by_day[day] = condition
        self.emit_fact("campsverso.world.weather.changed.v1", {"condition": condition, "day": day})

    def start_sleep(
        self,
        avatar_id: str,
        cause: SleepCause,
        wake_in_ticks: int,
        wake_needs: Mapping[str, float] | None = None,
    ) -> None:
        avatar = self.avatar_map[avatar_id]
        avatar.asleep = True
        avatar.sleep_cause = cause
        avatar.wake_tick = self.tick + wake_in_ticks
        avatar.wake_needs = dict(wake_needs or {})
        position = self.position_of(avatar_id)
        assert position is not None
        self.emit_fact(
            "campsverso.avatar.sleep.started.v1",
            {
                "avatar_id": avatar_id,
                "cause": cause,
                "position": position_data(position),
                "wake_at_tick": avatar.wake_tick,
            },
        )

    def wake(self, avatar_id: str) -> None:
        avatar = self.avatar_map[avatar_id]
        for need, value in sorted(avatar.wake_needs.items()):
            self.set_need_units(avatar_id, need, to_units(value))
        energy = next((n.need for n in self.definition.needs.values() if n.role == "energy"), None)
        cause = avatar.sleep_cause or "bed"
        avatar.asleep, avatar.sleep_cause, avatar.wake_tick, avatar.wake_needs = (
            False,
            None,
            None,
            {},
        )
        self.emit_fact(
            "campsverso.avatar.sleep.ended.v1",
            {
                "avatar_id": avatar_id,
                "cause": cause,
                "energy": self.need(avatar_id, energy) if energy is not None else 0.0,
            },
        )
        avatar.add_pending("woke_up")

    def interrupt_action(
        self, avatar_id: str, reason: Literal["cancelled", "fainted"]
    ) -> str | None:
        avatar = self.avatar_map[avatar_id]
        action = avatar.action
        if action is None:
            return None
        if action.trajectory is not None:
            position = action.trajectory.position_at(self.tick)
            self.entity_map[avatar_id].position = position
            self.emit_fact(
                "campsverso.world.entity.move_interrupted.v1",
                {
                    "entity_id": avatar_id,
                    "action_id": action.action_id,
                    "position": position_data(position),
                    "reason": reason,
                },
            )
        avatar.action = None
        self.emit_fact(
            "campsverso.action.failed.v1",
            {
                "action_id": action.action_id,
                "avatar_id": avatar_id,
                "action": action.name,
                "reason": reason,
            },
        )
        return action.action_id

    def faint(
        self,
        avatar_id: str,
        reason: Literal["late_night", "exhausted"],
        wake_in_ticks: int,
        wake_needs: Mapping[str, float],
    ) -> None:
        if self.avatar_map[avatar_id].asleep:
            return
        self.interrupt_action(avatar_id, "fainted")
        position = self.position_of(avatar_id)
        assert position is not None
        self.emit_fact(
            "campsverso.avatar.fainted.v1",
            {"avatar_id": avatar_id, "reason": reason, "position": position_data(position)},
        )
        self.start_sleep(avatar_id, "faint", wake_in_ticks, wake_needs)

    # ------------------------------------------------------------- WorldOps: regras e eventos

    def apply_rules(self, target: str, entity_id: str, base: float) -> float:
        value, contributions = self.rules.apply(self, target, self.entity(entity_id), base)
        for c in contributions:
            self.emit_fact(
                "campsverso.rules.effect_applied.v1",
                {
                    "rule": c.rule,
                    "version": c.version,
                    "entity_id": entity_id,
                    "property": target,
                    "base": c.base,
                    "applied": c.applied,
                },
            )
            self.contributions.setdefault(entity_id, {})[c.rule] = c
        return value

    def explain_effects(self, entity_id: str) -> None:
        action = self._context.action
        contributions = self.contributions.pop(entity_id, {})
        if action is None or not contributions:
            return
        rules = [
            {
                "rule": c.rule,
                "version": c.version,
                "hidden": c.hidden,
                "multiplier": c.applied / c.base if c.base else c.applied,
            }
            for _, c in sorted(contributions.items())
        ]
        self.emit_fact(
            "campsverso.action.effects_explained.v1",
            {"action_id": action.action_id, "rules_applied": rules},
        )

    def emit(self, event_type: str, data: Mapping[str, Any]) -> None:
        domain = event_type.split(".")[1]
        if domain not in {m.id for m in self.definition.chain}:
            raise WorldRuleError(
                f"{event_type}: o domínio precisa ser um cartucho da cadeia (ADR-0031)"
            )
        if event_type not in CONTRACT_TYPES:
            raise WorldRuleError(f"tipo de evento não declarado em contracts/: {event_type}")
        self.emit_fact(event_type, dict(data))
