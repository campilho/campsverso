"""Ritmo do relógio (tempo §3, §5): contínuo com acumulador, máximo e pausado.

Mede o tempo real pela porta WallClock e decide quantos ticks rodar; o núcleo nunca vê o relógio
de parede (princípio 4). O lockstep do modo máximo chega com os controladores, no M3.
"""

import asyncio
import contextlib

from campsverso_kernel.pacer import RealTimePacer
from campsverso_kernel.service import KernelService
from campsverso_ports import WallClock

_MAX_BATCH = 60  # ticks por volta no modo máximo, antes de ceder o laço a quem espera
_MAX_BEHIND = 600  # no contínuo, ticks a mais numa volta só (depois de uma pausa do processo)
_IDLE_SECONDS = 0.05


async def _wait(stop: asyncio.Event, seconds: float) -> None:
    with contextlib.suppress(TimeoutError):
        await asyncio.wait_for(stop.wait(), seconds)


class ClockLoop:
    def __init__(self, service: KernelService, clock: WallClock) -> None:
        self._service = service
        self._clock = clock

    async def run(self, stop: asyncio.Event) -> None:
        service, core = self._service, self._service.core
        tick_seconds = core.calendar.tick_seconds
        pacer = RealTimePacer(tick_seconds, core.scale)
        last = self._clock.monotonic()
        while not stop.is_set():
            if service.failure is not None:
                raise service.failure
            now = self._clock.monotonic()
            elapsed, last = now - last, now
            if core.paused:
                await _wait(stop, _IDLE_SECONDS)
                continue
            if core.mode == "max":
                await service.run_ticks(_MAX_BATCH)
                await asyncio.sleep(0)
                continue
            pacer.scale = core.scale
            ticks = pacer.ticks_for(elapsed)
            if ticks:
                await service.run_ticks(min(ticks, _MAX_BEHIND))
            await _wait(stop, min(_IDLE_SECONDS, tick_seconds / core.scale))
