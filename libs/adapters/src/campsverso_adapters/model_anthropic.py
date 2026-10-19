"""Adaptador da ModelPort para a API da Anthropic, pelo SDK oficial (ADR-0058).

Só este módulo (e o main.py de quem o compõe) importa o SDK. O adaptador não publica evento nem
calcula custo: isso é do decorador MeteredModel. Erros do SDK viram ModelCallError classificado;
as retentativas de 429 e 5xx são as do próprio SDK.
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
    WallClock,
)

DEFAULT_TIMEOUT_SECONDS = 30.0
SECONDS_PER_TOKEN = 0.01  # uns 100 tokens por segundo; o Haiku faz 200 e sobra folga


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
        started = self._clock.monotonic()
        try:
            raw = cast(
                anthropic.AsyncAPIResponse[Message],
                await self._client.messages.with_raw_response.create(
                    **params, timeout=self.timeout_for(request)
                ),
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
        latency_ms = round((self._clock.monotonic() - started) * 1000)
        message = await raw.parse()
        usage = message.usage
        content = [
            cast(Mapping[str, Any], block.to_dict(exclude_none=True)) for block in message.content
        ]
        return ModelResponse(
            content=content,
            stop_reason=str(message.stop_reason or "end_turn"),
            usage=ModelUsage(
                input_tokens=usage.input_tokens,
                output_tokens=usage.output_tokens,
                cache_read_input_tokens=usage.cache_read_input_tokens or 0,
                cache_creation_input_tokens=usage.cache_creation_input_tokens or 0,
            ),
            model=message.model,
            latency_ms=latency_ms,
            request_id=raw.headers.get("request-id"),
        )

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
