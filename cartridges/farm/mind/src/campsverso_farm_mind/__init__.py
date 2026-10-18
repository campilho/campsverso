"""A mente do gênero farm (ADR-0059): só dados. As notas do mundo dizem o que um fazendeiro
recém-chegado saberia (as partes visíveis da bíblia; nada da regra oculta, princípio 5), e o
catálogo de ferramentas tem uma ferramenta por ação do cartucho. O cenário põe o cartão por cima."""

from pathlib import Path

from campsverso_mind import Mind, load_tools

DATA = Path(__file__).parent / "data"
NOTES = DATA / "fazenda.md"
TOOLS = DATA / "tools.yaml"


def mind() -> Mind:
    """A mente do gênero, sem cartão: o cenário a estende com o seu."""
    return Mind("farm", card="", notes=NOTES.read_text(encoding="utf-8"), tools=load_tools(TOOLS))


__all__ = ["DATA", "NOTES", "TOOLS", "mind"]
