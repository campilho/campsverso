"""Porta do barramento de eventos (contratos §12)."""

from collections.abc import Awaitable, Callable, Mapping, Sequence
from typing import Any, Protocol

type Envelope = Mapping[str, Any]
type Handler = Callable[[str, Envelope], Awaitable[None]]
type BatchHandler = Callable[[Sequence[tuple[str, Envelope]]], Awaitable[None]]


class BusUnavailableError(Exception):
    """O barramento não respondeu (sem conexão ou tempo esgotado). Dá para tentar de novo."""


class PermissionDeniedError(Exception):
    """O servidor recusou a operação para esta credencial (permissões de assunto; escopo A8)."""


class Subscription(Protocol):
    async def unsubscribe(self) -> None: ...


class Consumer(Subscription, Protocol):
    async def caught_up(self) -> None:
        """Volta quando tudo o que já estava no stream foi entregue ao handler e confirmado.

        Serve para ler dois streams em ordem: antes de reagir a um evento de um deles, alcança
        o outro (a percepção alcança `world` antes de montar a foto de um pedido de decisão).
        """
        ...


class EventBus(Protocol):
    """Publicar e assinar por assunto. Padrões de assinatura seguem o NATS.

    `*` casa exatamente um token e `>` casa um ou mais tokens no fim.
    """

    async def publish(self, subject: str, envelope: Envelope) -> None:
        """Publica uma vez por `id`: republicar o mesmo envelope não duplica (contratos §5)."""
        ...

    async def subscribe(self, pattern: str, handler: Handler) -> Subscription:
        """Assinatura efêmera: só recebe o que for publicado enquanto estiver ativa."""
        ...

    async def consume(self, pattern: str, durable: str, handler: BatchHandler) -> Consumer:
        """Consumidor durável: entrega em ordem o que chegou desde a última confirmação.

        Cada lote só é confirmado depois que o handler termina sem erro; o que não foi
        confirmado volta a ser entregue, inclusive depois de o processo cair (ADR-0017).
        """
        ...
