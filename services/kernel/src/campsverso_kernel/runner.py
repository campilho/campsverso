"""Ritmo do relógio (tempo §3, §5): contínuo com acumulador, máximo e pausado.

Mede o tempo real pela porta WallClock e decide quantos ticks rodar; o núcleo nunca vê o relógio
de parede (princípio 4). O lockstep do modo máximo chega com os controladores, no M3.
"""

import asyncio
import contextlib

from campsverso_kernel.pacer import RealTimePacer
from campsverso_kernel.service import KernelService
from campsverso_ports import Telemetry, WallClock

_MAX_BATCH = 60  # ticks por volta no modo máximo, antes de ceder o laço a quem espera
_MAX_BEHIND = 600  # no contínuo, ticks a mais numa volta só (depois de uma pausa do processo)
_IDLE_SECONDS = 0.05
_WARN_EVERY = 10.0  # segundos de espera no lockstep entre um aviso e outro (ADR-0047)


async def _wait(stop: asyncio.Event, seconds: float) -> None:
    with contextlib.suppress(TimeoutError):
        await asyncio.wait_for(stop.wait(), seconds)


async def _wait_any(events: tuple[asyncio.Event, ...], seconds: float) -> None:
    waiters = [asyncio.ensure_future(e.wait()) for e in events]
    try:
        await asyncio.wait(waiters, timeout=seconds, return_when=asyncio.FIRST_COMPLETED)
    finally:
        for waiter in waiters:
            waiter.cancel()


class ClockLoop:
    def __init__(
        self, service: KernelService, clock: WallClock, telemetry: Telemetry | None = None
    ) -> None:
        self._service = service
        self._clock = clock
        self._telemetry = telemetry

    async def run(self, stop: asyncio.Event) -> None:
        service, core = self._service, self._service.core
        tick_seconds = core.calendar.tick_seconds
        pacer = RealTimePacer(tick_seconds, core.scale)
        last = self._clock.monotonic()
        waiting_since: float | None = None  # desde quando o lockstep espera um controlador
        warned = 0.0  # segundos de espera já avisados
        while not stop.is_set():
            if service.failure is not None:
                raise service.failure
            now = self._clock.monotonic()
            elapsed, last = now - last, now
            if core.paused:
                await _wait(stop, _IDLE_SECONDS)
                continue
            if core.mode == "max":
                if core.lockstep_blocked:
                    waiting_since = now if waiting_since is None else waiting_since
                    waited = now - waiting_since
                    if self._telemetry is not None and waited >= _WARN_EVERY + warned:
                        self._telemetry.warning(
                            "kernel.lockstep_waiting", tick=core.tick, seconds=round(waited, 1)
                        )
                        warned += _WARN_EVERY
                    service.commands_arrived.clear()
                    await _wait_any((stop, service.commands_arrived), _IDLE_SECONDS)
                    continue
                waiting_since, warned = None, 0.0
                await service.run_ticks(_MAX_BATCH)
                await asyncio.sleep(0)
                continue
            pacer.scale = core.scale
            ticks = pacer.ticks_for(elapsed)
            if ticks:
                await service.run_ticks(min(ticks, _MAX_BEHIND))
            await _wait(stop, min(_IDLE_SECONDS, tick_seconds / core.scale))
