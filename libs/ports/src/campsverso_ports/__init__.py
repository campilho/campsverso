"""Interfaces das portas. Implementações ficam em campsverso_adapters (princípio 3)."""

from campsverso_ports.archive import EventArchive
from campsverso_ports.blobs import BlobStore
from campsverso_ports.bus import (
    BatchHandler,
    BusUnavailableError,
    Envelope,
    EventBus,
    Handler,
    PermissionDeniedError,
    Subscription,
)
from campsverso_ports.clock import WallClock
from campsverso_ports.flags import FlagPort, RuleConfig
from campsverso_ports.ids import IdGenerator
from campsverso_ports.store import (
    Commit,
    InputKind,
    InputRow,
    OutboxRow,
    SnapshotRef,
    StoreState,
    WorldStore,
)
from campsverso_ports.telemetry import Telemetry
from campsverso_ports.validation import EnvelopeValidator

__all__ = [
    "BatchHandler",
    "BlobStore",
    "BusUnavailableError",
    "Commit",
    "Envelope",
    "EnvelopeValidator",
    "EventArchive",
    "EventBus",
    "FlagPort",
    "Handler",
    "IdGenerator",
    "InputKind",
    "InputRow",
    "OutboxRow",
    "PermissionDeniedError",
    "RuleConfig",
    "SnapshotRef",
    "StoreState",
    "Subscription",
    "Telemetry",
    "WallClock",
    "WorldStore",
]
