"""A fita e o decorador da porta de modelo (ADR-0058): gravar, reproduzir, medir e publicar."""

from pathlib import Path
from typing import Any

import pytest

from campsverso_adapters import (
    FakeWallClock,
    InMemoryBus,
    MeteredModel,
    ModelPrices,
    RecordingModel,
    SequentialUuid7Ids,
    ValidatingBus,
    cost_usd,
    load_env,
)
from campsverso_ports import (
    ModelCallError,
    ModelCapabilities,
    ModelRequest,
    ModelResponse,
    ModelUsage,
    SubCall,
    request_sha256,
)

HAIKU = ModelPrices(0.10, 0.50, 0.01, 0.125)
USAGE = ModelUsage(1040, 86, 2100, 0)


class FakeModel:
    """Uma porta que responde sempre o mesmo e conta as chamadas; pode falhar sob encomenda."""

    provider = "fake"

    def __init__(self, failure: ModelCallError | None = None) -> None:
        self.calls = 0
        self.failure = failure

    def capabilities(self) -> ModelCapabilities:
        return ModelCapabilities()

    async def count_tokens(self, request: ModelRequest) -> int:
        return 7

    async def complete(self, request: ModelRequest) -> ModelResponse:
        self.calls += 1
        if self.failure is not None:
            raise self.failure
        return ModelResponse(
            content=[{"type": "tool_use", "id": "t1", "name": "propose", "input": {"a": 1}}],
            stop_reason="tool_use",
            usage=USAGE,
            model=request.model,
            latency_ms=1840,
            request_id="req_1",
        )


def _request(text: str = "O que fazer?") -> ModelRequest:
    return ModelRequest(
        model="claude-haiku-5-5",
        messages=[{"role": "user", "content": text}],
        effort="low",
        avatar_id="camps",
    )


async def test_fita_grava_e_reproduz_pelo_hash_do_pedido(tmp_path: Path) -> None:
    path = tmp_path / "fita.jsonl"
    inner = FakeModel()
    recorder = RecordingModel(inner, path, "record", clock=FakeWallClock())
    first = await recorder.complete(_request())
    again = await recorder.complete(_request())  # já gravado: não chama de novo
    assert (inner.calls, first.replayed, again.replayed) == (1, False, True)
    assert len(path.read_text(encoding="utf-8").splitlines()) == 1

    player = RecordingModel(None, path, "replay")
    replayed = await player.complete(_request())
    assert replayed.replayed is True
    assert replayed.content == first.content
    assert replayed.usage == USAGE
    assert (player.provider, len(player)) == ("recorded", 1)
    with pytest.raises(ModelCallError) as miss:
        await player.complete(_request("outro pedido"))
    assert miss.value.kind == "cassette_miss"

    live = RecordingModel(FakeModel(), tmp_path / "nunca.jsonl", "live")
    assert (await live.complete(_request())).replayed is False
    assert not (tmp_path / "nunca.jsonl").exists()
    with pytest.raises(ValueError, match="só reproduz"):
        RecordingModel(None, path, "record")


def test_custo_sai_da_tabela_de_precos() -> None:
    # 1040 x 0,10 + 86 x 0,50 + 2100 x 0,01, por milhão: o exemplo do contrato.
    assert cost_usd(USAGE, HAIKU) == 0.000168
    assert cost_usd(ModelUsage(0, 0), HAIKU) == 0


def _metered(inner: Any, bus: ValidatingBus) -> MeteredModel:
    return MeteredModel(
        inner,
        bus=bus,
        worldid="farm-camps-01",
        cartridge="farm_camps",
        controller={"type": "llm", "id": "llm/haiku"},
        prices={"claude-haiku-5-5": HAIKU},
        clock=FakeWallClock(),
        ids=SequentialUuid7Ids(),
        sim_clock=lambda: (506, "2026-03-02T14:26:00-03:00"),
    )


async def test_decorador_publica_a_chamada_concluida_pelo_contrato() -> None:
    inner_bus = InMemoryBus()
    metered = _metered(FakeModel(), ValidatingBus(inner_bus))
    metered.assert_priced("claude-haiku-5-5")
    with pytest.raises(LookupError):
        metered.assert_priced("modelo-sem-preco")
    response = await metered.complete(_request())
    assert response.stop_reason == "tool_use"
    ((subject_name, envelope),) = inner_bus.published
    assert subject_name == "campsverso.farm-camps-01.observer.llm.call.completed.v1"
    assert envelope["visibility"] == "observer"
    assert envelope["subject"] == "avatar/camps"
    assert (envelope["tick"], envelope["simtime"]) == (506, "2026-03-02T14:26:00-03:00")
    data = envelope["data"]
    assert data["controller"] == {"type": "llm", "id": "llm/haiku"}
    assert (data["provider"], data["model"], data["purpose"]) == (
        "fake",
        "claude-haiku-5-5",
        "decision",
    )
    assert data["prompt_sha256"] == request_sha256(_request())
    assert (data["cost_usd"], data["charged"], data["stop_reason"]) == (0.000168, True, "tool_use")
    assert (data["usage"]["input_tokens"], data["request_id"], data["effort"]) == (
        1040,
        "req_1",
        "low",
    )
    assert metered.spent_usd == 0.000168


async def test_reproduzida_nao_e_cobrada_e_falha_vira_evento(tmp_path: Path) -> None:
    inner_bus = InMemoryBus()
    bus = ValidatingBus(inner_bus)
    recorder = RecordingModel(FakeModel(), tmp_path / "fita.jsonl", "record", clock=FakeWallClock())
    await recorder.complete(_request())
    metered = _metered(RecordingModel(None, tmp_path / "fita.jsonl", "replay"), bus)
    await metered.complete(_request())
    (_, completed) = inner_bus.published[-1]
    assert completed["data"]["charged"] is False
    assert completed["data"]["provider"] == "recorded"
    assert metered.spent_usd == 0

    failing = _metered(FakeModel(ModelCallError("rate_limit", "429 demais")), bus)
    with pytest.raises(ModelCallError):
        await failing.complete(_request())
    (subject_name, failed) = inner_bus.published[-1]
    assert subject_name == "campsverso.farm-camps-01.observer.llm.call.failed.v1"
    assert (failed["data"]["error"], failed["data"]["retryable"]) == ("rate_limit", True)
    assert failed["data"]["message"] == "429 demais"

    unpriced = FakeModel()
    with pytest.raises(ModelCallError) as caught:
        await _metered(unpriced, bus).complete(
            ModelRequest(model="modelo-sem-preco", messages=[{"role": "user", "content": "x"}])
        )
    assert (caught.value.kind, unpriced.calls) == ("bad_request", 0)


def test_tabela_de_precos_do_ambiente() -> None:
    env = load_env(Path("config/env/local.yaml"), Path.cwd())
    assert env.models["claude-haiku-5-5"] == ModelPrices(0.10, 0.50, 0.01, 0.125)
    assert set(env.models) == {
        "claude-haiku-5-5",
        "claude-sonnet-5-5",
        "claude-opus-5-5",
        "claude-opus-4-8",  # o conselheiro (ADR-0074)
        "claude-fable-5-1",
    }
    # A tabela conferida em 28/out (ADR-0074): o cache lido do Sonnet 5.5 é 0,10, não 0,20.
    assert env.models["claude-sonnet-5-5"] == ModelPrices(2.00, 10.00, 0.10, 2.50)


OPUS48 = ModelPrices(5.00, 25.00, 0.50, 6.25)
ADVICE_USAGE = ModelUsage(823, 1612)
ADVISOR_TOOL = {"type": "advisor_20260301", "name": "advisor", "model": "claude-opus-4-8"}


class AdvisedModel(FakeModel):
    """A resposta de um pedido com o conselheiro: o uso dele vem à parte (ADR-0074)."""

    async def complete(self, request: ModelRequest) -> ModelResponse:
        response = await super().complete(request)
        advisor = SubCall("claude-opus-4-8", 1, ADVICE_USAGE)
        return ModelResponse(
            content=response.content,
            stop_reason=response.stop_reason,
            usage=response.usage,
            model=response.model,
            latency_ms=response.latency_ms,
            request_id=response.request_id,
            advisor=advisor,
        )


def _advised(text: str = "Feche o dia.") -> ModelRequest:
    return ModelRequest(
        model="claude-haiku-5-5",
        messages=[{"role": "user", "content": text}],
        tools=[ADVISOR_TOOL],
        purpose="reflection",
        avatar_id="camps",
    )


async def test_o_conselheiro_e_cobrado_na_tarifa_dele_e_vai_no_evento(tmp_path: Path) -> None:
    inner_bus = InMemoryBus()
    prices = {"claude-haiku-5-5": HAIKU, "claude-opus-4-8": OPUS48}
    recorder = RecordingModel(
        AdvisedModel(), tmp_path / "fita.jsonl", "record", clock=FakeWallClock()
    )
    metered = MeteredModel(
        recorder,
        bus=ValidatingBus(inner_bus),
        worldid="farm-camps-01",
        cartridge="farm_camps",
        controller={"type": "llm", "id": "llm/haiku"},
        prices=prices,
        clock=FakeWallClock(),
        ids=SequentialUuid7Ids(),
    )
    response = await metered.complete(_advised())
    assert response.advisor == SubCall("claude-opus-4-8", 1, ADVICE_USAGE)
    ((_, envelope),) = inner_bus.published  # o barramento valida o campo novo pelo contrato
    advice_cost = cost_usd(ADVICE_USAGE, OPUS48)
    assert envelope["data"]["advisor"] == {
        "model": "claude-opus-4-8",
        "calls": 1,
        "usage": ADVICE_USAGE.as_dict(),
        "cost_usd": advice_cost,
    }
    assert envelope["data"]["cost_usd"] == round(0.000168 + advice_cost, 8)
    assert metered.spent_usd == envelope["data"]["cost_usd"]
    # A fita guarda o uso do conselheiro, e a resposta reproduzida o traz de volta.
    replayed = await RecordingModel(None, tmp_path / "fita.jsonl", "replay").complete(_advised())
    assert (replayed.replayed, replayed.advisor) == (True, response.advisor)


async def test_conselheiro_sem_preco_e_recusado_antes_de_gastar() -> None:
    inner = AdvisedModel()
    with pytest.raises(ModelCallError) as caught:
        await _metered(inner, ValidatingBus(InMemoryBus())).complete(_advised())
    assert (caught.value.kind, inner.calls) == ("bad_request", 0)
    assert "claude-opus-4-8" in caught.value.message
