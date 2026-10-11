"""Visão do mundo (leitura) e operações (as primitivas pelas quais um cartucho muda o mundo).

Cartuchos nunca acessam o estado diretamente: toda mudança passa por WorldOps e vira um evento
genérico publicado pelo kernel (ADR-0025).
"""

from collections.abc import Mapping, Sequence
from typing import Any, Literal, Protocol

from campsverso_cartridge_api.model import Attributes, EntityView, Position

type SleepCause = Literal["bed", "faint"]


class Rng(Protocol):
    def random(self) -> float:
        """Número em [0, 1)."""
        ...

    def randint(self, low: int, high: int) -> int:
        """Inteiro em [low, high]."""
        ...


class WorldView(Protocol):
    @property
    def tick(self) -> int: ...

    @property
    def day(self) -> int:
        """Dia corrente, contado a partir de 1 na virada configurada pelo cartucho."""
        ...

    @property
    def minute_of_day(self) -> int:
        """Minuto do relógio (0 a 1439)."""
        ...

    def ticks_until(self, hhmm: str) -> int:
        """Ticks até a próxima ocorrência de HH:MM (1 a um dia inteiro)."""
        ...

    def weather(self, day: int) -> str | None: ...

    def data(self, namespace: str) -> Mapping[str, Any]:
        """Dados do cartucho, já mesclados pelas camadas (ADR-0031)."""
        ...

    def entity(self, entity_id: str) -> EntityView: ...

    def entities(self, kind: str | None = None) -> Sequence[EntityView]:
        """Sempre em ordem de id (princípio 4)."""
        ...

    def items(self, container_id: str) -> Mapping[str, int]: ...

    def need(self, avatar_id: str, need: str) -> float: ...

    def is_asleep(self, avatar_id: str) -> bool: ...

    def avatars(self) -> Sequence[str]: ...

    def tiles_with(self, tile_property: str) -> Sequence[Position]: ...

    def rng(self, stream: str) -> Rng: ...


class WorldOps(Protocol):
    def set_attributes(
        self,
        entity_id: str,
        *,
        visible: Attributes | None = None,
        hidden: Attributes | None = None,
        cause: str | None = None,
    ) -> None: ...

    def create_item(self, item: str, qty: int, container_id: str, reason: str) -> None: ...

    def transfer_item(
        self, item: str, qty: int, from_container: str, to_container: str, reason: str
    ) -> None: ...

    def consume_item(self, item: str, qty: int, container_id: str, reason: str) -> None: ...

    def change_need(self, avatar_id: str, need: str, delta: float) -> None: ...

    def set_weather(self, condition: str, day: int) -> None: ...

    def start_sleep(
        self,
        avatar_id: str,
        cause: SleepCause,
        wake_in_ticks: int,
        wake_needs: Mapping[str, float] | None = None,
    ) -> None: ...

    def faint(
        self,
        avatar_id: str,
        reason: Literal["late_night", "exhausted"],
        wake_in_ticks: int,
        wake_needs: Mapping[str, float],
    ) -> None: ...

    def apply_rules(self, target: str, entity_id: str, base: float) -> float:
        """Aplica as regras ligadas que modificam `target` (ex.: growth_points).

        O kernel registra quais regras contribuíram, para explicar o resultado depois.
        """
        ...

    def explain_effects(self, entity_id: str) -> None:
        """Publica, para a ação em curso, as regras que contribuíram para o resultado (internal)."""
        ...

    def emit(self, event_type: str, data: Mapping[str, Any]) -> None:
        """Evento semântico próprio do cartucho, declarado em contracts/ (ADR-0025)."""
        ...
