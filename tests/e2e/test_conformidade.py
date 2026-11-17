"""A prova de conformidade do escritório (ADR-0077, decisão 11), com um modelo de mentira: o CI
nunca chama a API. Confere a contagem, a correção por fora e o veredito."""

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from campsverso_adapters import ModelPrices
from campsverso_ports import ModelCapabilities, ModelRequest, ModelResponse, ModelUsage
from campsverso_testkit.conformidade import TASKS, format_problem, prove, report

PRICES = ModelPrices(2.0, 10.0, 0.1, 2.5)


def use(name: str, **given: Any) -> dict[str, Any]:
    return {"type": "tool_use", "id": f"t-{name}", "name": name, "input": given}


class Scripted:
    """As respostas na ordem; uma resposta é (blocos, stop_reason)."""

    def __init__(self, *answers: tuple[Sequence[Mapping[str, Any]], str]) -> None:
        self.answers = list(answers)
        self.requests: list[ModelRequest] = []

    @property
    def provider(self) -> str:
        return "roteiro"

    def capabilities(self) -> ModelCapabilities:
        return ModelCapabilities()

    async def count_tokens(self, request: ModelRequest) -> int:
        return 0

    async def complete(self, request: ModelRequest) -> ModelResponse:
        self.requests.append(request)
        blocks, stop = self.answers.pop(0)
        return ModelResponse(
            content=[dict(b) for b in blocks],
            stop_reason=stop,
            usage=ModelUsage(1000, 100),
            model=request.model,
            latency_ms=1,
        )


def tool(*blocks: Mapping[str, Any]) -> tuple[Sequence[Mapping[str, Any]], str]:
    return (blocks, "tool_use")


GOOD = (
    tool(
        use(
            "escrever",
            path="calc/saudacao.py",
            content='def saudar(nome: str) -> str:\n    return f"Olá, {nome}!"\n',
        )
    ),
    tool(
        use(
            "escrever",
            path="tests/test_saudacao.py",
            content="from calc.saudacao import saudar\n\n\ndef test_saudar() -> None:\n"
            '    assert saudar("Bia") == "Olá, Bia!"\n',
        )
    ),
    tool(use("rodar_testes", path="tests")),
    tool(use("anotar", texto="Os testes rodam com o pytest em tests/.")),
    tool(use("pronto", resumo="Escrevi a saudação e o teste.")),
    tool(use("ler", path="calc/media.py")),
    tool(
        use(
            "editar",
            path="calc/media.py",
            old="(len(valores) + 1)",
            new="len(valores)",
        )
    ),
    tool(use("pronto", resumo="A média dividia por um a mais.")),
)


async def test_o_modelo_que_faz_os_dois_pedidos_passa(tmp_path: Path) -> None:
    port = Scripted(*GOOD)
    verdict = await prove("modelo-de-mentira", port, PRICES, tmp_path)
    assert [t.correct for t in verdict.tasks] == [True, True]
    assert verdict.tasks[0].notes == 1  # anotar é da mente: conta como ação
    assert verdict.tasks[1].files == ["calc/media.py"]
    assert verdict.tally.responses == 8
    assert verdict.tally.no_action == 0
    assert verdict.tally.format_errors == []
    assert verdict.passed
    # O caminho do escritório: as ferramentas da oficina, a de anotar e a memória vazia na abertura.
    first = port.requests[0]
    assert {t["name"] for t in first.tools} >= {"escrever", "rodar_testes", "pronto", "anotar"}
    text = first.messages[0]["content"][0]["text"]
    assert text.startswith("## O que você lembra\n")
    assert "Pedido 1: Saudação" in text
    assert (tmp_path / "modelo-de-mentira.json").is_file()
    assert "| modelo-de-mentira | sim |" in report([verdict])


async def test_mudar_o_teste_recusar_e_errar_o_formato_reprovam(tmp_path: Path) -> None:
    port = Scripted(
        ([{"type": "text", "text": "Não posso."}], "refusal"),  # a recusa encerra o pedido 1
        tool(use("apagar", path="calc/media.py")),  # não existe
        tool(
            use(
                "escrever",
                path="tests/test_media.py",
                content="def test_nada() -> None:\n    assert True\n",
            )
        ),
        tool(use("pronto", resumo="Arrumei o teste.")),
    )
    verdict = await prove("modelo-de-mentira", port, PRICES, tmp_path)
    escrever, consertar = verdict.tasks
    assert (escrever.done, escrever.reason, escrever.hidden_pass) == (
        False,
        "sem ferramenta",
        False,
    )
    assert consertar.done
    assert not consertar.hidden_pass  # o defeito continua no código
    assert consertar.touched == ["tests/test_media.py"]
    assert consertar.review  # a revisão recusa o teste a menos
    assert verdict.tally.refusals == 1
    assert verdict.tally.format_errors == ["ferramenta que não existe: apagar"]
    assert not verdict.passed


def test_os_erros_de_formato() -> None:
    tools = {
        "ler": {
            "name": "ler",
            "input_schema": {
                "type": "object",
                "properties": {"path": {"type": "string"}, "start": {"type": "integer"}},
                "required": ["path"],
            },
        }
    }
    assert format_problem(use("ler", path="a.py", start=2), tools) is None
    assert format_problem(use("ler"), tools) == "ler: falta path"
    assert format_problem(use("ler", path="a.py", start="2"), tools) == "ler: start não é inteiro"
    assert format_problem(use("ler", path="a.py", start=True), tools) == "ler: start não é inteiro"
    assert (
        format_problem({"name": "ler", "input": "x"}, tools)
        == "ler: os argumentos não são um objeto"
    )
    assert len(TASKS) == 2
