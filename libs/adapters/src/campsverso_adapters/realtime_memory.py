"""Tempo real em memória, para testes: cada `connect` é uma UI conectada (ADR-0050)."""

import asyncio
from collections.abc import AsyncIterator

from campsverso_ports import ConnectionClosedError, ConnectionHandler, Message, View

_CLOSED: Message = {}


class MemoryClient:
    """O lado da UI num teste: manda mensagens e espera as do gateway."""

    def __init__(self, view: View, run: str | None = None) -> None:
        self.view: View = view
        self.run = run  # a corrida pedida no modo de assistir (ADR-0068)
        self.inbox: asyncio.Queue[Message] = asyncio.Queue()  # do gateway para a UI
        self.outbox: asyncio.Queue[Message | None] = asyncio.Queue()  # da UI para o gateway
        self.closed = False

    async def send(self, message: Message) -> None:
        await self.outbox.put(message)

    async def receive(self, timeout: float = 5.0) -> Message:
        return await asyncio.wait_for(self.inbox.get(), timeout)

    async def receive_until(self, kind: str, timeout: float = 5.0) -> Message:
        """A próxima mensagem `campsverso.realtime.<kind>.v1`, pulando as outras."""
        async with asyncio.timeout(timeout):
            while True:
                message = await self.inbox.get()
                if message.get("type") == f"campsverso.realtime.{kind}.v1":
                    return message

    async def close(self) -> None:
        await self.outbox.put(None)


class _MemoryConnection:
    def __init__(self, client: MemoryClient) -> None:
        self._client = client

    @property
    def view(self) -> View:
        return self._client.view

    @property
    def run(self) -> str | None:
        return self._client.run

    async def send(self, message: Message) -> None:
        if self._client.closed:
            raise ConnectionClosedError
        await self._client.inbox.put(message)

    async def messages(self) -> AsyncIterator[Message]:
        while (message := await self._client.outbox.get()) is not None:
            yield message

    async def close(self) -> None:
        self._client.closed = True


class MemoryRealtime:
    def __init__(self) -> None:
        self._handler: ConnectionHandler | None = None
        self._ready = asyncio.Event()
        self._stopped = asyncio.Event()
        self._tasks: set[asyncio.Task[None]] = set()

    async def serve(self, handler: ConnectionHandler) -> None:
        self._handler = handler
        self._ready.set()
        await self._stopped.wait()

    async def stop(self) -> None:
        self._stopped.set()
        for task in self._tasks:
            task.cancel()

    async def connect(self, view: View = "player", run_name: str | None = None) -> MemoryClient:
        await self._ready.wait()
        assert self._handler is not None
        client = MemoryClient(view, run_name)
        connection = _MemoryConnection(client)
        handler = self._handler

        async def run() -> None:
            try:
                await handler(connection)
            finally:
                await connection.close()

        task = asyncio.create_task(run())
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return client
