"""Porta de memória (ADR-0060): o que um agente registra, lembra e reflete.

Três operações sobre quatro tipos: episódios (o que o agente viu e fez, uma linha por vez, com
importância), anotações (o que ele mesmo quis guardar), crenças (o que ele acredita, com
confiança, evidências e origem) e reflexões (o fechamento de um dia). A porta não conhece o modelo
nem o cartucho: quem transforma entregas em episódios e quem chama o modelo para refletir é a
mente; aqui fica só o que persiste.
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
        """Os episódios marcantes de um dia: importância vezes recência (a conta do memory stream)."""
        ...

    # ------------------------------------------------------------- refletir
    def save_reflection(self, reflection: Reflection) -> Sequence[BeliefChange]:
        """Guarda a reflexão e aplica as revisões às crenças; devolve o que mudou."""
        ...

    def close(self) -> None: ...
