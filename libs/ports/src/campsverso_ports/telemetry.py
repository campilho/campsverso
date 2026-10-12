"""Porta de telemetria: logs estruturados hoje, OpenTelemetry depois (contratos §12)."""

from typing import Any, Protocol


class Telemetry(Protocol):
    def info(self, event: str, **fields: Any) -> None: ...

    def warning(self, event: str, **fields: Any) -> None: ...

    def error(self, event: str, **fields: Any) -> None: ...
