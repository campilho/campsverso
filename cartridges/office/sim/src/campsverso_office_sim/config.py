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
# A copa e as pausas da rotina (ADR-0080): ilustrativas, sem efeito no trabalho. Na planta da arte
# nova (ADR-0082), o café sai da máquina, o almoço passa pela geladeira e pelo micro-ondas, e o
# banheiro fica fora da sala, com as portas no corredor.
WATER_COOLER, COPA_COUNTER, COPA_TABLE, COPA_CHAIR, RESTROOM_DOOR = (
    "water_cooler",
    "copa_counter",
    "copa_table",
    "copa_chair",
    "restroom_door",
)
COFFEE_MACHINE, FRIDGE, MICROWAVE, TRASH = "coffee_machine", "fridge", "microwave", "trash"
# Os robôs da bancada (o plano do M24, §4): ferramentas, nunca LLM. O cenário os põe sobre a
# bancada, um por linha do registro dele, e o dev os chama na oficina.
ROBOT = "robot"
# A mobília que só enfeita e ocupa lugar: os arquivos, as plantas, a sala de descompressão e o bloco
# do banheiro.
FILE_CABINET, PLANT, TV, SOFA, PUFF, RESTROOM = (
    "file_cabinet",
    "plant",
    "tv",
    "sofa",
    "puff",
    "restroom",
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


def tick_ms(view: WorldView) -> int:
    """O passo do escritório em milissegundos (ADR-0081)."""
    return round(float(section(view, "clock")["tick_seconds"]) * 1000)


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


def lunch_out(view: WorldView) -> bool:
    """O almoço é na rua (o dev sai pela porta) ou na copa (fica na sala; ADR-0080)."""
    return str(section(view, "schedule").get("lunch_where", "rua")) == "rua"


def lunch_end(view: WorldView) -> int:
    """O minuto do dia em que o almoço acaba."""
    return minutes(str(section(view, "schedule")["lunch"][1]))


def lunch_tail(view: WorldView) -> int:
    """Os minutos do fim do almoço que sobram depois de comer: jogar fora e voltar à mesa."""
    return int(section(view, "schedule").get("lunch_tail_minutes", 0))


def office_hours(view: WorldView) -> bool:
    """O dev está no escritório agora: num dia de expediente, entre a abertura e o fim, fora do
    almoço quando o almoço é na rua."""
    rules = section(view, "schedule")
    now = view.minute_of_day
    open_now = minutes(str(rules["opens"])) <= now < minutes(str(rules["closes"]))
    return workday(view) and open_now and not (at_lunch(view) and lunch_out(view))
