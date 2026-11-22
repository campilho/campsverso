"""A prova de conformidade do escritório (ADR-0077, decisão 11), com um modelo de mentira: o CI
nunca chama a API. Confere a contagem, a correção por fora e o veredito."""

import asyncio
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import httpx2
import pytest

from campsverso_adapters import ModelPrices
from campsverso_adapters.hands_claude_code import ClaudeCodeHands, bundled_cli
from campsverso_adapters.model_fake_http import FakeModel
from campsverso_adapters.model_fake_http import text as say
from campsverso_adapters.model_fake_http import use as act
from campsverso_ports import (
    CallMeter,
    Hands,
    ModelCapabilities,
    ModelRequest,
    ModelResponse,
    ModelUsage,
)
from campsverso_testkit.conformidade import (
    TASKS,
    ProbeMeter,
    Tally,
    format_problem,
    prove,
    prove_hands,
    report,
)

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
    assert "| modelo-de-mentira | api | sim |" in report([verdict])
    assert verdict.tasks[1].summary == "A média dividia por um a mais."


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


# ---------------------------------------------------------------- as mãos do Claude Code (ADR-0089)

SAUDACAO = 'def saudar(nome: str) -> str:\n    return f"Olá, {nome}!"\n'
TESTE = (
    "from calc.saudacao import saudar\n\n\ndef test_saudar() -> None:\n"
    '    assert saudar("Bia") == "Olá, Bia!"\n'
)
CLAUDE_CODE = (
    act("Bash", command=f"mkdir -p calc && cat > calc/saudacao.py <<'FIM'\n{SAUDACAO}FIM"),
    act("Bash", command=f"cat > tests/test_saudacao.py <<'FIM'\n{TESTE}FIM"),
    act("Bash", command="python -m pytest -q tests"),
    act("mcp__oficina__anotar", texto="Os testes rodam com o pytest em tests/."),
    say("Escrevi a saudação e o teste."),
    act("Bash", command="cat calc/media.py"),
    act("Bash", command="sed -i.bak 's/(len(valores) + 1)/len(valores)/' calc/media.py"),
    act("Bash", command="rm calc/media.py.bak && python -m pytest -q tests"),
    say("A média dividia por um a mais."),
)


async def test_o_claude_code_faz_os_dois_pedidos_pela_porta_e_passa(tmp_path: Path) -> None:
    try:
        cli = bundled_cli()
    except FileNotFoundError:
        pytest.skip("o SDK veio sem o Claude Code nesta plataforma")
    fake = FakeModel(CLAUDE_CODE)

    def hands_of(meter: CallMeter) -> Hands:
        return ClaudeCodeHands(
            meter,
            api_key="chave-de-verdade",
            home=tmp_path / "maos",
            cli=cli,
            upstream="http://modelo-falso",
            transport=httpx2.ASGITransport(app=fake.app()),
        )

    prices = {"claude-opus-5-5": PRICES}
    verdict = await asyncio.wait_for(
        prove_hands("claude-opus-5-5", hands_of, prices, tmp_path), 600
    )
    escrever, consertar = verdict.tasks
    assert (escrever.correct, consertar.correct) == (True, True), verdict.as_dict()
    assert escrever.summary == "Escrevi a saudação e o teste."
    assert escrever.notes == 1
    assert consertar.files == ["calc/media.py"]
    assert any("Bash" in step for step in escrever.trail)
    # A resposta final de cada pedido é o `pronto` do harness: nenhuma resposta sem ação.
    assert verdict.tally.responses == len(CLAUDE_CODE)
    assert verdict.tally.no_action == 0
    assert verdict.tally.format_errors == []
    assert verdict.harness == "claude_code"
    assert verdict.passed
    assert (tmp_path / "claude-opus-5-5--claude_code.json").is_file()
    assert "| claude-opus-5-5 | claude_code | sim |" in report([verdict])
    # As instruções do Claude Code são as das mãos de fora: sem o `pronto` do nosso harness.
    system = str(fake.seen[0]["body"]["system"])
    assert "Aqui não há o `pronto`" in system
    assert "Você é o Camps" in system


async def test_o_medidor_da_prova_conta_pela_porta() -> None:
    tally = Tally()
    meter = ProbeMeter(tally, {"claude-opus-5-5": PRICES})
    with pytest.raises(LookupError):
        meter.assert_priced("claude-desconhecido")
    read = {"name": "Read", "input_schema": {"type": "object", "required": ["file_path"]}}

    def answer(*blocks: Mapping[str, Any], stop: str = "tool_use") -> ModelResponse:
        return ModelResponse(
            content=[dict(b) for b in blocks],
            stop_reason=stop,
            usage=ModelUsage(1000, 100),
            model="claude-opus-5-5",
            latency_ms=500,
        )

    def asked(*tools: Mapping[str, Any]) -> ModelRequest:
        return ModelRequest(model="claude-opus-5-5", messages=[], tools=list(tools))

    await meter.observed(asked(), answer(stop="end_turn"), harness="claude_code")  # auxiliar
    await meter.observed(asked(read), answer(use("Read")), harness="claude_code")
    await meter.observed(asked(read), answer(use("Apagar", path="a")), harness="claude_code")
    assert (tally.auxiliary, tally.responses) == (1, 2)
    assert tally.format_errors == ["Read: falta file_path", "ferramenta que não existe: Apagar"]
    assert tally.cost_usd == pytest.approx(3 * (1000 * 2.0 + 100 * 10.0) / 1_000_000)
