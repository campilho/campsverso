"""Porta de memória (ADR-0060): o que um agente registra, lembra e reflete.

Três operações sobre cinco tipos: episódios (o que o agente viu e fez, uma linha por vez, com
importância), anotações (o que ele mesmo quis guardar), crenças (o que ele acredita, com
confiança, evidências e origem), reflexões (o fechamento de um dia) e lugares (o último estado
visto de cada coisa com posição, para lembrar o que saiu do raio de percepção; ADR-0067). O
caderno de campo (ADR-0070) acrescenta os plantios, as refeições e os experimentos da noite. A
porta não conhece o modelo nem o cartucho: quem transforma entregas em episódios e quem chama o
modelo para refletir é a mente; aqui fica só o que persiste.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal, Protocol

type BeliefStatus = Literal["new", "confirmed", "weakened", "retracted"]
type SourceKind = Literal["observation", "told"]
type ChangeKind = Literal["formed", "updated", "retracted"]


@dataclass(frozen=True, slots=True)
class Episode:
    tick: int
    day: int
    text: str  # uma linha legível
    importance: int  # 1 a 10, pela tabela da mente
    kind: str  # o tipo do evento percebido, ou "proposal"
    tags: tuple[str, ...] = ()  # ids de entidade citados
    sim_time: str = ""


@dataclass(frozen=True, slots=True)
class Note:
    tick: int
    day: int
    text: str
    sim_time: str = ""


@dataclass(frozen=True, slots=True)
class Belief:
    belief_id: str
    statement: str
    confidence: float
    evidence: tuple[str, ...] = ()
    source_kind: SourceKind = "observation"
    source_by: str | None = None
    reason: str | None = None
    first_day: int = 1
    last_day: int = 1
    retracted: bool = False


@dataclass(frozen=True, slots=True)
class BeliefRevision:
    """O que a reflexão diz de uma crença: a existente (`belief_id`) ou uma nova (`None`)."""

    statement: str
    confidence: float
    evidence: tuple[str, ...]
    status: BeliefStatus
    reason: str | None = None
    belief_id: str | None = None


@dataclass(frozen=True, slots=True)
class Reflection:
    day: int
    tick: int
    summary: str
    plan: str | None
    beliefs: tuple[BeliefRevision, ...]
    prompt_sha256: str | None = None


@dataclass(frozen=True, slots=True)
class Place:
    """O último estado visto de uma coisa com posição: onde estava e como estava (ADR-0067)."""

    entity_id: str
    kind: str
    x: int
    y: int
    attributes: tuple[tuple[str, str], ...]  # os atributos visíveis, em texto, ordenados
    tick: int  # quando foi vista pela última vez
    day: int
    sim_time: str = ""


@dataclass(frozen=True, slots=True)
class Planting:
    """Uma linha do caderno de campo (ADR-0070): um plantio, só com o que o avatar viu. A chave é
    o canteiro e o tick do plantio."""

    plot_id: str
    tick: int  # quando plantou
    day: int
    crop: str
    x: int | None = None
    y: int | None = None
    previous: str | None = None  # a cultura de antes no mesmo canteiro, pelo caderno
    fertilized: bool = False
    watered_days: tuple[int, ...] = ()  # os dias com rega (do regador ou da chuva)
    matured_day: int | None = None
    outcome: str | None = None  # colhida, comida, derrubada, murcha, sumiu
    outcome_day: int | None = None


@dataclass(frozen=True, slots=True)
class Meal:
    """O que uma comida tirou de fome (ADR-0070): a fome antes e depois de comer."""

    tick: int
    day: int
    item: str
    hunger_before: float
    hunger_after: float


@dataclass(frozen=True, slots=True)
class Experiment:
    """O experimento que a reflexão propôs para o dia seguinte (ADR-0070), e o que a reflexão da
    noite seguinte disse dele."""

    day: int  # a noite em que foi proposto
    hypothesis: str
    test: str
    prediction: str
    result: str | None = None  # cumpriu, falhou ou inconclusivo
    result_day: int | None = None


@dataclass(frozen=True, slots=True)
class BeliefChange:
    """A diferença que uma reflexão fez numa crença; vira um evento `memory.belief.*`."""

    kind: ChangeKind
    belief: Belief
    previous_confidence: float | None = None


class MemoryPort(Protocol):
    # ------------------------------------------------------------- registrar
    def record(self, episode: Episode) -> None: ...

    def note(self, note: Note) -> None: ...

    # ------------------------------------------------------------- lembrar
    def episodes(self, day: int, *, limit: int | None = None) -> list[Episode]:
        """Os episódios de um dia, na ordem; `limit` corta pelos mais recentes."""
        ...

    def notes(self, day: int) -> list[Note]: ...

    def beliefs(self) -> list[Belief]:
        """As crenças vivas, da mais confiante para a menos; empate pelo id."""
        ...

    def last_reflection(self) -> Reflection | None: ...

    def has_reflection(self, day: int) -> bool: ...

    def salient(self, day: int, *, now_tick: int, limit: int) -> list[Episode]:
        """Os episódios marcantes de um dia: importância vezes recência (o memory stream)."""
        ...

    def places(self) -> list[Place]:
        """Os lugares lembrados, do visto mais recente ao mais antigo; empate pelo id."""
        ...

    # ------------------------------------------------------------- lugares
    def remember(self, places: Sequence[Place]) -> None:
        """Guarda o estado visto agora, por cima do que havia de cada um."""
        ...

    def forget(self, entity_ids: Sequence[str]) -> None:
        """Esquece o que deixou de existir, ou o que estava à vista e não estava mais lá."""
        ...

    # ------------------------------------------------------------- o caderno de campo
    def save_planting(self, planting: Planting) -> None:
        """Guarda um plantio, por cima do que havia com o mesmo canteiro e o mesmo tick."""
        ...

    def plantings(self) -> list[Planting]:
        """Os plantios, do mais antigo ao mais recente."""
        ...

    def eat(self, meal: Meal) -> None: ...

    def meals(self) -> list[Meal]: ...

    def save_experiment(self, experiment: Experiment) -> None:
        """Guarda um experimento, por cima do que havia da mesma noite."""
        ...

    def experiments(self) -> list[Experiment]:
        """Os experimentos, do mais antigo ao mais recente."""
        ...

    # ------------------------------------------------------------- refletir
    def save_reflection(self, reflection: Reflection) -> Sequence[BeliefChange]:
        """Guarda a reflexão e aplica as revisões às crenças; devolve o que mudou."""
        ...

    def close(self) -> None: ...
