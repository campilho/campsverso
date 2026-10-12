"""Kernel: relógio, modelo de mundo, ações, regras e outbox. Único escritor da verdade do mundo."""

from campsverso_kernel.core import KernelCore, WorldConfig
from campsverso_kernel.definition import WorldDefinition
from campsverso_kernel.errors import DefinitionError, WorldRuleError
from campsverso_kernel.facts import Fact
from campsverso_kernel.loader import build_world, discover, resolve_chain
from campsverso_kernel.pacer import RealTimePacer
from campsverso_kernel.service import KernelService

__all__ = [
    "DefinitionError",
    "Fact",
    "KernelCore",
    "KernelService",
    "RealTimePacer",
    "WorldConfig",
    "WorldDefinition",
    "WorldRuleError",
    "build_world",
    "discover",
    "resolve_chain",
]
