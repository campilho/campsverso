"""Adaptador da ModelPort para a OpenRouter (ADR-0074, decisão 10), por HTTP com o `httpx2`.

A OpenRouter é um roteador: uma conta, uma chave e o formato de chat da OpenAI para os modelos de
outros laboratórios (o GPT-6 Astra, o Gemini 4 Argon). Os Claude continuam no AnthropicModel.

- **A tradução** fica aqui, nos dois sentidos, e é parte do harness (entra na ficha): os blocos
  da Messages API viram mensagens de chat (o `tool_use` vira `tool_calls`; o `tool_result`, uma
  mensagem `tool`), e a resposta volta em blocos. O raciocínio volta num bloco `reasoning`, com
  os `reasoning_details` como vieram; a janela o devolve sem mudança, como a OpenRouter pede
  quando há ferramentas. O `tool_use` guarda os argumentos como o modelo os escreveu
  (`arguments`), e é esse texto que volta.
- **Os marcadores de cache** vão nas partes de texto (o sistema e o texto do usuário), onde o
  provedor os aceita; a mensagem `tool` é só texto e não leva marcador.
- **O provedor é fixo** em cada modelo (`provider.order` com um só, sem fallback), e um modelo
  sem rota é recusado antes de sair. Quem atendeu volta em `ModelResponse.served_by`.
- **O custo** vem da resposta (`usage.cost`, em dólares) e vai em `ModelUsage.cost_usd`; o
  medidor o usa no lugar da tabela.
- Os erros viram ModelCallError classificado como na Anthropic. Como o SDK de lá, o adaptador
  repete aqui mesmo, até duas vezes, o 408, o 429, os 5xx e as falhas de rede.
"""

import asyncio
import json
import os
from collections.abc import Awaitable, Callable, Mapping, Sequence
from typing import Any, cast

import httpx2

from campsverso_ports import (
    ErrorKind,
    ModelCallError,
    ModelCapabilities,
    ModelRequest,
    ModelResponse,
    ModelUsage,
    WallClock,
)

BASE_URL = "https://openrouter.ai/api/v1"
KEY_VARIABLE = "OPENROUTER_API_KEY"
DEFAULT_TIMEOUT_SECONDS = 60.0
SECONDS_PER_TOKEN = 0.01  # o mesmo tempo limite crescente do AnthropicModel
MAX_WAIT_SECONDS = 8.0  # a espera mais longa entre duas tentativas
STOP_REASONS = {
    "tool_calls": "tool_use",
    "stop": "end_turn",
    "length": "max_tokens",
    "content_filter": "refusal",
}
ERROR_MARK = "(erro) "  # o formato de chat não tem o `is_error` do tool_result

type Sleep = Callable[[float], Awaitable[None]]


class _AttemptError(ModelCallError):
    """Uma tentativa que falhou, com a espera que o servidor pediu (`Retry-After`), se pediu."""

    def __init__(self, kind: ErrorKind, message: str, retry_after: float | None = None) -> None:
        super().__init__(kind, message)
        self.retry_after = retry_after


# ----------------------------------------------------------------------------- a ida


def _text_part(block: Mapping[str, Any]) -> dict[str, Any]:
    part: dict[str, Any] = {"type": "text", "text": str(block.get("text", ""))}
    if block.get("cache_control") is not None:
        part["cache_control"] = dict(cast(Mapping[str, Any], block["cache_control"]))
    return part


def _plain(content: Any) -> str:
    """O texto de um conteúdo que é texto ou uma lista de partes."""
    if isinstance(content, str):
        return content
    blocks = cast(Sequence[Mapping[str, Any]], content or ())
    return "".join(str(b.get("text", "")) for b in blocks if b.get("type") == "text")


def _user(blocks: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Um turno do usuário: cada `tool_result` vira uma mensagem `tool`, logo depois da chamada,
    e o texto que sobra vira uma mensagem do usuário depois delas."""
    answers: list[dict[str, Any]] = []
    parts: list[dict[str, Any]] = []
    for block in blocks:
        kind = block.get("type")
        if kind == "tool_result":
            text = _plain(block.get("content", ""))
            answers.append(
                {
                    "role": "tool",
                    "tool_call_id": str(block["tool_use_id"]),
                    "content": f"{ERROR_MARK}{text}" if block.get("is_error") else text,
                }
            )
        elif kind == "text":
            parts.append(_text_part(block))
        else:
            raise ValueError(f"o bloco {kind!r} do usuário não tem tradução para o chat")
    return [*answers, *([{"role": "user", "content": parts}] if parts else [])]


def _assistant(blocks: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Uma resposta que volta à conversa: o texto, as chamadas e o raciocínio, sem mudança."""
    texts: list[str] = []
    calls: list[dict[str, Any]] = []
    details: list[Any] = []
    reasoning: list[str] = []
    for block in blocks:
        kind = block.get("type")
        if kind == "text":
            texts.append(str(block.get("text", "")))
        elif kind == "tool_use":
            written = block.get("arguments")
            arguments = (
                written
                if isinstance(written, str)
                else json.dumps(block.get("input") or {}, ensure_ascii=False)
            )
            calls.append(
                {
                    "id": str(block["id"]),
                    "type": "function",
                    "function": {"name": str(block["name"]), "arguments": arguments},
                }
            )
        elif kind == "reasoning":
            details.extend(cast(Sequence[Any], block.get("details") or ()))
            if block.get("text"):
                reasoning.append(str(block["text"]))
        else:
            raise ValueError(f"o bloco {kind!r} do assistente não tem tradução para o chat")
    text = "".join(texts)
    message: dict[str, Any] = {"role": "assistant", "content": text if text or not calls else None}
    if calls:
        message["tool_calls"] = calls
    if details:
        message["reasoning_details"] = details
    elif reasoning:
        message["reasoning"] = "".join(reasoning)
    return message


def chat_messages(request: ModelRequest) -> list[dict[str, Any]]:
    """As mensagens do pedido no formato de chat, com o sistema primeiro."""
    messages: list[dict[str, Any]] = []
    if request.system is not None:
        system = request.system
        messages.append(
            {
                "role": "system",
                "content": system if isinstance(system, str) else [_text_part(b) for b in system],
            }
        )
    for message in request.messages:
        role = str(message["role"])
        content = message.get("content")
        if isinstance(content, str):
            messages.append({"role": role, "content": content})
        elif role == "assistant":
            messages.append(_assistant(cast(Sequence[Mapping[str, Any]], content)))
        else:
            messages.extend(_user(cast(Sequence[Mapping[str, Any]], content)))
    return messages


def chat_tools(tools: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """As ferramentas como funções; a estrita continua estrita. Uma ferramenta do servidor da
    Anthropic, como o conselheiro, não tem tradução (ADR-0074, decisão 19)."""
    functions: list[dict[str, Any]] = []
    for tool in tools:
        if "input_schema" not in tool:
            raise ValueError(
                f"a ferramenta {tool.get('type') or tool.get('name')!r} é da Anthropic"
            )
        function: dict[str, Any] = {
            "name": str(tool["name"]),
            "parameters": dict(cast(Mapping[str, Any], tool["input_schema"])),
        }
        if tool.get("description"):
            function["description"] = str(tool["description"])
        if "strict" in tool:
            function["strict"] = bool(tool["strict"])
        functions.append({"type": "function", "function": function})
    return functions


def chat_body(request: ModelRequest, provider: str) -> dict[str, Any]:
    """O corpo do pedido, com o provedor fixo e sem fallback."""
    body: dict[str, Any] = {
        "model": request.model,
        "messages": chat_messages(request),
        "max_tokens": request.max_tokens,
        "provider": {"order": [provider], "allow_fallbacks": False},
    }
    if request.tools:
        body["tools"] = chat_tools(request.tools)
        body["tool_choice"] = "auto"
        body["parallel_tool_calls"] = False  # uma ação por vez (ADR-0059)
    if request.effort is not None:
        body["reasoning"] = {"effort": request.effort}
    return body


# ----------------------------------------------------------------------------- a volta


def response_blocks(message: Mapping[str, Any]) -> list[dict[str, Any]]:
    """A mensagem da resposta em blocos: o raciocínio, o texto e as chamadas."""
    blocks: list[dict[str, Any]] = []
    details = cast(Sequence[Any], message.get("reasoning_details") or ())
    reasoning = message.get("reasoning")
    if details or reasoning:
        block: dict[str, Any] = {"type": "reasoning", "details": list(details)}
        if reasoning:
            block["text"] = str(reasoning)
        blocks.append(block)
    text = _plain(message.get("content"))
    if text:
        blocks.append({"type": "text", "text": text})
    for call in cast(Sequence[Mapping[str, Any]], message.get("tool_calls") or ()):
        function = cast(Mapping[str, Any], call.get("function") or {})
        written = str(function.get("arguments") or "")
        try:
            given: Any = json.loads(written) if written.strip() else {}
        except json.JSONDecodeError:
            given = {}
        blocks.append(
            {
                "type": "tool_use",
                "id": str(call.get("id")),
                "name": str(function.get("name")),
                "input": cast(dict[str, Any], given) if isinstance(given, dict) else {},
                "arguments": written or "{}",
            }
        )
    return blocks


def usage_of(raw: Mapping[str, Any]) -> ModelUsage:
    """Os tokens no sentido da Messages API: no chat, os do cache estão dentro do prompt."""
    details = cast(Mapping[str, Any], raw.get("prompt_tokens_details") or {})
    read = int(details.get("cached_tokens") or 0)
    written = int(details.get("cache_write_tokens") or 0)
    cost = raw.get("cost")
    return ModelUsage(
        input_tokens=max(int(raw.get("prompt_tokens") or 0) - read - written, 0),
        output_tokens=int(raw.get("completion_tokens") or 0),
        cache_read_input_tokens=read,
        cache_creation_input_tokens=written,
        cost_usd=None if cost is None else float(cost),
    )


def _kind(status: int) -> ErrorKind:
    if status in (401, 402, 403):
        return "auth"  # a chave, os créditos (402) ou a moderação, como o 403 da Anthropic
    if status == 408:
        return "timeout"
    if status == 429:
        return "rate_limit"
    if status >= 500:
        return "server"
    return "bad_request"


def _failure(status: int, body: Any, retry_after: str | None = None) -> _AttemptError:
    """O erro do corpo (`error.code`, `error.message`), que manda também num 200."""
    found: Mapping[str, Any] = cast(Mapping[str, Any], body) if isinstance(body, dict) else {}
    error = cast(Mapping[str, Any], found.get("error") or {})
    code = error.get("code")
    if isinstance(code, int) and code >= 400:
        status = code
    elif status < 400:
        status = 500  # um erro sem código no meio da geração
    metadata = cast(Mapping[str, Any], error.get("metadata") or {})
    message = str(error.get("message") or f"HTTP {status}")
    if metadata.get("provider_name"):
        message += f" ({metadata['provider_name']})"
    wait: float | None = None
    if retry_after is not None:
        try:
            wait = float(retry_after)
        except ValueError:
            wait = None
    return _AttemptError(_kind(status), message[:1000], wait)


# ----------------------------------------------------------------------------- o adaptador


class OpenRouterModel:
    provider = "openrouter"

    def __init__(
        self,
        routes: Mapping[str, str],  # modelo -> o provedor fixo (a tabela do ambiente)
        *,
        clock: WallClock,
        client: httpx2.AsyncClient | None = None,
        api_key: str | None = None,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        max_retries: int = 2,
        sleep: Sleep = asyncio.sleep,
    ) -> None:
        self._routes = dict(routes)
        self._clock = clock
        self._client = client or httpx2.AsyncClient(base_url=BASE_URL, timeout=timeout_seconds)
        # Sem chave dada, a do ambiente (OPENROUTER_API_KEY, do .env).
        self._key = api_key if api_key is not None else os.environ.get(KEY_VARIABLE)
        self._timeout_seconds = timeout_seconds
        self._max_retries = max_retries
        self._sleep = sleep

    async def aclose(self) -> None:
        """Fecha o cliente HTTP enquanto o laço existe (como o AnthropicModel)."""
        await self._client.aclose()

    def timeout_for(self, request: ModelRequest) -> float:
        return max(self._timeout_seconds, request.max_tokens * SECONDS_PER_TOKEN)

    def capabilities(self) -> ModelCapabilities:
        return ModelCapabilities(
            tool_use=True, prompt_cache=True, batch=False, max_context_tokens=1_000_000
        )

    def body(self, request: ModelRequest) -> dict[str, Any]:
        """O corpo do pedido; um modelo sem rota ou um bloco sem tradução são recusados aqui."""
        provider = self._routes.get(request.model)
        if provider is None:
            raise ModelCallError(
                "bad_request",
                f"modelo sem provedor fixo na rota da OpenRouter: {request.model}",
                retryable=False,
            )
        try:
            return chat_body(request, provider)
        except ValueError as error:
            raise ModelCallError("bad_request", str(error), retryable=False) from error

    async def complete(self, request: ModelRequest) -> ModelResponse:
        body = self.body(request)
        if not self._key:
            raise ModelCallError("auth", f"{KEY_VARIABLE} ausente no ambiente", retryable=False)
        started = self._clock.monotonic()
        answer: Mapping[str, Any] = {}
        for attempt in range(self._max_retries + 1):
            try:
                answer = await self._attempt(body, self.timeout_for(request))
                break
            except _AttemptError as failed:
                if not failed.retryable or attempt == self._max_retries:
                    raise ModelCallError(failed.kind, failed.message) from failed
                wait = failed.retry_after if failed.retry_after is not None else 0.5 * 2**attempt
                await self._sleep(min(wait, MAX_WAIT_SECONDS))
        choice = cast(Mapping[str, Any], cast(list[Any], answer["choices"])[0])
        content = response_blocks(cast(Mapping[str, Any], choice.get("message") or {}))
        stop = str(choice.get("finish_reason") or "stop")
        if any(b["type"] == "tool_use" for b in content):
            stop = "tool_calls"  # há provedores que dizem `stop` com chamadas na resposta
        served = answer.get("provider")
        return ModelResponse(
            content=content,
            stop_reason=STOP_REASONS.get(stop, "end_turn"),
            usage=usage_of(cast(Mapping[str, Any], answer.get("usage") or {})),
            model=str(answer.get("model") or request.model),
            latency_ms=round((self._clock.monotonic() - started) * 1000),
            request_id=cast(str | None, answer.get("id")),
            served_by=str(served) if served else None,
        )

    async def _attempt(self, body: Mapping[str, Any], timeout: float) -> Mapping[str, Any]:
        """Uma tentativa: o corpo da resposta, ou _AttemptError classificado."""
        try:
            reply = await self._client.post(
                "/chat/completions",
                json=body,
                headers={"Authorization": f"Bearer {self._key}"},
                timeout=timeout,
            )
        except httpx2.TimeoutException as error:
            raise _AttemptError("timeout", str(error) or "tempo esgotado") from error
        except httpx2.TransportError as error:
            raise _AttemptError("connection", str(error) or "sem conexão") from error
        try:
            answer: Any = reply.json()
        except ValueError:
            answer = None
        if reply.status_code >= 400:
            raise _failure(reply.status_code, answer, reply.headers.get("retry-after"))
        if not isinstance(answer, dict):
            raise _AttemptError("server", f"resposta sem JSON (HTTP {reply.status_code})")
        found = cast(dict[str, Any], answer)
        if found.get("error"):  # um erro depois que o status já tinha saído
            raise _failure(reply.status_code, found)
        choices = cast(list[Any], found.get("choices") or [])
        if not choices:
            raise _AttemptError("server", "resposta sem escolhas")
        if cast(Mapping[str, Any], choices[0]).get("finish_reason") == "error":
            raise _AttemptError("server", "o provedor falhou no meio da geração")
        return found

    async def count_tokens(self, request: ModelRequest) -> int:
        raise ModelCallError(
            "bad_request", "a OpenRouter não conta tokens sem gerar", retryable=False
        )
