"""A mente do gênero office (ADR-0080): só dados. As notas do escritório dizem o que um dev
recém-chegado saberia (o quadro, o expediente, a oficina e as regras dela); as ferramentas da
oficina estão no formato da Messages API; e há as instruções da sessão de trabalho e da conversa.
O cenário põe o cartão por cima."""

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, cast

import yaml

from campsverso_mind import Mind

DATA = Path(__file__).parent / "data"
NOTES = DATA / "escritorio.md"
WORKSHOP = DATA / "oficina.yaml"
SESSION = DATA / "sessao.md"
CHAT = DATA / "conversa.md"


def workshop_tools() -> list[dict[str, Any]]:
    """As oito ferramentas da oficina, prontas para o pedido ao modelo."""
    doc = cast(Mapping[str, Any], yaml.safe_load(WORKSHOP.read_text(encoding="utf-8")))
    return [dict(t) for t in cast(Sequence[Mapping[str, Any]], doc["tools"])]


def session_instructions() -> str:
    return SESSION.read_text(encoding="utf-8")


def chat_instructions() -> str:
    return CHAT.read_text(encoding="utf-8")


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
        conversation=chat_instructions(),
    )


__all__ = [
    "CHAT",
    "DATA",
    "NOTES",
    "SESSION",
    "WORKSHOP",
    "chat_instructions",
    "mind",
    "session_instructions",
    "workshop_tools",
]
