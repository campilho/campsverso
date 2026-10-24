"""O clima de um mundo ao ar livre (ADR-0069): o tempo de cada dia, sorteado pela estação.

Uma biblioteca, e não uma primitiva do kernel: o calendário e as estações são do kernel (o tempo é
física de todo mundo), e o tempo de cada dia é guardado por ele (`set_weather`). Aqui fica só o
sorteio: as chances de cada condição em cada estação, e o que sobra é o tempo limpo. Quem chama
decide quando sortear (na madrugada do próprio dia, ou na véspera, como previsão) e o que cada
condição faz no mundo. Um escritório não precisa disto.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Protocol


class Rng(Protocol):
    def random(self) -> float:
        """Número em [0, 1)."""
        ...


@dataclass(frozen=True, slots=True)
class ClimateRules:
    """As chances de cada condição por estação; `default` vale para as estações sem tabela e
    para os mundos sem ano. O que sobra das chances é `clear`."""

    default: Mapping[str, float]
    by_season: Mapping[str, Mapping[str, float]] = field(
        default_factory=dict[str, Mapping[str, float]]
    )
    clear: str = "sun"

    def chances(self, season: str | None) -> Mapping[str, float]:
        if season is None:
            return self.default
        return self.by_season.get(season, self.default)


def draw(rng: Rng, rules: ClimateRules, season: str | None = None) -> str:
    """O tempo de um dia: um número só do RNG, comparado com as chances somadas em ordem
    alfabética das condições. Com só a chuva na tabela, é o sorteio de sempre."""
    roll = rng.random()
    total = 0.0
    for condition, chance in sorted(rules.chances(season).items()):
        total += chance
        if roll < total:
            return condition
    return rules.clear


__all__ = ["ClimateRules", "Rng", "draw"]
