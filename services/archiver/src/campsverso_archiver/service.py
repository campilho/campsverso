"""Arquivador: lê todos os streams com consumidores duráveis e grava o JSONL (escopo A6; D3).

Cada lote só é confirmado depois de gravado e sincronizado no disco. Se o arquivador cair, o
JetStream guarda o que ele ainda não confirmou; ao voltar, ele retoma do ponto certo, e o que
chegar repetido (gravado, mas não confirmado) é descartado pelo id.
"""

from collections.abc import Sequence

from campsverso_ports import Envelope, EventArchive, EventBus, Subscription, Telemetry

STREAMS = ("world", "agent", "observer", "internal", "cmd")


class ArchiverService:
    def __init__(
        self, bus: EventBus, archive: EventArchive, telemetry: Telemetry, *, name: str = "archiver"
    ) -> None:
        self._bus = bus
        self._archive = archive
        self._telemetry = telemetry
        self._name = name
        self._subscriptions: list[Subscription] = []
        self.written = 0
        self.duplicates = 0
        self.failure: BaseException | None = None

    async def start(self) -> None:
        for path in self._archive.compress_old():
            self._telemetry.info("archiver.compressed", file=path)
        for stream in STREAMS:
            self._subscriptions.append(
                await self._bus.consume(
                    f"campsverso.*.{stream}.>", f"{self._name}-{stream}", self._on_batch
                )
            )

    async def _on_batch(self, batch: Sequence[tuple[str, Envelope]]) -> None:
        try:
            written = sum(self._archive.append(envelope) for _, envelope in batch)
            self._archive.flush()
        except Exception as error:
            self.failure = error
            raise
        self.written += written
        self.duplicates += len(batch) - written

    async def stop(self) -> None:
        for subscription in self._subscriptions:
            await subscription.unsubscribe()
        self._subscriptions.clear()
        self._archive.close()
