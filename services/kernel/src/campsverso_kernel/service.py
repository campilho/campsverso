"""Serviço do kernel: envolve o núcleo com IO (plano do M2 §1; ADR-0038).

Cada operação do núcleo (um comando ou um tick) vira uma transação no WorldStore: os fatos já
envelopados no outbox, a entrada no diário e a fronteira de tick gravam juntos. Só depois o
publicador lê o outbox em ordem de seq e publica. Se o barramento cair, o mundo segue e o outbox
cresce; quando ele volta, o publicador alcança. Republicar não duplica: o id do evento vai junto.
"""

from collections import OrderedDict
from collections.abc import Mapping, Sequence
from typing import Any

from campsverso_contracts import CONTRACT_TYPES, subject
from campsverso_kernel.core import KernelCore
from campsverso_kernel.engine import Engine, Snapshot
from campsverso_kernel.facts import Fact
from campsverso_kernel.world import plain
from campsverso_ports import (
    BlobStore,
    BusUnavailableError,
    Commit,
    Envelope,
    EventBus,
    IdGenerator,
    InputRow,
    OutboxRow,
    SnapshotRef,
    Subscription,
    Telemetry,
    WallClock,
    WorldStore,
)

_RECENT_IDS = 10_000  # seq -> id, para resolver causationid entre fatos próximos
_PUBLISH_BATCH = 256
_RETRY_SECONDS = 1.0


class KernelService:
    def __init__(
        self,
        engine: Engine,
        bus: EventBus,
        clock: WallClock,
        ids: IdGenerator,
        store: WorldStore,
        blobs: BlobStore,
        telemetry: Telemetry,
        *,
        keep_full: int = 0,
    ) -> None:
        self.engine = engine
        self._bus = bus
        self._clock = clock
        self._ids = ids
        self._store = store
        self._blobs = blobs
        self._telemetry = telemetry
        self._keep_full = keep_full
        self._worldid = engine.core.config.worldid
        self._source = f"/kernel/{self._worldid}"
        state = store.state()
        self._new = state is None
        self._next_input = 1 if state is None else state.next_input
        self._ids_by_seq: OrderedDict[int, str] = OrderedDict(store.recent_ids(_RECENT_IDS))
        self._subscription: Subscription | None = None
        self._publishing = False
        self._retry_at = 0.0
        self.failure: BaseException | None = None  # erro do consumidor de comandos

    @property
    def core(self) -> KernelCore:
        return self.engine.core

    # ------------------------------------------------------------- ciclo de vida

    async def start(self) -> None:
        if self._new:
            self.core.start()
            self._commit(snapshot=self.engine.snapshot())  # o snapshot inicial nunca sai
            self._new = False
        await self.publish_pending()
        self._subscription = await self._bus.consume(
            f"campsverso.{self._worldid}.cmd.>", f"kernel-{self._worldid}", self._on_commands
        )

    async def stop(self) -> None:
        """Parada elegante: grava um snapshot, para que a próxima versão retome sem incrementais."""
        if self._subscription is not None:
            await self._subscription.unsubscribe()
            self._subscription = None
        if self._has_news():
            row = InputRow(self._next_input, self.core.tick, "snapshot")
            self._next_input += 1
            self._commit(inputs=[row], snapshot=self.engine.snapshot())
        await self.publish_pending()

    def _has_news(self) -> bool:
        state, snapshots = self._store.state(), self._store.snapshots()
        if state is None or not snapshots:
            return True
        latest = snapshots[-1]
        return (state.tick, state.next_input, state.next_seq) != (
            latest.tick,
            latest.next_input,
            latest.next_seq,
        ) or self.core.tick != latest.tick

    # ------------------------------------------------------------- entradas

    async def _on_commands(self, batch: Sequence[tuple[str, Envelope]]) -> None:
        try:
            for _, envelope in batch:
                self.submit(envelope)
            await self.publish_pending()
        except Exception as error:
            self.failure = error
            raise

    def submit(self, command: Mapping[str, Any]) -> bool:
        """Grava o comando no diário junto com o que ele produziu. Repetido pelo id, ignora."""
        command_id = str(command.get("id") or "")
        if command_id and self._store.has_command(command_id):
            return False
        row = InputRow(self._next_input, self.core.tick, "command", command_id or None, command)
        self.engine.submit(command)
        self._next_input += 1
        self._commit(inputs=[row])
        return True

    async def run_ticks(self, ticks: int) -> None:
        for _ in range(ticks):
            self._commit(snapshot=self.engine.step())
            await self.publish_pending()

    # ------------------------------------------------------------- outbox

    def _commit(self, *, inputs: Sequence[InputRow] = (), snapshot: Snapshot | None = None) -> None:
        facts = self.core.drain()
        if not facts and not inputs and snapshot is None:
            return  # tick sem fatos: reexecutá-lo depois de uma queda não muda nada
        rows = [self._row(fact) for fact in facts]
        ref = None
        if snapshot is not None:
            self._blobs.put(snapshot.ref, snapshot.data)
            ref = SnapshotRef(
                ref=snapshot.ref,
                tick=snapshot.tick,
                sha256=snapshot.sha256,
                next_seq=snapshot.next_seq,
                next_input=self._next_input,
                version=self.engine.version.key,
            )
        self._store.commit(Commit(self.core.tick, self.engine.version.key, inputs, rows, ref))
        if ref is not None:
            self._rotate()

    def _rotate(self) -> None:
        """Mantém o snapshot inicial e os `keep_full` mais recentes; o outbox encolhe junto."""
        if self._keep_full < 1:
            return
        snapshots = self._store.snapshots()
        extra = snapshots[1 : -self._keep_full]
        for old in extra:
            self._store.forget_snapshot(old.ref)
            self._blobs.delete(old.ref)
        if extra:
            self._store.prune_outbox(snapshots[len(extra) + 1].next_seq)

    async def publish_pending(self) -> None:
        """Publica o outbox em ordem de seq. Quem chega durante uma publicação só grava e sai."""
        if self._publishing or self._clock.monotonic() < self._retry_at:
            return
        self._publishing = True
        published = -1
        try:
            while rows := self._store.unpublished(_PUBLISH_BATCH):
                for row in rows:
                    await self._bus.publish(row.subject, row.envelope)
                    published = row.seq
                self._store.mark_published(published)
        except BusUnavailableError as error:
            self._retry_at = self._clock.monotonic() + _RETRY_SECONDS
            self._telemetry.warning("kernel.publish_failed", error=str(error))
        finally:
            if published >= 0:
                self._store.mark_published(published)
            self._publishing = False

    def _row(self, fact: Fact) -> OutboxRow:
        envelope = self._envelope(fact)
        avatar_id = fact.data.get("avatar_id")
        return OutboxRow(fact.seq, subject(fact.type, self._worldid, avatar_id), envelope)

    def _envelope(self, fact: Fact) -> dict[str, Any]:
        info = CONTRACT_TYPES[fact.type]
        event_id = self._ids.new_id()
        self._ids_by_seq[fact.seq] = event_id
        if len(self._ids_by_seq) > _RECENT_IDS:
            self._ids_by_seq.popitem(last=False)
        envelope: dict[str, Any] = {
            "specversion": "1.0",
            "id": event_id,
            "source": self._source,
            "type": fact.type,
            "time": self._clock.now().isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            "datacontenttype": "application/json",
            "dataschema": info.dataschema,
            "worldid": self._worldid,
            "cartridge": self.core.definition.top.id,
            "tick": fact.tick,
            "simtime": self.core.calendar.simtime_iso(fact.tick),
            "seq": fact.seq,
            "actor": "system/kernel",
            "provenance": "simulated",
            "visibility": info.visibility,
            "data": plain(fact.data),
        }
        avatar_id = fact.data.get("avatar_id")
        if avatar_id is not None:
            envelope["subject"] = f"avatar/{avatar_id}"
        causation = (
            self._ids_by_seq.get(fact.caused_by)
            if isinstance(fact.caused_by, int)
            else fact.caused_by
        )
        if causation:
            envelope["causationid"] = causation
        correlation = self._ids.new_id() if fact.opens_correlation else fact.correlation
        if correlation:
            envelope["correlationid"] = correlation
        return envelope
