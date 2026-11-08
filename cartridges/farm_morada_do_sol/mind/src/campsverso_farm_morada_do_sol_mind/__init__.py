"""A mente do Camps na Fazenda Morada do Sol (ADR-0067): o cartão do Camps (cenário farm_camps) por
cima do manual deste cenário, com o catálogo de ferramentas da fazenda 3. Entry point
`campsverso.minds`: `camps_morada`."""

from pathlib import Path

import campsverso_farm_camps_mind
import campsverso_farm_mind
from campsverso_mind import Mind, load_seasons, load_tools

DATA = Path(__file__).parent / "data"
NOTES = DATA / "morada.md"
TOOLS = DATA / "tools.yaml"
# O procedimento, o playbook 4 (ADR-0071; ADR-0074, decisão 35), e o manual em números.
PROCEDURE = DATA / "procedimento.md"
SEASONS = DATA / "estacoes.yaml"


def load() -> Mind:
    card = campsverso_farm_camps_mind.CARD.read_text(encoding="utf-8")
    return Mind(
        "camps_morada",
        card=card,
        notes=NOTES.read_text(encoding="utf-8"),
        tools=load_tools(TOOLS),
        craft=PROCEDURE.read_text(encoding="utf-8"),
        field_notebook=True,  # o caderno de campo e o experimento da noite (ADR-0070)
        experiments=True,
        columns=campsverso_farm_mind.columns(),  # a comparação, ligada só no braço (ADR-0074)
        seasons=load_seasons(SEASONS),  # os dias esperados do caderno completo (decisão 35)
    )


mind = load()  # entry point campsverso.minds: camps_morada

__all__ = ["DATA", "NOTES", "PROCEDURE", "SEASONS", "TOOLS", "load", "mind"]
