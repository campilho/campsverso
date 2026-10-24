"""O RNG que a biblioteca recebe: o fluxo nomeado do mundo, passado por quem chama (princípio 4).
A biblioteca nunca sorteia por conta própria."""

from typing import Protocol


class Rng(Protocol):
    def random(self) -> float:
        """Número em [0, 1)."""
        ...

    def randint(self, low: int, high: int) -> int:
        """Inteiro em [low, high]."""
        ...
