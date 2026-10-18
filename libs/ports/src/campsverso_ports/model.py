"""Porta de modelo (ADR-0058): uma chamada a um LLM, no formato de blocos da Messages API.

A porta não conhece provedor nem preço. Quem chama passa mensagens, ferramentas e o esforço, e
recebe blocos de conteúdo, o motivo da parada e os tokens. Quem registra a chamada como evento e
calcula o custo é um decorador da porta (`campsverso_adapters.MeteredModel`); quem paga é o
orçamento do mundo. O prompt nunca sai daqui: para fora vai só o hash do pedido.
"""

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Literal, Protocol

type Effort = Literal["low", "medium", "high", "xhigh", "max"]
type ErrorKind = Literal[
    "rate_limit", "timeout", "connection", "auth", "bad_request", "server", "cassette_miss"
]
RETRYABLE_ERRORS: frozenset[str] = frozenset({"rate_limit", "timeout", "connection", "server"})


@dataclass(frozen=True, slots=True)
class ModelRequest:
    """O pedido. `messages` e `tools` seguem a Messages API (blocos `text`, `tool_use`,
    `tool_result`, e ferramentas com `input_schema`); `system` pode levar marcadores de cache.
    `purpose` e `avatar_id` são metadados para o evento: não entram no hash do pedido."""

    model: str
    messages: Sequence[Mapping[str, Any]]
    system: str | Sequence[Mapping[str, Any]] | None = None
    tools: Sequence[Mapping[str, Any]] = ()
    max_tokens: int = 4096
    effort: Effort | None = None
    purpose: str = "decision"
    avatar_id: str | None = None


@dataclass(frozen=True, slots=True)
class ModelUsage:
    input_tokens: int
    output_tokens: int
    cache_read_input_tokens: int = 0
    cache_creation_input_tokens: int = 0

    def as_dict(self) -> dict[str, int]:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cache_read_input_tokens": self.cache_read_input_tokens,
            "cache_creation_input_tokens": self.cache_creation_input_tokens,
        }


@dataclass(frozen=True, slots=True)
class ModelResponse:
    content: Sequence[Mapping[str, Any]]  # blocos text, tool_use, thinking, como vieram
    stop_reason: str  # end_turn, tool_use, max_tokens, refusal…
    usage: ModelUsage
    model: str
    latency_ms: int
    request_id: str | None = None
    replayed: bool = False  # veio da fita: ninguém pagou

    def tool_uses(self) -> list[Mapping[str, Any]]:
        return [block for block in self.content if block.get("type") == "tool_use"]

    def text(self) -> str:
        return "".join(str(b.get("text", "")) for b in self.content if b.get("type") == "text")


@dataclass(frozen=True, slots=True)
class ModelCapabilities:
    tool_use: bool = True
    prompt_cache: bool = True
    batch: bool = False
    max_context_tokens: int = 200_000


class ModelCallError(Exception):
    """A chamada falhou, classificada: quem chama decide se repete; o evento leva o tipo."""

    def __init__(self, kind: ErrorKind, message: str, *, retryable: bool | None = None) -> None:
        super().__init__(message)
        self.kind: ErrorKind = kind
        self.message = message
        self.retryable = retryable if retryable is not None else kind in RETRYABLE_ERRORS


def canonical_request(request: ModelRequest) -> dict[str, Any]:
    """O pedido sem metadados: o que identifica uma chamada na fita e no evento."""
    return {
        "model": request.model,
        "system": request.system,
        "messages": [dict(m) for m in request.messages],
        "tools": [dict(t) for t in request.tools],
        "max_tokens": request.max_tokens,
        "effort": request.effort,
    }


def request_sha256(request: ModelRequest) -> str:
    canonical = json.dumps(
        canonical_request(request),
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(canonical.encode()).hexdigest()


class ModelPort(Protocol):
    @property
    def provider(self) -> str: ...

    def capabilities(self) -> ModelCapabilities: ...

    async def complete(self, request: ModelRequest) -> ModelResponse:
        """Uma chamada. Levanta ModelCallError classificado quando não há resposta."""
        ...
