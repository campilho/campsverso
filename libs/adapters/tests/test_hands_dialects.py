"""As línguas de fora da porta das mãos (ADR-0093): a da OpenAI, que o Codex fala, e a do Gemini,
que o Antigravity fala. Contra um provedor falso de cada uma, sem rede: a chave da sessão na
entrada e a de verdade só na saída, a resposta repassada como veio, os tokens no sentido da
Anthropic, a recusa no formato de cada uma e a fita que devolve a resposta igual noutro espaço."""

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import httpx2
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route

from campsverso_adapters.hands_dialects import (
    GeminiDialect,
    GeminiReader,
    OpenAIDialect,
    ResponsesReader,
)
from campsverso_adapters.hands_gate import HandsGate, Tape
from campsverso_ports import ModelRequest, ModelResponse

KEY = "chave-de-verdade"
PRICES = {"openai/gpt-6.2-astra": (8.0, 40.0), "google/gemini-4-neon": (3.0, 15.0)}


class Meter:
    """O medidor dos testes: guarda o que a porta mediu e cobra pela tabela."""

    def __init__(self) -> None:
        self.calls: list[tuple[ModelRequest, ModelResponse, str]] = []

    def assert_priced(self, model: str) -> None:
        if model not in PRICES:
            raise LookupError(f"modelo sem preço na tabela do ambiente: {model}")

    async def observed(
        self, request: ModelRequest, response: ModelResponse, *, harness: str
    ) -> float:
        self.calls.append((request, response, harness))
        price_in, price_out = PRICES[request.model]
        usage = response.usage
        return (usage.input_tokens * price_in + usage.output_tokens * price_out) / 1_000_000


def _sse(events: Sequence[Mapping[str, Any]], named: bool = True) -> bytes:
    out = b""
    for event in events:
        head = f"event: {event['type']}\n" if named and "type" in event else ""
        out += f"{head}data: {json.dumps(event, ensure_ascii=False)}\n\n".encode()
    return out


class Upstream:
    """O provedor falso: guarda o que recebeu e devolve o que lhe deram."""

    def __init__(self, body: bytes, media: str = "text/event-stream") -> None:
        self.body = body
        self.media = media
        self.seen: list[tuple[str, str, dict[str, str]]] = []

    def app(self) -> Starlette:
        async def handle(request: Request) -> Response:
            self.seen.append((request.method, str(request.url), dict(request.headers)))
            return Response(self.body, media_type=self.media)

        return Starlette(routes=[Route("/{path:path}", handle, methods=["GET", "POST"])])


def _gate(upstream: Upstream, meter: Meter, dialect: Any, **kwargs: Any) -> HandsGate:
    return HandsGate(
        meter,
        api_key=KEY,
        harness=dialect.name,
        avatar_id="kenji",
        ticket_id="pedido-7",
        transport=httpx2.ASGITransport(app=upstream.app()),
        upstream="http://provedor-falso",
        dialect=dialect,
        **kwargs,
    )


# ------------------------------------------------------------------ a OpenAI (o Codex)

RESPONSE_EVENTS: list[Mapping[str, Any]] = [
    {
        "type": "response.created",
        "response": {"id": "resp_1", "model": "gpt-6.2-astra", "status": "in_progress"},
    },
    {
        "type": "response.output_item.done",
        "item": {
            "type": "message",
            "content": [{"type": "output_text", "text": "Vou ler o arquivo."}],
        },
    },
    {
        "type": "response.output_item.done",
        "item": {"type": "function_call", "name": "shell", "arguments": '{"command": ["ls"]}'},
    },
    {
        "type": "response.completed",
        "response": {
            "id": "resp_1",
            "model": "gpt-6.2-astra",
            "status": "completed",
            "usage": {
                "input_tokens": 1000,
                "input_tokens_details": {"cached_tokens": 400},
                "output_tokens": 200,
                "output_tokens_details": {"reasoning_tokens": 50},
            },
        },
    },
]


async def _responses(
    gate: HandsGate, token: str | None = None, stream: bool = True
) -> httpx2.Response:
    body = {
        "model": "gpt-6.2-astra",
        "stream": stream,
        "input": "oi",
        "instructions": "você é o dev",
        "tools": [{"type": "function", "name": "shell"}],
    }
    async with httpx2.AsyncClient(base_url=gate.url, timeout=10) as client:
        return await client.post(
            "/v1/responses",
            content=json.dumps(body),
            headers={
                "authorization": f"Bearer {gate.token if token is None else token}",
                "content-type": "application/json",
            },
        )


async def test_o_codex_chama_pela_porta_com_a_chave_da_sessao_e_a_de_verdade_so_sai_dela() -> None:
    raw = _sse(RESPONSE_EVENTS)
    upstream, meter = Upstream(raw), Meter()
    async with _gate(upstream, meter, OpenAIDialect()) as gate:
        reply = await _responses(gate)
    assert reply.status_code == 200
    assert reply.content == raw  # a resposta volta como veio
    ((method, url, headers),) = upstream.seen
    assert (method, url.endswith("/v1/responses")) == ("POST", True)
    assert headers["authorization"] == f"Bearer {KEY}"
    ((request, response, harness),) = meter.calls
    assert (request.model, harness, request.avatar_id, request.ticket_id) == (
        "openai/gpt-6.2-astra",
        "openai",
        "kenji",
        "pedido-7",
    )
    # A entrada sem o cache, o cache lido à parte, e a saída já com o raciocínio.
    assert (
        response.usage.input_tokens,
        response.usage.cache_read_input_tokens,
        response.usage.output_tokens,
    ) == (600, 400, 200)
    assert response.content == (
        {"type": "text", "text": "Vou ler o arquivo."},
        {"type": "tool_use", "name": "shell", "input": {"command": ["ls"]}},
    )
    assert gate.cost_usd > 0


async def test_sem_a_chave_da_sessao_ou_acima_do_teto_a_porta_recusa_no_formato_da_openai() -> None:
    upstream, meter = Upstream(_sse(RESPONSE_EVENTS)), Meter()
    async with _gate(
        upstream, meter, OpenAIDialect(), refuse=lambda: "o teto do pedido estourou"
    ) as gate:
        wrong = await _responses(gate, token="sk-qualquer")
        refused = await _responses(gate)
    assert wrong.status_code == 401
    assert wrong.json()["error"]["code"] == "invalid_api_key"
    assert refused.status_code == 403
    assert "o teto do pedido estourou" in refused.json()["error"]["message"]
    assert upstream.seen == []
    assert meter.calls == []


async def test_a_lista_dos_modelos_passa_sem_custo() -> None:
    upstream, meter = Upstream(b'{"object": "list", "data": []}', "application/json"), Meter()
    async with (
        _gate(upstream, meter, OpenAIDialect()) as gate,
        httpx2.AsyncClient(base_url=gate.url) as client,
    ):
        reply = await client.get("/v1/models", headers={"authorization": f"Bearer {gate.token}"})
    assert reply.status_code == 200
    assert upstream.seen[0][2]["authorization"] == f"Bearer {KEY}"
    assert meter.calls == []
    assert gate.calls == 0


def test_a_leitura_da_responses_junta_os_pedacos_do_streaming() -> None:
    reader = ResponsesReader()
    raw = _sse(RESPONSE_EVENTS)
    for i in range(0, len(raw), 7):
        reader.feed(raw[i : i + 7])
    reader.finish()
    assert (reader.model, reader.request_id, reader.stop_reason, reader.complete) == (
        "gpt-6.2-astra",
        "resp_1",
        "completed",
        True,
    )
    assert reader.tokens.input_tokens == 600


# ------------------------------------------------------------------ o Gemini (o Antigravity)

GEMINI_CHUNKS: list[Mapping[str, Any]] = [
    {
        "candidates": [
            {"content": {"role": "model", "parts": [{"text": "Pensando…", "thought": True}]}}
        ],
        "modelVersion": "gemini-4-neon",
        "responseId": "r1",
    },
    {"candidates": [{"content": {"role": "model", "parts": [{"text": "Vou ler o arquivo."}]}}]},
    {
        "candidates": [
            {
                "content": {
                    "role": "model",
                    "parts": [
                        {"functionCall": {"name": "read_file", "args": {"path": "README.md"}}}
                    ],
                },
                "finishReason": "STOP",
            }
        ],
        "usageMetadata": {
            "promptTokenCount": 1500,
            "cachedContentTokenCount": 500,
            "candidatesTokenCount": 150,
            "thoughtsTokenCount": 50,
            "totalTokenCount": 1700,
        },
    },
]


async def _gemini(
    gate: HandsGate, *, sse: bool = True, key_in_query: bool = True
) -> httpx2.Response:
    body = {
        "contents": [{"role": "user", "parts": [{"text": "oi"}]}],
        "systemInstruction": {"parts": [{"text": "você é o dev"}]},
        "tools": [{"functionDeclarations": [{"name": "read_file"}]}],
        "generationConfig": {"maxOutputTokens": 8192},
    }
    query = "&".join(
        part
        for part in ("alt=sse" if sse else "", f"key={gate.token}" if key_in_query else "")
        if part
    )
    headers = {
        "content-type": "application/json",
        **({} if key_in_query else {"x-goog-api-key": gate.token}),
    }
    async with httpx2.AsyncClient(base_url=gate.url, timeout=10) as client:
        return await client.post(
            f"/v1beta/models/gemini-4-neon:streamGenerateContent?{query}",
            content=json.dumps(body),
            headers=headers,
        )


async def test_o_antigravity_chama_pela_porta_e_a_chave_nunca_vai_na_url() -> None:
    raw = _sse(GEMINI_CHUNKS, named=False)
    upstream, meter = Upstream(raw), Meter()
    async with _gate(upstream, meter, GeminiDialect()) as gate:
        reply = await _gemini(gate)
    assert reply.status_code == 200
    assert reply.content == raw
    ((_, url, headers),) = upstream.seen
    assert "key=" not in url
    assert "alt=sse" in url
    assert headers["x-goog-api-key"] == KEY
    ((request, response, harness),) = meter.calls
    assert (request.model, harness, request.max_tokens) == ("google/gemini-4-neon", "gemini", 8192)
    # A entrada sem o cache; a saída é a dos candidatos mais a do pensamento.
    assert (
        response.usage.input_tokens,
        response.usage.cache_read_input_tokens,
        response.usage.output_tokens,
    ) == (1000, 500, 200)
    assert response.content == (
        {"type": "text", "text": "Vou ler o arquivo."},
        {"type": "tool_use", "name": "read_file", "input": {"path": "README.md"}},
    )
    assert response.stop_reason == "STOP"


async def test_o_streaming_do_gemini_sem_sse_vem_em_lista_e_tambem_e_medido() -> None:
    raw = json.dumps(GEMINI_CHUNKS).encode()
    upstream, meter = Upstream(raw, "application/json"), Meter()
    async with _gate(upstream, meter, GeminiDialect()) as gate:
        reply = await _gemini(gate, sse=False, key_in_query=False)
    assert reply.status_code == 200
    ((_, response, _),) = meter.calls
    assert response.usage.output_tokens == 200


async def test_a_recusa_do_gemini_vem_no_formato_dele_e_contar_os_tokens_passa_sem_custo() -> None:
    upstream, meter = Upstream(b'{"totalTokens": 12}', "application/json"), Meter()
    async with _gate(upstream, meter, GeminiDialect(), refuse=lambda: "o teto do dia") as gate:
        refused = await _gemini(gate)
        async with httpx2.AsyncClient(base_url=gate.url) as client:
            counted = await client.post(
                "/v1beta/models/gemini-4-neon:countTokens",
                content=b"{}",
                headers={"x-goog-api-key": gate.token},
            )
    assert refused.status_code == 403
    assert refused.json()["error"]["status"] == "PERMISSION_DENIED"
    assert counted.json() == {"totalTokens": 12}
    assert meter.calls == []


def test_a_leitura_do_gemini_junta_os_pedacos() -> None:
    reader = GeminiReader()
    raw = _sse(GEMINI_CHUNKS, named=False)
    for i in range(0, len(raw), 5):
        reader.feed(raw[i : i + 5])
    reader.finish()
    assert (reader.model, reader.request_id, reader.complete) == ("gemini-4-neon", "r1", True)
    assert reader.tokens.cache_read_input_tokens == 500


# ------------------------------------------------------------------ a fita


async def test_a_fita_grava_a_resposta_como_veio_e_a_devolve_igual_noutro_espaco(
    tmp_path: Path,
) -> None:
    space, elsewhere = tmp_path / "espaco-a", tmp_path / "espaco-b"
    space.mkdir()
    elsewhere.mkdir()
    events = [dict(e) for e in RESPONSE_EVENTS]
    events[1] = {
        "type": "response.output_item.done",
        "item": {
            "type": "message",
            "content": [{"type": "output_text", "text": f"li {space}/README.md"}],
        },
    }
    upstream, meter = Upstream(_sse(events)), Meter()
    tape_path = tmp_path / "fita.jsonl"
    async with _gate(
        upstream, meter, OpenAIDialect(), tape=Tape(tape_path, "record", space)
    ) as gate:
        await _responses(gate)
    entry = json.loads(tape_path.read_text())
    assert entry["model"] == "openai/gpt-6.2-astra"
    assert entry["stream"] is True
    assert str(space) not in entry["raw"]
    assert "{espaco}/README.md" in entry["raw"]
    # Na reprodução, noutro espaço e sem o provedor: a mesma resposta, com o espaço de agora.
    silent, replayed = Upstream(b""), Meter()
    async with _gate(
        silent, replayed, OpenAIDialect(), tape=Tape(tape_path, "replay", elsewhere)
    ) as gate:
        reply = await _responses(gate)
        over = await _responses(gate)
    assert silent.seen == []
    assert f"li {elsewhere}/README.md" in reply.text
    ((_, response, _),) = replayed.calls
    assert response.replayed
    assert response.usage.input_tokens == 600
    assert over.status_code == 400  # a fita acabou
