"""Um modelo falso da Messages API, por HTTP, para testar um harness de fora sem a API (ADR-0089).

Responde, na ordem, os passos de um roteiro: cada passo é um texto final ou o uso de uma ferramenta.
As chamadas auxiliares de um harness (sem ferramentas, como dar título a uma conversa) recebem um
texto curto e não gastam o roteiro. Serve em processo, pelo transporte ASGI do `httpx2`, atrás da
porta das mãos: o harness fala com a porta, e a porta, com o falso.
"""

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, cast

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

USAGE = {
    "input_tokens": 1000,
    "output_tokens": 50,
    "cache_read_input_tokens": 0,
    "cache_creation_input_tokens": 0,
}


def text(value: str) -> dict[str, Any]:
    """Um passo do roteiro: a resposta final, em texto."""
    return {"text": value}


def use(tool: str, **given: Any) -> dict[str, Any]:
    """Um passo do roteiro: o modelo usa uma ferramenta com estes argumentos."""
    return {"tool": tool, "input": given}


def _sse(event: str, data: Mapping[str, Any]) -> bytes:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n".encode()


@dataclass
class FakeModel:
    """O falso, com o roteiro e o que ele viu: cada pedido, os cabeçalhos e as ferramentas."""

    script: Sequence[Mapping[str, Any]]
    usage: Mapping[str, int] = field(default_factory=lambda: dict(USAGE))
    seen: list[dict[str, Any]] = field(default_factory=list[dict[str, Any]])
    _next: int = 0

    def _step(self, body: Mapping[str, Any]) -> Mapping[str, Any]:
        if not body.get("tools"):
            return text("ok")
        if self._next >= len(self.script):
            return text("fim do roteiro")
        step = self.script[self._next]
        self._next += 1
        return step

    @property
    def used(self) -> int:
        """Quantos passos do roteiro já foram."""
        return self._next

    async def _messages(self, request: Request) -> Response:
        body = cast(dict[str, Any], json.loads(await request.body() or b"{}"))
        self.seen.append({"path": request.url.path, "headers": dict(request.headers), "body": body})
        if request.url.path.endswith("/count_tokens"):
            return JSONResponse({"input_tokens": 100})
        step = self._step(body)
        model = str(body.get("model") or "x")
        if "tool" in step:
            block: dict[str, Any] = {
                "type": "tool_use",
                "id": f"toolu_{len(self.seen):04d}",
                "name": step["tool"],
                "input": step["input"],
            }
            stop = "tool_use"
        else:
            block = {"type": "text", "text": step["text"]}
            stop = "end_turn"
        if not body.get("stream"):
            return JSONResponse(
                {
                    "id": f"msg_{len(self.seen):04d}",
                    "type": "message",
                    "role": "assistant",
                    "model": model,
                    "content": [block],
                    "stop_reason": stop,
                    "stop_sequence": None,
                    "usage": dict(self.usage),
                }
            )
        start: dict[str, Any] = {
            "id": f"msg_{len(self.seen):04d}",
            "type": "message",
            "role": "assistant",
            "model": model,
            "content": [],
            "stop_reason": None,
            "stop_sequence": None,
            "usage": {**self.usage, "output_tokens": 1},
        }
        out = _sse("message_start", {"type": "message_start", "message": start})
        if block["type"] == "text":
            opening: dict[str, Any] = {"type": "text", "text": ""}
            delta: dict[str, Any] = {"type": "text_delta", "text": block["text"]}
        else:
            opening = {"type": "tool_use", "id": block["id"], "name": block["name"], "input": {}}
            delta = {"type": "input_json_delta", "partial_json": json.dumps(block["input"])}
        out += _sse(
            "content_block_start",
            {"type": "content_block_start", "index": 0, "content_block": opening},
        )
        out += _sse(
            "content_block_delta", {"type": "content_block_delta", "index": 0, "delta": delta}
        )
        out += _sse("content_block_stop", {"type": "content_block_stop", "index": 0})
        out += _sse(
            "message_delta",
            {
                "type": "message_delta",
                "delta": {"stop_reason": stop, "stop_sequence": None},
                "usage": {"output_tokens": self.usage["output_tokens"]},
            },
        )
        out += _sse("message_stop", {"type": "message_stop"})
        return Response(out, media_type="text/event-stream")

    def app(self) -> Starlette:
        return Starlette(routes=[Route("/v1/{rest:path}", self._messages, methods=["POST"])])
