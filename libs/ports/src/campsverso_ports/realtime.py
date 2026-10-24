"""Porta do tempo real: conexões WebSocket entre o gateway e a UI (escopo §4.1; ADR-0050).

A porta só transporta mensagens JSON já decodificadas. O que cada mensagem significa está em
`contracts/realtime`; quem decide o que mandar é o serviço do gateway.
"""

from collections.abc import AsyncIterator, Awaitable, Callable, Mapping
from typing import Any, Literal, Protocol

type View = Literal["player", "operator"]
type Message = Mapping[str, Any]


class ConnectionClosedError(Exception):
    """A UI fechou a conexão (ou ela caiu); não adianta mandar mais nada por ela."""


class RealtimeConnection(Protocol):
    @property
    def view(self) -> View:
        """A visão pedida pela UI ao conectar (`/ws?view=player|operator`)."""
        ...

    @property
    def run(self) -> str | None:
        """A corrida pedida no modo de assistir (`/ws?run=<nome>`; ADR-0068), ou None."""
        ...

    async def send(self, message: Message) -> None:
        """Manda uma mensagem; levanta ConnectionClosedError se a conexão já fechou."""
        ...

    def messages(self) -> AsyncIterator[Message]:
        """As mensagens da UI, em ordem, até a conexão fechar. JSON inválido chega como `{}`."""
        ...

    async def close(self) -> None: ...


type ConnectionHandler = Callable[[RealtimeConnection], Awaitable[None]]


class RealtimeGateway(Protocol):
    async def serve(self, handler: ConnectionHandler) -> None:
        """Aceita conexões e chama `handler` para cada uma, até `stop`. A conexão fecha quando o
        handler termina."""
        ...

    async def stop(self) -> None: ...
