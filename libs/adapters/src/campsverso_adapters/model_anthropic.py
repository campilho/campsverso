"""Adaptador da ModelPort para a API da Anthropic, pelo SDK oficial (ADR-0058).

Só este módulo (e o main.py de quem o compõe) importa o SDK. O adaptador não publica evento nem
calcula custo: isso é do decorador MeteredModel. Erros do SDK viram ModelCallError classificado;
as retentativas de 429 e 5xx são as do próprio SDK.

O conselheiro (ADR-0074) é uma ferramenta do servidor, no beta `advisor-tool-2026-03-01`: um
pedido com ele (ou com blocos dele na conversa) vai pela API beta. O uso do conselheiro vem fora
do `usage` de quem respondeu, em `usage.iterations`, e volta somado em `ModelResponse.advisor`. Uma
resposta `pause_turn` (o servidor parou no meio de uma consulta) é retomada aqui mesmo: a resposta
volta, sem mudança, como a mensagem do assistente, e a continuação se junta a ela.
"""

from collections.abc import Mapping
from typing import Any, cast

import anthropic
from anthropic.types import Message

from campsverso_ports import (
    ModelCallError,
    ModelCapabilities,
    ModelRequest,
    ModelResponse,
    ModelUsage,
    SubCall,
    WallClock,
)

DEFAULT_TIMEOUT_SECONDS = 30.0
SECONDS_PER_TOKEN = 0.01  # uns 100 tokens por segundo; o Haiku faz 200 e sobra folga
ADVISOR_BETA = "advisor-tool-2026-03-01"
ADVISOR_BLOCKS = frozenset({"advisor_tool_result"})
MAX_PAUSES = 3  # retomadas de um pause_turn numa chamada


def _betas(request: ModelRequest) -> list[str]:
    """O beta do conselheiro, quando o pedido o oferece ou a conversa já tem blocos dele."""
    if any(str(t.get("type", "")).startswith("advisor_") for t in request.tools):
        return [ADVISOR_BETA]
    for message in request.messages:
        content = message.get("content")
        if isinstance(content, list):
            blocks = cast(list[Mapping[str, Any]], content)
            if any(b.get("type") in ADVISOR_BLOCKS for b in blocks):
                return [ADVISOR_BETA]
    return []


def _plus(total: ModelUsage, used: Any) -> ModelUsage:
    """Soma o uso de uma resposta (ou de uma iteração do conselheiro) ao que já havia."""
    return ModelUsage(
        input_tokens=total.input_tokens + int(used.input_tokens or 0),
        output_tokens=total.output_tokens + int(used.output_tokens or 0),
        cache_read_input_tokens=total.cache_read_input_tokens
        + int(used.cache_read_input_tokens or 0),
        cache_creation_input_tokens=total.cache_creation_input_tokens
        + int(used.cache_creation_input_tokens or 0),
    )


def _advised(found: SubCall | None, usage: Any) -> SubCall | None:
    """As iterações do conselheiro numa resposta, somadas às de antes (as de um pause_turn)."""
    for item in cast(list[Any], getattr(usage, "iterations", None) or []):
        if getattr(item, "type", None) != "advisor_message":
            continue
        before = found or SubCall(str(item.model), 0, ModelUsage(0, 0))
        found = SubCall(before.model, before.calls + 1, _plus(before.usage, item))
    return found


class AnthropicModel:
    provider = "anthropic"

    def __init__(
        self,
        client: anthropic.AsyncAnthropic | None = None,
        *,
        clock: WallClock,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        max_retries: int = 2,
    ) -> None:
        # Sem cliente, o SDK resolve a chave pelo ambiente (ANTHROPIC_API_KEY, do .env).
        self._client = client or anthropic.AsyncAnthropic(
            timeout=timeout_seconds, max_retries=max_retries
        )
        self._clock = clock
        self._timeout_seconds = timeout_seconds

    async def aclose(self) -> None:
        """Fecha o cliente HTTP enquanto o laço ainda existe. Quem roda várias corridas no mesmo
        processo, cada uma no seu `asyncio.run` (a arena, ADR-0061), precisa disto: um cliente
        recolhido pelo coletor de lixo depois tenta fechar o transporte num laço já fechado."""
        await self._client.close()

    def timeout_for(self, request: ModelRequest) -> float:
        """O tempo limite cresce com o que se pede: um centésimo de segundo por token de saída
        (a reflexão com 8 mil tokens leva mais de 30 s; cada tentativa cortada é cobrada)."""
        return max(self._timeout_seconds, request.max_tokens * SECONDS_PER_TOKEN)

    def capabilities(self) -> ModelCapabilities:
        return ModelCapabilities(
            tool_use=True, prompt_cache=True, batch=False, max_context_tokens=1_000_000
        )

    async def complete(self, request: ModelRequest) -> ModelResponse:
        params: dict[str, Any] = {
            "model": request.model,
            "max_tokens": request.max_tokens,
            "messages": [dict(m) for m in request.messages],
            # Raciocínio adaptativo, o padrão dos modelos atuais; a profundidade vai por `effort`.
            "thinking": {"type": "adaptive"},
        }
        if request.system is not None:
            params["system"] = (
                request.system if isinstance(request.system, str) else list(request.system)
            )
        if request.tools:
            params["tools"] = [dict(t) for t in request.tools]
            # O forçado é recusado nos modelos atuais; e uma ação por vez (ADR-0059).
            params["tool_choice"] = {"type": "auto", "disable_parallel_tool_use": True}
        if request.effort is not None:
            params["output_config"] = {"effort": request.effort}
        betas = _betas(request)
        started = self._clock.monotonic()
        content: list[Mapping[str, Any]] = []
        usage = ModelUsage(0, 0)
        advisor: SubCall | None = None
        raw: anthropic.AsyncAPIResponse[Any] | None = None
        message: Any = None
        for _ in range(MAX_PAUSES + 1):
            if content:  # a retomada de um pause_turn: a resposta volta como veio
                params["messages"] = [
                    *(dict(m) for m in request.messages),
                    {"role": "assistant", "content": [dict(b) for b in content]},
                ]
            raw = await self._create(params, betas, self.timeout_for(request))
            message = cast(Any, await raw.parse())
            content.extend(
                cast(Mapping[str, Any], block.to_dict(exclude_none=True))
                for block in message.content
            )
            usage = _plus(usage, message.usage)
            advisor = _advised(advisor, message.usage)
            if message.stop_reason != "pause_turn":
                break
        latency_ms = round((self._clock.monotonic() - started) * 1000)
        assert raw is not None
        return ModelResponse(
            content=content,
            stop_reason=str(message.stop_reason or "end_turn"),
            usage=usage,
            model=str(message.model),
            latency_ms=latency_ms,
            request_id=raw.headers.get("request-id"),
            advisor=advisor,
        )

    async def _create(
        self, params: Mapping[str, Any], betas: list[str], timeout: float
    ) -> anthropic.AsyncAPIResponse[Any]:
        """Uma chamada à API, a beta quando há conselheiro; os erros do SDK, classificados."""
        try:
            if betas:
                return cast(
                    anthropic.AsyncAPIResponse[Any],
                    await self._client.beta.messages.with_raw_response.create(
                        **params, betas=betas, timeout=timeout
                    ),
                )
            return cast(
                anthropic.AsyncAPIResponse[Message],
                await self._client.messages.with_raw_response.create(**params, timeout=timeout),
            )
        except anthropic.APITimeoutError as error:
            raise ModelCallError("timeout", str(error)) from error
        except anthropic.APIConnectionError as error:
            raise ModelCallError("connection", str(error)) from error
        except (anthropic.AuthenticationError, anthropic.PermissionDeniedError) as error:
            raise ModelCallError("auth", error.message) from error
        except anthropic.RateLimitError as error:
            raise ModelCallError("rate_limit", error.message) from error
        except anthropic.APIStatusError as error:
            kind = "server" if error.status_code >= 500 else "bad_request"
            raise ModelCallError(kind, error.message) from error

    async def count_tokens(self, request: ModelRequest) -> int:
        params: dict[str, Any] = {
            "model": request.model,
            "messages": [dict(m) for m in request.messages],
        }
        if request.system is not None:
            params["system"] = (
                request.system if isinstance(request.system, str) else list(request.system)
            )
        if request.tools:
            params["tools"] = [dict(t) for t in request.tools]
        try:
            counted = await self._client.messages.count_tokens(**params)
        except anthropic.APIStatusError as error:
            kind = "auth" if error.status_code in (401, 403) else "bad_request"
            raise ModelCallError(kind, error.message) from error
        except anthropic.APIConnectionError as error:
            raise ModelCallError("connection", str(error)) from error
        return int(counted.input_tokens)
