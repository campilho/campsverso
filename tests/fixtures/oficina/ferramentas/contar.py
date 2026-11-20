def contar_linhas(texto: str) -> int:
    """Quantas linhas não vazias o texto tem."""
    return sum(1 for linha in texto.splitlines() if linha.strip())
