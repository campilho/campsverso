"""Fita de chamadas de modelo (ADR-0058): grava e reproduz respostas pelo hash do pedido.

Três modos: `live` não grava; `record` chama de verdade e grava o que ainda não tinha; `replay`
só lê a fita, e um pedido sem gravação é `cassette_miss`. Uma resposta reproduzida volta com
`replayed=True`: ninguém pagou por ela, e o decorador publica `charged: false`.
"""

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Literal, cast

from campsverso_ports import (
    ModelCallError,
    ModelCapabilities,
    ModelPort,
    ModelRequest,
    ModelResponse,
    ModelUsage,
    WallClock,
    canonical_request,
    request_sha256,
)

type RecordingMode = Literal["live", "record", "replay"]


class RecordingModel:
    def __init__(
        self,
        inner: ModelPort | None,
        path: Path,
        mode: RecordingMode,
        *,
        clock: WallClock | None = None,
    ) -> None:
        if inner is None and mode != "replay":
            raise ValueError("sem porta por baixo, a fita só reproduz (mode='replay')")
        self._inner = inner
        self._path = path
        self._mode: RecordingMode = mode
        self._clock = clock
        self._entries: dict[str, dict[str, Any]] = {}
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    entry = cast(dict[str, Any], json.loads(line))
                    self._entries[str(entry["sha256"])] = entry

    @property
    def provider(self) -> str:
        return self._inner.provider if self._inner is not None else "recorded"

    @property
    def mode(self) -> RecordingMode:
        return self._mode

    def __len__(self) -> int:
        return len(self._entries)

    def capabilities(self) -> ModelCapabilities:
        return self._inner.capabilities() if self._inner is not None else ModelCapabilities()

    async def complete(self, request: ModelRequest) -> ModelResponse:
        key = request_sha256(request)
        if self._mode != "live":
            entry = self._entries.get(key)
            if entry is not None:
                return _response_from(cast(Mapping[str, Any], entry["response"]))
        if self._inner is None or self._mode == "replay":
            raise ModelCallError(
                "cassette_miss", f"sem gravação para o pedido {key[:12]}… em {self._path}"
            )
        response = await self._inner.complete(request)
        if self._mode == "record":
            self._append(key, request, response)
        return response

    async def count_tokens(self, request: ModelRequest) -> int:
        if self._inner is None:
            raise ModelCallError(
                "cassette_miss", "a fita não conta tokens; precisa da porta por baixo"
            )
        return await self._inner.count_tokens(request)

    def _append(self, key: str, request: ModelRequest, response: ModelResponse) -> None:
        entry: dict[str, Any] = {
            "sha256": key,
            "recorded_at": self._clock.now().isoformat() if self._clock is not None else None,
            "provider": self.provider,
            "request": canonical_request(request),
            "response": {
                "content": [dict(block) for block in response.content],
                "stop_reason": response.stop_reason,
                "usage": response.usage.as_dict(),
                "model": response.model,
                "latency_ms": response.latency_ms,
                "request_id": response.request_id,
            },
        }
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
        self._entries[key] = entry


def _response_from(recorded: Mapping[str, Any]) -> ModelResponse:
    usage = cast(Mapping[str, int], recorded["usage"])
    return ModelResponse(
        content=[dict(block) for block in cast(list[Mapping[str, Any]], recorded["content"])],
        stop_reason=str(recorded["stop_reason"]),
        usage=ModelUsage(
            input_tokens=int(usage["input_tokens"]),
            output_tokens=int(usage["output_tokens"]),
            cache_read_input_tokens=int(usage.get("cache_read_input_tokens", 0)),
            cache_creation_input_tokens=int(usage.get("cache_creation_input_tokens", 0)),
        ),
        model=str(recorded["model"]),
        latency_ms=int(recorded["latency_ms"]),
        request_id=cast(str | None, recorded.get("request_id")),
        replayed=True,
    )
