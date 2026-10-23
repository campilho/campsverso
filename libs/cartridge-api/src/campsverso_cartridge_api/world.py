"""Visão do mundo (leitura) e operações (as primitivas pelas quais um cartucho muda o mundo).

Cartuchos nunca acessam o estado diretamente: toda mudança passa por WorldOps e vira um evento
genérico publicado pelo kernel (ADR-0025).
"""

from collections.abc import Mapping, Sequence
from typing import Any, Literal, Protocol

from campsverso_cartridge_api.definitions import SpawnDef
from campsverso_cartridge_api.model import Attributes, EntityView, Position

type SleepCause = Literal["voluntary", "faint"]


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

    def targeted(self, entity_id: str) -> bool:
        """Se alguma ação em andamento aponta para a entidade (ADR-0067): o que não se remove."""
        ...

    def season(self, day: int) -> str | None:
        """A estação do dia, se o cartucho declarou um ano (ADR-0067)."""
        ...

    def date(self, day: int) -> str | None:
        """A data do calendário do dia, "AAAA-MM-DD", se o cartucho declarou um ano."""
        ...

    def data(self, namespace: str) -> Mapping[str, Any]:
        """Dados do cartucho, já mesclados pelas camadas (ADR-0031)."""
        ...

    def entity(self, entity_id: str) -> EntityView: ...

    def entities(self, kind: str | None = None) -> Sequence[EntityView]:
        """Sempre em ordem de id (princípio 4)."""
        ...

    def items(self, container_id: str) -> Mapping[str, int]: ...

    def weight(self, container_id: str) -> float:
        """O peso do que o contêiner guarda (ADR-0062)."""
        ...

    def capacity(self, container_id: str) -> float | None:
        """A capacidade do contêiner, pelo tipo dele; None é sem limite."""
        ...

    def fits(self, item: str, qty: int, container_id: str) -> bool:
        """Se `qty` de `item` ainda cabe no contêiner. Quem cria ou transfere confere antes e
        recusa com `too_heavy`; o kernel trata não caber como violação."""
        ...

    def fits_entity(self, kind: str, container_id: str) -> bool:
        """Se uma entidade deste tipo (uma ferramenta, pelo peso do tipo) ainda cabe."""
        ...

    def need(self, avatar_id: str, need: str) -> float: ...

    def is_asleep(self, avatar_id: str) -> bool: ...

    def avatars(self) -> Sequence[str]: ...

    def tiles_with(self, tile_property: str) -> Sequence[Position]: ...

    def tile_kind(self, position: Position) -> str | None:
        """A classe do tile (grass, path, soil...), ou None fora do mapa (ADR-0062)."""
        ...

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

    def spawn(self, entity: SpawnDef) -> None:
        """Cria uma entidade em tempo de execução (um canteiro cavado), publicando
        `world.entity.spawned` como no início da sessão (ADR-0062). O id tem de ser novo."""
        ...

    def next_seq(self, name: str) -> int:
        """O próximo número do contador `name`, a partir de 1, guardado no snapshot (ADR-0067)."""
        ...

    def despawn(self, entity_id: str, reason: str) -> None:
        """Remove uma entidade em tempo de execução (o canteiro vazio que volta a ser grama),
        publicando `world.entity.despawned` (ADR-0067). Recusa avatar, contêiner com itens ou com
        entidades dentro, e o alvo de uma ação em andamento."""
        ...

    def move_entity(self, entity_id: str, to_container: str) -> None:
        """Guarda uma entidade noutro contêiner (a ferramenta que vai para o baú), publicando
        `world.entity.stored` (ADR-0062); ela deixa de ter posição no mapa."""
        ...

    def change_need(self, avatar_id: str, need: str, delta: float) -> None: ...

    def add_need_modifier(
        self, avatar_id: str, need: str, factor: float, ticks: int, label: str
    ) -> None:
        """Multiplica a taxa de uma necessidade por `factor` durante `ticks` (ADR-0062): o
        ensopado que segura a fome. `label` é o atributo visível do avatar que mostra até quando
        (hora do mundo); um modificador novo com o mesmo rótulo substitui o anterior."""
        ...

    def set_weather(self, condition: str, day: int) -> None: ...

    def start_sleep(
        self,
        avatar_id: str,
        cause: SleepCause,
        wake_in_ticks: int,
        wake_needs: Mapping[str, float] | None = None,
        rates_per_hour: Mapping[str, float] | None = None,
        bed_id: str | None = None,
    ) -> None:
        """Dorme até `wake_in_ticks`. `rates_per_hour` substitui a taxa `asleep` das necessidades
        durante este sono (a cama recupera mais; ADR-0041). `bed_id` é a cama ou análogo usado."""
        ...

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
