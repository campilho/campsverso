"""A mente do Tiago, o dev do escritório (ADR-0080, ADR-0092): o cartão de identidade do cenário por
cima da mente do gênero office (ADR-0031). Entry point `campsverso.minds`: `tiago_escritorio`."""

from pathlib import Path

import campsverso_office_mind
from campsverso_mind import Mind

CARD = Path(__file__).parent / "data" / "tiago.md"


def load() -> Mind:
    return campsverso_office_mind.mind().extend(card=CARD.read_text(encoding="utf-8"))


mind = load()  # entry point campsverso.minds: tiago_escritorio

__all__ = ["CARD", "load", "mind"]
