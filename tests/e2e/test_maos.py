"""As mãos do dev no escritório (ADR-0089), em memória e sem a API.

O gerente escreve um pedido para o Claude Code com o Opus 5.5. O dev senta, o robô do briefing
abre a sessão, e o Claude Code de verdade trabalha no espaço contra um modelo falso, pela porta das
mãos. A entrega passa pela revisão da oficina e vira um PR no GitHub falso, como as do nosso
harness. No Linux (o CI), sem o `sandbox-exec`: valem o gancho e a porta.
"""

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import httpx2
import pytest

from campsverso_adapters.hands_claude_code import ClaudeCodeHands, bundled_cli
from campsverso_adapters.model_fake_http import FakeModel, text, use
from campsverso_ports import (
    CallMeter,
    Hands,
    ModelCapabilities,
    ModelRequest,
    ModelResponse,
    ModelUsage,
)
from campsverso_testkit.oficina import example_office_repo
from campsverso_testkit.pipeline import Pipeline

LINHAS = (
    'def linhas(texto: str) -> int:\n    """Quantas linhas o texto tem."""\n'
    "    return len(texto.splitlines())\n"
)
TESTE = (
    "from ferramentas.linhas import linhas\n\n\ndef test_linhas() -> None:\n"
    '    assert linhas("a\\nb") == 2\n'
)
SESSION = (
    use("Bash", command=f"cat > ferramentas/linhas.py <<'FIM'\n{LINHAS}FIM"),
    use("Bash", command=f"cat > tests/test_linhas.py <<'FIM'\n{TESTE}FIM"),
    text("Escrevi o contador de linhas e o teste dele."),
)
TICKET = {
    "at": "09:30",
    "title": "Contador de linhas",
    "description": "Uma função que conta as linhas de um texto, em ferramentas/linhas.py.",
    "acceptance": "O teste de tests/test_linhas.py passa.",
    "size": "P",
    "harness": "claude_code",
    "model": "claude-opus-5-5",
}


class Chat:
    """A porta da mente fora da oficina: o bom-dia ao gerente."""

    @property
    def provider(self) -> str:
        return "conversa"

    def capabilities(self) -> ModelCapabilities:
        return ModelCapabilities()

    async def count_tokens(self, request: ModelRequest) -> int:
        return 0

    async def complete(self, request: ModelRequest) -> ModelResponse:
        return ModelResponse(
            content=[{"type": "text", "text": "Bom dia! Vou ver o quadro."}],
            stop_reason="end_turn",
            usage=ModelUsage(100, 10),
            model=request.model,
            latency_ms=1,
        )


def _one(pipeline: Pipeline, kind: str) -> dict[str, Any]:
    found = pipeline.of_type(kind)
    assert len(found) == 1, (kind, found)
    return found[0]


async def test_o_pedido_pelo_claude_code_vira_um_pr(tmp_path: Path) -> None:
    try:
        cli = bundled_cli()
    except FileNotFoundError:
        pytest.skip("o SDK veio sem o Claude Code nesta plataforma")
    fake = FakeModel(SESSION)

    def hands(meter: CallMeter) -> Mapping[str, Hands]:
        return {
            "claude_code": ClaudeCodeHands(
                meter,
                api_key="chave-de-verdade",
                home=tmp_path / "maos",
                cli=cli,
                upstream="http://modelo-falso",
                transport=httpx2.ASGITransport(app=fake.app()),
            )
        }

    pipeline = Pipeline(
        controller="llm",
        port=Chat(),
        cartridge="office_campsverso",
        workshop_repo=example_office_repo(tmp_path),
        model="claude-sonnet-5-5",
        codehost=True,
        hands=hands,
        helper_config={"gerente": {"tickets": [TICKET]}},
    )
    await pipeline.start()
    end = pipeline.core.tick + pipeline.day * 12 // 24
    while not pipeline.of_type("office.ticket.pr_opened.v1"):
        assert pipeline.core.tick < end, "o PR não abriu na manhã"
        await pipeline.run_until(pipeline.core.tick + pipeline.day // 48)

    # A prancheta: o pedido com as mãos e o modelo.
    created = _one(pipeline, "office.ticket.created.v1")
    assert (created["harness"], created["model"]) == ("claude_code", "claude-opus-5-5")
    # O briefing abriu a sessão, e o Claude Code trabalhou pela porta, com o modelo do pedido.
    assert fake.used == len(SESSION)
    opening = str(fake.seen[0]["body"]["messages"][0]["content"])
    assert "# Briefing" in opening
    assert "Contador de linhas" in opening
    assert {s["body"]["model"] for s in fake.seen} == {"claude-opus-5-5"}
    briefing = [c for c in pipeline.of_type("workshop.robot_called.v1") if c["ok"]]
    assert [c["robot_id"] for c in briefing] == ["robo-briefing"]
    steps = pipeline.of_type("workshop.step.v2")
    assert [(s["tool"], s["harness"], s["ok"]) for s in steps] == [
        ("Bash", "claude_code", True),
        ("Bash", "claude_code", True),
    ]
    calls = [c for c in pipeline.of_type("llm.call.completed.v1") if c.get("harness")]
    assert len(calls) == len(SESSION)
    assert {(c["harness"], c["ticket_id"], c["purpose"]) for c in calls} == {
        ("claude_code", "pedido-001", "workshop")
    }
    finished = _one(pipeline, "workshop.session_finished.v1")
    assert (finished["harness"], finished["model"], finished["done"]) == (
        "claude_code",
        "claude-opus-5-5",
        True,
    )
    assert finished["reason"] == "pronto"
    assert finished["cost_usd"] == pytest.approx(sum(float(c["cost_usd"]) for c in calls))
    # Do patch em diante, o caminho é o de sempre: a entrega e o PR no ramo do dev.
    delivered = _one(pipeline, "office.ticket.delivered.v1")
    assert sorted(delivered["patch"]["files"]) == ["ferramentas/linhas.py", "tests/test_linhas.py"]
    opened = _one(pipeline, "office.ticket.pr_opened.v1")
    assert (opened["ticket_id"], opened["branch"]) == ("pedido-001", "dev/pedido-1")
    assert pipeline.host is not None
    commit = pipeline.host.branches["dev/pedido-1"][-1]
    assert sorted(commit.files) == ["ferramentas/linhas.py", "tests/test_linhas.py"]
