"""Os sistemas do gênero office (ADR-0078): quem está no escritório a cada hora.

O dev chega na abertura, sai para almoçar (quando o almoço é na rua; na copa, fica) e vai embora no
fim do expediente; o vigia fica sempre
que o dev não está, à noite, no fim de semana e nos feriados (o almoço não conta). Tudo pela data e
pela hora do relógio do mundo: funções do estado e do tick (princípio 4).
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from campsverso_cartridge_api import DailyAt, OnSessionStart, SystemContext, Trigger, WorldOps
from campsverso_office_sim.config import (
    AVATAR,
    DEV,
    GUARD,
    at_lunch,
    door,
    lunch_out,
    office_hours,
    workday,
)
from campsverso_office_sim.config import minutes as minute_of


@dataclass(frozen=True)
class OfficeSystem:
    name: str
    stage: str
    priority: int
    triggers: tuple[Trigger, ...]
    fn: Callable[[SystemContext, WorldOps], None]

    def run(self, ctx: SystemContext, ops: WorldOps) -> None:
        self.fn(ctx, ops)


def _with_role(ctx: SystemContext, role: str) -> list[str]:
    """Os avatares do papel, dentro ou fora do escritório (`avatars()` só traz os presentes)."""
    return [e.entity_id for e in ctx.view.entities(AVATAR) if e.attributes.get("papel") == role]


def staff(ctx: SystemContext, ops: WorldOps) -> None:
    """Põe e tira o dev e o vigia conforme o expediente de agora: primeiro quem sai, depois quem
    entra, para os dois nunca estarem lá dentro ao mesmo tempo."""
    view = ctx.view
    rules = view.data("office")["schedule"]
    opens, closes = minute_of(str(rules["opens"])), minute_of(str(rules["closes"]))
    wanted: dict[str, tuple[bool, str]] = {}
    for dev in _with_role(ctx, DEV):
        lunch = at_lunch(view) and workday(view) and lunch_out(view)
        wanted[dev] = (office_hours(view), "almoco" if lunch else "expediente")
    after_hours = not workday(view) or not opens <= view.minute_of_day < closes
    for guard in _with_role(ctx, GUARD):
        wanted[guard] = (after_hours, "plantao")
    for avatar_id, (inside, reason) in sorted(wanted.items()):
        if not inside and view.present(avatar_id):
            ops.leave(avatar_id, reason)
    for avatar_id, (inside, reason) in sorted(wanted.items()):
        if inside and not view.present(avatar_id):
            ops.enter(avatar_id, door(view), reason)


def build_systems(data: dict[str, Any]) -> tuple[OfficeSystem, ...]:
    """Os horários vêm dos dados no momento de montar o mundo; a meia-noite vira o dia útil."""
    schedule = data["schedule"]
    times = (
        "00:00",
        str(schedule["opens"]),
        *(str(hhmm) for hhmm in schedule["lunch"]),
        str(schedule["closes"]),
    )
    return (
        OfficeSystem(
            "staff", "scheduled", 10, (OnSessionStart(), DailyAt(tuple(sorted(set(times))))), staff
        ),
    )
