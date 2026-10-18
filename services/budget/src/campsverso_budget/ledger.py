"""O livro-caixa da guarda (ADR-0058): quanto já se gastou por dia simulado e no total, e quais
avisos já saíram. Função pura do que entrou; serializável em JSON, para voltar depois de uma
queda."""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal

THRESHOLDS: tuple[int, ...] = (50, 80, 100)
MAX_SEEN = 2000  # ids recentes, para não contar duas vezes uma reentrega
type Scope = Literal["day", "total"]


@dataclass(frozen=True, slots=True)
class BudgetLimits:
    usd_per_sim_day: float
    usd_total: float


@dataclass(frozen=True, slots=True)
class Notice:
    scope: Scope
    day: int | None
    threshold_pct: int
    spent_usd: float
    limit_usd: float

    @property
    def exceeded(self) -> bool:
        return self.threshold_pct >= 100


class BudgetLedger:
    def __init__(self, limits: BudgetLimits, state: Mapping[str, Any] | None = None) -> None:
        raw: Mapping[str, Any] = state or {}
        self.limits = limits
        self.by_day: dict[str, float] = {k: float(v) for k, v in raw.get("by_day", {}).items()}
        self.total: float = float(raw.get("total", 0.0))
        self.reached: dict[str, list[int]] = {
            k: [int(p) for p in v] for k, v in raw.get("reached", {}).items()
        }
        self.seen: list[str] = [str(i) for i in raw.get("seen", [])]

    def export(self) -> dict[str, Any]:
        return {
            "by_day": self.by_day,
            "total": self.total,
            "reached": self.reached,
            "seen": self.seen[-MAX_SEEN:],
        }

    def record(self, event_id: str, day: int, cost_usd: float) -> list[Notice]:
        """Soma uma chamada cobrada e devolve os avisos novos, do menor limiar ao maior."""
        if event_id in self.seen:
            return []
        self.seen.append(event_id)
        del self.seen[:-MAX_SEEN]
        key = str(day)
        self.by_day[key] = round(self.by_day.get(key, 0.0) + cost_usd, 8)
        self.total = round(self.total + cost_usd, 8)
        notices: list[Notice] = []
        notices += self._notices("day", day, self.by_day[key], self.limits.usd_per_sim_day)
        notices += self._notices("total", None, self.total, self.limits.usd_total)
        return notices

    def _notices(self, scope: Scope, day: int | None, spent: float, limit: float) -> list[Notice]:
        key = f"{scope}:{day}" if day is not None else scope
        announced = self.reached.setdefault(key, [])
        notices: list[Notice] = []
        for pct in THRESHOLDS:
            if pct not in announced and spent >= limit * pct / 100:
                announced.append(pct)
                notices.append(Notice(scope, day, pct, spent, limit))
        return notices
