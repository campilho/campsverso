"""Aleatoriedade determinística por fluxo nomeado (princípio 4; ADR-0038).

SplitMix64 em Python puro: a sequência não depende da versão do Python nem do `random` global.
"""

import hashlib

_MASK = (1 << 64) - 1


def stream_seed(seed: int, name: str) -> int:
    digest = hashlib.sha256(f"{seed}:{name}".encode()).digest()
    return int.from_bytes(digest[:8], "big")


class SplitMix64:
    def __init__(self, state: int) -> None:
        self.state = state & _MASK

    def next_u64(self) -> int:
        self.state = (self.state + 0x9E3779B97F4A7C15) & _MASK
        z = self.state
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & _MASK
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & _MASK
        return z ^ (z >> 31)

    def random(self) -> float:
        return (self.next_u64() >> 11) / float(1 << 53)

    def randint(self, low: int, high: int) -> int:
        if high < low:
            raise ValueError("intervalo vazio")
        span = high - low + 1
        limit = (1 << 64) - ((1 << 64) % span)  # rejeição: sem viés de módulo
        while True:
            value = self.next_u64()
            if value < limit:
                return low + value % span


class RngStreams:
    def __init__(self, seed: int) -> None:
        self._seed = seed
        self._streams: dict[str, SplitMix64] = {}

    def get(self, name: str) -> SplitMix64:
        if name not in self._streams:
            self._streams[name] = SplitMix64(stream_seed(self._seed, name))
        return self._streams[name]

    def states(self) -> dict[str, int]:
        """Estado de cada fluxo já usado, para snapshots (M2)."""
        return {name: stream.state for name, stream in sorted(self._streams.items())}

    def restore(self, states: dict[str, int]) -> None:
        """Fluxos nunca usados não entram no snapshot: nascem da seed quando forem pedidos."""
        self._streams = {name: SplitMix64(state) for name, state in states.items()}
