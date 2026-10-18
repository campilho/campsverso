"""Adaptadores das portas. Único lugar, além dos main.py, com SDKs externos (princípio 3)."""

from campsverso_adapters.archive_jsonl import JsonlArchive, read_world_archive
from campsverso_adapters.blobs import DiskBlobStore, MemoryBlobStore
from campsverso_adapters.bus_memory import InMemoryBus, subject_matches
from campsverso_adapters.bus_nats import NatsBus, StreamSpec
from campsverso_adapters.bus_validating import ContractViolationError, ValidatingBus
from campsverso_adapters.clocks import FakeWallClock, SystemWallClock
from campsverso_adapters.contract_validation import ContractValidator, Problem
from campsverso_adapters.flags_yaml import YamlFlags
from campsverso_adapters.ids import SequentialUuid7Ids, Uuid7Ids
from campsverso_adapters.model_anthropic import AnthropicModel
from campsverso_adapters.realtime_memory import MemoryClient, MemoryRealtime
from campsverso_adapters.settings import (
    EnvSettings,
    GatewaySettings,
    WorldSettings,
    load_env,
    load_world,
)
from campsverso_adapters.store_sqlite import SqliteWorldStore
from campsverso_adapters.telemetry import JsonTelemetry, MemoryTelemetry

__all__ = [
    "AnthropicModel",
    "ContractValidator",
    "ContractViolationError",
    "DiskBlobStore",
    "EnvSettings",
    "FakeWallClock",
    "GatewaySettings",
    "InMemoryBus",
    "JsonTelemetry",
    "JsonlArchive",
    "MemoryBlobStore",
    "MemoryClient",
    "MemoryRealtime",
    "MemoryTelemetry",
    "NatsBus",
    "Problem",
    "SequentialUuid7Ids",
    "SqliteWorldStore",
    "StreamSpec",
    "SystemWallClock",
    "Uuid7Ids",
    "ValidatingBus",
    "WorldSettings",
    "YamlFlags",
    "load_env",
    "load_world",
    "read_world_archive",
    "subject_matches",
]
