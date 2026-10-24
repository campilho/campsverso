"""O mercado (ADR-0069): o preço de cada item parte de uma referência e se afasta dela com o que se
negocia. Vender empurra o preço para baixo, comprar empurra para cima, e na virada do dia ele
recupera parte da distância até a referência. O que é raro custa caro; o que sobra custa pouco.

Tudo aqui é função pura. O estado de cada item é um número só, o **fator** (1 é a referência), que
o mundo guarda onde quiser (na fazenda, nos atributos da caixa e do quiosque) e passa de volta.
"""

import math
from dataclasses import dataclass

from campsverso_economy.rng import Rng


@dataclass(frozen=True, slots=True)
class MarketRules:
    """Como um lado do mercado reage ao que se negocia.

    - `step`: quanto cada unidade move o fator, em fração da referência;
    - `floor` e `ceiling`: os limites do fator;
    - `recovery`: a fração da distância até a referência que volta a cada dia (1 volta inteira,
      0 nunca volta).
    """

    step: float
    floor: float = 0.0
    ceiling: float = math.inf
    recovery: float = 1.0


@dataclass(frozen=True, slots=True)
class Trade:
    """O resultado de negociar algumas unidades: o fator depois, o total (cada unidade ao preço
    do momento em que foi negociada) e o preço da próxima unidade."""

    factor: float
    total: int
    next_price: int


def unit_price(reference: float, factor: float) -> int:
    """O preço de uma unidade agora, em moedas inteiras (meio para cima), nunca menos de 1."""
    return max(1, int(reference * factor + 0.5))


def sell(reference: float, factor: float, qty: int, rules: MarketRules) -> Trade:
    """Alguém vende `qty` unidades ao mercado: cada uma derruba o preço, até o piso."""
    total = 0
    for _ in range(qty):
        total += unit_price(reference, factor)
        factor = max(rules.floor, factor - rules.step)
    factor = round(factor, 6)
    return Trade(factor, total, unit_price(reference, factor))


def buy(reference: float, factor: float, qty: int, rules: MarketRules) -> Trade:
    """Alguém compra `qty` unidades do mercado: cada uma sobe o preço, até o teto."""
    total = 0
    for _ in range(qty):
        total += unit_price(reference, factor)
        factor = min(rules.ceiling, factor + rules.step)
    factor = round(factor, 6)
    return Trade(factor, total, unit_price(reference, factor))


def recover(factor: float, rules: MarketRules) -> float:
    """A virada do dia: o fator volta `recovery` da distância até 1."""
    return round(factor + (1.0 - factor) * rules.recovery, 6)


def reference(base: float, season: float = 1.0, drift: float = 0.0, shock: float = 0.0) -> float:
    """A referência de hoje: a tabela, vezes o fator da estação (o que está fora da estação é
    raro e vale mais), vezes a oscilação do dia, vezes um choque (o clima, uma notícia)."""
    return base * season * (1.0 + drift) * (1.0 + shock)


def drift(current: float, rng: Rng, step: float, limit: float) -> float:
    """A oscilação anda até `step` para cima ou para baixo por dia, sem passar de `limit`."""
    moved = current + (rng.random() * 2.0 - 1.0) * step
    return round(max(-limit, min(limit, moved)), 6)
