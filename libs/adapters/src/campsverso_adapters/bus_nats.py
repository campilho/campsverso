"""EventBus com NATS JetStream (contratos §6, D3; ADR-0017, ADR-0024).

- `publish` usa o JetStream com o cabeçalho `Nats-Msg-Id` = `id` do envelope: republicar depois de
  uma queda não duplica dentro da janela de deduplicação do stream.
- `consume` cria (ou retoma) um consumidor durável de pull e confirma cada lote depois do handler.
- `subscribe` é uma assinatura comum do NATS, sem persistência.
- Os streams são criados ou atualizados de forma idempotente por quem tem `manage_streams`.
"""

import asyncio
import contextlib
import json
from collections.abc import Awaitable, Sequence
from dataclasses import dataclass
from typing import Any, cast

import nats
import nats.errors
import nats.js.errors
from nats.aio.client import Client
from nats.aio.msg import Msg
from nats.aio.subscription import Subscription as NatsSubscription
from nats.js import api
from nats.js.client import JetStreamContext

from campsverso_ports import (
    BatchHandler,
    BusUnavailableError,
    Envelope,
    Handler,
    PermissionDeniedError,
    Telemetry,
)

_UNAVAILABLE = (
    TimeoutError,  # o nats-py às vezes deixa escapar o TimeoutError do asyncio, não o dele
    nats.errors.TimeoutError,
    nats.errors.NoRespondersError,
    nats.errors.ConnectionClosedError,
    nats.errors.ConnectionReconnectingError,
    nats.errors.OutboundBufferLimitError,
    nats.errors.StaleConnectionError,
)


@dataclass(frozen=True, slots=True)
class StreamSpec:
    """Um stream do JetStream com retenção por limites (D3; ADR-0017)."""

    name: str
    subjects: tuple[str, ...]
    max_age_seconds: float
    max_bytes: int


def _covers(general: str, specific: str) -> bool:
    """Todo assunto que casa com `specific` também casa com `general`?"""
    wanted, given = general.split("."), specific.split(".")
    for index, token in enumerate(wanted):
        if token == ">":
            return len(given) > index
        if index >= len(given):
            return False
        if token != "*" and token != given[index]:
            return False
        if token == "*" and given[index] == ">":
            return False
    return len(wanted) == len(given)


class _CoreSubscription:
    def __init__(self, inner: NatsSubscription) -> None:
        self._inner = inner

    async def unsubscribe(self) -> None:
        with contextlib.suppress(
            nats.errors.ConnectionClosedError, nats.errors.BadSubscriptionError
        ):
            await self._inner.unsubscribe()


class _PullConsumer:
    """Laço de fetch de um consumidor durável. O fetch do nats-py pode engolir o cancelamento,
    então o laço também olha a marca `stopped`."""

    def __init__(self, js: JetStreamContext, stream: str, durable: str) -> None:
        self.stopped = False
        self.task: asyncio.Task[None] | None = None
        self._js = js
        self._stream = stream
        self._durable = durable

    async def caught_up(self) -> None:
        while True:
            info = await self._js.consumer_info(self._stream, self._durable)
            if not info.num_pending and not info.num_ack_pending:
                return
            await asyncio.sleep(0.001)

    async def unsubscribe(self) -> None:
        self.stopped = True
        if self.task is None:
            return
        self.task.cancel()
        # Um erro do handler já foi registrado por _report; aqui só esperamos o laço terminar.
        with contextlib.suppress(asyncio.CancelledError, Exception):
            await asyncio.wait_for(asyncio.shield(self.task), 5)


class NatsBus:
    def __init__(
        self,
        nc: Client,
        js: JetStreamContext,
        streams: Sequence[StreamSpec],
        user: str,
        telemetry: Telemetry | None,
        errors: list[Exception],
        closing: list[bool],
    ) -> None:
        self._nc = nc
        self._js = js
        self._streams = tuple(streams)
        self._user = user
        self._telemetry = telemetry
        self._errors = errors
        self._closing = closing
        self._consumers: list[_PullConsumer] = []

    @classmethod
    async def connect(
        cls,
        url: str,
        *,
        user: str,
        password: str,
        name: str,
        streams: Sequence[StreamSpec],
        manage_streams: bool = False,
        duplicate_window_seconds: float = 120,
        telemetry: Telemetry | None = None,
    ) -> NatsBus:
        errors: list[Exception] = []
        closing: list[bool] = []  # preenchida por close(): a desconexão esperada não é aviso

        async def on_error(error: Exception) -> None:
            errors.append(error)
            if telemetry is not None and "permissions violation" not in str(error).lower():
                telemetry.warning("nats.error", error=str(error))

        async def on_disconnected() -> None:
            if telemetry is not None and not closing:
                telemetry.warning("nats.disconnected")

        async def on_reconnected() -> None:
            if telemetry is not None:
                telemetry.info("nats.reconnected")

        try:
            nc = await nats.connect(  # pyright: ignore[reportUnknownMemberType]
                servers=[url],
                user=user,
                password=password,
                name=name,
                inbox_prefix=f"_INBOX_{user}",
                error_cb=on_error,
                disconnected_cb=on_disconnected,
                reconnected_cb=on_reconnected,
                max_reconnect_attempts=-1,
                reconnect_time_wait=0.5,
                connect_timeout=2,
            )
        except (OSError, *_UNAVAILABLE) as error:
            raise BusUnavailableError(f"sem conexão com o NATS em {url}: {error}") from error
        js = nc.jetstream(timeout=5)  # pyright: ignore[reportUnknownMemberType]
        bus = cls(nc, js, streams, user, telemetry, errors, closing)
        if manage_streams:
            await bus.ensure_streams(duplicate_window_seconds)
        return bus

    async def ensure_streams(self, duplicate_window_seconds: float) -> None:
        for spec in self._streams:
            config = api.StreamConfig(
                name=spec.name,
                subjects=list(spec.subjects),
                retention=api.RetentionPolicy.LIMITS,
                storage=api.StorageType.FILE,
                max_age=spec.max_age_seconds,
                max_bytes=spec.max_bytes,
                duplicate_window=duplicate_window_seconds,
            )
            try:
                await self._js.add_stream(config)  # pyright: ignore[reportUnknownMemberType]
            except nats.js.errors.BadRequestError:
                await self._js.update_stream(config)  # pyright: ignore[reportUnknownMemberType]

    def _stream_for(self, pattern: str) -> str:
        for spec in self._streams:
            if any(_covers(subjects, pattern) for subjects in spec.subjects):
                return spec.name
        raise ValueError(f"nenhum stream cobre {pattern}")

    # ------------------------------------------------------------- publicar

    async def _unless_denied[T](self, request: Awaitable[T], what: str) -> T:
        """Espera a resposta, mas desiste assim que o servidor avisar violação de permissão: sem
        isso, um pedido negado só falharia no fim do tempo limite, como se o NATS tivesse caído."""
        known = len(self._errors)
        task = asyncio.ensure_future(request)
        while not task.done():
            await asyncio.wait({task}, timeout=0.01)
            denied = [e for e in self._errors[known:] if "permissions violation" in str(e).lower()]
            if denied and not task.done():
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError, *_UNAVAILABLE):
                    await task
                raise PermissionDeniedError(f"{self._user} não pode {what}: {denied[-1]}")
        return task.result()

    async def publish(self, subject: str, envelope: Envelope) -> None:
        payload = json.dumps(envelope, ensure_ascii=False, separators=(",", ":")).encode()
        headers = {"Nats-Msg-Id": str(envelope["id"])}
        try:
            await self._unless_denied(
                self._js.publish(subject, payload, headers=headers), f"publicar em {subject}"
            )
        except _UNAVAILABLE as error:
            raise BusUnavailableError(f"publicação em {subject} falhou: {error!r}") from error

    # ------------------------------------------------------------- assinar

    async def _check_permission(self, pattern: str) -> None:
        """O servidor avisa a violação antes de responder ao flush (PING/PONG), mas o nats-py só
        chama o error_cb numa tarefa à parte: damos a ela umas voltas do laço para rodar."""
        await self._nc.flush(timeout=2)
        for _ in range(20):
            for error in self._errors:
                text = str(error)
                if "permissions violation" in text.lower() and f'"{pattern}"' in text:
                    raise PermissionDeniedError(f"{self._user} não pode assinar {pattern}: {text}")
            await asyncio.sleep(0.005)

    async def subscribe(self, pattern: str, handler: Handler) -> _CoreSubscription:
        async def deliver(msg: Msg) -> None:
            await handler(msg.subject, cast(dict[str, Any], json.loads(msg.data)))

        inner = await self._nc.subscribe(pattern, cb=deliver)  # pyright: ignore[reportUnknownMemberType]
        try:
            await self._check_permission(pattern)
        except PermissionDeniedError:
            await _CoreSubscription(inner).unsubscribe()
            raise
        return _CoreSubscription(inner)

    async def consume(self, pattern: str, durable: str, handler: BatchHandler) -> _PullConsumer:
        stream = self._stream_for(pattern)
        for _ in range(120):  # no primeiro `make run`, quem cria os streams pode subir depois
            try:
                await self._unless_denied(self._js.stream_info(stream), f"consultar {stream}")
            except nats.js.errors.NotFoundError:
                await asyncio.sleep(0.5)
                continue
            except Exception:  # sem permissão de consultar: o pull_subscribe dirá o que houver
                pass
            break
        try:
            sub = await self._unless_denied(
                self._js.pull_subscribe(
                    pattern,
                    durable=durable,
                    stream=stream,
                    config=api.ConsumerConfig(
                        ack_policy=api.AckPolicy.EXPLICIT,
                        deliver_policy=api.DeliverPolicy.ALL,
                        ack_wait=30,
                        max_ack_pending=1000,
                    ),
                ),
                f"consumir {pattern}",
            )
        except nats.js.errors.APIError as error:
            if error.code == 403 or "permission" in str(error).lower():
                raise PermissionDeniedError(f"{self._user}: {error}") from error
            raise
        except _UNAVAILABLE as error:
            if self._errors and "permissions violation" in str(self._errors[-1]).lower():
                raise PermissionDeniedError(f"{self._user}: {self._errors[-1]}") from error
            raise BusUnavailableError(f"consumidor {durable} em {stream}: {error!r}") from error

        consumer = _PullConsumer(self._js, stream, durable)

        async def pump() -> None:
            try:
                while not consumer.stopped and not self._nc.is_closed:
                    try:
                        msgs = await sub.fetch(batch=100, timeout=1)
                    except TimeoutError:  # inclui o do nats-py: nada novo no stream
                        continue
                    except Exception as error:  # conexão caindo ou voltando: tenta de novo
                        if self._telemetry is not None and not self._closing:
                            self._telemetry.warning("nats.fetch_failed", error=repr(error))
                        await asyncio.sleep(0.5)
                        continue
                    if consumer.stopped:
                        break  # sem confirmar: volta a ser entregue para quem consumir depois
                    batch = [(m.subject, cast(dict[str, Any], json.loads(m.data))) for m in msgs]
                    await handler(batch)
                    for msg in msgs:
                        await msg.ack()
            finally:
                with contextlib.suppress(Exception):
                    await sub.unsubscribe()

        consumer.task = asyncio.create_task(pump(), name=f"consume:{durable}")
        consumer.task.add_done_callback(self._report)
        self._consumers.append(consumer)
        return consumer

    def _report(self, task: asyncio.Task[None]) -> None:
        if not task.cancelled() and task.exception() is not None and self._telemetry is not None:
            self._telemetry.error(
                "nats.consumer_failed", consumer=task.get_name(), error=repr(task.exception())
            )

    async def close(self) -> None:
        self._closing.append(True)
        for consumer in self._consumers:
            await consumer.unsubscribe()
        with contextlib.suppress(nats.errors.ConnectionClosedError):
            await self._nc.drain()
