"""Adaptadores das portas. Único lugar, além dos main.py, com SDKs externos (princípio 3)."""

from campsverso_adapters.bus_memory import InMemoryBus, subject_matches
from campsverso_adapters.bus_validating import ContractViolationError, ValidatingBus
from campsverso_adapters.clocks import FakeWallClock, SystemWallClock
from campsverso_adapters.contract_validation import ContractValidator, Problem
from campsverso_adapters.flags_yaml import YamlFlags
from campsverso_adapters.ids import SequentialUuid7Ids, Uuid7Ids

__all__ = [
    "ContractValidator",
    "ContractViolationError",
    "FakeWallClock",
    "InMemoryBus",
    "Problem",
    "SequentialUuid7Ids",
    "SystemWallClock",
    "Uuid7Ids",
    "ValidatingBus",
    "YamlFlags",
    "subject_matches",
]
