"""Adaptadores da porta Telemetry: uma linha JSON por registro, e um coletor para testes."""

import json
import sys
from datetime import UTC, datetime
from typing import Any, TextIO


class JsonTelemetry:
    def __init__(self, service: str, stream: TextIO | None = None) -> None:
        self._service = service
        self._stream = stream or sys.stderr

    def _write(self, level: str, event: str, fields: dict[str, Any]) -> None:
        record = {
            "ts": datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            "level": level,
            "service": self._service,
            "event": event,
            **fields,
        }
        self._stream.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
        self._stream.flush()

    def info(self, event: str, **fields: Any) -> None:
        self._write("info", event, fields)

    def warning(self, event: str, **fields: Any) -> None:
        self._write("warning", event, fields)

    def error(self, event: str, **fields: Any) -> None:
        self._write("error", event, fields)


class MemoryTelemetry:
    def __init__(self) -> None:
        self.records: list[tuple[str, str, dict[str, Any]]] = []

    def events(self, level: str | None = None) -> list[str]:
        return [event for lvl, event, _ in self.records if level is None or lvl == level]

    def info(self, event: str, **fields: Any) -> None:
        self.records.append(("info", event, fields))

    def warning(self, event: str, **fields: Any) -> None:
        self.records.append(("warning", event, fields))

    def error(self, event: str, **fields: Any) -> None:
        self.records.append(("error", event, fields))
