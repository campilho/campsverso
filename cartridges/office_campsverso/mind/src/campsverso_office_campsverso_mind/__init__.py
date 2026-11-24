"""As mentes dos devs do escritório (ADR-0080, ADR-0092, ADR-0093): o cartão de identidade de cada
um, do cenário, por cima da mente do gênero office (ADR-0031). Entry points `campsverso.minds`:
`tiago_escritorio` e `kenji_escritorio`. O cartão diz quem o dev é, nunca com que sistema ele
programa: o dev e o sistema são independentes (ADR-0093, decisão 18)."""

from pathlib import Path

import campsverso_office_mind
from campsverso_mind import Mind

DATA = Path(__file__).parent / "data"
CARD = DATA / "tiago.md"
KENJI_CARD = DATA / "kenji.md"


def load(card: Path = CARD) -> Mind:
    return campsverso_office_mind.mind().extend(card=card.read_text(encoding="utf-8"))


mind = load()  # entry point campsverso.minds: tiago_escritorio
kenji = load(KENJI_CARD)  # entry point campsverso.minds: kenji_escritorio

__all__ = ["CARD", "KENJI_CARD", "kenji", "load", "mind"]
