"""O playbook (ADR-0071): um jeito de trabalhar que a corrida pode dar a qualquer modelo.

Da versão 4 em diante (ADR-0074, decisão 35) ele é um procedimento operacional: o que o modelo
recebe e onde, as etapas da manhã, do dia e da noite, os formatos fixos e o que nunca e sempre
fazer. O texto inteiro vem da mente do cenário (`Mind.craft`), porque cita o manual e o calendário
dele; o método genérico das versões 1 a 3 ficou no git. Só método: nenhuma regra oculta, nem dica
dela (princípio 5); o teste de palavras proibidas de cada cenário lê o procedimento. Uma corrida
sem playbook, o padrão, não o vê.
"""

from campsverso_mind.mind import Mind

HEADING = "## O procedimento"
# A versão do texto: sobe a cada mudança, e a corrida grava a versão com que jogou. As versões
# antigas ficam no git (a 1 em 7cd7e06, a 2 em eb5c78a, a 3, que nunca rodou, em 315a280).
PLAYBOOK_VERSION = 4


def playbook(mind: Mind) -> str:
    """O texto que entra no prompt de sistema, depois do manual: o procedimento da mente."""
    text = mind.craft.strip()
    if not text.startswith(HEADING):
        raise ValueError(f"a mente {mind.name} não tem procedimento (começa com {HEADING!r})")
    return text
