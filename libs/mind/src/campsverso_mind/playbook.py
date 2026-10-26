"""O playbook (ADR-0071): um jeito de trabalhar que a corrida pode dar a qualquer modelo.

São duas camadas. O método vale em qualquer mundo e fica aqui (`data/metodo.md`). O ofício diz
como o método se aplica num gênero e vem da mente (`Mind.craft`), como as notas do mundo. Só
método: nenhuma regra oculta, nem dica dela (princípio 5); o teste de palavras proibidas de cada
cenário lê o playbook. Uma corrida sem playbook, o padrão, não o vê.
"""

from pathlib import Path

from campsverso_mind.mind import Mind

METHOD = Path(__file__).parent / "data" / "metodo.md"
HEADING = "## O playbook"
# A versão do texto, do método e do ofício juntos: sobe a cada mudança, e a corrida grava a versão
# com que jogou. As versões antigas ficam no git (a 1 em 7cd7e06).
PLAYBOOK_VERSION = 2


def playbook(mind: Mind) -> str:
    """O texto que entra no prompt de sistema, depois do manual: o método e o ofício."""
    parts = [HEADING, "", METHOD.read_text(encoding="utf-8").strip()]
    if mind.craft.strip():
        parts += ["", mind.craft.strip()]
    return "\n".join(parts)
