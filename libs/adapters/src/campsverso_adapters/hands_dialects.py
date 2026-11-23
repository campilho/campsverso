"""As línguas de fora da porta das mãos (ADR-0093): a da OpenAI, que o Codex fala, e a do Gemini,
que o Antigravity CLI fala. A da Anthropic, a do Claude Code, fica em `hands_gate.py`.

Cada dialeto diz à porta:
- **as rotas:** a chamada ao modelo, medida, e o que só se repassa (a lista dos modelos, contar os
  tokens);
- **as chaves:** onde vem a chave da sessão, e como vai a de verdade;
- **o modelo:** qual é, e o nome dele na tabela de preços do ambiente, que usa os nomes da
  OpenRouter (`openai/gpt-6.2-astra`, `google/gemini-4-neon`);
- **o leitor:** os tokens no sentido da Anthropic, isto é, a entrada sem o que veio do cache;
- **os erros:** o formato que o harness entende.

Os leitores seguem a documentação de cada API: os eventos do streaming da Responses API, e os
pedaços do `streamGenerateContent` do Gemini. A primeira sessão de verdade de cada harness (o plano
do M27, parte 1) confere o que ele manda de fato, e a fita guarda a resposta como veio.
"""

import contextlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, cast

from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from campsverso_adapters.hands_gate import Reader, Route_
from campsverso_ports import ModelUsage

OPENAI = "https://api.openai.com"
GEMINI = "https://generativelanguage.googleapis.com"
# Os cabeçalhos do harness que seguem para o modelo; a chave é a da porta.
OPENAI_FORWARDED = ("content-type", "accept", "openai-beta", "originator", "session_id", "version")
GEMINI_FORWARDED = ("content-type", "accept", "x-goog-api-client")
# Os métodos do Gemini que chamam o modelo, e os que só se repassam.
GEMINI_CALLS = ("generateContent", "streamGenerateContent")
GEMINI_PASSES = ("countTokens",)


def _sse_events(buffer: bytes) -> tuple[list[Mapping[str, Any]], bytes]:
    """Os eventos inteiros de um streaming SSE (as linhas `data:` com JSON), e o resto, que
    espera o pedaço seguinte."""
    *done, rest = buffer.replace(b"\r\n", b"\n").split(b"\n\n")
    events: list[Mapping[str, Any]] = []
    for raw in done:
        for line in raw.split(b"\n"):
            if line.startswith(b"data:"):
                payload = line[5:].strip()
                if payload and payload != b"[DONE]":
                    with contextlib.suppress(ValueError):
                        value = json.loads(payload)
                        if isinstance(value, Mapping):
                            events.append(cast(Mapping[str, Any], value))
    return events, rest


def _int(value: Any) -> int:
    return value if isinstance(value, int) else 0


def _arguments(raw: Any) -> Any:
    """Os argumentos de uma ferramenta, que a OpenAI manda como texto em JSON."""
    if isinstance(raw, str):
        try:
            return json.loads(raw) if raw.strip() else {}
        except ValueError:
            return raw
    return raw if raw is not None else {}


# ------------------------------------------------------------------ a OpenAI (Responses)


@dataclass(slots=True)
class ResponsesReader:
    """Lê a Responses API: o streaming (`response.output_item.done`, `response.completed`) ou a
    resposta inteira. Na OpenAI, `input_tokens` já inclui o que veio do cache, e `output_tokens` já
    inclui o raciocínio: a medida separa o cache da entrada, e conta a saída uma vez só."""

    model: str = ""
    stop_reason: str = ""
    request_id: str | None = None
    usage: dict[str, int] = field(default_factory=dict[str, int])
    items: list[dict[str, Any]] = field(default_factory=list[dict[str, Any]])
    _pending: bytes = b""

    def _response(self, response: Mapping[str, Any]) -> None:
        self.model = str(response.get("model") or self.model)
        self.request_id = cast(str | None, response.get("id")) or self.request_id
        status = response.get("status")
        if isinstance(status, str) and status not in ("in_progress", "queued"):
            self.stop_reason = status
        usage = response.get("usage")
        if isinstance(usage, Mapping):
            usage = cast(Mapping[str, Any], usage)
            details = cast(Mapping[str, Any], usage.get("input_tokens_details") or {})
            self.usage = {
                "input_tokens": _int(usage.get("input_tokens")),
                "cached_tokens": _int(details.get("cached_tokens")),
                "output_tokens": _int(usage.get("output_tokens")),
            }
        output = response.get("output")
        if isinstance(output, list) and output and not self.items:
            self.items = [
                dict(cast(Mapping[str, Any], i))
                for i in cast(list[Any], output)
                if isinstance(i, Mapping)
            ]

    def event(self, data: Mapping[str, Any]) -> None:
        kind = str(data.get("type") or "")
        response = data.get("response")
        if isinstance(response, Mapping):
            self._response(cast(Mapping[str, Any], response))
        item = data.get("item")
        if kind == "response.output_item.done" and isinstance(item, Mapping):
            self.items.append(dict(cast(Mapping[str, Any], item)))

    def feed(self, chunk: bytes) -> None:
        events, self._pending = _sse_events(self._pending + chunk)
        for event in events:
            self.event(event)

    def finish(self) -> None:
        events, self._pending = _sse_events(self._pending + b"\n\n")
        for event in events:
            self.event(event)

    def message(self, data: Any) -> None:
        if isinstance(data, Mapping):
            self._response(cast(Mapping[str, Any], data))

    @property
    def content(self) -> tuple[dict[str, Any], ...]:
        blocks: list[dict[str, Any]] = []
        for item in self.items:
            kind = item.get("type")
            if kind == "message":
                for part in cast(list[Any], item.get("content") or []):
                    if (
                        isinstance(part, Mapping)
                        and cast(Mapping[str, Any], part).get("type") == "output_text"
                    ):
                        blocks.append(
                            {
                                "type": "text",
                                "text": str(cast(Mapping[str, Any], part).get("text") or ""),
                            }
                        )
            elif kind in ("function_call", "custom_tool_call", "local_shell_call"):
                name = item.get("name") or kind
                raw = item.get("arguments", item.get("input", item.get("action")))
                blocks.append({"type": "tool_use", "name": str(name), "input": _arguments(raw)})
        return tuple(blocks)

    @property
    def tokens(self) -> ModelUsage:
        cached = self.usage.get("cached_tokens", 0)
        return ModelUsage(
            input_tokens=max(0, self.usage.get("input_tokens", 0) - cached),
            output_tokens=self.usage.get("output_tokens", 0),
            cache_read_input_tokens=cached,
        )

    @property
    def complete(self) -> bool:
        return self.stop_reason in ("completed", "incomplete")


def _bearer(request: Request) -> str:
    value = request.headers.get("authorization") or ""
    return value[7:] if value.lower().startswith("bearer ") else ""


class OpenAIDialect:
    """A língua da OpenAI, a do Codex: a Responses API (`POST /v1/responses`), em streaming pelo
    `stream` do corpo. A lista dos modelos passa sem custo."""

    name = "openai"
    upstream = OPENAI
    lean = False

    def route(self, method: str, path: str) -> Route_ | None:
        if method == "POST" and path.rstrip("/") == "/v1/responses":
            return "call"
        if method == "GET" and path.rstrip("/").startswith("/v1/models"):
            return "pass"
        return None

    def session_key(self, request: Request) -> str:
        return _bearer(request)

    def headers(self, request: Request, key: str) -> dict[str, str]:
        headers = {k: v for k in OPENAI_FORWARDED if (v := request.headers.get(k)) is not None}
        headers["authorization"] = f"Bearer {key}"
        return headers

    def target(self, request: Request) -> str:
        query = request.url.query
        return request.url.path + (f"?{query}" if query else "")

    def model(self, path: str, body: Mapping[str, Any]) -> str:
        return str(body.get("model") or "")

    def priced(self, model: str) -> str:
        return model if "/" in model or not model else f"openai/{model}"

    def streaming(self, request: Request, body: Mapping[str, Any]) -> bool:
        return bool(body.get("stream"))

    def parts(
        self, body: Mapping[str, Any]
    ) -> tuple[list[Mapping[str, Any]], Any, list[Mapping[str, Any]], int]:
        given = body.get("input")
        messages: list[Mapping[str, Any]] = (
            [{"role": "user", "content": given}]
            if isinstance(given, str)
            else cast(list[Mapping[str, Any]], given or [])
        )
        return (
            messages,
            body.get("instructions"),
            cast(list[Mapping[str, Any]], body.get("tools") or []),
            _int(body.get("max_output_tokens")),
        )

    def reader(self) -> Reader:
        return ResponsesReader()

    def error(self, status: int, kind: str, message: str) -> Response:
        types = {
            "auth": "invalid_request_error",
            "not_found": "invalid_request_error",
            "bad_request": "invalid_request_error",
            "refused": "insufficient_quota",
        }
        codes = {"auth": "invalid_api_key", "refused": "refused_by_gate"}
        error = {
            "message": message,
            "type": types.get(kind, "server_error"),
            "param": None,
            "code": codes.get(kind),
        }
        return JSONResponse({"error": error}, status_code=status)

    def stub(self, path: str) -> Response:
        return JSONResponse({"object": "list", "data": []})


# ------------------------------------------------------------------ o Gemini


@dataclass(slots=True)
class GeminiReader:
    """Lê o `generateContent` do Gemini: os pedaços do streaming (SSE, com `alt=sse`, ou um JSON
    em lista) ou a resposta inteira. O `usageMetadata` vem somado no último pedaço: o
    `promptTokenCount` já inclui o `cachedContentTokenCount`, e a saída é a dos candidatos mais a
    do pensamento (`thoughtsTokenCount`)."""

    model: str = ""
    stop_reason: str = ""
    request_id: str | None = None
    usage: dict[str, int] = field(default_factory=dict[str, int])
    parts: list[dict[str, Any]] = field(default_factory=list[dict[str, Any]])
    _pending: bytes = b""
    _raw: list[bytes] = field(default_factory=list[bytes])
    _seen: bool = False

    def chunk(self, data: Mapping[str, Any]) -> None:
        self._seen = True
        self.model = str(data.get("modelVersion") or self.model)
        self.request_id = cast(str | None, data.get("responseId")) or self.request_id
        for candidate in cast(list[Any], data.get("candidates") or [])[:1]:
            if not isinstance(candidate, Mapping):
                continue
            candidate = cast(Mapping[str, Any], candidate)
            content = cast(Mapping[str, Any], candidate.get("content") or {})
            for part in cast(list[Any], content.get("parts") or []):
                if isinstance(part, Mapping):
                    self.parts.append(dict(cast(Mapping[str, Any], part)))
            reason = candidate.get("finishReason")
            if isinstance(reason, str) and reason:
                self.stop_reason = reason
        meta = data.get("usageMetadata")
        if isinstance(meta, Mapping):
            meta = cast(Mapping[str, Any], meta)
            self.usage = {
                "prompt": _int(meta.get("promptTokenCount"))
                + _int(meta.get("toolUsePromptTokenCount")),
                "cached": _int(meta.get("cachedContentTokenCount")),
                "output": _int(meta.get("candidatesTokenCount"))
                + _int(meta.get("thoughtsTokenCount")),
            }

    def feed(self, chunk: bytes) -> None:
        self._raw.append(chunk)
        events, self._pending = _sse_events(self._pending + chunk)
        for event in events:
            self.chunk(event)

    def finish(self) -> None:
        events, self._pending = _sse_events(self._pending + b"\n\n")
        for event in events:
            self.chunk(event)
        if not self._seen:
            # Sem `alt=sse`, o streaming do Gemini é um JSON em lista, inteiro no fim.
            with contextlib.suppress(ValueError):
                self.message(json.loads(b"".join(self._raw)))

    def message(self, data: Any) -> None:
        if isinstance(data, list):
            for item in cast(list[Any], data):
                if isinstance(item, Mapping):
                    self.chunk(cast(Mapping[str, Any], item))
        elif isinstance(data, Mapping):
            self.chunk(cast(Mapping[str, Any], data))

    @property
    def content(self) -> tuple[dict[str, Any], ...]:
        blocks: list[dict[str, Any]] = []
        text: list[str] = []
        for part in self.parts:
            call = part.get("functionCall")
            if isinstance(call, Mapping):
                call = cast(Mapping[str, Any], call)
                blocks.append(
                    {
                        "type": "tool_use",
                        "name": str(call.get("name") or ""),
                        "input": call.get("args") or {},
                    }
                )
            elif isinstance(part.get("text"), str) and not part.get("thought"):
                text.append(str(part["text"]))
        if text:
            blocks.insert(0, {"type": "text", "text": "".join(text)})
        return tuple(blocks)

    @property
    def tokens(self) -> ModelUsage:
        cached = self.usage.get("cached", 0)
        return ModelUsage(
            input_tokens=max(0, self.usage.get("prompt", 0) - cached),
            output_tokens=self.usage.get("output", 0),
            cache_read_input_tokens=cached,
        )

    @property
    def complete(self) -> bool:
        return bool(self.stop_reason)


def _gemini_call(path: str) -> tuple[str, str] | None:
    """O modelo e o método de um caminho do Gemini, como
    `/v1beta/models/gemini-4-neon:streamGenerateContent`."""
    tail = path.rstrip("/")
    for prefix in ("/v1beta/models/", "/v1/models/", "/v1alpha/models/"):
        if tail.startswith(prefix) and ":" in tail[len(prefix) :]:
            model, method = tail[len(prefix) :].rsplit(":", 1)
            return model, method
    return None


class GeminiDialect:
    """A língua do Gemini, a do Antigravity CLI pelo `GOOGLE_GEMINI_BASE_URL`: o `generateContent`
    e o `streamGenerateContent`, com o modelo no caminho. A chave vem no `x-goog-api-key` ou no
    `?key=`, e vai no `x-goog-api-key`, nunca na URL."""

    name = "gemini"
    upstream = GEMINI
    lean = False

    def route(self, method: str, path: str) -> Route_ | None:
        found = _gemini_call(path)
        if method != "POST" or found is None:
            return None
        return "call" if found[1] in GEMINI_CALLS else "pass" if found[1] in GEMINI_PASSES else None

    def session_key(self, request: Request) -> str:
        return (
            request.headers.get("x-goog-api-key")
            or request.query_params.get("key")
            or _bearer(request)
        )

    def headers(self, request: Request, key: str) -> dict[str, str]:
        headers = {k: v for k in GEMINI_FORWARDED if (v := request.headers.get(k)) is not None}
        headers["x-goog-api-key"] = key
        return headers

    def target(self, request: Request) -> str:
        query = "&".join(f"{k}={v}" for k, v in request.query_params.multi_items() if k != "key")
        return request.url.path + (f"?{query}" if query else "")

    def model(self, path: str, body: Mapping[str, Any]) -> str:
        found = _gemini_call(path)
        return "" if found is None else found[0].removeprefix("models/")

    def priced(self, model: str) -> str:
        return model if "/" in model or not model else f"google/{model}"

    def streaming(self, request: Request, body: Mapping[str, Any]) -> bool:
        found = _gemini_call(request.url.path)
        return found is not None and found[1] == "streamGenerateContent"

    def parts(
        self, body: Mapping[str, Any]
    ) -> tuple[list[Mapping[str, Any]], Any, list[Mapping[str, Any]], int]:
        config = cast(Mapping[str, Any], body.get("generationConfig") or {})
        return (
            cast(list[Mapping[str, Any]], body.get("contents") or []),
            body.get("systemInstruction"),
            cast(list[Mapping[str, Any]], body.get("tools") or []),
            _int(config.get("maxOutputTokens")),
        )

    def reader(self) -> Reader:
        return GeminiReader()

    def error(self, status: int, kind: str, message: str) -> Response:
        statuses = {
            "auth": "UNAUTHENTICATED",
            "not_found": "NOT_FOUND",
            "bad_request": "INVALID_ARGUMENT",
            "refused": "PERMISSION_DENIED",
        }
        error = {"code": status, "message": message, "status": statuses.get(kind, "INTERNAL")}
        return JSONResponse({"error": error}, status_code=status)

    def stub(self, path: str) -> Response:
        return JSONResponse({"totalTokens": 0})
