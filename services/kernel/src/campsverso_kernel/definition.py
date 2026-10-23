"""Montagem do mundo a partir da cadeia de cartuchos (ADR-0031, ADR-0036)."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, cast

from campsverso_cartridge_api import (
    ActionSpec,
    AffordanceDef,
    AvatarDef,
    CartridgeManifest,
    ClockDef,
    ItemDef,
    KindDef,
    MetricDef,
    NeedDef,
    RuleImpl,
    SpawnDef,
    SystemSpec,
    ThresholdDef,
    YearDef,
)
from campsverso_contracts import CONTRACT_TYPES
from campsverso_kernel.calendar import month_day
from campsverso_kernel.errors import DefinitionError
from campsverso_kernel.pipeline import DEFAULT_STAGES
from campsverso_kernel.space import GridMap

KERNEL_ACTIONS = frozenset({"move", "wait"})  # física do espaço e do tempo (ADR-0038)


@dataclass(frozen=True)
class WorldDefinition:
    chain: tuple[CartridgeManifest, ...]  # da base para o topo
    clock: ClockDef
    tiles_per_minute: float
    data: Mapping[str, Mapping[str, Any]]
    kinds: Mapping[str, KindDef]
    items: Mapping[str, ItemDef]
    needs: Mapping[str, NeedDef]
    thresholds: tuple[ThresholdDef, ...]
    actions: Mapping[str, ActionSpec]
    systems: Mapping[str, SystemSpec]
    rule_impls: Mapping[str, RuleImpl]
    grid: GridMap
    spawns: Mapping[str, SpawnDef]
    avatars: Mapping[str, AvatarDef]
    initial_items: tuple[tuple[str, str, int], ...]
    stages: tuple[str, ...] = DEFAULT_STAGES
    affordances: tuple[AffordanceDef, ...] = ()  # catálogo de ações para quem joga (ADR-0051)
    metrics: tuple[MetricDef, ...] = ()  # métricas do dia para o operador (ADR-0054)
    perception_radius: int | None = None  # None: o mapa inteiro (ADR-0056)
    movement_cost: tuple[str, float] | None = None  # (necessidade, pontos por tile) (ADR-0062)
    year: YearDef | None = None  # o ano com estações (ADR-0067); None: sem data do ano

    @property
    def top(self) -> CartridgeManifest:
        return self.chain[-1]


def _deep_merge(base: Mapping[str, Any], extra: Mapping[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in extra.items():
        current = merged.get(key)
        if isinstance(current, Mapping) and isinstance(value, Mapping):
            merged[key] = _deep_merge(
                cast(Mapping[str, Any], current), cast(Mapping[str, Any], value)
            )
        else:
            merged[key] = value
    return merged


def _register[T](table: dict[str, T], name: str, value: T, *, override: bool, what: str) -> None:
    if override and name not in table:
        raise DefinitionError(f"override de {what} {name!r}, que não existe nas camadas de baixo")
    if not override and name in table:
        raise DefinitionError(f"{what} {name!r} repetido sem override (ADR-0036)")
    table[name] = value


@dataclass
class DefinitionBuilder:
    """Implementa WorldBuilder. Cada camada contribui; `build` valida o conjunto."""

    stages: tuple[str, ...] = DEFAULT_STAGES
    clock: ClockDef | None = None
    year: YearDef | None = None
    tiles_per_minute: float = 1.0
    perception_radius: int | None = None
    movement_cost: tuple[str, float] | None = None
    data: dict[str, dict[str, Any]] = field(default_factory=dict[str, dict[str, Any]])
    kinds: dict[str, KindDef] = field(default_factory=dict[str, KindDef])
    items: dict[str, ItemDef] = field(default_factory=dict[str, ItemDef])
    needs: dict[str, NeedDef] = field(default_factory=dict[str, NeedDef])
    thresholds: list[ThresholdDef] = field(default_factory=list[ThresholdDef])
    actions: dict[str, ActionSpec] = field(default_factory=dict[str, ActionSpec])
    affordances: list[AffordanceDef] = field(default_factory=list[AffordanceDef])
    metrics: dict[str, MetricDef] = field(default_factory=dict[str, MetricDef])
    systems: dict[str, SystemSpec] = field(default_factory=dict[str, SystemSpec])
    rule_impls: dict[str, RuleImpl] = field(default_factory=dict[str, RuleImpl])
    tiled: Mapping[str, Any] | None = None
    spawns: dict[str, SpawnDef] = field(default_factory=dict[str, SpawnDef])
    avatars: dict[str, AvatarDef] = field(default_factory=dict[str, AvatarDef])
    initial_items: list[tuple[str, str, int]] = field(default_factory=list[tuple[str, str, int]])

    def configure_clock(self, clock: ClockDef) -> None:
        self.clock = clock

    def configure_year(self, year: YearDef) -> None:
        if year.days < len(year.seasons) or not year.seasons:
            raise DefinitionError("o ano precisa de estações e de pelo menos um dia por estação")
        names = [name for name, _ in year.seasons]
        if len(set(names)) != len(names):
            raise DefinitionError(f"estação repetida no ano: {names}")
        for when in (year.start, *(start for _, start in year.seasons)):
            try:
                month_day(when)
            except ValueError as error:
                raise DefinitionError(f"data do ano inválida: {when!r}") from error
        self.year = year

    def set_tiles_per_minute(self, speed: float) -> None:
        if speed <= 0:
            raise DefinitionError("a velocidade precisa ser positiva")
        self.tiles_per_minute = speed

    def set_perception_radius(self, radius: int | None) -> None:
        if radius is not None and radius < 0:
            raise DefinitionError("o raio de percepção não pode ser negativo")
        self.perception_radius = radius

    def set_movement_cost(self, need: str, points_per_tile: float) -> None:
        if points_per_tile < 0:
            raise DefinitionError("o custo de andar não pode ser negativo")
        self.movement_cost = (need, points_per_tile)

    def merge_data(self, namespace: str, data: Mapping[str, Any]) -> None:
        self.data[namespace] = _deep_merge(self.data.get(namespace, {}), data)

    def define_kind(self, kind: KindDef, *, override: bool = False) -> None:
        _register(self.kinds, kind.kind, kind, override=override, what="tipo de entidade")

    def define_item(self, item: ItemDef, *, override: bool = False) -> None:
        _register(self.items, item.item_id, item, override=override, what="item")

    def define_need(self, need: NeedDef, *, override: bool = False) -> None:
        _register(self.needs, need.need, need, override=override, what="necessidade")

    def add_threshold(self, threshold: ThresholdDef) -> None:
        self.thresholds.append(threshold)

    def add_action(self, spec: ActionSpec, *, override: bool = False) -> None:
        if spec.name in KERNEL_ACTIONS:
            raise DefinitionError(f"a ação {spec.name!r} é do kernel (ADR-0038)")
        _register(self.actions, spec.name, spec, override=override, what="ação")

    def add_system(self, spec: SystemSpec, *, override: bool = False) -> None:
        _register(self.systems, spec.name, spec, override=override, what="sistema")

    def add_rule_impl(self, impl: RuleImpl, *, override: bool = False) -> None:
        _register(
            self.rule_impls, impl.name, impl, override=override, what="implementação de regra"
        )

    def add_affordance(self, affordance: AffordanceDef, *, replace: bool = False) -> None:
        if replace:
            self.affordances = [a for a in self.affordances if a.action != affordance.action]
        self.affordances.append(affordance)

    def add_metric(self, metric: MetricDef, *, override: bool = False) -> None:
        _register(self.metrics, metric.id, metric, override=override, what="métrica")

    def set_map(self, tiled: Mapping[str, Any]) -> None:
        self.tiled = tiled

    def spawn(self, entity: SpawnDef, *, override: bool = False) -> None:
        _register(self.spawns, entity.entity_id, entity, override=override, what="entidade")

    def add_avatar(self, avatar: AvatarDef, *, override: bool = False) -> None:
        _register(self.avatars, avatar.entity_id, avatar, override=override, what="avatar")

    def add_items(self, container_id: str, item: str, qty: int) -> None:
        self.initial_items.append((container_id, item, qty))

    def _metrics(self) -> tuple[MetricDef, ...]:
        """Cada métrica cita o que existe: um evento dos contratos, uma necessidade, um item."""
        for metric in self.metrics.values():
            problem = None
            if metric.kind == "count" and metric.event not in CONTRACT_TYPES:
                problem = f"o evento {metric.event!r} não está nos contratos"
            elif metric.kind == "count" and metric.by_attribute and not metric.by_field:
                problem = "agrupar por atributo exige o campo com o id da entidade"
            elif metric.kind == "max_need" and metric.need not in self.needs:
                problem = f"a necessidade {metric.need!r} não existe"
            elif metric.kind == "item" and metric.item not in self.items:
                problem = f"o item {metric.item!r} não existe"
            if problem is not None:
                raise DefinitionError(f"métrica {metric.id!r}: {problem}")
        return tuple(self.metrics.values())

    def _affordances(self) -> tuple[AffordanceDef, ...]:
        for affordance in self.affordances:
            if affordance.action not in self.actions and affordance.action not in KERNEL_ACTIONS:
                raise DefinitionError(
                    f"o catálogo cita a ação {affordance.action!r}, que não existe"
                )
        return tuple(self.affordances)

    def build(self, chain: Sequence[CartridgeManifest]) -> WorldDefinition:
        if self.clock is None:
            raise DefinitionError("nenhuma camada configurou o relógio")
        if self.tiled is None:
            raise DefinitionError("nenhuma camada definiu o mapa")
        grid = GridMap.from_tiled(self.tiled, chain[-1].id)
        for obj in grid.objects:  # objetos nomeados do mapa viram entidades
            self.spawn(
                SpawnDef(
                    entity_id=obj.name,
                    kind=obj.kind,
                    position=obj.position,
                    blocking=bool(obj.properties.get("blocking", False)),
                    display_name=cast(str | None, obj.properties.get("display_name")),
                    # As outras propriedades viram atributos visíveis (o `group` dos canteiros).
                    attributes={
                        k: v
                        for k, v in sorted(obj.properties.items())
                        if k not in ("blocking", "display_name")
                    },
                )
            )
        self._validate(grid)
        return WorldDefinition(
            chain=tuple(chain),
            clock=self.clock,
            year=self.year,
            tiles_per_minute=self.tiles_per_minute,
            data=dict(self.data),
            kinds=dict(self.kinds),
            items=dict(self.items),
            needs=dict(self.needs),
            thresholds=tuple(self.thresholds),
            actions=dict(self.actions),
            affordances=self._affordances(),
            metrics=self._metrics(),
            systems=dict(self.systems),
            rule_impls=dict(self.rule_impls),
            grid=grid,
            spawns=dict(sorted(self.spawns.items())),
            avatars=dict(sorted(self.avatars.items())),
            initial_items=tuple(self.initial_items),
            stages=self.stages,
            perception_radius=self.perception_radius,
            movement_cost=self.movement_cost,
        )

    def _validate(self, grid: GridMap) -> None:
        if self.movement_cost is not None and self.movement_cost[0] not in self.needs:
            raise DefinitionError(
                f"custo de andar numa necessidade indefinida: {self.movement_cost[0]}"
            )
        """Junta todos os problemas e falha uma vez só, com a lista completa."""
        problems: list[str] = []
        for spawn in self.spawns.values():
            if spawn.kind not in self.kinds:
                problems.append(f"entidade {spawn.entity_id}: tipo {spawn.kind!r} indefinido")
            if (spawn.position is None) == (spawn.container_id is None):
                problems.append(f"entidade {spawn.entity_id}: precisa de posição ou de contêiner")
            if spawn.position is not None and not grid.in_bounds(spawn.position):
                problems.append(f"entidade {spawn.entity_id} fora do mapa")
        problems.extend(
            f"avatar {avatar} não está entre as entidades"
            for avatar in self.avatars
            if avatar not in self.spawns
        )
        for container, item, qty in self.initial_items:
            if container not in self.spawns:
                problems.append(f"contêiner {container!r} inexistente")
            if item not in self.items:
                problems.append(f"item {item!r} indefinido")
            if qty <= 0:
                problems.append(f"quantidade inicial de {item} precisa ser positiva")
        problems.extend(
            f"limiar de necessidade indefinida: {t.need}"
            for t in self.thresholds
            if t.need not in self.needs
        )
        problems.extend(
            f"sistema {s.name}: etapa {s.stage!r} desconhecida"
            for s in self.systems.values()
            if s.stage not in self.stages
        )
        if problems:
            raise DefinitionError("; ".join(problems))
