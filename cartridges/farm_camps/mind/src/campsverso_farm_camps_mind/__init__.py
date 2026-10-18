"""A mente do Camps (ADR-0059): o cartão de identidade do cenário por cima da mente do gênero
farm (ADR-0031). Entry point `campsverso.minds`: `camps`."""

from pathlib import Path

import campsverso_farm_mind
from campsverso_mind import Mind

CARD = Path(__file__).parent / "data" / "camps.md"


def load() -> Mind:
    return campsverso_farm_mind.mind().extend(card=CARD.read_text(encoding="utf-8"))


mind = load()  # entry point campsverso.minds: camps

__all__ = ["CARD", "load", "mind"]
