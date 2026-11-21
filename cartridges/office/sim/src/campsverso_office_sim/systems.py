"""Os sistemas do gênero office (ADR-0078): quem está no escritório a cada hora.

O dev chega na abertura, sai para almoçar (quando o almoço é na rua; na copa, fica) e vai embora no
fim do expediente; o vigia fica sempre que o dev não está, à noite, no fim de semana e nos feriados
(o almoço não conta). Tudo pela data e pela hora do relógio do mundo: funções do estado e do tick
(princípio 4).

**A convocação** (a parte 5 do M25): fora do expediente, o gerente chama o dev, pelo botão ou só de
entrar, se o acordo do dev diz que ele vem ao entrar (no momento da entrada, uma vez por visita). O
dev chega depois do deslocamento e fica até ser dispensado, até o gerente sair, até o teto de horas,
até o fim da janela do dia ou até o expediente começar, que o assume. Enquanto um dev está lá, o
vigia sai. O sistema roda a cada minuto, além dos horários do expediente, para os prazos.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, cast

from campsverso_cartridge_api import (
    DailyAt,
    EveryMinutes,
    OnSessionStart,
    SystemContext,
    Trigger,
    WorldOps,
    WorldView,
)
from campsverso_office_sim.config import (
    AVATAR,
    DEV,
    GUARD,
    MANAGER,
    at_lunch,
    door,
    in_window,
    lunch_out,
    office_hours,
    on_call,
    ticks_of_minutes,
    workday,
)
from campsverso_office_sim.config import minutes as minute_of

SUMMONED = "campsverso.office.staff.summoned.v1"
DISMISSED = "campsverso.office.staff.dismissed.v1"
SUMMON_REASON = "convocacao"  # o motivo de entrar e sair de quem foi convocado


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


@dataclass(frozen=True)
class Summon:
    """A convocação de um dev, nos atributos dele: quem chamou, de onde, quando chega e o teto."""

    by: str
    origin: str
    arrives: int
    until: int


def summon_of(view: WorldView, avatar_id: str) -> Summon | None:
    attributes = view.entity(avatar_id).attributes
    if attributes.get("convocado_por") is None:
        return None
    return Summon(
        str(attributes["convocado_por"]),
        str(attributes["convocado_origem"]),
        int(cast(int, attributes["convocado_chega"])),
        int(cast(int, attributes["convocado_ate"])),
    )


def start_summon(view: WorldView, ops: WorldOps, dev: str, by: str, origin: str) -> None:
    """A convocação começa: o dev chega depois do deslocamento e fica até o teto."""
    rules = on_call(view, dev)
    arrives = view.tick + ticks_of_minutes(view, float(rules.get("arrive_minutes", 2)))
    until = view.tick + ticks_of_minutes(view, float(rules.get("max_hours", 6)) * 60)
    ops.set_attributes(
        dev,
        visible={
            "convocado_por": by,
            "convocado_origem": origin,
            "convocado_chega": arrives,
            "convocado_ate": until,
        },
    )
    data = {"avatar_id": dev, "by": by, "origin": origin, "arrives_tick": arrives}
    ops.emit(SUMMONED, {**data, "until_tick": until})


def end_summon(ops: WorldOps, dev: str, reason: str, by: str | None = None) -> None:
    """A convocação acaba. O dev não volta sozinho: a convocação ao entrar vale só no momento em
    que o gerente entra, uma vez por visita, e depois disso só o botão o chama."""
    ops.set_attributes(
        dev,
        visible={
            "convocado_por": None,
            "convocado_origem": None,
            "convocado_chega": None,
            "convocado_ate": None,
        },
    )
    data: dict[str, Any] = {"avatar_id": dev, "reason": reason}
    if by is not None:
        data["by"] = by
    ops.emit(DISMISSED, data)


def _follow_summon(
    view: WorldView,
    ops: WorldOps,
    dev: str,
    working: bool,
    managers: list[str],
    arrived: list[str],
) -> tuple[Summon | None, bool]:
    """A convocação do dev depois deste minuto (a que segue, a que começa ao entrar ou nenhuma) e
    se uma acabou agora."""
    rules = on_call(view, dev)
    summon = summon_of(view, dev)
    if summon is not None:
        why = (
            "expediente"
            if working
            else "saida"
            if not managers
            else "teto"
            if view.tick >= summon.until
            else "janela"
            if not in_window(view, rules)
            else None
        )
        if why is None:
            return summon, False
        end_summon(ops, dev, why)
        return None, True
    comes = rules.get("enabled") and rules.get("on_manager_enter")
    if comes and arrived and not working and in_window(view, rules):
        start_summon(view, ops, dev, arrived[0], "entrada")
        return summon_of(view, dev), False
    return None, False


def _arrivals(ctx: SystemContext, ops: WorldOps) -> tuple[list[str], list[str]]:
    """Os gerentes lá dentro e os que acabaram de entrar. A visita fica marcada no gerente
    (`visita`) até ele sair; quem já estava lá quando o mundo começou não conta como entrada."""
    view = ctx.view
    managers: list[str] = []
    arrived: list[str] = []
    for manager in _with_role(ctx, MANAGER):
        visiting = bool(view.entity(manager).attributes.get("visita"))
        if view.present(manager):
            managers.append(manager)
            if not visiting:
                ops.set_attributes(manager, visible={"visita": True})
                if not isinstance(ctx.trigger, OnSessionStart):
                    arrived.append(manager)
        elif visiting:
            ops.set_attributes(manager, visible={"visita": False})
    return managers, arrived


def staff(ctx: SystemContext, ops: WorldOps) -> None:
    """Põe e tira o dev e o vigia conforme o expediente de agora e as convocações: primeiro quem
    sai, depois quem entra, para os dois nunca estarem lá dentro ao mesmo tempo."""
    view = ctx.view
    rules = view.data("office")["schedule"]
    opens, closes = minute_of(str(rules["opens"])), minute_of(str(rules["closes"]))
    managers, arrived = _arrivals(ctx, ops)
    wanted: dict[str, tuple[bool, str]] = {}
    for dev in _with_role(ctx, DEV):
        working = office_hours(view)
        summon, ended = _follow_summon(view, ops, dev, working, managers, arrived)
        if summon is not None:
            wanted[dev] = (view.tick >= summon.arrives, SUMMON_REASON)
        elif ended and not working:
            wanted[dev] = (False, SUMMON_REASON)  # a convocação acabou agora
        else:
            lunch = at_lunch(view) and workday(view) and lunch_out(view)
            wanted[dev] = (working, "almoco" if lunch else "expediente")
    after_hours = not workday(view) or not opens <= view.minute_of_day < closes
    devs_inside = any(inside for inside, _ in wanted.values())
    for guard in _with_role(ctx, GUARD):
        wanted[guard] = (after_hours and not devs_inside, "plantao")
    for avatar_id, (inside, reason) in sorted(wanted.items()):
        if not inside and view.present(avatar_id):
            ops.leave(avatar_id, reason)
    for avatar_id, (inside, reason) in sorted(wanted.items()):
        if inside and not view.present(avatar_id):
            ops.enter(avatar_id, door(view), reason)


def build_systems(data: dict[str, Any]) -> tuple[OfficeSystem, ...]:
    """Os horários vêm dos dados no momento de montar o mundo; a meia-noite vira o dia útil. O
    sistema roda também a cada minuto, para os prazos da convocação: o cenário a liga depois de o
    gênero montar os sistemas, e o próprio sistema confere o acordo de cada dev."""
    schedule = data["schedule"]
    times = (
        "00:00",
        str(schedule["opens"]),
        *(str(hhmm) for hhmm in schedule["lunch"]),
        str(schedule["closes"]),
    )
    triggers = (OnSessionStart(), DailyAt(tuple(sorted(set(times)))), EveryMinutes(1))
    return (OfficeSystem("staff", "scheduled", 10, triggers, staff),)
