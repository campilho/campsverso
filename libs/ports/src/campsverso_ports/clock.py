"""Porta do relógio de parede. A simulação nunca a usa diretamente (princípio 4)."""

from datetime import datetime
from typing import Protocol


class WallClock(Protocol):
    def now(self) -> datetime:
        """Agora, com fuso horário (UTC)."""
        ...

    def monotonic(self) -> float:
        """Segundos de um relógio monotônico, para medir intervalos."""
        ...
