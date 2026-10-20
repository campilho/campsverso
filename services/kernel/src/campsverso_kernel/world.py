"""Estado do mundo, com a visão de leitura e as operações primitivas dos cartuchos (ADR-0025).

Toda mudança de estado vira um fato genérico. Iterações que afetam o resultado são sempre em
ordem de id (princípio 4).
"""

import math
from collections.abc import Generator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Literal, cast

from campsverso_cartridge_api import (
    ActionContext,
    Attributes,
    ControllerRef,
    EntityView,
    Interrupt,
    Position,
    Scalar,
    SleepCause,
    SpawnDef,
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
    interrupt: Interrupt = "cancel"  # ADR-0052


@dataclass
class Avatar:
    avatar_id: str
    controller: ControllerRef
    default_controller: ControllerRef
    action: RunningAction | None = None
    asleep: bool = False
    sleep_cause: SleepCause | None = None
    bed_id: str | None = None
    wake_tick: int | None = None
    wake_needs: dict[str, float] = field(default_factory=dict[str, float])
    sleep_rates: dict[str, int] = field(default_factory=dict[str, int])  # unidades por tick
    pending: list[str] = field(default_factory=list[str])
    awaiting: bool = False  # pediu decisão e o controlador ainda não respondeu (lockstep)
    # Modificadores de necessidade (ADR-0062): {need, factor, until_tick, label}, por ordem.
    modifiers: list[dict[str, Any]] = field(default_factory=list[dict[str, Any]])

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
        # Lotes dos itens com validade (ADR-0062): contêiner -> item -> [[dia_de_origem, qty]...],
        # do mais velho ao mais novo; as contagens continuam em `containers`.
        self.lots: dict[str, dict[str, list[list[int]]]] = {}
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

    def _unit_rate(self, need: str, per_hour: float) -> int:
        exact = per_hour * SCALE * self.calendar.tick_seconds / 3600
        if abs(exact - round(exact)) > 1e-9:
            raise WorldRuleError(f"taxa de {need} ({per_hour}/h) não vira unidade inteira por tick")
        return round(exact)

    def _unit_rates(self) -> dict[str, dict[str, int]]:
        return {
            need.need: {
                state: self._unit_rate(need.need, per_hour)
                for state, per_hour in need.rates_per_hour.items()
            }
            for need in self.definition.needs.values()
        }

    def base_rate(self, avatar_id: str, need: str) -> int:
        """Unidades por tick sem modificadores: o sono em curso pode trocar a taxa `asleep`
        (ADR-0041)."""
        avatar = self.avatar_map[avatar_id]
        if avatar.asleep and need in avatar.sleep_rates:
            return avatar.sleep_rates[need]
        return self.rates[need].get("asleep" if avatar.asleep else "awake", 0)

    def rate(self, avatar_id: str, need: str, at_tick: int | None = None) -> int:
        """Unidades por tick no tick dado (o atual, por padrão), com os modificadores ativos
        (ADR-0062). O produto tem de dar unidades inteiras: com 120 unidades por ponto, 3 por hora
        são 6 por tick, e um fator 0,5 dá 3."""
        base = self.base_rate(avatar_id, need)
        factor = self._factor(avatar_id, need, self.tick if at_tick is None else at_tick)
        if factor == 1.0 or base == 0:
            return base
        exact = base * factor
        if abs(exact - round(exact)) > 1e-9:
            raise WorldRuleError(
                f"modificador {factor} de {need} não dá unidades inteiras por tick"
            )
        return round(exact)

    def _factor(self, avatar_id: str, need: str, tick: int) -> float:
        factor = 1.0
        for modifier in self.avatar_map[avatar_id].modifiers:
            if modifier["need"] == need and tick < int(modifier["until_tick"]):
                factor *= float(modifier["factor"])
        return factor

    def add_need_modifier(
        self, avatar_id: str, need: str, factor: float, ticks: int, label: str
    ) -> None:
        if need not in self.needs[avatar_id]:
            raise WorldRuleError(f"necessidade indefinida: {need}")
        if ticks < 1 or factor < 0:
            raise WorldRuleError(
                f"modificador inválido de {need}: fator {factor} por {ticks} ticks"
            )
        avatar = self.avatar_map[avatar_id]
        until = self.tick + ticks
        avatar.modifiers = [m for m in avatar.modifiers if m["label"] != label]
        avatar.modifiers.append(
            {"need": need, "factor": float(factor), "until_tick": until, "label": label}
        )
        self.rate(avatar_id, need)  # confere já que o produto dá unidades inteiras
        self.set_attributes(
            avatar_id, visible={label: self.calendar.simtime(until).strftime("%H:%M")}
        )

    def modifier_expiries(self) -> list[int]:
        """Os ticks em que algum modificador vence: o salto do modo máximo para neles."""
        return sorted({int(m["until_tick"]) for a in self.avatar_map.values() for m in a.modifiers})

    def _expire_modifiers(self, avatar_id: str, tick: int) -> None:
        avatar = self.avatar_map[avatar_id]
        expired = [m for m in avatar.modifiers if int(m["until_tick"]) <= tick]
        if not expired:
            return
        avatar.modifiers = [m for m in avatar.modifiers if int(m["until_tick"]) > tick]
        self.set_attributes(avatar_id, visible={str(m["label"]): None for m in expired})

    def spawn_all(self) -> None:
        """Cria entidades, itens iniciais, necessidades e avatares, publicando os fatos."""
        spawns = sorted(
            self.definition.spawns.values(), key=lambda s: (s.position is None, s.entity_id)
        )
        for spawn in spawns:
            self._spawn_entity(spawn)
        self._reblock()
        for container, item, qty in sorted(self.definition.initial_items):
            self.create_item(item, qty, container, "initial")
        for avatar in self.definition.avatars.values():
            self.avatar_map[avatar.entity_id] = Avatar(
                avatar.entity_id, avatar.default_controller, avatar.default_controller
            )
            units = {n.need: to_units(n.initial) for n in self.definition.needs.values()}
            self.needs[avatar.entity_id] = dict(sorted(units.items()))
            self.reported_needs[avatar.entity_id] = dict(sorted(units.items()))

    def _spawn_entity(self, spawn: SpawnDef) -> Entity:
        """Cria a entidade com os padrões do tipo e publica `world.entity.spawned`. Um tipo com
        capacidade mostra `capacity` como atributo visível (ADR-0062)."""
        kind = self.definition.kinds[spawn.kind]
        attributes: dict[str, Scalar] = {**kind.attributes, **spawn.attributes}
        if kind.capacity is not None:
            attributes.setdefault("capacity", kind.capacity)
        entity = Entity(
            entity_id=spawn.entity_id,
            kind=spawn.kind,
            position=spawn.position,
            container_id=spawn.container_id,
            blocking=spawn.blocking or kind.blocking,
            display_name=spawn.display_name,
            attributes=attributes,
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
        self.emit_fact("campsverso.world.entity.spawned.v1", self._with_action(data))
        return entity

    def _reblock(self) -> None:
        self.blocked = frozenset(
            e.position for e in self.entity_map.values() if e.blocking and e.position is not None
        )

    def spawn(self, entity: SpawnDef) -> None:
        """WorldOps: uma entidade nova em tempo de execução (ADR-0062)."""
        if entity.entity_id in self.entity_map:
            raise WorldRuleError(f"entidade já existe: {entity.entity_id}")
        if entity.kind not in self.definition.kinds:
            raise WorldRuleError(f"tipo indefinido: {entity.kind}")
        if entity.container_id is not None and entity.container_id not in self.entity_map:
            raise WorldRuleError(f"contêiner inexistente: {entity.container_id}")
        if entity.container_id is not None and not self.fits_entity(
            entity.kind, entity.container_id
        ):
            raise WorldRuleError(
                f"{entity.container_id} não aguenta {entity.entity_id} (too_heavy): "
                "a ação devia ter recusado"
            )
        created = self._spawn_entity(entity)
        if entity.container_id is not None:
            self._weigh(entity.container_id)
        if created.blocking and created.position is not None:
            self._reblock()

    # ------------------------------------------------------------- snapshot (M2)

    def export_state(self) -> dict[str, Any]:
        """Estado completo numa fronteira de tick, em tipos JSON e na ordem atual dos dicionários.

        Guardar a ordem faz o mundo restaurado iterar exatamente como o original.
        """
        if self.crossings:
            raise WorldRuleError("snapshot no meio de um tick: há limiares cruzados pendentes")
        return {
            "tick": self.tick,
            "entities": [_entity_data(e) for e in self.entity_map.values()],
            "containers": {c: dict(stock) for c, stock in self.containers.items()},
            "lots": {
                c: {item: [list(lot) for lot in lots] for item, lots in by_item.items()}
                for c, by_item in self.lots.items()
            },
            "needs": {a: dict(units) for a, units in self.needs.items()},
            "reported_needs": {a: dict(units) for a, units in self.reported_needs.items()},
            "avatars": [_avatar_data(a) for a in self.avatar_map.values()],
            "weather": [[day, condition] for day, condition in self.weather_by_day.items()],
            "contributions": {
                entity: {
                    name: {
                        "rule": c.rule,
                        "version": c.version,
                        "hidden": c.hidden,
                        "base": c.base,
                        "applied": c.applied,
                    }
                    for name, c in rules.items()
                }
                for entity, rules in self.contributions.items()
            },
            "rng": self._rng.states(),
            "rules": self.rules.export_state(),
        }

    def import_state(self, state: Mapping[str, Any]) -> None:
        self.tick = int(state["tick"])
        self.entity_map = {
            e["entity_id"]: _entity_from(e) for e in cast(list[dict[str, Any]], state["entities"])
        }
        self.containers = {c: dict(stock) for c, stock in state["containers"].items()}
        self.lots = {
            str(c): {
                str(item): [[int(d), int(q)] for d, q in lots] for item, lots in by_item.items()
            }
            for c, by_item in cast(Mapping[str, Any], state.get("lots") or {}).items()
        }
        self.needs = {a: dict(units) for a, units in state["needs"].items()}
        self.reported_needs = {a: dict(units) for a, units in state["reported_needs"].items()}
        self.avatar_map = {
            a["avatar_id"]: _avatar_from(a) for a in cast(list[dict[str, Any]], state["avatars"])
        }
        self.weather_by_day = {int(day): str(condition) for day, condition in state["weather"]}
        self.contributions = {
            entity: {name: Contribution(**c) for name, c in rules.items()}
            for entity, rules in state["contributions"].items()
        }
        self.crossings = []
        self.blocked = frozenset(
            e.position for e in self.entity_map.values() if e.blocking and e.position is not None
        )
        self._rng.restore(dict(state["rng"]))
        self.rules.restore_state(state["rules"])

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

    def tile_kind(self, position: Position) -> str | None:
        grid = self.definition.grid
        return grid.tile_kinds[position.y][position.x] if grid.in_bounds(position) else None

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

    # --- peso e capacidade (ADR-0062)

    def weight(self, container_id: str) -> float:
        """Os itens pelo peso de cada um, mais as entidades guardadas pelo peso do tipo."""
        stock = self.containers.get(container_id, {})
        items = sum(qty * float(self.definition.items[item].weight) for item, qty in stock.items())
        held = sum(
            float(self.definition.kinds[e.kind].weight)
            for e in self.entity_map.values()
            if e.container_id == container_id
        )
        return round(items + held, 3)

    def fits_entity(self, kind: str, container_id: str) -> bool:
        capacity = self.capacity(container_id)
        if capacity is None:
            return True
        extra = float(self.definition.kinds[kind].weight)
        return self.weight(container_id) + extra <= capacity + 1e-9

    def move_entity(self, entity_id: str, to_container: str) -> None:
        entity = self.entity_map.get(entity_id)
        if entity is None:
            raise WorldRuleError(f"entidade inexistente: {entity_id}")
        if to_container not in self.entity_map or to_container == entity_id:
            raise WorldRuleError(f"contêiner inválido: {to_container}")
        if entity.container_id == to_container:
            raise WorldRuleError(f"{entity_id} já está em {to_container}")
        if not self.fits_entity(entity.kind, to_container):
            raise WorldRuleError(
                f"{to_container} não aguenta {entity_id} (too_heavy): a ação devia ter recusado"
            )
        data: dict[str, Any] = {"entity_id": entity_id, "to_container": to_container}
        if entity.container_id is not None:
            data["from_container"] = entity.container_id
        origin = entity.container_id
        was_blocking = entity.blocking and entity.position is not None
        entity.container_id, entity.position = to_container, None
        self.emit_fact("campsverso.world.entity.stored.v1", self._with_action(data))
        if was_blocking:
            self._reblock()
        if origin is not None:
            self._weigh(origin)
        self._weigh(to_container)

    def capacity(self, container_id: str) -> float | None:
        entity = self.entity_map.get(container_id)
        if entity is None:
            return None
        return self.definition.kinds[entity.kind].capacity

    def fits(self, item: str, qty: int, container_id: str) -> bool:
        capacity = self.capacity(container_id)
        if capacity is None:
            return True
        extra = qty * float(self.definition.items[item].weight)
        return self.weight(container_id) + extra <= capacity + 1e-9

    def _ensure_fits(self, item: str, qty: int, container_id: str) -> None:
        if not self.fits(item, qty, container_id):
            raise WorldRuleError(
                f"{container_id} não aguenta {qty} {item} (too_heavy): a ação devia ter recusado"
            )

    def _weigh(self, container_id: str) -> None:
        """Quem tem capacidade mostra o peso que carrega como atributo visível."""
        if self.capacity(container_id) is not None:
            self.set_attributes(
                container_id, visible={"weight": round(self.weight(container_id), 1)}
            )

    # --- lotes e validade (ADR-0062)

    def _shelf_life(self, item: str) -> int | None:
        return self.definition.items[item].shelf_life_days

    def _add_lot(self, container_id: str, item: str, born_day: int, qty: int) -> None:
        lots = self.lots.setdefault(container_id, {}).setdefault(item, [])
        for lot in lots:
            if lot[0] == born_day:
                lot[1] += qty
                return
        lots.append([born_day, qty])
        lots.sort(key=lambda lot: lot[0])

    def _take_lots(self, container_id: str, item: str, qty: int) -> list[tuple[int, int]]:
        """Tira `qty` dos lotes mais velhos primeiro; devolve [(dia_de_origem, qty)]."""
        lots = self.lots.get(container_id, {}).get(item, [])
        taken: list[tuple[int, int]] = []
        left = qty
        while left > 0:
            if not lots:
                raise WorldRuleError(f"{container_id}: lotes de {item} não batem com a contagem")
            born, available = lots[0]
            use = min(available, left)
            taken.append((born, use))
            left -= use
            if use == available:
                lots.pop(0)
            else:
                lots[0][1] = available - use
        if not lots:
            self.lots[container_id].pop(item, None)
        return taken

    def _add_stock(self, item: str, qty: int, container_id: str) -> None:
        stock = self.containers.setdefault(container_id, {})
        stock[item] = stock.get(item, 0) + qty

    def _take_stock(self, item: str, qty: int, container_id: str) -> None:
        stock = self.containers.get(container_id, {})
        if stock.get(item, 0) < qty:
            raise WorldRuleError(f"{container_id} não tem {qty} {item}")
        stock[item] -= qty
        if stock[item] == 0:
            del stock[item]

    def _expires(self, item: str, born_day: int) -> dict[str, int]:
        shelf = self._shelf_life(item)
        return {} if shelf is None else {"expires_day": born_day + shelf}

    def create_item(self, item: str, qty: int, container_id: str, reason: str) -> None:
        self._check_item(item, qty, container_id)
        self._ensure_fits(item, qty, container_id)
        self._add_stock(item, qty, container_id)
        data: dict[str, Any] = {
            "item": item,
            "qty": qty,
            "container_id": container_id,
            "reason": reason,
        }
        if self._shelf_life(item) is not None:
            self._add_lot(container_id, item, self.day, qty)
            data.update(self._expires(item, self.day))
        self.emit_fact("campsverso.world.item.created.v1", self._with_action(data))
        self._weigh(container_id)

    def transfer_item(
        self, item: str, qty: int, from_container: str, to_container: str, reason: str
    ) -> None:
        self._check_item(item, qty, from_container)
        self._check_item(item, qty, to_container)
        self._ensure_fits(item, qty, to_container)
        self._take_stock(item, qty, from_container)
        self._add_stock(item, qty, to_container)
        base = {"item": item, "from_container": from_container, "to_container": to_container}
        if self._shelf_life(item) is None:
            self.emit_fact(
                "campsverso.world.item.transferred.v1",
                self._with_action({**base, "qty": qty, "reason": reason}),
            )
        else:  # um evento por lote: a validade viaja com ele
            for born, moved in self._take_lots(from_container, item, qty):
                self._add_lot(to_container, item, born, moved)
                self.emit_fact(
                    "campsverso.world.item.transferred.v1",
                    self._with_action(
                        {**base, "qty": moved, "reason": reason, **self._expires(item, born)}
                    ),
                )
        self._weigh(from_container)
        self._weigh(to_container)

    def consume_item(self, item: str, qty: int, container_id: str, reason: str) -> None:
        self._check_item(item, qty, container_id)
        self._take_stock(item, qty, container_id)
        base = {"item": item, "container_id": container_id, "reason": reason}
        if self._shelf_life(item) is None:
            self.emit_fact(
                "campsverso.world.item.consumed.v1", self._with_action({**base, "qty": qty})
            )
        else:
            for born, used in self._take_lots(container_id, item, qty):
                self.emit_fact(
                    "campsverso.world.item.consumed.v1",
                    self._with_action({**base, "qty": used, **self._expires(item, born)}),
                )
        self._weigh(container_id)

    def spoil(self) -> None:
        """Na virada do dia: consome os lotes vencidos, com a validade multiplicada pelo fator
        do contêiner (o baú conserva; ADR-0062). Determinístico: contêineres, itens e lotes em
        ordem."""
        today = self.day
        for container_id in sorted(self.lots):
            factor = float(
                self.definition.kinds[self.entity_map[container_id].kind].shelf_life_factor
            )
            for item in sorted(self.lots[container_id]):
                shelf = self._shelf_life(item)
                if shelf is None:
                    continue
                for born, qty in list(self.lots[container_id][item]):
                    if today - born < shelf * factor - 1e-9:
                        continue
                    self._take_stock(item, qty, container_id)
                    self._take_lots(container_id, item, qty)
                    self.emit_fact(
                        "campsverso.world.item.consumed.v1",
                        {
                            "item": item,
                            "qty": qty,
                            "container_id": container_id,
                            "reason": "spoiled",
                            **self._expires(item, born),
                        },
                    )
                self._weigh(container_id)
            if not self.lots[container_id]:
                del self.lots[container_id]

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
        """Avança as necessidades por `ticks` a partir do tick atual, por trechos quando um
        modificador vence no meio (ADR-0062); os vencidos saem e o atributo visível se apaga."""
        start, end = self.tick, self.tick + ticks
        for avatar_id in sorted(self.avatar_map):
            avatar = self.avatar_map[avatar_id]
            cuts = sorted(
                {end}
                | {
                    int(m["until_tick"])
                    for m in avatar.modifiers
                    if start < int(m["until_tick"]) < end
                }
            )
            for need in sorted(self.needs[avatar_id]):
                units, at = 0, start
                for cut in cuts:
                    units += self.rate(avatar_id, need, at) * (cut - at)
                    at = cut
                if units:
                    self.set_need_units(avatar_id, need, self.needs[avatar_id][need] + units)
            self._expire_modifiers(avatar_id, end)

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
        rates_per_hour: Mapping[str, float] | None = None,
        bed_id: str | None = None,
    ) -> None:
        if bed_id is not None and bed_id not in self.entity_map:
            raise WorldRuleError(f"entidade de dormir inexistente: {bed_id}")
        avatar = self.avatar_map[avatar_id]
        avatar.asleep = True
        avatar.sleep_cause = cause
        avatar.bed_id = bed_id
        avatar.wake_tick = self.tick + wake_in_ticks
        avatar.wake_needs = dict(wake_needs or {})
        avatar.sleep_rates = {
            need: self._unit_rate(need, per_hour)
            for need, per_hour in sorted((rates_per_hour or {}).items())
        }
        position = self.position_of(avatar_id)
        assert position is not None
        data: dict[str, Any] = {"avatar_id": avatar_id, "cause": cause}
        if bed_id is not None:
            data["bed_id"] = bed_id
        data |= {"position": position_data(position), "wake_at_tick": avatar.wake_tick}
        self.emit_fact("campsverso.avatar.sleep.started.v2", data)

    def wake(self, avatar_id: str) -> None:
        avatar = self.avatar_map[avatar_id]
        for need, value in sorted(avatar.wake_needs.items()):
            self.set_need_units(avatar_id, need, to_units(value))
        energy = next((n.need for n in self.definition.needs.values() if n.role == "energy"), None)
        data: dict[str, Any] = {"avatar_id": avatar_id, "cause": avatar.sleep_cause or "voluntary"}
        if avatar.bed_id is not None:
            data["bed_id"] = avatar.bed_id
        data["energy"] = self.need(avatar_id, energy) if energy is not None else 0.0
        avatar.asleep, avatar.sleep_cause, avatar.bed_id, avatar.wake_tick = False, None, None, None
        avatar.wake_needs, avatar.sleep_rates = {}, {}
        self.emit_fact("campsverso.avatar.sleep.ended.v2", data)
        avatar.add_pending("woke_up")

    def interrupt_action(
        self, avatar_id: str, reason: Literal["cancelled", "fainted"]
    ) -> str | None:
        """Para a ação em andamento; numa ação `partial`, o cartucho grava o trabalho feito
        (ADR-0052)."""
        avatar = self.avatar_map[avatar_id]
        action = avatar.action
        if action is None:
            return None
        elapsed = self.tick - action.applied_tick
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
        spec = self.definition.actions.get(action.name)
        if action.interrupt == "partial" and spec is not None:
            outer = self._context
            with self.context(
                action=action,
                cause=action.name,
                caused_by=outer.caused_by,
                correlation=outer.correlation,
            ):
                spec.interrupted(
                    ActionContext(avatar_id, action.action_id, action.params, self), self, elapsed
                )
        self.emit_fact(
            "campsverso.action.failed.v1",
            {
                "action_id": action.action_id,
                "avatar_id": avatar_id,
                "action": action.name,
                "reason": reason,
                "elapsed_ticks": elapsed,
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


# ----------------------------------------------------------------- snapshot: (de)serialização


def _position_from(raw: Any) -> Position | None:
    return None if raw is None else Position(int(raw["x"]), int(raw["y"]))


def _controller_from(raw: Mapping[str, Any]) -> ControllerRef:
    return ControllerRef(raw["type"], str(raw["id"]))


def _entity_data(e: Entity) -> dict[str, Any]:
    return {
        "entity_id": e.entity_id,
        "kind": e.kind,
        "position": None if e.position is None else position_data(e.position),
        "container_id": e.container_id,
        "blocking": e.blocking,
        "display_name": e.display_name,
        "attributes": dict(e.attributes),
        "hidden": dict(e.hidden),
    }


def _entity_from(raw: Mapping[str, Any]) -> Entity:
    return Entity(
        entity_id=str(raw["entity_id"]),
        kind=str(raw["kind"]),
        position=_position_from(raw["position"]),
        container_id=raw["container_id"],
        blocking=bool(raw["blocking"]),
        display_name=raw["display_name"],
        attributes=dict(raw["attributes"]),
        hidden=dict(raw["hidden"]),
    )


def _action_data(action: RunningAction) -> dict[str, Any]:
    trajectory = action.trajectory
    return {
        "action_id": action.action_id,
        "name": action.name,
        "params": plain(action.params),
        "applied_tick": action.applied_tick,
        "end_tick": action.end_tick,
        "command_id": action.command_id,
        "correlation": action.correlation,
        "interrupt": action.interrupt,
        "trajectory": None
        if trajectory is None
        else {
            "origin": position_data(trajectory.origin),
            "path": [[p.x, p.y] for p in trajectory.path],
            "depart_tick": trajectory.depart_tick,
            "tiles_per_tick": trajectory.tiles_per_tick,
        },
    }


def _action_from(raw: Mapping[str, Any]) -> RunningAction:
    trajectory = raw["trajectory"]
    return RunningAction(
        action_id=str(raw["action_id"]),
        name=str(raw["name"]),
        params=dict(raw["params"]),
        applied_tick=int(raw["applied_tick"]),
        end_tick=int(raw["end_tick"]),
        command_id=raw["command_id"],
        correlation=raw["correlation"],
        interrupt=raw.get("interrupt", "cancel"),  # fotos de antes da ADR-0052
        trajectory=None
        if trajectory is None
        else Trajectory(
            origin=Position(int(trajectory["origin"]["x"]), int(trajectory["origin"]["y"])),
            path=tuple(Position(int(x), int(y)) for x, y in trajectory["path"]),
            depart_tick=int(trajectory["depart_tick"]),
            tiles_per_tick=float(trajectory["tiles_per_tick"]),
        ),
    )


def _avatar_data(a: Avatar) -> dict[str, Any]:
    return {
        "avatar_id": a.avatar_id,
        "controller": controller_data(a.controller),
        "default_controller": controller_data(a.default_controller),
        "action": None if a.action is None else _action_data(a.action),
        "asleep": a.asleep,
        "sleep_cause": a.sleep_cause,
        "bed_id": a.bed_id,
        "wake_tick": a.wake_tick,
        "wake_needs": dict(a.wake_needs),
        "sleep_rates": dict(a.sleep_rates),
        "pending": list(a.pending),
        "awaiting": a.awaiting,
        "modifiers": [dict(m) for m in a.modifiers],
    }


def _avatar_from(raw: Mapping[str, Any]) -> Avatar:
    return Avatar(
        avatar_id=str(raw["avatar_id"]),
        controller=_controller_from(raw["controller"]),
        default_controller=_controller_from(raw["default_controller"]),
        action=None if raw["action"] is None else _action_from(raw["action"]),
        asleep=bool(raw["asleep"]),
        sleep_cause=raw["sleep_cause"],
        bed_id=raw["bed_id"],
        wake_tick=raw["wake_tick"],
        wake_needs=dict(raw["wake_needs"]),
        sleep_rates=dict(raw["sleep_rates"]),
        pending=list(raw["pending"]),
        awaiting=bool(raw["awaiting"]),
        modifiers=[dict(m) for m in cast(list[Mapping[str, Any]], raw.get("modifiers") or [])],
    )


def plain(value: Any) -> Any:
    """Cópia em tipos JSON simples (MappingProxyType e tuplas viram dict e list)."""
    if isinstance(value, Mapping):
        return {str(k): plain(v) for k, v in value.items()}  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]
    if isinstance(value, list | tuple):
        return [plain(v) for v in value]  # pyright: ignore[reportUnknownVariableType]
    return value
