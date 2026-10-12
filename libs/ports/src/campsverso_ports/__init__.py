"""Interfaces das portas. Implementações ficam em campsverso_adapters (princípio 3)."""

from campsverso_ports.archive import EventArchive
from campsverso_ports.blobs import BlobStore
from campsverso_ports.bus import (
    BatchHandler,
    BusUnavailableError,
    Consumer,
    Envelope,
    EventBus,
    Handler,
    PermissionDeniedError,
    Subscription,
)
from campsverso_ports.clock import WallClock
from campsverso_ports.flags import FlagPort, RuleConfig
from campsverso_ports.ids import IdGenerator
from campsverso_ports.realtime import (
    ConnectionClosedError,
    ConnectionHandler,
    Message,
    RealtimeConnection,
    RealtimeGateway,
    View,
)
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
    "ConnectionClosedError",
    "ConnectionHandler",
    "Consumer",
    "Envelope",
    "EnvelopeValidator",
    "EventArchive",
    "EventBus",
    "FlagPort",
    "Handler",
    "IdGenerator",
    "InputKind",
    "InputRow",
    "Message",
    "OutboxRow",
    "PermissionDeniedError",
    "RealtimeConnection",
    "RealtimeGateway",
    "RuleConfig",
    "SnapshotRef",
    "StoreState",
    "Subscription",
    "Telemetry",
    "View",
    "WallClock",
    "WorldStore",
]
