"""As encomendas (ADR-0069): pedidos de clientes com item, quantidade, prazo e pagamento, que
alguém aceita e entrega. Na fazenda são os pedidos do quadro; no escritório vão ser os tickets.

A reputação de quem aceita muda com o que ele faz: entregar sobe, deixar vencer um pedido aceito
desce. Ela mexe na chance de aparecerem pedidos e no prêmio deles. Num mundo que a esconde, é uma
regra oculta (a R-004 da Morada do Sol): quem joga só vê o quadro ficar mais cheio, ou mais vazio.

Tudo aqui é função pura; o mundo guarda os pedidos e a reputação onde quiser.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace

from campsverso_economy.rng import Rng


@dataclass(frozen=True, slots=True)
class Order:
    order_id: str
    client: str
    item: str
    qty: int
    reward: int  # o pagamento total, na entrega
    posted_day: int
    due_day: int  # o último dia para entregar
    taker: str | None = None


@dataclass(frozen=True, slots=True)
class OrderRules:
    """Quantos pedidos, de que tamanho, com que prazo e com que prêmio sobre a referência."""

    max_open: int  # pedidos no quadro, aceitos ou não
    max_taken: int  # aceitos ao mesmo tempo por quem aceita
    new_per_day: int  # vagas para pedidos novos a cada dia
    chance: float  # a chance de cada vaga virar pedido, com a reputação neutra
    qty: tuple[int, int]
    days: tuple[int, int]  # o prazo, contado do dia em que o pedido aparece
    premium: float  # 0,5 paga 50% acima da referência, com a reputação neutra


@dataclass(frozen=True, slots=True)
class ReputationRules:
    """A reputação vai de 0 a 1, e 0,5 é neutra. `spread` é quanto ela mexe na chance e no prêmio:
    de 1 - spread (reputação 0) a 1 + spread (reputação 1)."""

    start: float = 0.5
    gain: float = 0.1  # por pedido entregue
    loss: float = 0.2  # por pedido aceito que venceu
    spread: float = 0.5


def effect(reputation: float, rules: ReputationRules) -> float:
    """O peso da reputação na chance e no prêmio: 1 com ela neutra."""
    return 1.0 + rules.spread * (2.0 * reputation - 1.0)


def draw(
    rng: Rng,
    day: int,
    open_count: int,
    candidates: Sequence[tuple[str, float]],
    clients: Sequence[str],
    rules: OrderRules,
    reputation: float,
    reputation_rules: ReputationRules,
    next_id: Callable[[], str],
) -> list[Order]:
    """Os pedidos novos do dia. `candidates` são os itens que se pedem hoje, com a referência de
    cada um; a ordem deles e a dos clientes é a de quem chama (ordene por id para o sorteio ser o
    mesmo em toda corrida). `reputation` é a que vale para o quadro."""
    weight = effect(reputation, reputation_rules)
    chance = max(0.0, min(1.0, rules.chance * weight))
    orders: list[Order] = []
    for _ in range(rules.new_per_day):
        if not candidates or not clients or open_count + len(orders) >= rules.max_open:
            break
        if rng.random() >= chance:
            continue
        item, price = candidates[rng.randint(0, len(candidates) - 1)]
        client = clients[rng.randint(0, len(clients) - 1)]
        qty = rng.randint(rules.qty[0], rules.qty[1])
        days = rng.randint(rules.days[0], rules.days[1])
        reward = max(1, int(qty * price * (1.0 + rules.premium * weight) + 0.5))
        orders.append(Order(next_id(), client, item, qty, reward, day, day + days))
    return orders


def refuse_take(order: Order, taker: str, taken_by_taker: int, rules: OrderRules) -> str | None:
    """Por que `taker` não pode aceitar o pedido, ou nada."""
    if order.taker is not None:
        return "order_taken"
    if taken_by_taker >= rules.max_taken:
        return "too_many_orders"
    return None


def take(order: Order, taker: str) -> Order:
    return replace(order, taker=taker)


def refuse_delivery(order: Order, taker: str, day: int) -> str | None:
    """Por que `taker` não pode entregar o pedido (os itens, quem chama confere), ou nada."""
    if order.taker != taker:
        return "not_your_order"
    if expired(order, day):
        return "order_expired"
    return None


def expired(order: Order, day: int) -> bool:
    """O prazo passou: o pedido sai do quadro, e quem o aceitou perde reputação."""
    return day > order.due_day


def after_delivery(reputation: float, rules: ReputationRules) -> float:
    return round(min(1.0, reputation + rules.gain), 6)


def after_expiry(reputation: float, rules: ReputationRules) -> float:
    return round(max(0.0, reputation - rules.loss), 6)
