"""As métricas de exploração (ADR-0070; plano do M19, §6), a partir do arquivo de uma corrida.

    uv run python -m campsverso_tools.metrics data/arena/<rodada>/<corrida>   # entram no fim

Como as outras métricas, lê só o arquivo: o mapa inteiro e a percepção do `session.started`, as
fotos e os deltas da percepção (o que o avatar viu) e os fatos do kernel (onde cavou e plantou, os
espantalhos, a lanterna). As zonas usam a verdade das regras ocultas da Morada do Sol (bíblia 3
§8): o avaliador pode saber as regras, e nada disto volta ao mundo.

- **Tiles vistos:** a união dos recortes das fotos e, entre uma foto e outra, do quadrado em volta
  do avatar a cada delta, com o raio da fase e da luz que ele carrega.
- **As zonas de um canteiro:** a várzea (até 4 tiles de qualquer água, a R-001) e longe (a mais de
  18 tiles da porta, onde os corvos da R-002 comem), cruzadas: `várzea`, `várzea longe`, `longe` e
  `resto`.
- **Plantar onde rende:** dos plantios feitos depois de ver a água, quantos foram na várzea.
- **Exposto:** o plantio longe sem espantalho a até 6 tiles.
- **Rotação:** dos plantios num canteiro que já teve cultura, quantos repetiram a anterior (a
  R-003, a fadiga do solo).
"""

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, cast

WATER_RADIUS = 4  # R-001: a grama até 4 tiles da água cresce mais (bíblias 2 §10 e 3 §8)
CROW_DISTANCE = 18  # R-002: os corvos comem a mais de 18 tiles da porta (bíblia 3 §8)
SCARECROW_RADIUS = 6  # e o espantalho protege até 6 tiles
SEEN_ENOUGH = 0.9  # "viu o mapa": 90% dos tiles (os cantos atrás da mata quase nunca entram)
ZONES = ("várzea", "várzea longe", "longe", "resto")
AVATAR = "camps"

type Tile = tuple[int, int]


@dataclass
class Exploration:
    map_tiles: int
    limited_view: bool = False  # o mundo tem raio de percepção (a Morada do Sol); senão, vê tudo
    seen_tiles: int = 0
    seen_by_day: dict[int, int] = field(default_factory=dict[int, int])  # acumulado no fim do dia
    seen_most_day: int | None = None  # o dia em que os vistos passaram de 90% do mapa
    first_water: str | None = None  # "dia 2, 09:40": quando um tile de água entrou na vista
    plots_by_zone: dict[str, int] = field(default_factory=dict[str, int])  # cavados
    plantings_by_zone: dict[str, int] = field(default_factory=dict[str, int])
    fertile_after_water: tuple[int, int] = (0, 0)  # na várzea, de quantos, depois de ver a água
    exposed: int = 0  # plantios longe sem espantalho por perto
    door_distance: float | None = None  # a média dos canteiros cavados
    repeats: tuple[int, int] = (0, 0)  # repetiram a cultura anterior, de quantos com anterior

    @property
    def seen_fraction(self) -> float:
        return self.seen_tiles / self.map_tiles if self.map_tiles else 0.0

    def as_dict(self) -> dict[str, Any]:
        return {
            "map_tiles": self.map_tiles,
            "limited_view": self.limited_view,
            "seen_tiles": self.seen_tiles,
            "seen_fraction": round(self.seen_fraction, 3),
            "seen_by_day": dict(sorted(self.seen_by_day.items())),
            "seen_most_day": self.seen_most_day,
            "first_water": self.first_water,
            "plots_by_zone": {z: self.plots_by_zone.get(z, 0) for z in ZONES},
            "plantings_by_zone": {z: self.plantings_by_zone.get(z, 0) for z in ZONES},
            "fertile_after_water": list(self.fertile_after_water),
            "exposed": self.exposed,
            "door_distance": self.door_distance,
            "repeats": list(self.repeats),
        }


def _chebyshev(a: Tile, b: Tile) -> int:
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def _tile(position: object) -> Tile | None:
    if not isinstance(position, Mapping):
        return None
    where = cast(Mapping[str, Any], position)
    return int(where["x"]), int(where["y"])


def _water(terrain: Mapping[str, Any]) -> set[Tile]:
    legend = cast(Mapping[str, Mapping[str, Any]], terrain.get("legend") or {})
    wet = {
        symbol
        for symbol, entry in legend.items()
        if bool(cast(Mapping[str, Any], entry.get("properties") or {}).get("water"))
    }
    rows = cast(Sequence[str], terrain.get("rows") or [])
    return {(x, y) for y, row in enumerate(rows) for x, symbol in enumerate(row) if symbol in wet}


class _Sight:
    """O que o avatar já viu, tile a tile, e quando a água apareceu."""

    def __init__(self, width: int, height: int, water: set[Tile]) -> None:
        self.width, self.height, self.water = width, height, water
        self.seen: set[Tile] = set()
        self.first_water: str | None = None

    def box(self, x0: int, y0: int, x1: int, y1: int, when: str) -> None:
        fresh = {
            (x, y)
            for y in range(max(0, y0), min(self.height - 1, y1) + 1)
            for x in range(max(0, x0), min(self.width - 1, x1) + 1)
        } - self.seen
        self.seen |= fresh
        if self.first_water is None and fresh & self.water:
            self.first_water = when

    def around(self, center: Tile, radius: int, when: str) -> None:
        x, y = center
        self.box(x - radius, y - radius, x + radius, y + radius, when)


def _when(envelope: Mapping[str, Any], ticks_per_day: int) -> tuple[int, str]:
    tick = int(envelope.get("tick") or 0)
    day = tick // ticks_per_day + 1
    return day, f"dia {day}, {str(envelope.get('simtime', ''))[11:16]}"


def explore(envelopes: Iterable[Mapping[str, Any]], avatar: str = AVATAR) -> Exploration | None:
    """As métricas de exploração da corrida; `None` sem o mapa no `session.started`."""
    ordered = sorted(envelopes, key=lambda e: (int(e.get("tick") or 0), int(e.get("seq") or 0)))
    start = next(
        (e for e in ordered if e.get("type") == "campsverso.world.session.started.v1"), None
    )
    if start is None:
        return None
    session = cast(Mapping[str, Any], start["data"])
    terrain = cast(Mapping[str, Any], session.get("map") or {})
    rows = cast(Sequence[str], terrain.get("rows") or ())
    if not rows:
        return None
    width, height = (
        int(terrain.get("width") or len(rows[0])),
        int(terrain.get("height") or len(rows)),
    )
    ticks_per_day = 86400 // int(session["tick_seconds"])
    perception = cast(Mapping[str, Any], session.get("perception") or {})
    by_phase = cast(Mapping[str, int], perception.get("by_phase") or {})
    lights = cast(Mapping[str, int], perception.get("lights") or {})
    radius = perception.get("radius")
    water = _water(terrain)
    fertile = {
        (x, y)
        for y in range(height)
        for x in range(width)
        if any(_chebyshev((x, y), w) <= WATER_RADIUS for w in water)
    }
    sight = _Sight(width, height, water)
    found = Exploration(width * height, limited_view=radius is not None)
    door: Tile | None = None
    plots: dict[str, Tile] = {}
    last_crop: dict[str, str] = {}
    scarecrows: list[Tile] = []
    held: dict[str, int] = {}  # as luzes no inventário do avatar
    distances: list[int] = []
    water_day: int | None = None
    fertile_count, after_water = 0, 0
    repeated, with_previous = 0, 0

    def zone(tile: Tile) -> str:
        far = door is not None and _chebyshev(tile, door) > CROW_DISTANCE
        if tile in fertile:
            return "várzea longe" if far else "várzea"
        return "longe" if far else "resto"

    for envelope in ordered:
        kind = str(envelope.get("type", ""))
        data = cast(Mapping[str, Any], envelope.get("data") or {})
        day, when = _when(envelope, ticks_per_day)
        if kind == "campsverso.perception.delivered.v1" and data.get("avatar_id") == avatar:
            view = cast(Mapping[str, Any], data.get("view") or {})
            for entity in cast(Sequence[Mapping[str, Any]], view.get("entities") or ()):
                if entity.get("kind") == "door" and door is None:
                    door = _tile(entity.get("position"))
            crop = cast(Mapping[str, Any], view.get("map") or {})
            rows = cast(Sequence[str], crop.get("rows") or ())
            origin = _tile(crop.get("origin"))
            if origin is not None and rows:
                x0, y0 = origin
                sight.box(x0, y0, x0 + len(rows[0]) - 1, y0 + len(rows) - 1, when)
        elif kind == "campsverso.perception.updated.v1" and data.get("avatar_id") == avatar:
            me = cast(Mapping[str, Any], data.get("self") or {})
            where = _tile(me.get("position"))
            clock = cast(Mapping[str, Any], data.get("clock") or {})
            if where is not None and radius is not None:
                reach = int(by_phase.get(str(clock.get("phase")), int(radius)))
                lit = [lights[item] for item, qty in held.items() if qty > 0 and item in lights]
                sight.around(where, max([reach, *lit]), when)
        elif kind == "campsverso.world.entity.spawned.v1":
            tile = _tile(data.get("position"))
            if data.get("kind") == "plot" and tile is not None:
                plots[str(data["entity_id"])] = tile
                if data.get("action_id") is not None:  # cavado, não do mapa
                    name = zone(tile)
                    found.plots_by_zone[name] = found.plots_by_zone.get(name, 0) + 1
                    if door is not None:
                        distances.append(_chebyshev(tile, door))
            elif data.get("kind") == "scarecrow" and tile is not None:
                scarecrows.append(tile)
        elif kind == "campsverso.action.completed.v1" and data.get("action") == "plant":
            params = cast(Mapping[str, Any], data.get("params") or {})
            plot, crop = str(params.get("target")), str(params.get("crop"))
            tile = plots.get(plot)
            if tile is None:
                continue
            name = zone(tile)
            found.plantings_by_zone[name] = found.plantings_by_zone.get(name, 0) + 1
            if water_day is not None:
                after_water += 1
                fertile_count += tile in fertile
            guarded = any(_chebyshev(tile, s) <= SCARECROW_RADIUS for s in scarecrows)
            found.exposed += name in ("várzea longe", "longe") and not guarded
            if plot in last_crop:
                with_previous += 1
                repeated += last_crop[plot] == crop
            last_crop[plot] = crop
        elif kind.startswith("campsverso.world.item.") and data.get("item") in lights:
            item, qty = str(data["item"]), int(data["qty"])
            gained = (data.get("container_id") == avatar and kind.endswith("created.v1")) or (
                data.get("to_container") == avatar
            )
            lost = (data.get("container_id") == avatar and kind.endswith("consumed.v1")) or (
                data.get("from_container") == avatar
            )
            held[item] = held.get(item, 0) + qty * (gained - lost)
        if sight.first_water is not None and water_day is None:
            water_day = day
        found.seen_by_day[day] = len(sight.seen)
        if found.seen_most_day is None and len(sight.seen) >= SEEN_ENOUGH * found.map_tiles:
            found.seen_most_day = day
    found.seen_tiles = len(sight.seen)
    found.first_water = sight.first_water
    found.fertile_after_water = (fertile_count, after_water)
    found.door_distance = round(sum(distances) / len(distances), 1) if distances else None
    found.repeats = (repeated, with_previous)
    return found


def lines(found: Exploration) -> list[str]:
    """A exploração em texto, para o `make metrics`."""
    fertile, after = found.fertile_after_water
    repeated, previous = found.repeats
    return [
        "exploração (ADR-0070):",
        f"  tiles vistos: {found.seen_tiles} de {found.map_tiles} ({found.seen_fraction:.0%});"
        f" 90% do mapa no dia {found.seen_most_day or '-'}",
        f"  a primeira água à vista: {found.first_water or 'nunca'}",
        "  canteiros cavados por zona: "
        + ", ".join(f"{z} {found.plots_by_zone.get(z, 0)}" for z in ZONES),
        "  plantios por zona: "
        + ", ".join(f"{z} {found.plantings_by_zone.get(z, 0)}" for z in ZONES),
        f"  plantios na várzea depois de ver a água: {fertile} de {after}",
        f"  plantios longe sem espantalho: {found.exposed}",
        f"  distância média dos canteiros à porta: {found.door_distance or '-'}",
        f"  plantios que repetiram a cultura do canteiro: {repeated} de {previous}",
    ]
