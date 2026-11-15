"""Leitura dos dados do gênero office (data/office.yaml), mesclados pelo cenário (ADR-0031)."""

from collections.abc import Mapping
from datetime import date
from pathlib import Path
from typing import Any, cast

import yaml

from campsverso_cartridge_api import Position, WorldView

DATA_FILE = Path(__file__).parent / "data" / "office.yaml"
NAMESPACE = "office"

# Os tipos de entidade do escritório.
AVATAR, DESK, CHAIR, BOARD, BENCH, DOOR, TICKET = (
    "avatar",
    "desk",
    "chair",
    "board",
    "bench",
    "door",
    "ticket",
)
# Os papéis, no atributo `papel` de cada avatar (ADR-0077: o dev é sempre um LLM ou um script).
DEV, MANAGER, GUARD = "dev", "gerente", "vigia"


def load() -> dict[str, Any]:
    return cast(dict[str, Any], yaml.safe_load(DATA_FILE.read_text(encoding="utf-8")))


def section(view: WorldView, *path: str) -> Mapping[str, Any]:
    node: Any = view.data(NAMESPACE)
    for key in path:
        node = cast(Mapping[str, Any], node)[key]
    return cast(Mapping[str, Any], node)


def tick_seconds(view: WorldView) -> int:
    return int(section(view, "clock")["tick_seconds"])


def minutes(hhmm: str) -> int:
    return int(hhmm[:2]) * 60 + int(hhmm[3:5])


def door(view: WorldView) -> Position:
    """Por onde se entra no escritório: o tile do corredor diante da porta (o cenário diz)."""
    spot = section(view, "door")
    return Position(int(spot["x"]), int(spot["y"]))


def workday(view: WorldView) -> bool:
    """Hoje é dia de expediente: um dia útil que não é feriado (a data do relógio do mundo)."""
    rules = section(view, "schedule")
    today = view.today
    holidays = cast(Mapping[str, Any], rules.get("holidays") or {})
    return date.fromisoformat(today).isoweekday() in rules["workdays"] and today not in holidays


def at_lunch(view: WorldView) -> bool:
    start, end = (minutes(str(hhmm)) for hhmm in section(view, "schedule")["lunch"])
    return start <= view.minute_of_day < end


def office_hours(view: WorldView) -> bool:
    """O dev está no escritório agora: num dia de expediente, entre a abertura e o fim, fora do
    almoço."""
    rules = section(view, "schedule")
    now = view.minute_of_day
    open_now = minutes(str(rules["opens"])) <= now < minutes(str(rules["closes"]))
    return workday(view) and open_now and not at_lunch(view)
