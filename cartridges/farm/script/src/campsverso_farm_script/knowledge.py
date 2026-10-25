"""O que o fazendeiro-script 3 acha do mundo (ADR-0070, decisão 4): uma crença que aprende.

Duas perguntas, as duas sobre o que qualquer um vê:

- **O ritmo:** quantas vezes mais rápido (ou mais devagar) que o manual uma planta cresce num
  lugar. O logaritmo do ritmo é a soma dos efeitos dos atributos do plantio: as faixas de
  distância do tile à água, à mata, ao caminho e à porta, se a cultura é a mesma de antes no
  canteiro, se foi adubado. A crença de cada efeito começa larga (pode não ser nada, pode ajudar
  ou atrapalhar) e estreita a cada colheita medida: uma regressão linear bayesiana, com a
  crença normal e o erro da medida conhecido.
- **A perda:** a chance de a planta madura sumir antes da colheita, por faixa de distância da
  porta e do espantalho mais perto. Uma distribuição Beta por faixa.

`world(rng)` sorteia um mundo plausível da crença (a amostragem de Thompson); sem `rng`, devolve
o mundo médio. Nada aqui tem o nome de uma regra: os atributos que não importam ficam com o
efeito perto de zero, e o script só "sabe" o que os dados mostraram.
"""

import math
import random
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol, cast

type Tile = tuple[int, int]
Z90 = 1.645  # o intervalo de 90% de uma normal


@dataclass(frozen=True)
class Spot:
    """Os atributos de um plantio: a distância do tile a cada coisa (na ordem do modelo) e o
    histórico do canteiro."""

    distances: tuple[int, ...]
    repeat: bool = False
    fertilized: bool = False


class World(Protocol):
    """Um mundo, sorteado da crença ou o verdadeiro (o oráculo)."""

    def speed(self, spot: Spot) -> float: ...

    def loss(self, door: int, guard: int | None) -> float: ...


@dataclass(frozen=True)
class Effect:
    """A crença sobre o efeito de um atributo, em vezes: a média e o intervalo de 90%."""

    name: str
    mean: float
    low: float
    high: float
    measured: int  # plantios medidos com o atributo


# ----------------------------------------------------------------------------- álgebra pequena


def _cholesky(a: Sequence[Sequence[float]]) -> list[list[float]]:
    n = len(a)
    low = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1):
            s = a[i][j] - sum(low[i][k] * low[j][k] for k in range(j))
            low[i][j] = math.sqrt(max(s, 1e-12)) if i == j else s / low[j][j]
    return low


def _forward(low: Sequence[Sequence[float]], b: Sequence[float]) -> list[float]:
    """Resolve L x = b."""
    x: list[float] = []
    for i, row in enumerate(low):
        x.append((b[i] - sum(row[k] * x[k] for k in range(i))) / row[i])
    return x


def _backward(low: Sequence[Sequence[float]], b: Sequence[float]) -> list[float]:
    """Resolve Lᵀ x = b."""
    n = len(low)
    x = [0.0] * n
    for i in reversed(range(n)):
        x[i] = (b[i] - sum(low[k][i] * x[k] for k in range(i + 1, n))) / low[i][i]
    return x


# ----------------------------------------------------------------------------- a crença


@dataclass
class _Sampled:
    """Um mundo sorteado: os coeficientes do ritmo e a perda de cada faixa."""

    beliefs: Beliefs
    beta: list[float]
    losses: dict[tuple[int, int], float]

    def speed(self, spot: Spot) -> float:
        x = self.beliefs.features(spot)
        return math.exp(sum(a * b for a, b in zip(x, self.beta, strict=True)))

    def loss(self, door: int, guard: int | None) -> float:
        return self.losses[self.beliefs.loss_cell(door, guard)]


@dataclass
class Beliefs:
    """A crença do script 3, que começa larga e aprende com o caderno de campo."""

    config: Mapping[str, Any]
    xtx: list[list[float]] = field(default_factory=list[list[float]])
    xty: list[float] = field(default_factory=list[float])
    counts: list[int] = field(default_factory=list[int])  # plantios medidos com cada atributo
    lost: dict[tuple[int, int], tuple[float, float]] = field(
        default_factory=dict[tuple[int, int], tuple[float, float]]
    )
    _fit: tuple[list[float], list[list[float]]] | None = None

    def __post_init__(self) -> None:
        n = len(self.names)
        if not self.xtx:
            self.xtx = [[0.0] * n for _ in range(n)]
            self.xty = [0.0] * n
            self.counts = [0] * n

    # ------------------------------------------------------------- os atributos

    @property
    def bins(self) -> tuple[int, ...]:
        return tuple(int(b) for b in cast(Sequence[Any], self.config["bins"]))

    @property
    def distances(self) -> tuple[str, ...]:
        return tuple(str(d) for d in cast(Sequence[Any], self.config["distances"]))

    @property
    def names(self) -> tuple[str, ...]:
        """O intercepto, uma faixa por distância (a mais longe é a base) e o histórico."""
        bands = [f"{d}<={b}" for d in self.distances for b in self.bins]
        return ("base", *bands, "repetida", "adubada")

    def features(self, spot: Spot) -> list[float]:
        x = [1.0]
        for distance in spot.distances:
            band = next((i for i, b in enumerate(self.bins) if distance <= b), None)
            x.extend(1.0 if i == band else 0.0 for i in range(len(self.bins)))
        x += [float(spot.repeat), float(spot.fertilized)]
        return x

    def loss_cell(self, door: int, guard: int | None) -> tuple[int, int]:
        doors = cast(Sequence[int], self.config["loss_door"])
        guards = cast(Sequence[int], self.config["loss_guard"])
        d = next((i for i, b in enumerate(doors) if door <= b), len(doors))
        g = (
            len(guards)
            if guard is None
            else next((i for i, b in enumerate(guards) if guard <= b), len(guards))
        )
        return d, g

    # ------------------------------------------------------------- aprender

    def learn_growth(self, spot: Spot, log_speed: float) -> None:
        """Um plantio medido: o logaritmo do ritmo que ele teve."""
        x = self.features(spot)
        noise = float(self.config["noise_sd"]) ** 2
        for i, a in enumerate(x):
            self.xty[i] += a * log_speed / noise
            self.counts[i] += int(a != 0.0)
            for j, b in enumerate(x):
                self.xtx[i][j] += a * b / noise
        self._fit = None

    def learn_loss(self, door: int, guard: int | None, lost: bool) -> None:
        cell = self.loss_cell(door, guard)
        a, b = self.lost.get(cell, self._prior(cell))
        self.lost[cell] = (a + lost, b + (not lost))

    def _prior(self, cell: tuple[int, int]) -> tuple[float, float]:
        """Sem dado nenhum: uma perda pequena e incerta; perto de um espantalho, menor ainda (o
        manual diz que ele protege a lavoura)."""
        guarded = cell[1] < len(cast(Sequence[int], self.config["loss_guard"]))
        return (0.5, 4.0) if guarded else (0.5, 2.5)

    def _posterior(self) -> tuple[list[float], list[list[float]]]:
        """A média dos coeficientes e o fator de Cholesky da precisão da crença."""
        if self._fit is None:
            n = len(self.names)
            sd = [float(self.config["intercept_sd"])] + [float(self.config["prior_sd"])] * (n - 1)
            precision = [
                [self.xtx[i][j] + (1.0 / sd[i] ** 2 if i == j else 0.0) for j in range(n)]
                for i in range(n)
            ]
            low = _cholesky(precision)
            mean = _backward(low, _forward(low, self.xty))
            self._fit = (mean, low)
        return self._fit

    # ------------------------------------------------------------- consultar

    def world(self, rng: random.Random | None = None) -> World:
        """Um mundo plausível sorteado da crença, ou o mundo médio sem `rng`."""
        mean, low = self._posterior()
        beta = list(mean)
        if rng is not None:
            noise = _backward(low, [rng.gauss(0.0, 1.0) for _ in mean])
            beta = [m + e for m, e in zip(mean, noise, strict=True)]
        doors = len(cast(Sequence[int], self.config["loss_door"])) + 1
        guards = len(cast(Sequence[int], self.config["loss_guard"])) + 1
        losses: dict[tuple[int, int], float] = {}
        for cell in ((d, g) for d in range(doors) for g in range(guards)):
            a, b = self.lost.get(cell, self._prior(cell))
            losses[cell] = rng.betavariate(a, b) if rng is not None else a / (a + b)
        return _Sampled(self, beta, losses)

    def uncertainty(self, spot: Spot) -> float:
        """O desvio da crença sobre o logaritmo do ritmo de um plantio: o que testar ensina."""
        _, low = self._posterior()
        v = _forward(low, self.features(spot))
        return math.sqrt(sum(a * a for a in v))

    def effects(self) -> list[Effect]:
        """A crença sobre cada atributo, em vezes, com o intervalo de 90% (a prova, o relatório)."""
        mean, low = self._posterior()
        found: list[Effect] = []
        for i, name in enumerate(self.names):
            unit = [1.0 if j == i else 0.0 for j in range(len(mean))]
            sd = math.sqrt(sum(a * a for a in _forward(low, unit)))
            found.append(
                Effect(
                    name,
                    round(math.exp(mean[i]), 3),
                    round(math.exp(mean[i] - Z90 * sd), 3),
                    round(math.exp(mean[i] + Z90 * sd), 3),
                    self.counts[i],
                )
            )
        return found

    def loss_rates(self) -> dict[tuple[int, int], tuple[float, int]]:
        """A perda média de cada faixa com dado, e quantos plantios a mediram."""
        return {
            cell: (round(a / (a + b), 3), round(a + b - sum(self._prior(cell))))
            for cell, (a, b) in sorted(self.lost.items())
        }


# ----------------------------------------------------------------------------- o oráculo


@dataclass
class Truth:
    """O que o oráculo sabe (ADR-0070, decisão 6): as regras ocultas, com os números da bíblia, no
    lugar da crença. Tem a mesma cara da crença, e não aprende nada."""

    config: Mapping[str, Any]
    beliefs: Beliefs  # só para as faixas dos atributos e da perda, as mesmas do script 3

    def _distance(self, spot: Spot, name: str) -> int:
        return spot.distances[self.beliefs.distances.index(name)]

    def speed(self, spot: Spot) -> float:
        water = cast(Mapping[str, Any], self.config["water"])
        fast = (
            float(water["multiplier"])
            if self._distance(spot, "agua") <= int(water["radius"])
            else 1.0
        )
        tired = float(self.config["fatigue"]) if spot.repeat else 1.0
        fertilized = 1.0 + float(self.config["fertilizer_points"]) if spot.fertilized else 1.0
        return fast * tired * fertilized

    def loss(self, door: int, guard: int | None) -> float:
        crows = cast(Mapping[str, Any], self.config["crows"])
        guarded = guard is not None and guard <= int(crows["scarecrow_radius"])
        return float(crows["chance"]) if door > int(crows["distance"]) and not guarded else 0.0

    def world(self, rng: random.Random | None = None) -> World:
        return self

    def learn_growth(self, spot: Spot, log_speed: float) -> None:
        self.beliefs.learn_growth(spot, log_speed)  # conta os plantios medidos, como o script 3

    def learn_loss(self, door: int, guard: int | None, lost: bool) -> None:
        self.beliefs.learn_loss(door, guard, lost)

    def uncertainty(self, spot: Spot) -> float:
        return 0.0

    def effects(self) -> list[Effect]:
        """A verdade, na forma da crença: o efeito de cada atributo, sem intervalo."""
        found: list[Effect] = []
        for name in self.beliefs.names:
            band, _, edge = name.partition("<=")
            value = 1.0
            if band == "agua" and edge and int(edge) <= int(self.config["water"]["radius"]):
                value = float(self.config["water"]["multiplier"])
            elif name == "repetida":
                value = float(self.config["fatigue"])
            elif name == "adubada":
                value = 1.0 + float(self.config["fertilizer_points"])
            found.append(Effect(name, value, value, value, 0))
        return found

    @property
    def counts(self) -> list[int]:
        return self.beliefs.counts

    def loss_rates(self) -> dict[tuple[int, int], tuple[float, int]]:
        return self.beliefs.loss_rates()


class Knowledge(Protocol):
    """O que o script 3 consulta: a crença que aprende (`Beliefs`) ou a verdade (`Truth`)."""

    @property
    def counts(self) -> list[int]: ...

    def world(self, rng: random.Random | None = None) -> World: ...

    def learn_growth(self, spot: Spot, log_speed: float) -> None: ...

    def learn_loss(self, door: int, guard: int | None, lost: bool) -> None: ...

    def uncertainty(self, spot: Spot) -> float: ...

    def effects(self) -> list[Effect]: ...

    def loss_rates(self) -> dict[tuple[int, int], tuple[float, int]]: ...
