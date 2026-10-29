"""O adaptador da OpenRouter sem rede: um transporte HTTP falso (ADR-0074, decisão 10)."""

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import httpx2
import pytest

from campsverso_adapters import (
    AnthropicModel,
    FakeWallClock,
    InMemoryBus,
    MeteredModel,
    ModelPrices,
    OpenRouterModel,
    RecordingModel,
    SequentialUuid7Ids,
    ValidatingBus,
    key_variable,
    model_port,
)
from campsverso_adapters.model_openrouter import chat_messages, response_blocks
from campsverso_ports import ModelCallError, ModelRequest

ASTRA = "openai/gpt-6-astra"
ROUTES = {ASTRA: "openai"}
CACHE = {"type": "ephemeral"}
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
DETAILS = [
    {
        "type": "reasoning.encrypted",
        "id": "rs_1",
        "format": "openai-responses-v1",
        "index": 0,
        "data": "gAAA",
    }
]


def _model(
    handler: Callable[[httpx2.Request], httpx2.Response],
    *,
    waits: list[float] | None = None,
    key: str | None = "chave-de-teste",
) -> OpenRouterModel:
    async def sleep(seconds: float) -> None:
        if waits is not None:
            waits.append(seconds)

    client = httpx2.AsyncClient(
        base_url="https://openrouter.test/api/v1", transport=httpx2.MockTransport(handler)
    )
    return OpenRouterModel(ROUTES, clock=FakeWallClock(), client=client, api_key=key, sleep=sleep)


def _answer(**overrides: Any) -> dict[str, Any]:
    answer: dict[str, Any] = {
        "id": "gen-123",
        "provider": "OpenAI",
        "model": ASTRA,
        "object": "chat.completion",
        "choices": [
            {
                "index": 0,
                "finish_reason": "tool_calls",
                "native_finish_reason": "completed",
                "message": {
                    "role": "assistant",
                    "content": "Vou regar.",
                    "reasoning": "O canteiro está seco.",
                    "reasoning_details": DETAILS,
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "type": "function",
                            "function": {"name": "propose", "arguments": '{"action": "water"}'},
                        }
                    ],
                },
            }
        ],
        "usage": {
            "prompt_tokens": 4300,
            "completion_tokens": 142,
            "total_tokens": 4442,
            "prompt_tokens_details": {"cached_tokens": 3072, "cache_write_tokens": 0},
            "completion_tokens_details": {"reasoning_tokens": 96},
            "cost": 0.022002,
        },
    }
    answer.update(overrides)
    return answer


def _request(**overrides: Any) -> ModelRequest:
    fields: dict[str, Any] = {
        "model": ASTRA,
        "system": [{"type": "text", "text": "Você é o Camps.", "cache_control": CACHE}],
        "messages": [{"role": "user", "content": "O que fazer agora?"}],
        "tools": [TOOL],
        "effort": "low",
        "max_tokens": 512,
    }
    fields.update(overrides)
    return ModelRequest(**fields)


async def test_o_pedido_vai_no_formato_de_chat_com_o_provedor_fixo() -> None:
    seen: dict[str, Any] = {}

    def handler(request: httpx2.Request) -> httpx2.Response:
        seen["url"] = str(request.url)
        seen["auth"] = request.headers["authorization"]
        seen["body"] = json.loads(request.content)
        return httpx2.Response(200, json=_answer())

    response = await _model(handler).complete(_request())
    assert seen["url"] == "https://openrouter.test/api/v1/chat/completions"
    assert seen["auth"] == "Bearer chave-de-teste"
    body = seen["body"]
    assert body["model"] == ASTRA
    assert body["provider"] == {"order": ["openai"], "allow_fallbacks": False}
    assert body["reasoning"] == {"effort": "low"}
    assert (body["max_tokens"], body["tool_choice"], body["parallel_tool_calls"]) == (
        512,
        "auto",
        False,
    )
    assert body["tools"] == [
        {
            "type": "function",
            "function": {
                "name": "propose",
                "description": "Propõe a próxima ação.",
                "parameters": TOOL["input_schema"],
                "strict": True,
            },
        }
    ]
    assert body["messages"] == [
        {
            "role": "system",
            "content": [{"type": "text", "text": "Você é o Camps.", "cache_control": CACHE}],
        },
        {"role": "user", "content": "O que fazer agora?"},
    ]
    # A resposta volta em blocos: o raciocínio como veio, o texto e a chamada.
    assert response.content == [
        {"type": "reasoning", "details": DETAILS, "text": "O canteiro está seco."},
        {"type": "text", "text": "Vou regar."},
        {
            "type": "tool_use",
            "id": "call_1",
            "name": "propose",
            "input": {"action": "water"},
            "arguments": '{"action": "water"}',
        },
    ]
    assert response.tool_uses()[0]["input"] == {"action": "water"}
    assert (response.stop_reason, response.model, response.request_id) == (
        "tool_use",
        ASTRA,
        "gen-123",
    )
    assert response.served_by == "OpenAI"
    # No chat, o cache está dentro do prompt; na porta, a entrada é o que sobra.
    assert (response.usage.input_tokens, response.usage.cache_read_input_tokens) == (1228, 3072)
    assert (response.usage.output_tokens, response.usage.cost_usd) == (142, 0.022002)


def test_a_conversa_volta_ao_chat_sem_mudanca() -> None:
    """O turno respondido volta como veio: os argumentos escritos e o raciocínio inteiro; os
    resultados viram mensagens `tool`, e o texto do usuário, com o marcador, vem depois."""
    answered = response_blocks(_answer()["choices"][0]["message"])
    request = _request(
        messages=[
            {"role": "user", "content": [{"type": "text", "text": "Manhã."}]},
            {"role": "assistant", "content": answered},
            {
                "role": "user",
                "content": [
                    {"type": "tool_result", "tool_use_id": "call_1", "content": "regou o canteiro"},
                    {
                        "type": "tool_result",
                        "tool_use_id": "call_2",
                        "content": "ignorada",
                        "is_error": True,
                    },
                    {"type": "text", "text": "Meio-dia.", "cache_control": CACHE},
                ],
            },
        ]
    )
    assert chat_messages(request)[1:] == [
        {"role": "user", "content": [{"type": "text", "text": "Manhã."}]},
        {
            "role": "assistant",
            "content": "Vou regar.",
            "tool_calls": [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {"name": "propose", "arguments": '{"action": "water"}'},
                }
            ],
            "reasoning_details": DETAILS,
        },
        {"role": "tool", "tool_call_id": "call_1", "content": "regou o canteiro"},
        {"role": "tool", "tool_call_id": "call_2", "content": "(erro) ignorada"},
        {
            "role": "user",
            "content": [{"type": "text", "text": "Meio-dia.", "cache_control": CACHE}],
        },
    ]
    # Uma resposta só com a chamada: o conteúdo vai nulo, e o raciocínio em texto, sem detalhes.
    bare: list[dict[str, Any]] = [
        {"type": "reasoning", "details": [], "text": "pensei"},
        {"type": "tool_use", "id": "c", "name": "propose", "input": {"action": "eat"}},
    ]
    assert chat_messages(
        _request(system=None, messages=[{"role": "assistant", "content": bare}])
    ) == [
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "c",
                    "type": "function",
                    "function": {"name": "propose", "arguments": '{"action": "eat"}'},
                }
            ],
            "reasoning": "pensei",
        }
    ]


def test_argumentos_que_nao_sao_json_viram_entrada_vazia() -> None:
    message = {
        "content": None,
        "tool_calls": [{"id": "c", "function": {"name": "propose", "arguments": "{quebrado"}}],
    }
    (block,) = response_blocks(message)
    assert (block["input"], block["arguments"]) == ({}, "{quebrado")


async def test_sem_rota_sem_chave_ou_com_o_conselheiro_nada_sai() -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        raise AssertionError("não devia chamar")

    with pytest.raises(ModelCallError) as caught:
        await _model(handler).complete(_request(model="openai/outro"))
    assert (caught.value.kind, caught.value.retryable) == ("bad_request", False)
    advisor = {"type": "advisor_20260301", "name": "advisor", "model": "claude-opus-4-8"}
    with pytest.raises(ModelCallError) as caught:
        await _model(handler).complete(_request(tools=[advisor]))
    assert caught.value.kind == "bad_request"
    with pytest.raises(ModelCallError) as caught:
        await _model(handler, key="").complete(_request())
    assert (caught.value.kind, caught.value.retryable) == ("auth", False)
    with pytest.raises(ModelCallError) as caught:
        await _model(handler).count_tokens(_request())
    assert caught.value.kind == "bad_request"


async def test_os_erros_sao_classificados_e_os_passageiros_repetidos() -> None:
    calls: list[int] = []
    waits: list[float] = []

    def busy(request: httpx2.Request) -> httpx2.Response:
        calls.append(1)
        if len(calls) == 1:
            return httpx2.Response(
                429,
                json={"error": {"code": 429, "message": "devagar"}},
                headers={"retry-after": "3"},
            )
        return httpx2.Response(200, json=_answer())

    response = await _model(busy, waits=waits).complete(_request())
    assert (len(calls), waits, response.served_by) == (2, [3.0], "OpenAI")

    def status(code: int, message: str = "falhou") -> Callable[[httpx2.Request], httpx2.Response]:
        def handler(request: httpx2.Request) -> httpx2.Response:
            calls.append(code)
            return httpx2.Response(
                code,
                json={
                    "error": {
                        "code": code,
                        "message": message,
                        "metadata": {"provider_name": "OpenAI"},
                    }
                },
            )

        return handler

    for code, kind, attempts in [
        (400, "bad_request", 1),
        (401, "auth", 1),
        (402, "auth", 1),  # sem créditos
        (403, "auth", 1),
        (408, "timeout", 3),
        (502, "server", 3),
        (503, "server", 3),
    ]:
        calls.clear()
        waits.clear()
        with pytest.raises(ModelCallError) as caught:
            await _model(status(code), waits=waits).complete(_request())
        assert (caught.value.kind, len(calls)) == (kind, attempts), code
        assert caught.value.message == "falhou (OpenAI)"
        assert waits == [0.5, 1.0][: attempts - 1]

    def slow(request: httpx2.Request) -> httpx2.Response:
        raise httpx2.ReadTimeout("lento", request=request)

    def down(request: httpx2.Request) -> httpx2.Response:
        raise httpx2.ConnectError("fora do ar", request=request)

    for handler, kind in [(slow, "timeout"), (down, "connection")]:
        with pytest.raises(ModelCallError) as caught:
            await _model(handler).complete(_request())
        assert (caught.value.kind, caught.value.retryable) == (kind, True)


async def test_o_erro_que_chega_num_200_tambem_e_erro() -> None:
    def midway(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(200, json={"error": {"code": 502, "message": "caiu no meio"}})

    def choice(request: httpx2.Request) -> httpx2.Response:
        failed = _answer()
        failed["choices"][0]["finish_reason"] = "error"
        return httpx2.Response(200, json=failed)

    for handler in (midway, choice):
        with pytest.raises(ModelCallError) as caught:
            await _model(handler, waits=[]).complete(_request())
        assert caught.value.kind == "server"


async def test_parada_por_tamanho_e_por_filtro() -> None:
    def cut(request: httpx2.Request) -> httpx2.Response:
        answer = _answer()
        answer["choices"][0] = {
            "finish_reason": "length",
            "message": {"role": "assistant", "content": "Vou"},
        }
        return httpx2.Response(200, json=answer)

    def filtered(request: httpx2.Request) -> httpx2.Response:
        answer = _answer()
        answer["choices"][0] = {
            "finish_reason": "content_filter",
            "message": {"role": "assistant", "content": None},
        }
        return httpx2.Response(200, json=answer)

    assert (await _model(cut).complete(_request())).stop_reason == "max_tokens"
    refused = await _model(filtered).complete(_request())
    assert (refused.stop_reason, refused.content) == ("refusal", [])


async def test_o_medidor_usa_o_custo_da_resposta_e_grava_quem_atendeu(tmp_path: Path) -> None:
    """O custo da resposta vale no lugar da tabela; o evento leva quem atendeu e o modelo que a
    resposta disse ser, e a fita guarda os dois para a reprodução."""

    def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(200, json=_answer(model="openai/gpt-6-astra-2026-09"))

    inner_bus = InMemoryBus()
    tape = tmp_path / "fita.jsonl"
    metered = MeteredModel(
        RecordingModel(_model(handler), tape, "record", clock=FakeWallClock()),
        bus=ValidatingBus(inner_bus),
        worldid="farm-morada-do-sol-01",
        cartridge="farm_morada_do_sol",
        controller={"type": "llm", "id": "llm/camps"},
        prices={ASTRA: ModelPrices(10.0, 50.0, 1.0, 12.5)},
        clock=FakeWallClock(),
        ids=SequentialUuid7Ids(),
    )
    await metered.complete(_request(avatar_id="camps"))
    ((_, envelope),) = inner_bus.published  # o barramento valida os campos novos pelo contrato
    data = envelope["data"]
    assert (data["provider"], data["served_by"], data["response_model"]) == (
        "openrouter",
        "OpenAI",
        "openai/gpt-6-astra-2026-09",
    )
    assert (data["cost_usd"], metered.spent_usd) == (0.022002, 0.022002)
    replayed = await RecordingModel(None, tape, "replay").complete(_request(avatar_id="camps"))
    assert (replayed.replayed, replayed.served_by, replayed.usage.cost_usd) == (
        True,
        "OpenAI",
        0.022002,
    )
    assert replayed.content == response_blocks(_answer()["choices"][0]["message"])


def test_cada_modelo_vai_para_quem_o_atende() -> None:
    clock = FakeWallClock()
    assert isinstance(model_port(ASTRA, routes=ROUTES, clock=clock), OpenRouterModel)
    assert isinstance(model_port("claude-haiku-5-5", routes=ROUTES, clock=clock), AnthropicModel)
    assert key_variable(ASTRA, ROUTES) == "OPENROUTER_API_KEY"
    assert key_variable("claude-haiku-5-5", ROUTES) == "ANTHROPIC_API_KEY"
