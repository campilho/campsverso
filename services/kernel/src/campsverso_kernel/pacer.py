"""Acumulador do game loop clássico (tempo §3.3): tempo real decorrido -> ticks a rodar."""


class RealTimePacer:
    """Não lê relógio: recebe o tempo real decorrido de quem o mediu (princípio 4)."""

    def __init__(self, tick_seconds: int, scale: float) -> None:
        self._tick_seconds = tick_seconds
        self.scale = scale
        self._accumulated = 0.0  # segundos simulados ainda não virados em ticks; negativo é dívida

    def ticks_for(self, wall_seconds: float) -> int:
        self._accumulated += wall_seconds * self.scale
        if self._accumulated < self._tick_seconds:
            return 0  # inclusive enquanto paga a dívida de um tick antecipado
        ticks = int(self._accumulated // self._tick_seconds)
        self._accumulated -= ticks * self._tick_seconds
        return ticks

    def advance_early(self) -> bool:
        """Um tick agora, descontado do tempo real que ainda vai passar (ADR-0057).

        Só um antecipado por vez: com a dívida em aberto, o próximo comando espera o ritmo normal,
        então a quantidade de ticks por minuto real não muda.
        """
        if self._accumulated < 0:
            return False
        self._accumulated -= self._tick_seconds
        return True
