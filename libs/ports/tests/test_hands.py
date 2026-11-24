"""O texto do modelo entre os passos (ADR-0093, decisão 12): numa linha e no tamanho do contrato."""

from campsverso_ports import note_of
from campsverso_ports.hands import NOTE_MAX


def test_o_texto_do_modelo_vira_uma_linha_curta() -> None:
    assert note_of(None) is None
    assert note_of("  \n ") is None
    assert note_of("Vou ler\n  o arquivo.") == "Vou ler o arquivo."
    long = note_of("palavra " * 60)
    assert long is not None
    assert len(long) == NOTE_MAX
    assert long.endswith("…")
