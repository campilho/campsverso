"""A agenda (ADR-0069): eventos que se repetem pelo calendário, como a feira a cada 7 dias. No
escritório, a reunião de toda segunda; no vilarejo, o dia de feira da praça."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Recurring:
    """Um evento a cada `every` dias, a partir do dia `first` (os dias contam de 1)."""

    every: int
    first: int

    def happens(self, day: int) -> bool:
        return day >= self.first and (day - self.first) % self.every == 0

    def next_on(self, day: int) -> int:
        """O dia do evento a partir de `day` (ele mesmo, se for dia de evento)."""
        if day <= self.first:
            return self.first
        return day + (-(day - self.first)) % self.every
