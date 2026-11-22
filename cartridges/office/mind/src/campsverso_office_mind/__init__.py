"""A mente do gênero office (ADR-0080): só dados. As notas do escritório dizem o que um dev
recém-chegado saberia (o quadro, o expediente, a oficina e as regras dela); as ferramentas da
oficina estão no formato da Messages API; há as instruções da sessão de trabalho (as do nosso
harness e as das mãos de fora, ADR-0089) e da conversa; e o perfil da memória, com a revisão da
manhã (o plano do M24, §2.2 e §2.3). O cenário põe o cartão por cima."""

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, cast

import yaml

from campsverso_mind import MemoryProfile, Mind, load_profile

DATA = Path(__file__).parent / "data"
NOTES = DATA / "escritorio.md"
WORKSHOP = DATA / "oficina.yaml"
SESSION = DATA / "sessao.md"
HANDS_SESSION = DATA / "sessao-maos.md"
CHAT = DATA / "conversa.md"
MEMORY = DATA / "memoria.yaml"


def workshop_tools() -> list[dict[str, Any]]:
    """As oito ferramentas da oficina, prontas para o pedido ao modelo."""
    doc = cast(Mapping[str, Any], yaml.safe_load(WORKSHOP.read_text(encoding="utf-8")))
    return [dict(t) for t in cast(Sequence[Mapping[str, Any]], doc["tools"])]


def robot_tool() -> dict[str, Any] | None:
    """A ferramenta da bancada, que a mente oferece quando há robô (o plano do M24, §4)."""
    doc = cast(Mapping[str, Any], yaml.safe_load(WORKSHOP.read_text(encoding="utf-8")))
    raw = cast(Mapping[str, Any] | None, doc.get("robot_tool"))
    return None if raw is None else dict(raw)


def session_instructions() -> str:
    return SESSION.read_text(encoding="utf-8")


def hands_session_instructions() -> str:
    """As instruções da sessão quando as mãos são de fora, como o Claude Code (ADR-0089): as
    ferramentas são as do harness, e a resposta final é a entrega."""
    return HANDS_SESSION.read_text(encoding="utf-8")


def chat_instructions() -> str:
    return CHAT.read_text(encoding="utf-8")


def memory_profile() -> MemoryProfile:
    """O que a memória guarda do dia de trabalho, e a revisão da manhã."""
    return load_profile(MEMORY)


def mind() -> Mind:
    """A mente do gênero, sem cartão e sem ferramentas do mundo: a rotina anda pela sala, e a
    mente pensa na oficina e na conversa."""
    return Mind(
        "office",
        card="",
        notes=NOTES.read_text(encoding="utf-8"),
        tools=(),
        workshop=tuple(workshop_tools()),
        session=session_instructions(),
        hands_session=hands_session_instructions(),
        conversation=chat_instructions(),
        memory=memory_profile(),
        robot_tool=robot_tool(),
    )


__all__ = [
    "CHAT",
    "DATA",
    "HANDS_SESSION",
    "MEMORY",
    "NOTES",
    "SESSION",
    "WORKSHOP",
    "chat_instructions",
    "hands_session_instructions",
    "memory_profile",
    "mind",
    "robot_tool",
    "session_instructions",
    "workshop_tools",
]
