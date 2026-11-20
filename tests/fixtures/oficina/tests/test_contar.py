from ferramentas.contar import contar_linhas


def test_conta_so_as_linhas_com_texto() -> None:
    assert contar_linhas("um\n\ndois\n  \ntrês\n") == 3


def test_texto_vazio_nao_tem_linhas() -> None:
    assert contar_linhas("") == 0
