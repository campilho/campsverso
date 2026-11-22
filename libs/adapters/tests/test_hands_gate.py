"""A porta das mãos (ADR-0089, decisão 7): a chave da sessão, a chave de verdade só na chamada de
fora, a medida, a recusa acima do teto e a fita."""

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import httpx2
import pytest

from campsverso_adapters.hands_gate import HandsGate, Tape, UsageReader, sse_of
from campsverso_adapters.model_fake_http import FakeModel, text, use
from campsverso_ports import ModelRequest, ModelResponse

KEY = "chave-de-verdade"
PRICES = {"claude-opus-5-5": (4.0, 20.0)}


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


def _gate(fake: FakeModel, meter: Meter, **kwargs: Any) -> HandsGate:
    return HandsGate(
        meter,
        api_key=KEY,
        harness="claude_code",
        avatar_id="camps",
        ticket_id="pedido-7",
        transport=httpx2.ASGITransport(app=fake.app()),
        upstream="http://modelo-falso",
        **kwargs,
    )


def _body(stream: bool = True, model: str = "claude-opus-5-5") -> dict[str, Any]:
    return {
        "model": model,
        "max_tokens": 1024,
        "stream": stream,
        "system": [{"type": "text", "text": "você é o dev"}],
        "messages": [{"role": "user", "content": [{"type": "text", "text": "oi"}]}],
        "tools": [{"name": "Read", "input_schema": {"type": "object"}}],
    }


async def _post(
    gate: HandsGate, body: Mapping[str, Any], token: str | None = None
) -> httpx2.Response:
    async with httpx2.AsyncClient(base_url=gate.url, timeout=10) as client:
        return await client.post(
            "/v1/messages?beta=true",
            content=json.dumps(body),
            headers={
                "x-api-key": gate.token if token is None else token,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
        )


async def test_sem_a_chave_da_sessao_a_porta_recusa_e_nao_chama_o_modelo() -> None:
    fake, meter = FakeModel([text("ok")]), Meter()
    async with _gate(fake, meter) as gate:
        response = await _post(gate, _body(), token=KEY)
    assert response.status_code == 401
    assert fake.seen == []
    assert meter.calls == []


async def test_a_chamada_em_streaming_passa_com_a_chave_de_verdade_e_e_medida() -> None:
    fake, meter = FakeModel([use("Read", file_path="a.py")]), Meter()
    async with _gate(fake, meter) as gate:
        response = await _post(gate, _body())
        cost = gate.cost_usd
    assert response.status_code == 200
    assert b"tool_use" in response.content
    assert b"message_stop" in response.content
    # A chave de verdade só na chamada de fora; a da sessão nunca sai da porta.
    (seen,) = fake.seen
    assert seen["headers"]["x-api-key"] == KEY
    assert seen["headers"]["anthropic-version"] == "2023-06-01"
    assert seen["body"]["messages"][0]["content"][0]["text"] == "oi"
    (request, measured, harness) = meter.calls[0]
    assert harness == "claude_code"
    assert (request.purpose, request.avatar_id, request.ticket_id) == (
        "workshop",
        "camps",
        "pedido-7",
    )
    assert (measured.usage.input_tokens, measured.usage.output_tokens) == (1000, 50)
    assert measured.stop_reason == "tool_use"
    assert not measured.replayed
    assert cost == pytest.approx((1000 * 4 + 50 * 20) / 1_000_000)


async def test_a_chamada_sem_streaming_tambem_e_medida() -> None:
    fake, meter = FakeModel([text("pronto")]), Meter()
    async with _gate(fake, meter) as gate:
        response = await _post(gate, _body(stream=False))
    assert response.json()["content"][0]["text"] == "pronto"
    assert meter.calls[0][1].stop_reason == "end_turn"


async def test_acima_do_teto_a_porta_recusa_com_403_sem_chamar_o_modelo() -> None:
    fake, meter = FakeModel([text("ok")]), Meter()
    async with _gate(fake, meter, refuse=lambda: "o teto do pedido") as gate:
        response = await _post(gate, _body())
        refused = gate.refused
    assert response.status_code == 403
    assert "o teto do pedido" in response.json()["error"]["message"]
    assert refused == 1
    assert fake.seen == []


async def test_modelo_sem_preco_e_recusado_antes_de_gastar() -> None:
    fake, meter = FakeModel([text("ok")]), Meter()
    async with _gate(fake, meter) as gate:
        response = await _post(gate, _body(model="claude-desconhecido"))
    assert response.status_code == 400
    assert fake.seen == []


async def test_a_fita_grava_magra_e_responde_na_ordem_noutro_espaco(tmp_path: Path) -> None:
    path = tmp_path / "fita.jsonl"
    here, there = tmp_path / "espaco-1", tmp_path / "espaco-2"
    fake, meter = FakeModel([use("Read", file_path=f"{here}/a.py"), text("pronto")]), Meter()
    async with _gate(fake, meter, tape=Tape(path, "record", here)) as gate:
        await _post(gate, _body())
        second = await _post(gate, _body(stream=False))
    entries = [json.loads(line) for line in path.read_text().splitlines()]
    # Magra: os blocos, o motivo e os tokens, sem o streaming; o espaço vira um marcador.
    assert [e["message"]["stop_reason"] for e in entries] == ["tool_use", "end_turn"]
    assert entries[0]["message"]["content"][0]["input"] == {"file_path": "{espaco}/a.py"}
    assert entries[0]["tools"] is True
    assert str(tmp_path) not in path.read_text()

    offline, replay_meter = FakeModel([]), Meter()
    async with _gate(offline, replay_meter, tape=Tape(path, "replay", there)) as gate:
        again_first = await _post(gate, _body())
        again_second = await _post(gate, _body(stream=False))
        exhausted = await _post(gate, _body())
    assert offline.seen == []  # ninguém chamou o modelo
    reader = UsageReader()
    reader.feed(again_first.content)
    assert reader.content[0]["input"] == {"file_path": f"{there}/a.py"}  # o espaço de agora
    assert again_second.json()["content"] == second.json()["content"]
    assert exhausted.status_code == 400  # o harness não repete
    assert [r.replayed for _, r, _ in replay_meter.calls] == [True, True]
    assert replay_meter.calls[0][1].tool_uses()[0]["name"] == "Read"


def test_a_leitura_dos_tokens_junta_os_pedacos_do_streaming() -> None:
    reader = UsageReader()
    raw = (
        b'event: message_start\ndata: {"type":"message_start","message":{"id":"msg_1","model":"m",'
        b'"usage":{"input_tokens":3,"cache_read_input_tokens":900,"output_tokens":1}}}\n\n'
        b'event: message_delta\ndata: {"type":"message_delta","delta":{"stop_reason":"end_turn"},'
        b'"usage":{"output_tokens":42}}\n\n'
    )
    for i in range(0, len(raw), 7):  # em pedaços que cortam os eventos no meio
        reader.feed(raw[i : i + 7])
    assert reader.tokens.input_tokens == 3
    assert reader.tokens.cache_read_input_tokens == 900
    assert reader.tokens.output_tokens == 42
    assert (reader.model, reader.stop_reason, reader.request_id) == ("m", "end_turn", "msg_1")


def test_a_resposta_inteira_volta_igual_do_streaming_em_pedacos() -> None:
    message: dict[str, Any] = {
        "id": "msg_9",
        "model": "claude-opus-5-5",
        "content": [
            {"type": "thinking", "thinking": "vou ler o arquivo", "signature": "assinatura"},
            {"type": "text", "text": "Vou ler."},
            {"type": "tool_use", "id": "toolu_1", "name": "Read", "input": {"file_path": "á.py"}},
        ],
        "stop_reason": "tool_use",
        "usage": {"input_tokens": 10, "output_tokens": 7},
    }
    raw = sse_of(message)
    reader = UsageReader()
    for i in range(0, len(raw), 5):  # o JSON dos argumentos chega cortado em vários pedaços
        reader.feed(raw[i : i + 5])
    assert list(reader.content) == message["content"]
    assert reader.as_message()["usage"] == {"input_tokens": 10, "output_tokens": 7}
    assert reader.stop_reason == "tool_use"
