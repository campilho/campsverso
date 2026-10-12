"""Kernel: relógio, modelo de mundo, ações, regras e outbox. Único escritor da verdade do mundo."""

from campsverso_kernel.core import KernelCore, WorldConfig
from campsverso_kernel.definition import WorldDefinition
from campsverso_kernel.engine import Engine, Snapshot
from campsverso_kernel.errors import DefinitionError, WorldRuleError
from campsverso_kernel.facts import Fact
from campsverso_kernel.loader import build_world, discover, resolve_chain
from campsverso_kernel.pacer import RealTimePacer
from campsverso_kernel.recovery import Recovery, RecoveryError, open_world
from campsverso_kernel.runner import ClockLoop
from campsverso_kernel.service import KernelService
from campsverso_kernel.version import RunVersion, run_version

__all__ = [
    "ClockLoop",
    "DefinitionError",
    "Engine",
    "Fact",
    "KernelCore",
    "KernelService",
    "RealTimePacer",
    "Recovery",
    "RecoveryError",
    "RunVersion",
    "Snapshot",
    "WorldConfig",
    "WorldDefinition",
    "WorldRuleError",
    "build_world",
    "discover",
    "open_world",
    "resolve_chain",
    "run_version",
]
