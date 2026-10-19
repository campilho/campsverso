"""O adaptador da Anthropic sem rede: um transporte HTTP falso do próprio SDK (ADR-0058)."""

import json
from collections.abc import Callable
from typing import Any

import httpx2
import pytest
from anthropic import AsyncAnthropic, DefaultAsyncHttpxClient

from campsverso_adapters import AnthropicModel, FakeWallClock
from campsverso_ports import ModelCallError, ModelRequest

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
        return httpx2.Response(200, json=_message(), headers={"request-id": "req_123"})

    model = AnthropicModel(_client(handler), clock=FakeWallClock())
    response = await model.complete(_request())

    assert seen["url"].endswith("/v1/messages")
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
