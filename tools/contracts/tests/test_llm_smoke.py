"""A fumaça da porta, sem rede: uma porta falsa no lugar da Anthropic (ADR-0058)."""

from pathlib import Path

from campsverso_adapters import FakeWallClock, ModelPrices, SequentialUuid7Ids
from campsverso_ports import ModelCapabilities, ModelRequest, ModelResponse, ModelUsage
from campsverso_tools.llm_smoke import smoke


class FakeModel:
    provider = "fake"

    def capabilities(self) -> ModelCapabilities:
        return ModelCapabilities()

    async def count_tokens(self, request: ModelRequest) -> int:
        return 42

    async def complete(self, request: ModelRequest) -> ModelResponse:
        return ModelResponse(
            content=[
                {"type": "tool_use", "id": "t", "name": "propose", "input": {"action": "harvest"}}
            ],
            stop_reason="tool_use",
            usage=ModelUsage(100, 20),
            model=request.model,
            latency_ms=5,
            request_id="req_x",
        )


async def test_a_chamada_real_e_a_gravada_passam_pelo_mesmo_contrato(tmp_path: Path) -> None:
    result = await smoke(
        FakeModel(),
        {"claude-haiku-5-5": ModelPrices(0.10, 0.50, 0.01, 0.125)},
        model="claude-haiku-5-5",
        prompt="oi",
        cassette=tmp_path / "fita.jsonl",
        clock=FakeWallClock(),
        ids=SequentialUuid7Ids(),
    )
    assert result["live"]["tool_uses"][0]["input"] == {"action": "harvest"}
    assert result["replayed"] is True
    first, second = result["events"]  # os dois passaram pelo ValidatingBus
    assert first["type"] == second["type"] == "campsverso.llm.call.completed.v1"
    assert (first["data"]["charged"], second["data"]["charged"]) == (True, False)
    assert first["data"]["purpose"] == "probe"
    assert result["spent_usd"] == first["data"]["cost_usd"] == 0.00002
