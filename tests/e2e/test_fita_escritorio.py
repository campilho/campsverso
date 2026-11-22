"""A manhã do escritório com o dev pensando com o modelo, reproduzida da fita (o plano do M24, §8).

A fita foi gravada de novo em 22/nov com `make fita CARTUCHO=office_campsverso`, com o Sonnet 5.5
(14 chamadas, US$ 0,046), depois que o dev passou a se chamar Tiago e o gerente, Camps (ADR-0092):
o nome novo muda o cartão e o bom-dia, e a fita antiga deixou de bater. A anterior, da mesma manhã,
tinha 13 chamadas (o briefing abrindo a sessão, ADR-0089, decisão 4); a de 21/nov, 14, e a de
20/nov, 17. É o bom-dia do gerente e os pedidos das 9:30 e das 10:30 do mundo de teste, com a
oficina no repositório de exemplo (`tests/fixtures/oficina`). O CI só a reproduz: os mesmos pedidos
ao modelo, na mesma ordem, sem rede e sem custo. Se a mente, a oficina ou o mundo mudarem o que vai
ao modelo, a fita deixa de bater, e é preciso gravar de novo (uns centavos).
"""

from campsverso_adapters import RecordingModel
from campsverso_testkit.fita import FIXTURES, run_office

TAPE = FIXTURES / "escritorio-manha.jsonl"


async def test_a_manha_do_escritorio_com_o_modelo_reproduz_da_fita() -> None:
    summary = await run_office(RecordingModel(None, TAPE, "replay"))
    assert (summary["calls"], summary["replayed"], summary["charged"]) == (14, 14, 0)
    assert summary["failed"] == 0  # nenhum pedido fora da fita
    assert summary["replies"] == 1  # o bom-dia do gerente
    assert summary["sessions"] == 2
    assert summary["unfinished"] == []
    assert summary["delivered"] == ["pedido-001", "pedido-002"]
    assert summary["patches"] == 2
    # A busca virou um robô irmão do testador, com o teste rodado; o resumo do diário, lido. Com o
    # briefing apontando os arquivos, o dev olhou menos pastas (eram 4 `ver_arquivos`). Nesta
    # gravação, o Tiago ainda acertou um arquivo com uma edição.
    assert summary["steps"] == {
        "buscar": 1,
        "editar": 1,
        "escrever": 2,
        "ler": 4,
        "pronto": 2,
        "rodar_testes": 1,
        "ver_arquivos": 2,
    }
    assert summary["robots"] == 2  # o briefing, que abriu cada uma das duas sessões
