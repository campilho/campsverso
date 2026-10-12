"""EventBus em memória: testes e, no futuro, forks sem NATS (D4)."""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from campsverso_ports import BatchHandler, Envelope, Handler


def subject_matches(pattern: str, subject: str) -> bool:
    """Casamento de assunto no estilo NATS: `*` é um token, `>` é o resto (um ou mais tokens)."""
    wanted, actual = pattern.split("."), subject.split(".")
    for index, token in enumerate(wanted):
        if token == ">":
            return len(actual) > index
        if index >= len(actual) or (token != "*" and token != actual[index]):
            return False
    return len(wanted) == len(actual)


@dataclass(eq=False)
class _Subscription:
    bus: InMemoryBus
    pattern: str
    handler: Handler

    async def unsubscribe(self) -> None:
        self.bus.remove(self)

    async def caught_up(self) -> None:
        """A entrega em memória é síncrona: quem publicou já foi entregue."""


class InMemoryBus:
    """Entrega síncrona, na ordem de publicação, a cada assinatura que casa com o assunto."""

    def __init__(self) -> None:
        self._subscriptions: list[_Subscription] = []
        self.published: list[tuple[str, Envelope]] = []
        self.announced: list[tuple[str, Mapping[str, Any]]] = []  # avisos: fora do `published`

    async def announce(self, subject: str, message: Mapping[str, Any]) -> None:
        self.announced.append((subject, message))
        for subscription in list(self._subscriptions):
            if subject_matches(subscription.pattern, subject):
                await subscription.handler(subject, message)

    async def publish(self, subject: str, envelope: Envelope) -> None:
        self.published.append((subject, envelope))
        for subscription in list(self._subscriptions):
            if subject_matches(subscription.pattern, subject):
                await subscription.handler(subject, envelope)

    async def subscribe(self, pattern: str, handler: Handler) -> _Subscription:
        subscription = _Subscription(self, pattern, handler)
        self._subscriptions.append(subscription)
        return subscription

    async def consume(self, pattern: str, durable: str, handler: BatchHandler) -> _Subscription:
        """Sem durabilidade em memória: entrega cada mensagem como um lote de uma."""

        async def one(subject: str, envelope: Envelope) -> None:
            await handler([(subject, envelope)])

        return await self.subscribe(pattern, one)

    def remove(self, subscription: _Subscription) -> None:
        self._subscriptions.remove(subscription)
