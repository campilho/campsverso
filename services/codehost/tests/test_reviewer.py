"""O revisor de outra família sem a API (ADR-0083, parte 3): o pedido, a resposta, a reserva e a
fita. As respostas reais da calibração estão em `tests/fixtures/revisor/calibracao.json`."""

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import pytest

from campsverso_adapters import FakeWallClock, RecordingModel
from campsverso_codehost.reviewer import (
    MAX_DIFF_CHARS,
    Review,
    Reviewer,
    ReviewInput,
    comment_body,
    findings_of,
    guide_from,
    parse,
    review_request,
)
from campsverso_ports import (
    ErrorKind,
    ModelCallError,
    ModelCapabilities,
    ModelPort,
    ModelRequest,
    ModelResponse,
    ModelUsage,
)

CALIBRATION = Path(__file__).resolve().parents[3] / "tests/fixtures/revisor/calibracao.json"
ITEM = ReviewInput(
    9, "Sexta curta", "O expediente acaba às 17h.", "Sai às 17h.", "diff\n", "c" * 40
)
GOOD = """Veredito: devolver

A sexta caiu na quinta.

1. **grave** · cartridges/office/sim/src/campsverso_office_sim/config.py:84 · `== 4` é \
quinta. O dev sai cedo no dia errado.
2. **leve** · services/kernel/tests/test_sexta_curta.py:27 · o comentário diz sexta, mas 19/nov é \
quinta."""


class Scripted:
    """Uma porta que responde o texto dado, ou falha com o tipo dado."""

    def __init__(self, text: str | None, kind: ErrorKind = "server") -> None:
        self.text = text
        self.kind: ErrorKind = kind
        self.requests: list[ModelRequest] = []

    @property
    def provider(self) -> str:
        return "falso"

    def capabilities(self) -> ModelCapabilities:
        return ModelCapabilities(tool_use=False)

    async def complete(self, request: ModelRequest) -> ModelResponse:
        self.requests.append(request)
        if self.text is None:
            raise ModelCallError(self.kind, "falhou")
        return ModelResponse(
            content=[{"type": "text", "text": self.text}],
            stop_reason="end_turn",
            usage=ModelUsage(1000, 500, cost_usd=0.0125),
            model=request.model,
            latency_ms=10,
            served_by="Google AI Studio",
        )

    async def count_tokens(self, request: ModelRequest) -> int:
        return 0


def _reviewer(ports: dict[str, ModelPort], models: Sequence[str]) -> Reviewer:
    return Reviewer(ports.__getitem__, models, "## Princípios\n- um", ["CLAUDE.md", "config/"])


def test_o_veredito_vem_da_primeira_linha_e_os_achados_da_lista() -> None:
    verdict, body, findings = parse(GOOD)
    assert verdict == "devolver"
    assert body.startswith("A sexta caiu na quinta.")
    assert findings == 2
    assert [s for s, _ in findings_of(body)] == ["grave", "leve"]
    assert parse("**Veredito:** Mesclar\n\nNada a apontar.")[:2] == ("mesclar", "Nada a apontar.")
    assert parse("Achei pouca coisa.")[0] is None


def test_as_regras_sao_as_secoes_do_claude_md_que_valem_para_um_diff() -> None:
    claude = "# T\n\n## Stack\nPython\n\n## Princípios inegociáveis\n1. um\n\n## Nunca faça\n- x\n"
    guide = guide_from(claude)
    assert "1. um" in guide
    assert "- x" in guide
    assert "Python" not in guide
    assert guide_from("sem seções") == "sem seções"


def test_o_pedido_leva_o_pedido_as_regras_a_constituicao_e_o_diff_sem_ferramentas() -> None:
    request = review_request("google/gemini-4-neon", ITEM, "REGRAS", ["config/", "CLAUDE.md"])
    text = request.messages[0]["content"][0]["text"]
    assert "# O pedido 9: Sexta curta" in text
    assert "**Aceite:** Sai às 17h." in text
    assert "REGRAS" in text
    assert "- `config/`" in text
    assert "```diff\ndiff\n```" in text
    assert request.tools == ()
    assert request.purpose == "review"
    huge = ReviewInput(1, "t", "", "", "x" * (MAX_DIFF_CHARS + 10), "h")
    cut = review_request("m", huge, "", []).messages[0]["content"][0]["text"]
    assert f"aqui vão só os primeiros {MAX_DIFF_CHARS}" in cut
    assert "x" * (MAX_DIFF_CHARS + 1) not in cut


async def test_o_plano_b_revisa_quando_o_a_falha() -> None:
    first, second = Scripted(None, "timeout"), Scripted(GOOD)
    reviewer = _reviewer({"a": first, "b": second}, ["a", "b"])
    review = await reviewer.review(ITEM)
    assert review is not None
    assert (review.model, review.verdict, review.findings) == ("b", "devolver", 2)
    assert review.failed == (("a", "timeout"),)
    comment = comment_body(review, ITEM)
    assert comment.startswith("### Revisão do pedido 9: devolva ao dev")
    assert "antes, `a` falhou (timeout)" in comment
    assert "US$ 0,013" in comment
    assert "servido por Google AI Studio" in comment


async def test_sem_resposta_de_nenhum_nao_ha_revisao() -> None:
    reviewer = _reviewer({"a": Scripted(None), "b": Scripted("   ")}, ["a", "b"])
    assert await reviewer.review(ITEM) is None


async def test_a_fita_responde_de_graca_a_revisao_ja_paga(tmp_path: Path) -> None:
    tape = tmp_path / "revisor.jsonl"
    clock = FakeWallClock()
    paid = RecordingModel(Scripted(GOOD), tape, "record", clock=clock)
    first = await _reviewer({"a": paid}, ["a"]).review(ITEM)
    replay = RecordingModel(None, tape, "replay", clock=clock)
    again = await _reviewer({"a": replay}, ["a"]).review(ITEM)
    assert first is not None
    assert again is not None
    assert again.replayed
    assert not first.replayed
    assert (again.verdict, again.text) == (first.verdict, first.text)
    assert "reproduzida da fita, sem custo" in comment_body(again, ITEM)


@pytest.mark.skipif(not CALIBRATION.is_file(), reason="a calibração ainda não rodou")
def test_as_respostas_da_calibracao_se_leem_e_viram_comentario() -> None:
    saved: dict[str, Any] = json.loads(CALIBRATION.read_text(encoding="utf-8"))
    for result in saved["results"]:
        verdict, body, findings = parse(str(result["raw"]))
        assert verdict == result["verdict"]
        assert findings == result["findings"]
        review = Review(result["model"], verdict, body, findings, None, True, None, "h")
        assert comment_body(review, ITEM).startswith("### Revisão do pedido 9: ")
