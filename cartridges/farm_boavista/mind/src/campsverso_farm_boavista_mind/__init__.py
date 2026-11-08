"""A mente do Camps na Fazenda Boa Vista (ADR-0062): o cartão do Camps (cenário farm_camps) por
cima do manual deste cenário, com o catálogo de ferramentas da fazenda 2. Entry point
`campsverso.minds`: `camps_boavista`."""

from pathlib import Path

import campsverso_farm_camps_mind
from campsverso_mind import Mind, load_tools

DATA = Path(__file__).parent / "data"
NOTES = DATA / "boavista.md"
TOOLS = DATA / "tools.yaml"


def load() -> Mind:
    card = campsverso_farm_camps_mind.CARD.read_text(encoding="utf-8")
    return Mind(
        "camps_boavista",
        card=card,
        notes=NOTES.read_text(encoding="utf-8"),
        tools=load_tools(TOOLS),
    )


mind = load()  # entry point campsverso.minds: camps_boavista

__all__ = ["DATA", "NOTES", "TOOLS", "load", "mind"]
