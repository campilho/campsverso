"""Acumulador do game loop clássico (tempo §3.3): tempo real decorrido -> ticks a rodar."""


class RealTimePacer:
    """Não lê relógio: recebe o tempo real decorrido de quem o mediu (princípio 4)."""

    def __init__(self, tick_seconds: int, scale: float) -> None:
        self._tick_seconds = tick_seconds
        self.scale = scale
        self._accumulated = 0.0

    def ticks_for(self, wall_seconds: float) -> int:
        self._accumulated += wall_seconds * self.scale
        ticks = int(self._accumulated // self._tick_seconds)
        self._accumulated -= ticks * self._tick_seconds
        return ticks
