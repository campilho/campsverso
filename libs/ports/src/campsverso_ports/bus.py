"""Porta do barramento de eventos (contratos §12)."""

from collections.abc import Awaitable, Callable, Mapping
from typing import Any, Protocol

type Envelope = Mapping[str, Any]
type Handler = Callable[[str, Envelope], Awaitable[None]]


class Subscription(Protocol):
    async def unsubscribe(self) -> None: ...


class EventBus(Protocol):
    """Publicar e assinar por assunto. Padrões de assinatura seguem o NATS.

    `*` casa exatamente um token e `>` casa um ou mais tokens no fim.
    """

    async def publish(self, subject: str, envelope: Envelope) -> None: ...

    async def subscribe(self, pattern: str, handler: Handler) -> Subscription: ...
