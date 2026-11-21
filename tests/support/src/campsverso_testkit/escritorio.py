"""Os invariantes do escritório (o plano do M24, §8), conferidos nos fatos do kernel: o soak de 5
dias (`make soak MUNDO=office-campsverso-teste`) e o dia de ponta a ponta os usam.

- **Todo pedido de dia de expediente é entregue:** cada pedido escrito num dia útil que não é
  feriado tem a entrega dele.
- **As pausas acontecem:** em cada dia de expediente, o dev bebe água, toma café ou vai ao
  banheiro, e almoça (na copa ou na rua, como o cenário diz).
- **Ninguém na copa fora do expediente:** as ações da copa só começam num dia de expediente, entre
  a abertura e o fim.

A data e a hora de cada fato vêm do `simtime` dele, na hora local do mundo.
"""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

# As ações da copa e do banheiro (ADR-0080, ADR-0082): ilustrativas, sem efeito no trabalho.
COPA = frozenset(
    {"drink", "coffee", "restroom", "fridge", "microwave", "lunch", "trash", "tv", "videogame"}
)
PAUSES = frozenset({"drink", "coffee", "restroom"})
ACCEPTED = "campsverso.action.accepted.v1"
CREATED = "campsverso.office.ticket.created.v1"
DELIVERED = "campsverso.office.ticket.delivered.v1"
LEFT = "campsverso.avatar.left.v1"
ENTERED = "campsverso.avatar.entered.v1"


@dataclass
class OfficeReport:
    """O que os fatos mostram, por dia de expediente, e o que fugiu dos invariantes."""

    workdays: list[str] = field(default_factory=list[str])
    created: int = 0
    delivered: int = 0
    pauses: dict[str, int] = field(default_factory=dict[str, int])  # dia -> pausas do dev
    lunches: dict[str, int] = field(default_factory=dict[str, int])  # dia -> almoços do dev
    problems: list[str] = field(default_factory=list[str])

    @property
    def ok(self) -> bool:
        return not self.problems


def _minutes(hhmm: str) -> int:
    return int(hhmm[:2]) * 60 + int(hhmm[3:5])


def _workday(day: str, schedule: Mapping[str, Any]) -> bool:
    holidays: Mapping[str, Any] = schedule.get("holidays") or {}
    return date.fromisoformat(day).isoweekday() in schedule["workdays"] and day not in holidays


def office_report(
    envelopes: Iterable[Mapping[str, Any]], schedule: Mapping[str, Any], dev: str = "camps"
) -> OfficeReport:
    """Os invariantes nos fatos de um mundo do escritório; `schedule` é o expediente do cenário
    (`office.schedule`, com os feriados)."""
    report = OfficeReport()
    opens, closes = _minutes(str(schedule["opens"])), _minutes(str(schedule["closes"]))
    created: dict[str, str] = {}  # pedido -> dia em que foi escrito
    delivered: set[str] = set()
    days: dict[str, int] = {}  # dia -> o último minuto com fatos
    summoned = False  # o dev convocado fora do expediente (a parte 5 do M25) pode usar a copa
    for envelope in envelopes:
        simtime = envelope.get("simtime")
        if not isinstance(simtime, str):
            continue
        at = datetime.fromisoformat(simtime)
        day, minute = at.date().isoformat(), at.hour * 60 + at.minute
        days[day] = max(days.get(day, minute), minute)
        data: Mapping[str, Any] = envelope["data"]
        kind = envelope["type"]
        if kind == CREATED:
            created[str(data["ticket_id"])] = day
        elif kind == DELIVERED:
            delivered.add(str(data["ticket_id"]))
        elif kind in (ENTERED, LEFT) and data.get("avatar_id") == dev:
            summoned = kind == ENTERED and data.get("reason") == "convocacao"
            if kind == LEFT and data.get("reason") == "almoco":
                report.lunches[day] = report.lunches.get(day, 0) + 1
        elif kind == ACCEPTED and data["action"] in COPA:
            open_now = _workday(day, schedule) and opens <= minute < closes
            if not open_now and not (summoned and data["avatar_id"] == dev):
                report.problems.append(
                    f"{data['avatar_id']} fez {data['action']} na copa fora do expediente "
                    f"({simtime})"
                )
            if data["avatar_id"] == dev and data["action"] in PAUSES:
                report.pauses[day] = report.pauses.get(day, 0) + 1
            if data["avatar_id"] == dev and data["action"] == "lunch":
                report.lunches[day] = report.lunches.get(day, 0) + 1
    # Os dias de expediente que os fatos cobrem até o fim do expediente: o soak para à meia-noite,
    # e o primeiro minuto do dia seguinte não é um dia sem pausa.
    report.workdays = [d for d, last in days.items() if _workday(d, schedule) and last >= closes]
    report.created, report.delivered = len(created), len(delivered & set(created))
    for ticket, day in sorted(created.items()):
        if ticket not in delivered and _workday(day, schedule):
            report.problems.append(f"o pedido {ticket}, escrito em {day}, não foi entregue")
    for day in report.workdays:
        if not report.pauses.get(day):
            report.problems.append(f"o dev não fez nenhuma pausa em {day}")
        if not report.lunches.get(day):
            report.problems.append(f"o dev não almoçou em {day}")
    return report
