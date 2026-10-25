"""Manifesto do cartucho e o construtor do mundo, pelo qual cada camada contribui (ADR-0031)."""

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from campsverso_cartridge_api.definitions import (
    AffordanceDef,
    AvatarDef,
    ClockDef,
    EventLabelDef,
    ItemDef,
    KindDef,
    MetricDef,
    NeedDef,
    SpawnDef,
    ThresholdDef,
    YearDef,
)
from campsverso_cartridge_api.specs import ActionSpec, RuleImpl, SystemSpec


@dataclass(frozen=True, slots=True)
class CartridgeManifest:
    id: str  # também é o domínio dos eventos que o cartucho declara
    version: str
    extends: tuple[str, ...] = ()


class WorldBuilder(Protocol):
    """Implementado pelo kernel. Repetir um nome sem override é erro de carga (ADR-0036)."""

    def configure_clock(self, clock: ClockDef) -> None: ...

    def configure_year(self, year: YearDef) -> None:
        """Um ano com estações (ADR-0067); sem ele, o mundo não tem data do ano nem estação."""
        ...

    def use_domain(self, domain: str) -> None:
        """O domínio de eventos de uma biblioteca de mundo que o cartucho usa (`economy`, ADR-0069):
        com ele, o cartucho publica os eventos dela, além dos do próprio domínio."""
        ...

    def set_tiles_per_minute(self, speed: float) -> None: ...

    def set_movement_cost(self, need: str, points_per_tile: float) -> None:
        """Andar gasta `points_per_tile` da necessidade por tile percorrido (ADR-0062)."""
        ...

    def set_perception_light(self, by_phase: Mapping[str, int], lights: Mapping[str, int]) -> None:
        """O raio por fase do dia e os itens que garantem um raio mínimo (ADR-0068)."""
        ...

    def set_perception_landmarks(self, kinds: tuple[str, ...]) -> None:
        """Tipos que se enxergam além do raio: as construções fixas (ADR-0067)."""
        ...

    def set_perception_radius(self, radius: int | None) -> None:
        """Até onde um avatar enxerga, em tiles (distância de Chebyshev; ADR-0056).

        None é o mapa inteiro.
        """
        ...

    def merge_data(self, namespace: str, data: Mapping[str, Any]) -> None: ...

    def define_kind(self, kind: KindDef, *, override: bool = False) -> None: ...

    def define_item(self, item: ItemDef, *, override: bool = False) -> None: ...

    def define_need(self, need: NeedDef, *, override: bool = False) -> None: ...

    def add_threshold(self, threshold: ThresholdDef) -> None: ...

    def add_action(self, spec: ActionSpec, *, override: bool = False) -> None: ...

    def add_system(self, spec: SystemSpec, *, override: bool = False) -> None: ...

    def add_rule_impl(self, impl: RuleImpl, *, override: bool = False) -> None: ...

    def add_affordance(self, affordance: AffordanceDef, *, replace: bool = False) -> None:
        """Uma entrada do catálogo de ações para quem joga (ADR-0051); a ação precisa existir.
        Com `replace`, as afordâncias já registradas para a mesma ação saem (ADR-0062)."""
        ...

    def add_metric(self, metric: MetricDef, *, override: bool = False) -> None:
        """Uma métrica do dia (ADR-0054); um cartucho que estende outro acrescenta as suas."""
        ...

    def add_label(self, label: EventLabelDef, *, replace: bool = False) -> None:
        """Um rótulo da linha do tempo (ADR-0068). Com `replace`, os já registrados para o mesmo
        evento e o mesmo `where` saem: o cenário troca o do gênero."""
        ...

    def set_map(self, tiled: Mapping[str, Any]) -> None:
        """Mapa no formato JSON do Tiled; objetos nomeados viram entidades."""
        ...

    def add_map_variant(self, name: str, tiled: Mapping[str, Any]) -> None:
        """Outro mapa do mesmo cenário (ADR-0070): o arquivo do mundo escolhe uma variante pelo
        nome (`map:`) no lugar do mapa de `set_map`, e o id do mapa vira `<cartucho>-<nome>`."""
        ...

    def spawn(self, entity: SpawnDef, *, override: bool = False) -> None: ...

    def add_avatar(self, avatar: AvatarDef, *, override: bool = False) -> None:
        """Com `override`, um cenário troca o controlador padrão do avatar que herdou."""
        ...

    def add_items(self, container_id: str, item: str, qty: int) -> None: ...


class Cartridge(Protocol):
    @property
    def manifest(self) -> CartridgeManifest: ...

    def contribute(self, world: WorldBuilder) -> None: ...

    def rules_file(self) -> Path | None:
        """Arquivo de flags das regras (FlagPort), quando o cartucho declara instâncias de regra."""
        ...
