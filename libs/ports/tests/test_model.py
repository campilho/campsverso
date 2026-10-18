"""A porta de modelo: o hash do pedido ignora metadados e a ordem das chaves (ADR-0058)."""

from campsverso_ports import ModelCallError, ModelRequest, ModelResponse, ModelUsage, request_sha256


def test_hash_do_pedido_ignora_metadados_e_ordem_das_chaves() -> None:
    a = ModelRequest(
        model="claude-haiku-5-5",
        messages=[{"role": "user", "content": "oi"}],
        tools=[{"name": "x", "input_schema": {"type": "object", "properties": {}}}],
        purpose="decision",
        avatar_id="camps",
    )
    b = ModelRequest(
        model="claude-haiku-5-5",
        messages=[{"content": "oi", "role": "user"}],
        tools=[{"input_schema": {"properties": {}, "type": "object"}, "name": "x"}],
        purpose="reflection",
        avatar_id=None,
    )
    assert request_sha256(a) == request_sha256(b)
    assert len(request_sha256(a)) == 64
    assert request_sha256(ModelRequest(model="claude-haiku-5-5", messages=[], effort="high")) != (
        request_sha256(ModelRequest(model="claude-haiku-5-5", messages=[]))
    )


def test_resposta_separa_texto_e_tool_use_e_erro_sabe_se_vale_repetir() -> None:
    response = ModelResponse(
        content=[
            {"type": "text", "text": "Vou "},
            {"type": "text", "text": "regar."},
            {"type": "tool_use", "id": "t1", "name": "propose", "input": {}},
        ],
        stop_reason="tool_use",
        usage=ModelUsage(10, 5),
        model="m",
        latency_ms=12,
    )
    assert response.text() == "Vou regar."
    assert [t["name"] for t in response.tool_uses()] == ["propose"]
    assert ModelCallError("rate_limit", "x").retryable is True
    assert ModelCallError("bad_request", "x").retryable is False
    assert ModelCallError("server", "x", retryable=False).retryable is False
