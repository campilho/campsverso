"""O perfil da memória de um mundo (o plano do M24, §2.2 e §2.3; adendo da ADR-0080).

A memória (ADR-0060) nasceu na fazenda: um tick de um minuto, o peso de colher e de desmaiar, a
reflexão ao dormir. O perfil é o que ela tira do pacote de mente do cartucho em vez de saber da
fazenda:
- a duração do tick, para dar a hora de cada acontecimento;
- o peso de cada acontecimento e a linha legível dele;
- o que é ruído (as ações da rotina) e se ela guarda os lugares vistos;
- os textos e a ferramenta da revisão, e quantos dias ela olha para trás;
- a ferramenta de anotar, para uma mente que não anota na proposta.

Um campo vazio é o da fazenda: o perfil padrão é a fazenda, byte a byte, e as fitas do CI conferem.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

import yaml


@dataclass(frozen=True, slots=True)
class MemoryProfile:
    tick_seconds: float = 60.0
    importance_by_type: Mapping[str, int] | None = None  # None: a tabela da fazenda
    importance_by_action: Mapping[str, int] | None = None
    # A linha legível de um tipo de evento, com `{when}` e os campos do evento; com `:self` no fim
    # da chave, a linha de quando o próprio avatar é o autor (`avatar_id` ou `by`: a fala dele, o
    # pedido que ele pegou).
    lines: Mapping[str, str] = field(default_factory=dict[str, str])
    quiet_actions: frozenset[str] = frozenset()  # as ações da rotina: nem a conclusão nem a recusa
    # Os prefixos de tipos de evento que não viram episódio, além dos de sempre.
    skipped: tuple[str, ...] = ()
    places: bool = True  # os lugares vistos (ADR-0067): numa sala sem raio, tudo está à vista
    reflected_when: str = "ao dormir"  # "Dia 3, ao dormir: <resumo>", no bloco de abertura
    empty: str = "O caderno ainda está vazio: é o seu primeiro dia."
    beliefs_header: str = "Crenças (confiança de 0 a 1):"  # no bloco e na revisão
    # A revisão de vários dias de uma vez (§2.3): sem instruções, a mente reflete como a fazenda.
    review_instructions: str | None = None
    review_tool: Mapping[str, Any] | None = None
    review_closing: str = "Feche o dia com a ferramenta reflect."
    review_days: int = 3
    note_tool: Mapping[str, Any] | None = None


def load_profile(path: Path) -> MemoryProfile:
    """O perfil de um `memoria.yaml`: `tick_seconds`, `importance` (`events` e `actions`),
    `lines`, `quiet_actions`, `skipped`, `places`, `reflected_when`, `empty`, `beliefs_header`,
    `review` (`instructions`, `tool`, `closing`, `days`) e `note_tool`."""
    doc = cast(Mapping[str, Any], yaml.safe_load(path.read_text(encoding="utf-8")))
    importance = cast(Mapping[str, Any], doc.get("importance") or {})
    review = cast(Mapping[str, Any], doc.get("review") or {})
    defaults = MemoryProfile()

    def table(key: str) -> Mapping[str, int] | None:
        raw = cast(Mapping[str, Any] | None, importance.get(key))
        return None if raw is None else {str(k): int(v) for k, v in raw.items()}

    return MemoryProfile(
        tick_seconds=float(doc.get("tick_seconds", defaults.tick_seconds)),
        importance_by_type=table("events"),
        importance_by_action=table("actions"),
        lines={str(k): str(v) for k, v in cast(Mapping[str, Any], doc.get("lines") or {}).items()},
        quiet_actions=frozenset(
            str(a) for a in cast(Sequence[Any], doc.get("quiet_actions") or ())
        ),
        skipped=tuple(str(x) for x in cast(Sequence[Any], doc.get("skipped") or ())),
        places=bool(doc.get("places", defaults.places)),
        reflected_when=str(doc.get("reflected_when", defaults.reflected_when)),
        empty=str(doc.get("empty", defaults.empty)).strip(),
        beliefs_header=str(doc.get("beliefs_header", defaults.beliefs_header)).strip(),
        review_instructions=(
            None if review.get("instructions") is None else str(review["instructions"]).strip()
        ),
        review_tool=cast(Mapping[str, Any] | None, review.get("tool")),
        review_closing=str(review.get("closing", defaults.review_closing)).strip(),
        review_days=int(review.get("days", defaults.review_days)),
        note_tool=cast(Mapping[str, Any] | None, doc.get("note_tool")),
    )
