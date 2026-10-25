"""O caderno de campo da mente (ADR-0070, decisão 8): os plantios e as refeições, calculados por
código só com o que o avatar viu, e mostrados ao modelo como uma tabela curta no bloco de
abertura. O mundo nunca escreve aqui, então o caderno não vaza regra oculta: o canteiro, a
cultura, a de antes, os dias de rega e os dias até amadurecer são fatos que o avatar viu.

Os fatos que alimentam o caderno vêm das entregas da percepção: as ações que o próprio avatar
completou (plantar, regar, colher, limpar, adubar, comer), a chuva do dia, a planta que
amadureceu, foi comida, derrubada ou murchou à vista. Uma planta que sumiu fora da vista fica
"sumiu" quando o avatar vê o canteiro vazio.
"""

from collections.abc import Mapping, Sequence
from dataclasses import replace
from typing import Any, cast

from campsverso_ports import Meal, MemoryPort, Place, Planting

WET = frozenset({"rain", "storm"})  # o tempo que rega todos os canteiros do dia (o manual)
SEEN_END = {
    "campsverso.farm.crop.eaten.v1": "comida",
    "campsverso.farm.crop.knocked_down.v1": "derrubada",
    "campsverso.farm.crop.withered.v1": "murcha",
}


def _hunger(delivery: Mapping[str, Any], need: str) -> float | None:
    view = cast(Mapping[str, Any] | None, delivery.get("view"))
    me = cast(Mapping[str, Any], (view or delivery).get("self") or {})
    needs = cast(Mapping[str, Any], me.get("needs") or {})
    value = needs.get(need)
    return float(value) if isinstance(value, int | float) else None


class FieldNotebook:
    """O caderno de campo de um avatar, sobre a porta de memória."""

    def __init__(self, port: MemoryPort, avatar_id: str, hunger_need: str = "fome") -> None:
        self.port = port
        self.avatar_id = avatar_id
        self.hunger_need = hunger_need
        self.fertilized: set[str] = set()  # canteiros adubados que ainda não receberam planta
        self.hunger: float | None = None  # a fome na última entrega

    def _open(self, plot: str) -> Planting | None:
        rows = [p for p in self.port.plantings() if p.plot_id == plot and p.outcome is None]
        return rows[-1] if rows else None

    def _close(self, plot: str, outcome: str, day: int) -> None:
        planting = self._open(plot)
        if planting is not None:
            self.port.save_planting(replace(planting, outcome=outcome, outcome_day=day))

    def observe(
        self,
        day: int,
        delivery: Mapping[str, Any],
        places: Mapping[str, Place],
        in_view: set[str],
    ) -> None:
        """Os fatos de uma entrega entram no caderno."""
        before = self.hunger
        now = _hunger(delivery, self.hunger_need)
        for event in cast(Sequence[Mapping[str, Any]], delivery.get("events") or ()):
            kind = str(event.get("type", ""))
            data = cast(Mapping[str, Any], event.get("data") or {})
            if kind == "campsverso.action.completed.v1" and data.get("avatar_id") == self.avatar_id:
                self._action(day, int(event.get("tick", 0)), data, places, before, now)
            elif kind == "campsverso.world.weather.changed.v1" and not data.get("forecast"):
                if data.get("condition") in WET:
                    rained = int(data.get("day", day))
                    for planting in self.port.plantings():
                        if planting.outcome is None and rained not in planting.watered_days:
                            watered = (*planting.watered_days, rained)
                            self.port.save_planting(replace(planting, watered_days=watered))
            elif kind == "campsverso.farm.crop.matured.v1":
                planting = self._open(str(data.get("plot_id")))
                if planting is not None and planting.matured_day is None:
                    matured = int(data.get("day", day))
                    self.port.save_planting(replace(planting, matured_day=matured))
            elif kind in SEEN_END:
                self._close(str(data.get("plot_id")), SEEN_END[kind], day)
        for planting in self.port.plantings():  # o canteiro à vista, vazio, sem colheita
            seen = places.get(planting.plot_id)
            # Visto vazio depois do plantio (e não o estado de antes de plantar, lembrado).
            empty = seen is not None and dict(seen.attributes).get("crop") in (None, "null")
            later = seen is not None and seen.tick > planting.tick
            if planting.outcome is None and planting.plot_id in in_view and empty and later:
                self._close(planting.plot_id, "sumiu", day)
        if now is not None:
            self.hunger = now

    def _action(
        self,
        day: int,
        tick: int,
        data: Mapping[str, Any],
        places: Mapping[str, Place],
        before: float | None,
        now: float | None,
    ) -> None:
        action = str(data.get("action", ""))
        params = cast(Mapping[str, Any], data.get("params") or {})
        target = params.get("target")
        plot = target if isinstance(target, str) else ""
        if action == "plant" and plot:
            done = [p for p in self.port.plantings() if p.plot_id == plot]
            seen = places.get(plot)
            self.port.save_planting(
                Planting(
                    plot,
                    tick,
                    day,
                    str(params.get("crop")),
                    None if seen is None else seen.x,
                    None if seen is None else seen.y,
                    previous=done[-1].crop if done else None,
                    fertilized=plot in self.fertilized,
                )
            )
            self.fertilized.discard(plot)
        elif action == "water" and plot:
            planting = self._open(plot)
            if planting is not None and day not in planting.watered_days:
                watered = (*planting.watered_days, day)
                self.port.save_planting(replace(planting, watered_days=watered))
        elif action == "harvest" and plot:
            self._close(plot, "colhida", day)
        elif action == "clear" and plot:
            self._close(plot, "murcha", day)
        elif action == "fertilize" and plot:
            self.fertilized.add(plot)
        elif action == "eat" and before is not None and now is not None:
            self.port.eat(Meal(tick, day, str(params.get("item")), before, now))

    # ------------------------------------------------------------- o bloco de abertura

    def lines(self, limit: int) -> list[str]:
        """Os últimos plantios, o resumo por cultura e a comida, em poucas linhas."""
        plantings = self.port.plantings()
        found: list[str] = []
        if plantings:
            found.append(f"Caderno de campo (os últimos {min(limit, len(plantings))} plantios):")
            found.extend(_planting_line(p) for p in plantings[-limit:])
            found.append("Por cultura: " + "; ".join(_by_crop(plantings)) + ".")
        meals = self.port.meals()
        if meals:
            found.append(
                "A comida (a fome que cada uma tirou): " + "; ".join(_by_food(meals)) + "."
            )
        return found


def _planting_line(p: Planting) -> str:
    where = "" if p.x is None or p.y is None else f" ({p.x},{p.y})"
    before = f", antes {p.previous}" if p.previous else ", canteiro novo"
    fed = ", adubado" if p.fertilized else ""
    watered = f"rega em {len(p.watered_days)} dia{'s' if len(p.watered_days) != 1 else ''}"
    if p.matured_day is not None:
        grown = f"madura no dia {p.matured_day} ({p.matured_day - p.day} dias)"
    else:
        grown = "ainda não madura"
    end = p.outcome or "crescendo"
    head = f"- {p.plot_id}{where} {p.crop}{before}{fed}"
    return f"{head}: plantou no dia {p.day}, {watered}, {grown}; {end}"


def _by_crop(plantings: Sequence[Planting]) -> list[str]:
    found: list[str] = []
    for crop in sorted({p.crop for p in plantings}):
        rows = [p for p in plantings if p.crop == crop]
        days = [p.matured_day - p.day for p in rows if p.matured_day is not None]
        outcomes: dict[str, int] = {}
        for p in rows:
            if p.outcome is not None:
                outcomes[p.outcome] = outcomes.get(p.outcome, 0) + 1
        parts = [f"{n} {outcome}" for outcome, n in sorted(outcomes.items())]
        if days:
            mean = f"{sum(days) / len(days):.1f}".replace(".", ",")
            parts.append(f"madura de {min(days)} a {max(days)} dias (média {mean})")
        growing = sum(1 for p in rows if p.outcome is None)
        if growing:
            parts.append(f"{growing} crescendo")
        found.append(f"{crop} " + ", ".join(parts))
    return found


def _by_food(meals: Sequence[Meal]) -> list[str]:
    found: list[str] = []
    for item in sorted({m.item for m in meals}):
        killed = [m.hunger_before - m.hunger_after for m in meals if m.item == item]
        mean = round(sum(killed) / len(killed))
        times = f"{len(killed)} vez" + ("es" if len(killed) != 1 else "")
        found.append(f"{item} tirou {mean} ({times})")
    return found
