"""Interfaces das portas. Implementações ficam em campsverso_adapters (princípio 3)."""

from campsverso_ports.bus import Envelope, EventBus, Handler, Subscription
from campsverso_ports.clock import WallClock
from campsverso_ports.flags import FlagPort, RuleConfig
from campsverso_ports.ids import IdGenerator

__all__ = [
    "Envelope",
    "EventBus",
    "FlagPort",
    "Handler",
    "IdGenerator",
    "RuleConfig",
    "Subscription",
    "WallClock",
]
