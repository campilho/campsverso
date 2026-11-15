"""O livro-caixa da guarda (ADR-0058): quanto já se gastou por dia simulado, por pedido do
escritório (ADR-0080) e no total, e quais avisos já saíram. Função pura do que entrou; serializável
em JSON, para voltar depois de uma queda.

Cada limiar avisa uma vez. O teto é diferente: depois de estourado, toda chamada cobrada devolve o
aviso de novo, marcado `repeated`, para a guarda pausar outra vez (ou lembrar a mente de que está
desligada). Sem isso, o operador retomava o mundo e o gasto seguia sem limite.

Os tetos vêm do arquivo do mundo até o operador mudá-los com o mundo vivo (`cmd.ops.budget.set`);
daí em diante, os do comando ficam gravados aqui e valem também depois de uma queda. Um teto que
sobe acima do gasto deixa de estar estourado, e os avisos acima do gasto voltam a valer."""

from collections.abc import Mapping
from dataclasses import dataclass, replace
from typing import Any, Literal

THRESHOLDS: tuple[int, ...] = (50, 80, 100)
MAX_SEEN = 2000  # ids recentes, para não contar duas vezes uma reentrega
type Scope = Literal["day", "ticket", "total"]


@dataclass(frozen=True, slots=True)
class BudgetLimits:
    usd_per_sim_day: float
    usd_total: float
    usd_per_ticket: float | None = None  # sem ele, o gasto por pedido só é somado

    def changed(self, changes: Mapping[str, Any]) -> BudgetLimits:
        """Os tetos com o que o comando trouxe; o que não veio fica."""
        fields = ("usd_per_sim_day", "usd_total", "usd_per_ticket")
        return replace(self, **{k: float(changes[k]) for k in fields if changes.get(k) is not None})

    def export(self) -> dict[str, float]:
        out = {"usd_per_sim_day": self.usd_per_sim_day, "usd_total": self.usd_total}
        if self.usd_per_ticket is not None:
            out["usd_per_ticket"] = self.usd_per_ticket
        return out

    @classmethod
    def load(cls, raw: Mapping[str, Any]) -> BudgetLimits:
        ticket = raw.get("usd_per_ticket")
        return cls(
            float(raw["usd_per_sim_day"]),
            float(raw["usd_total"]),
            None if ticket is None else float(ticket),
        )


@dataclass(frozen=True, slots=True)
class Notice:
    scope: Scope
    day: int | None
    threshold_pct: int
    spent_usd: float
    limit_usd: float
    repeated: bool = False  # o teto já tinha estourado: pausa de novo, sem limiar novo
    ticket_id: str | None = None

    @property
    def exceeded(self) -> bool:
        return self.threshold_pct >= 100


class BudgetLedger:
    def __init__(self, limits: BudgetLimits, state: Mapping[str, Any] | None = None) -> None:
        raw: Mapping[str, Any] = state or {}
        changed = raw.get("limits")
        self.limits = limits if changed is None else BudgetLimits.load(changed)
        self.limits_changed = changed is not None
        self.by_day: dict[str, float] = {k: float(v) for k, v in raw.get("by_day", {}).items()}
        self.by_ticket: dict[str, float] = {
            k: float(v) for k, v in raw.get("by_ticket", {}).items()
        }
        self.total: float = float(raw.get("total", 0.0))
        self.reached: dict[str, list[int]] = {
            k: [int(p) for p in v] for k, v in raw.get("reached", {}).items()
        }
        self.seen: list[str] = [str(i) for i in raw.get("seen", [])]
        last = raw.get("last_day")
        self.last_day: int | None = None if last is None else int(last)

    def export(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "by_day": self.by_day,
            "by_ticket": self.by_ticket,
            "total": self.total,
            "reached": self.reached,
            "seen": self.seen[-MAX_SEEN:],
            "last_day": self.last_day,
        }
        if self.limits_changed:
            out["limits"] = self.limits.export()
        return out

    def record(
        self, event_id: str, day: int, cost_usd: float, ticket_id: str | None = None
    ) -> list[Notice]:
        """Soma uma chamada cobrada e devolve os avisos novos, do menor limiar ao maior: o dia, o
        pedido, o total. Com um teto já estourado, devolve o aviso dele de novo (`repeated`)."""
        if event_id in self.seen:
            return []
        self.seen.append(event_id)
        del self.seen[:-MAX_SEEN]
        key = str(day)
        self.last_day = day
        self.by_day[key] = round(self.by_day.get(key, 0.0) + cost_usd, 8)
        self.total = round(self.total + cost_usd, 8)
        notices: list[Notice] = []
        notices += self._notices("day", day, None, self.by_day[key], self.limits.usd_per_sim_day)
        if ticket_id is not None:
            spent = round(self.by_ticket.get(ticket_id, 0.0) + cost_usd, 8)
            self.by_ticket[ticket_id] = spent
            if self.limits.usd_per_ticket is not None:
                notices += self._notices(
                    "ticket", None, ticket_id, spent, self.limits.usd_per_ticket
                )
        notices += self._notices("total", None, None, self.total, self.limits.usd_total)
        return notices

    def set_limits(self, limits: BudgetLimits) -> None:
        """Os tetos novos do operador. Os avisos que o gasto de agora não alcança mais voltam a
        valer: subir o teto acima do gasto desfaz o estouro."""
        self.limits = limits
        self.limits_changed = True
        for key, announced in self.reached.items():
            spent, limit = self._spent_and_limit(key)
            announced[:] = [p for p in announced if limit is not None and spent >= limit * p / 100]

    def exceeded_now(self) -> list[str]:
        """Os tetos estourados agora: o do último dia (`day`), `total` e os pedidos, pelo id."""
        out: list[str] = []
        if self.last_day is not None and THRESHOLDS[-1] in self.reached.get(
            f"day:{self.last_day}", []
        ):
            out.append("day")
        if THRESHOLDS[-1] in self.reached.get("total", []):
            out.append("total")
        out += sorted(
            key.removeprefix("ticket:")
            for key, announced in self.reached.items()
            if key.startswith("ticket:") and THRESHOLDS[-1] in announced
        )
        return out

    def _spent_and_limit(self, key: str) -> tuple[float, float | None]:
        scope, _, which = key.partition(":")
        if scope == "day":
            return self.by_day.get(which, 0.0), self.limits.usd_per_sim_day
        if scope == "ticket":
            return self.by_ticket.get(which, 0.0), self.limits.usd_per_ticket
        return self.total, self.limits.usd_total

    def _notices(
        self, scope: Scope, day: int | None, ticket_id: str | None, spent: float, limit: float
    ) -> list[Notice]:
        key = f"{scope}:{day if day is not None else ticket_id}" if scope != "total" else scope
        announced = self.reached.setdefault(key, [])
        if THRESHOLDS[-1] in announced:  # o gasto só cresce: o teto continua estourado
            return [Notice(scope, day, THRESHOLDS[-1], spent, limit, True, ticket_id)]
        notices: list[Notice] = []
        for pct in THRESHOLDS:
            if pct not in announced and spent >= limit * pct / 100:
                announced.append(pct)
                notices.append(Notice(scope, day, pct, spent, limit, ticket_id=ticket_id))
        return notices
