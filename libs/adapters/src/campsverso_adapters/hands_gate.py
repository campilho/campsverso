"""A porta das mãos (ADR-0089, decisão 7): o endereço local por onde um harness de fora chama o
modelo.

O Claude Code chama o modelo sozinho, por HTTP. Em vez da API, ele recebe o endereço desta porta
(`ANTHROPIC_BASE_URL`) e uma chave falsa, que só vale para a sessão. A porta:

- **confere a chave da sessão** e põe a chave de verdade, que nunca entra no processo do dev;
- **repassa a chamada** ao modelo e devolve a resposta como veio, em streaming;
- **mede** cada resposta pelo `CallMeter`, com o mesmo evento da porta de modelo, e a guarda soma
  por pedido e por dia como sempre;
- **recusa** a chamada seguinte quando o teto do pedido ou do dia estourou (`refuse`);
- **grava a fita**, de que os testes respondem, na ordem, sem a API.

Roda dentro do processo de quem a abre, numa porta efêmera de `127.0.0.1`, enquanto a sessão dura.
"""

import asyncio
import contextlib
import json
import secrets
import socket
import time
from collections.abc import AsyncIterator, Callable, Generator, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

import httpx2
import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response, StreamingResponse
from starlette.routing import Route

from campsverso_ports import CallMeter, ModelRequest, ModelResponse, ModelUsage

ANTHROPIC = "https://api.anthropic.com"
MESSAGES = "/v1/messages"
COUNT_TOKENS = "/v1/messages/count_tokens"
# Os cabeçalhos do harness que seguem para o modelo; a chave é a da porta.
FORWARDED = ("anthropic-version", "anthropic-beta", "content-type", "accept")
TIMEOUT_SECONDS = 600.0

type Refuse = Callable[[], str | None]


def _error(status: int, kind: str, message: str) -> JSONResponse:
    """Um erro no formato da Messages API, que o harness entende e mostra."""
    return JSONResponse(
        {"type": "error", "error": {"type": kind, "message": message}}, status_code=status
    )


@dataclass(slots=True)
class UsageReader:
    """Lê os tokens, o modelo e o motivo do fim de uma resposta, em streaming ou não."""

    model: str = ""
    stop_reason: str = ""
    request_id: str | None = None
    usage: dict[str, int] = field(default_factory=dict[str, int])
    _pending: bytes = b""

    def _take(self, usage: Mapping[str, Any]) -> None:
        for key in (
            "input_tokens",
            "output_tokens",
            "cache_read_input_tokens",
            "cache_creation_input_tokens",
        ):
            value = usage.get(key)
            if isinstance(value, int):
                self.usage[key] = value

    def event(self, data: Mapping[str, Any]) -> None:
        kind = data.get("type")
        if kind == "message_start":
            message = cast(Mapping[str, Any], data.get("message") or {})
            self.model = str(message.get("model") or self.model)
            self.request_id = cast(str | None, message.get("id")) or self.request_id
            self._take(cast(Mapping[str, Any], message.get("usage") or {}))
        elif kind == "message_delta":
            delta = cast(Mapping[str, Any], data.get("delta") or {})
            self.stop_reason = str(delta.get("stop_reason") or self.stop_reason)
            self._take(cast(Mapping[str, Any], data.get("usage") or {}))

    def feed(self, chunk: bytes) -> None:
        """Um pedaço do streaming (SSE): os eventos inteiros são lidos, o resto espera."""
        self._pending += chunk
        *events, self._pending = self._pending.replace(b"\r\n", b"\n").split(b"\n\n")
        for raw in events:
            for line in raw.split(b"\n"):
                if line.startswith(b"data:"):
                    with contextlib.suppress(ValueError):
                        self.event(cast(Mapping[str, Any], json.loads(line[5:].strip())))

    def message(self, data: Mapping[str, Any]) -> None:
        """Uma resposta inteira, sem streaming."""
        self.model = str(data.get("model") or "")
        self.stop_reason = str(data.get("stop_reason") or "")
        self.request_id = cast(str | None, data.get("id"))
        self._take(cast(Mapping[str, Any], data.get("usage") or {}))

    @property
    def tokens(self) -> ModelUsage:
        return ModelUsage(
            input_tokens=self.usage.get("input_tokens", 0),
            output_tokens=self.usage.get("output_tokens", 0),
            cache_read_input_tokens=self.usage.get("cache_read_input_tokens", 0),
            cache_creation_input_tokens=self.usage.get("cache_creation_input_tokens", 0),
        )

    @property
    def complete(self) -> bool:
        return bool(self.stop_reason)


class Tape:
    """A fita da porta: cada chamada ao modelo e a resposta, uma por linha.

    No modo `record`, grava. No modo `replay`, responde na ordem, pela primeira resposta ainda não
    usada do mesmo caminho e do mesmo modelo (as chamadas auxiliares de um harness usam outro
    modelo e não tiram a ordem das principais)."""

    def __init__(self, path: Path, mode: str) -> None:
        if mode not in ("record", "replay"):
            raise ValueError(f"modo da fita desconhecido: {mode}")
        self.path = path
        self.mode = mode
        self._entries: list[dict[str, Any]] = []
        self._used: set[int] = set()
        if mode == "replay":
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    self._entries.append(cast(dict[str, Any], json.loads(line)))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, entry: Mapping[str, Any]) -> None:
        with self.path.open("a", encoding="utf-8") as tape:
            tape.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def next(self, path: str, model: str) -> dict[str, Any] | None:
        same_path = [
            i for i, e in enumerate(self._entries) if i not in self._used and e["path"] == path
        ]
        exact = [i for i in same_path if self._entries[i].get("model") == model]
        chosen = (exact or same_path or [None])[0]
        if chosen is None:
            return None
        self._used.add(chosen)
        return self._entries[chosen]


class _QuietServer(uvicorn.Server):
    """O uvicorn sem mexer nos sinais do processo: quem para a porta é quem a abriu."""

    @contextlib.contextmanager
    def capture_signals(self) -> Generator[None]:
        yield


class HandsGate:
    """A porta de uma sessão. Use com `async with`: `url` e `token` vão para o harness."""

    def __init__(
        self,
        meter: CallMeter,
        *,
        api_key: str,
        harness: str,
        avatar_id: str,
        ticket_id: str,
        refuse: Refuse = lambda: None,
        upstream: str = ANTHROPIC,
        transport: httpx2.AsyncBaseTransport | None = None,
        tape: Tape | None = None,
    ) -> None:
        self._meter = meter
        self._key = api_key
        self._harness = harness
        self._avatar = avatar_id
        self._ticket = ticket_id
        self._refuse = refuse
        self._upstream = upstream.rstrip("/")
        self._transport = transport
        self._tape = tape
        self.token = f"sessao-{secrets.token_hex(16)}"
        self.url = ""
        self.calls = 0
        self.refused = 0
        self.cost_usd = 0.0
        self._client: httpx2.AsyncClient | None = None
        self._server: _QuietServer | None = None
        self._task: asyncio.Task[None] | None = None

    # ------------------------------------------------------------- o ciclo

    async def __aenter__(self) -> HandsGate:
        self._client = httpx2.AsyncClient(
            base_url=self._upstream, timeout=TIMEOUT_SECONDS, transport=self._transport
        )
        app = Starlette(routes=[Route("/{path:path}", self._handle, methods=["GET", "POST"])])
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("127.0.0.1", 0))
        port = int(sock.getsockname()[1])
        config = uvicorn.Config(
            app, log_level="warning", access_log=False, lifespan="off", timeout_keep_alive=30
        )
        self._server = _QuietServer(config)
        self._task = asyncio.create_task(self._server.serve(sockets=[sock]))
        while not self._server.started:
            if self._task.done():
                await self._task  # a porta não subiu: o erro aparece aqui
            await asyncio.sleep(0.01)
        self.url = f"http://127.0.0.1:{port}"
        return self

    async def __aexit__(self, *exc: object) -> None:
        if self._server is not None:
            self._server.should_exit = True
        if self._task is not None:
            with contextlib.suppress(Exception):
                await asyncio.wait_for(self._task, 10)
        if self._client is not None:
            await self._client.aclose()

    # ------------------------------------------------------------- as chamadas

    def _authorized(self, request: Request) -> bool:
        given = request.headers.get("x-api-key") or ""
        bearer = request.headers.get("authorization") or ""
        if bearer.lower().startswith("bearer "):
            given = given or bearer[7:]
        return secrets.compare_digest(given, self.token)

    async def _handle(self, request: Request) -> Response:
        if not self._authorized(request):
            return _error(401, "authentication_error", "chave da sessão inválida")
        path = request.url.path
        if request.method != "POST" or path not in (MESSAGES, COUNT_TOKENS):
            return _error(404, "not_found_error", f"a porta das mãos não serve {path}")
        raw = await request.body()
        try:
            body = cast(dict[str, Any], json.loads(raw or b"{}"))
        except ValueError:
            return _error(400, "invalid_request_error", "o corpo não é JSON")
        model = str(body.get("model") or "")
        if path == COUNT_TOKENS:
            return await self._count(request, raw)
        try:
            self._meter.assert_priced(model)
        except LookupError as error:
            return _error(400, "invalid_request_error", str(error))
        reason = self._refuse()
        if reason:
            self.refused += 1
            # Um 403 não é repetido pelo harness: a sessão termina com o motivo.
            return _error(403, "permission_error", f"a porta das mãos recusou: {reason}")
        self.calls += 1
        if self._tape is not None and self._tape.mode == "replay":
            return await self._replay(path, model, body)
        if body.get("stream"):
            return await self._stream(request, raw, body)
        return await self._once(request, raw, body)

    def _headers(self, request: Request) -> dict[str, str]:
        headers = {k: v for k in FORWARDED if (v := request.headers.get(k)) is not None}
        headers["x-api-key"] = self._key
        return headers

    def _target(self, request: Request) -> str:
        query = request.url.query
        return request.url.path + (f"?{query}" if query else "")

    async def _count(self, request: Request, raw: bytes) -> Response:
        """Contar tokens não custa nem vira evento; na fita, não há o que contar."""
        if self._tape is not None and self._tape.mode == "replay":
            return JSONResponse({"input_tokens": 0})
        assert self._client is not None
        response = await self._client.post(
            self._target(request), content=raw, headers=self._headers(request)
        )
        return Response(
            response.content,
            status_code=response.status_code,
            media_type=response.headers.get("content-type"),
        )

    async def _once(self, request: Request, raw: bytes, body: Mapping[str, Any]) -> Response:
        assert self._client is not None
        started = time.monotonic()
        response = await self._client.post(
            self._target(request), content=raw, headers=self._headers(request)
        )
        if response.status_code == 200:
            reader = UsageReader()
            with contextlib.suppress(ValueError):
                reader.message(cast(Mapping[str, Any], response.json()))
            await self._measure(body, reader, started, replayed=False)
            self._record(request.url.path, body, response.status_code, False, response.text)
        return Response(
            response.content,
            status_code=response.status_code,
            media_type=response.headers.get("content-type"),
        )

    async def _stream(self, request: Request, raw: bytes, body: Mapping[str, Any]) -> Response:
        assert self._client is not None
        started = time.monotonic()
        upstream = self._client.build_request(
            "POST", self._target(request), content=raw, headers=self._headers(request)
        )
        response = await self._client.send(upstream, stream=True)
        if response.status_code != 200:
            content = await response.aread()
            await response.aclose()
            return Response(
                content,
                status_code=response.status_code,
                media_type=response.headers.get("content-type"),
            )
        reader = UsageReader()
        path = request.url.path

        async def relay() -> AsyncIterator[bytes]:
            kept: list[bytes] = []
            try:
                async for chunk in response.aiter_raw():
                    reader.feed(chunk)
                    kept.append(chunk)
                    yield chunk
            finally:
                await response.aclose()
                # O que passou foi cobrado, mesmo que o harness tenha largado a resposta no meio.
                if reader.usage:
                    await self._measure(body, reader, started, replayed=False)
                    text = b"".join(kept).decode("utf-8", errors="replace")
                    self._record(path, body, 200, True, text)

        return StreamingResponse(relay(), media_type="text/event-stream")

    async def _replay(self, path: str, model: str, body: Mapping[str, Any]) -> Response:
        assert self._tape is not None
        entry = self._tape.next(path, model)
        if entry is None:
            return _error(500, "api_error", "a fita acabou: não há resposta gravada para isto")
        started = time.monotonic()
        text = str(entry["body"])
        reader = UsageReader()
        if entry.get("stream"):
            reader.feed(text.encode() + b"\n\n")
        else:
            with contextlib.suppress(ValueError):
                reader.message(cast(Mapping[str, Any], json.loads(text)))
        if int(entry.get("status", 200)) == 200:
            await self._measure(body, reader, started, replayed=True)
        media = "text/event-stream" if entry.get("stream") else "application/json"
        return Response(text.encode(), status_code=int(entry.get("status", 200)), media_type=media)

    def _record(
        self, path: str, body: Mapping[str, Any], status: int, stream: bool, text: str
    ) -> None:
        if self._tape is None or self._tape.mode != "record":
            return
        self._tape.write(
            {
                "path": path,
                "model": str(body.get("model") or ""),
                "status": status,
                "stream": stream,
                "body": text,
            }
        )

    async def _measure(
        self, body: Mapping[str, Any], reader: UsageReader, started: float, *, replayed: bool
    ) -> None:
        model = str(body.get("model") or "")
        request = ModelRequest(
            model=model,
            messages=cast(list[Mapping[str, Any]], body.get("messages") or []),
            system=cast(Any, body.get("system")),
            tools=cast(list[Mapping[str, Any]], body.get("tools") or []),
            max_tokens=int(body.get("max_tokens") or 0),
            purpose="workshop",
            avatar_id=self._avatar,
            ticket_id=self._ticket,
        )
        response = ModelResponse(
            content=(),
            stop_reason=reader.stop_reason or "unknown",
            usage=reader.tokens,
            model=reader.model or model,
            latency_ms=round((time.monotonic() - started) * 1000),
            request_id=reader.request_id,
            replayed=replayed,
        )
        self.cost_usd += await self._meter.observed(request, response, harness=self._harness)
