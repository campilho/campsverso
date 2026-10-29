"""O adaptador da Anthropic sem rede: um transporte HTTP falso do próprio SDK (ADR-0058)."""

import json
from collections.abc import Callable
from typing import Any

import httpx2
import pytest
from anthropic import AsyncAnthropic, DefaultAsyncHttpxClient

from campsverso_adapters import AnthropicModel, FakeWallClock
from campsverso_ports import ModelCallError, ModelRequest, ModelUsage, SubCall

TOOL: dict[str, Any] = {
    "name": "propose",
    "description": "Propõe a próxima ação.",
    "strict": True,
    "input_schema": {
        "type": "object",
        "properties": {"action": {"type": "string"}},
        "required": ["action"],
        "additionalProperties": False,
    },
}


def _client(handler: Callable[[httpx2.Request], httpx2.Response]) -> AsyncAnthropic:
    transport = httpx2.MockTransport(handler)
    return AsyncAnthropic(
        api_key="chave-de-teste",
        max_retries=0,
        http_client=DefaultAsyncHttpxClient(transport=transport),
    )


def _message(**overrides: Any) -> dict[str, Any]:
    message: dict[str, Any] = {
        "id": "msg_01",
        "type": "message",
        "role": "assistant",
        "model": "claude-haiku-5-5",
        "content": [
            {"type": "thinking", "thinking": "", "signature": "abc"},
            {"type": "text", "text": "Vou regar."},
            {"type": "tool_use", "id": "toolu_01", "name": "propose", "input": {"action": "water"}},
        ],
        "stop_reason": "tool_use",
        "stop_sequence": None,
        "usage": {
            "input_tokens": 1040,
            "output_tokens": 86,
            "cache_read_input_tokens": 2100,
            "cache_creation_input_tokens": 0,
        },
    }
    message.update(overrides)
    return message


def _request(**overrides: Any) -> ModelRequest:
    fields: dict[str, Any] = {
        "model": "claude-haiku-5-5",
        "system": "Você é o Camps.",
        "messages": [{"role": "user", "content": "O que fazer agora?"}],
        "tools": [TOOL],
        "effort": "low",
        "max_tokens": 512,
    }
    fields.update(overrides)
    return ModelRequest(**fields)


async def test_pedido_vai_no_formato_da_api_e_a_resposta_volta_em_blocos() -> None:
    seen: dict[str, Any] = {}

    def handler(request: httpx2.Request) -> httpx2.Response:
        seen["url"] = str(request.url)
        seen["body"] = json.loads(request.content)
        seen["timeout"] = request.extensions.get("timeout")
        return httpx2.Response(200, json=_message(), headers={"request-id": "req_123"})

    model = AnthropicModel(_client(handler), clock=FakeWallClock())
    response = await model.complete(_request())

    assert seen["url"].endswith("/v1/messages")
    assert seen["timeout"]["read"] == 30.0  # 512 tokens: o mínimo
    body = seen["body"]
    assert body["model"] == "claude-haiku-5-5"
    assert body["system"] == "Você é o Camps."
    assert body["tool_choice"] == {"type": "auto", "disable_parallel_tool_use": True}
    assert body["tools"][0]["strict"] is True
    assert body["output_config"] == {"effort": "low"}
    assert body["thinking"] == {"type": "adaptive"}
    assert body["max_tokens"] == 512

    assert response.stop_reason == "tool_use"
    assert response.model == "claude-haiku-5-5"
    assert response.request_id == "req_123"
    assert response.text() == "Vou regar."
    assert response.tool_uses() == [
        {"type": "tool_use", "id": "toolu_01", "name": "propose", "input": {"action": "water"}}
    ]
    assert response.usage.as_dict() == {
        "input_tokens": 1040,
        "output_tokens": 86,
        "cache_read_input_tokens": 2100,
        "cache_creation_input_tokens": 0,
    }
    assert response.replayed is False


async def test_sem_ferramentas_nem_esforco_o_pedido_nao_os_leva() -> None:
    seen: dict[str, Any] = {}

    def handler(request: httpx2.Request) -> httpx2.Response:
        seen["body"] = json.loads(request.content)
        return httpx2.Response(200, json=_message(stop_reason="end_turn"))

    model = AnthropicModel(_client(handler), clock=FakeWallClock())
    response = await model.complete(_request(tools=(), effort=None, system=None))
    assert "tools" not in seen["body"]
    assert "tool_choice" not in seen["body"]
    assert "output_config" not in seen["body"]
    assert "system" not in seen["body"]
    assert response.stop_reason == "end_turn"
    assert response.request_id is None


async def test_recusa_passa_adiante_como_motivo_de_parada() -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(
            200,
            json=_message(
                content=[],
                stop_reason="refusal",
                stop_details={"type": "refusal", "category": "cyber", "explanation": "..."},
            ),
        )

    model = AnthropicModel(_client(handler), clock=FakeWallClock())
    response = await model.complete(_request())
    assert response.stop_reason == "refusal"
    assert response.content == []


@pytest.mark.parametrize(
    ("status", "error_type", "kind", "retryable"),
    [
        (429, "rate_limit_error", "rate_limit", True),
        (500, "api_error", "server", True),
        (529, "overloaded_error", "server", True),
        (400, "invalid_request_error", "bad_request", False),
        (404, "not_found_error", "bad_request", False),
        (401, "authentication_error", "auth", False),
        (403, "permission_error", "auth", False),
    ],
)
async def test_erros_http_viram_erro_classificado(
    status: int, error_type: str, kind: str, retryable: bool
) -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(
            status, json={"type": "error", "error": {"type": error_type, "message": "nope"}}
        )

    model = AnthropicModel(_client(handler), clock=FakeWallClock())
    with pytest.raises(ModelCallError) as caught:
        await model.complete(_request())
    assert (caught.value.kind, caught.value.retryable) == (kind, retryable)


async def test_tempo_esgotado_e_falha_de_conexao() -> None:
    def slow(request: httpx2.Request) -> httpx2.Response:
        raise httpx2.ReadTimeout("demorou", request=request)

    def down(request: httpx2.Request) -> httpx2.Response:
        raise httpx2.ConnectError("sem rede", request=request)

    with pytest.raises(ModelCallError) as timeout:
        await AnthropicModel(_client(slow), clock=FakeWallClock()).complete(_request())
    assert (timeout.value.kind, timeout.value.retryable) == ("timeout", True)
    with pytest.raises(ModelCallError) as connection:
        await AnthropicModel(_client(down), clock=FakeWallClock()).complete(_request())
    assert (connection.value.kind, connection.value.retryable) == ("connection", True)


def test_o_tempo_limite_cresce_com_o_max_tokens() -> None:
    """A reflexão com 8 mil tokens de saída leva mais de 30 s (ADR-0060); cada tentativa cortada
    é cobrada, então o limite acompanha o pedido: um centésimo de segundo por token."""

    def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(500)

    model = AnthropicModel(_client(handler), clock=FakeWallClock())
    assert model.timeout_for(_request(max_tokens=512)) == 30.0
    assert model.timeout_for(_request(max_tokens=8192)) == 81.92
    assert model.timeout_for(_request(max_tokens=3000)) == 30.0


async def test_fechar_o_cliente_e_idempotente() -> None:
    """A arena fecha a porta ao fim de cada corrida (ADR-0061); fechar duas vezes não quebra."""

    def handler(request: httpx2.Request) -> httpx2.Response:  # pragma: no cover - nunca chamado
        raise AssertionError("não devia chamar a API")

    model = AnthropicModel(_client(handler), clock=FakeWallClock())
    await model.aclose()
    await model.aclose()


# ------------------------------------------------------------- o conselheiro (ADR-0074)

ADVISOR: dict[str, Any] = {
    "type": "advisor_20260301",
    "name": "advisor",
    "model": "claude-opus-4-8",
    "max_uses": 1,
    "max_tokens": 1024,
}
ASKED: dict[str, Any] = {
    "type": "server_tool_use",
    "id": "srvtoolu_01",
    "name": "advisor",
    "input": {},
}
ADVICE = {
    "type": "advisor_tool_result",
    "tool_use_id": "srvtoolu_01",
    "content": {"type": "advisor_result", "text": "Regue antes de colher."},
}
PROPOSED = {"type": "tool_use", "id": "toolu_01", "name": "propose", "input": {"action": "water"}}


def _iteration(kind: str, tokens_in: int, tokens_out: int, **extra: Any) -> dict[str, Any]:
    return {
        "type": kind,
        "input_tokens": tokens_in,
        "output_tokens": tokens_out,
        "cache_read_input_tokens": 0,
        "cache_creation_input_tokens": 0,
        **extra,
    }


async def test_o_conselheiro_vai_pela_api_beta_e_o_uso_dele_volta_a_parte() -> None:
    seen: dict[str, Any] = {}

    def handler(request: httpx2.Request) -> httpx2.Response:
        seen["url"] = str(request.url)
        seen["beta"] = request.headers.get("anthropic-beta")
        seen["body"] = json.loads(request.content)
        usage = {
            "input_tokens": 1760,
            "output_tokens": 531,
            "cache_read_input_tokens": 0,
            "cache_creation_input_tokens": 0,
            "iterations": [
                _iteration("message", 412, 89),
                _iteration("advisor_message", 823, 1612, model="claude-opus-4-8"),
                _iteration("message", 1348, 442),
            ],
        }
        return httpx2.Response(200, json=_message(content=[ASKED, ADVICE, PROPOSED], usage=usage))

    model = AnthropicModel(_client(handler), clock=FakeWallClock())
    response = await model.complete(_request(tools=[ADVISOR, TOOL]))
    assert "beta=true" in seen["url"]
    assert seen["beta"] == "advisor-tool-2026-03-01"
    assert seen["body"]["tools"][0] == ADVISOR
    assert response.content == [ASKED, ADVICE, PROPOSED]  # voltam sem mudança, para a janela
    assert response.usage == ModelUsage(1760, 531)  # só o de quem respondeu
    assert response.advisor == SubCall("claude-opus-4-8", 1, ModelUsage(823, 1612))
    assert response.tool_uses() == [PROPOSED]


async def test_sem_conselheiro_o_pedido_nao_vai_pela_beta() -> None:
    seen: dict[str, Any] = {}

    def handler(request: httpx2.Request) -> httpx2.Response:
        seen["url"] = str(request.url)
        seen["beta"] = request.headers.get("anthropic-beta")
        return httpx2.Response(200, json=_message())

    response = await AnthropicModel(_client(handler), clock=FakeWallClock()).complete(_request())
    assert seen["url"].endswith("/v1/messages")
    assert seen["beta"] is None
    assert response.advisor is None


async def test_o_pause_turn_e_retomado_com_a_resposta_como_veio() -> None:
    bodies: list[dict[str, Any]] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        bodies.append(json.loads(request.content))
        if len(bodies) == 1:
            usage = {"input_tokens": 400, "output_tokens": 30}
            return httpx2.Response(
                200, json=_message(content=[ASKED], stop_reason="pause_turn", usage=usage)
            )
        usage = {
            "input_tokens": 900,
            "output_tokens": 60,
            "iterations": [
                _iteration("advisor_message", 800, 300, model="claude-opus-4-8"),
                _iteration("message", 900, 60),
            ],
        }
        return httpx2.Response(200, json=_message(content=[ADVICE, PROPOSED], usage=usage))

    model = AnthropicModel(_client(handler), clock=FakeWallClock())
    response = await model.complete(_request(tools=[ADVISOR, TOOL]))
    assert len(bodies) == 2
    assert bodies[1]["messages"][:-1] == bodies[0]["messages"]
    assert bodies[1]["messages"][-1] == {"role": "assistant", "content": [ASKED]}
    assert bodies[1]["tools"] == bodies[0]["tools"]  # sem o conselheiro, a retomada daria 400
    assert response.content == [ASKED, ADVICE, PROPOSED]
    assert response.stop_reason == "tool_use"
    assert response.usage == ModelUsage(1300, 90)
    assert response.advisor == SubCall("claude-opus-4-8", 1, ModelUsage(800, 300))


async def test_a_conversa_com_blocos_do_conselheiro_vai_pela_beta() -> None:
    seen: dict[str, Any] = {}

    def handler(request: httpx2.Request) -> httpx2.Response:
        seen["beta"] = request.headers.get("anthropic-beta")
        return httpx2.Response(200, json=_message())

    history: list[dict[str, Any]] = [
        {"role": "user", "content": "O que fazer?"},
        {"role": "assistant", "content": [ASKED, ADVICE, PROPOSED]},
        {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "toolu_01"}]},
    ]
    await AnthropicModel(_client(handler), clock=FakeWallClock()).complete(
        _request(messages=history)
    )
    assert seen["beta"] == "advisor-tool-2026-03-01"
