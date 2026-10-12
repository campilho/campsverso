"""Manifesto do cartucho e o construtor do mundo, pelo qual cada camada contribui (ADR-0031)."""

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from campsverso_cartridge_api.definitions import (
    AffordanceDef,
    AvatarDef,
    ClockDef,
    ItemDef,
    KindDef,
    NeedDef,
    SpawnDef,
    ThresholdDef,
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

    def set_tiles_per_minute(self, speed: float) -> None: ...

    def merge_data(self, namespace: str, data: Mapping[str, Any]) -> None: ...

    def define_kind(self, kind: KindDef, *, override: bool = False) -> None: ...

    def define_item(self, item: ItemDef, *, override: bool = False) -> None: ...

    def define_need(self, need: NeedDef, *, override: bool = False) -> None: ...

    def add_threshold(self, threshold: ThresholdDef) -> None: ...

    def add_action(self, spec: ActionSpec, *, override: bool = False) -> None: ...

    def add_system(self, spec: SystemSpec, *, override: bool = False) -> None: ...

    def add_rule_impl(self, impl: RuleImpl, *, override: bool = False) -> None: ...

    def add_affordance(self, affordance: AffordanceDef) -> None:
        """Uma entrada do catálogo de ações para quem joga (ADR-0051); a ação precisa existir."""
        ...

    def set_map(self, tiled: Mapping[str, Any]) -> None:
        """Mapa no formato JSON do Tiled; objetos nomeados viram entidades."""
        ...

    def spawn(self, entity: SpawnDef, *, override: bool = False) -> None: ...

    def add_avatar(self, avatar: AvatarDef) -> None: ...

    def add_items(self, container_id: str, item: str, qty: int) -> None: ...


class Cartridge(Protocol):
    @property
    def manifest(self) -> CartridgeManifest: ...

    def contribute(self, world: WorldBuilder) -> None: ...

    def rules_file(self) -> Path | None:
        """Arquivo de flags das regras (FlagPort), quando o cartucho declara instâncias de regra."""
        ...
