"""Espaço: grade de tiles a partir de um mapa do Tiled e caminhos A* determinísticos."""

import heapq
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, cast

from campsverso_cartridge_api import Position, Scalar


@dataclass(frozen=True, slots=True)
class MapObject:
    name: str
    kind: str
    position: Position
    properties: Mapping[str, Scalar] = field(default_factory=dict[str, Scalar])


def _properties(raw: Any) -> dict[str, Scalar]:
    items = cast(list[dict[str, Any]], raw or [])
    return {str(p["name"]): cast(Scalar, p["value"]) for p in items}


@dataclass(frozen=True, slots=True)
class GridMap:
    map_id: str
    width: int
    height: int
    tiles: tuple[tuple[Mapping[str, Scalar], ...], ...]  # [y][x] -> propriedades do tile
    tile_kinds: tuple[tuple[str, ...], ...]  # [y][x] -> classe do tile (para depuração e testes)
    objects: tuple[MapObject, ...]

    @classmethod
    def from_tiled(cls, tiled: Mapping[str, Any], map_id: str) -> GridMap:
        width, height = int(tiled["width"]), int(tiled["height"])
        tile_w, tile_h = int(tiled["tilewidth"]), int(tiled["tileheight"])
        by_gid: dict[int, tuple[str, dict[str, Scalar]]] = {}
        for tileset in cast(list[dict[str, Any]], tiled["tilesets"]):
            first = int(tileset["firstgid"])
            for tile in cast(list[dict[str, Any]], tileset.get("tiles", [])):
                kind = str(tile.get("type") or tile.get("class") or "")
                by_gid[first + int(tile["id"])] = (kind, _properties(tile.get("properties")))
        layers = cast(list[dict[str, Any]], tiled["layers"])
        terrain = next(layer for layer in layers if layer["type"] == "tilelayer")
        data = cast(list[int], terrain["data"])
        if len(data) != width * height:
            raise ValueError("camada de terreno com tamanho diferente do mapa")
        tiles: list[tuple[Mapping[str, Scalar], ...]] = []
        kinds: list[tuple[str, ...]] = []
        for y in range(height):
            row = [by_gid.get(data[y * width + x], ("", {})) for x in range(width)]
            tiles.append(tuple(props for _, props in row))
            kinds.append(tuple(kind for kind, _ in row))
        objects: list[MapObject] = []
        for layer in layers:
            if layer["type"] != "objectgroup":
                continue
            for obj in cast(list[dict[str, Any]], layer["objects"]):
                position = Position(int(obj["x"]) // tile_w, int(obj["y"]) // tile_h)
                kind = str(obj.get("type") or obj.get("class") or "")
                objects.append(
                    MapObject(str(obj["name"]), kind, position, _properties(obj.get("properties")))
                )
        return cls(
            map_id,
            width,
            height,
            tuple(tiles),
            tuple(kinds),
            tuple(sorted(objects, key=lambda o: o.name)),
        )

    def in_bounds(self, pos: Position) -> bool:
        return 0 <= pos.x < self.width and 0 <= pos.y < self.height

    def tile_property(self, pos: Position, name: str) -> Scalar:
        return self.tiles[pos.y][pos.x].get(name) if self.in_bounds(pos) else None

    def tiles_with(self, name: str) -> tuple[Position, ...]:
        return tuple(
            Position(x, y)
            for y in range(self.height)
            for x in range(self.width)
            if self.tiles[y][x].get(name) is True
        )


_STEPS = (Position(0, -1), Position(1, 0), Position(0, 1), Position(-1, 0))  # N, L, S, O


def find_path(
    start: Position, goal: Position, walkable: Callable[[Position], bool]
) -> list[Position] | None:
    """A* em 4 direções. Empates decididos por (custo estimado, y, x), sempre na mesma ordem."""
    if start == goal:
        return [start]
    if not walkable(goal):
        return None

    def estimate(p: Position) -> int:
        return abs(p.x - goal.x) + abs(p.y - goal.y)

    frontier: list[tuple[int, int, int, int]] = [(estimate(start), 0, start.y, start.x)]
    came_from: dict[Position, Position] = {}
    cost: dict[Position, int] = {start: 0}
    while frontier:
        _, spent, y, x = heapq.heappop(frontier)
        current = Position(x, y)
        if current == goal:
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            return path[::-1]
        if spent > cost[current]:
            continue
        for step in _STEPS:
            neighbor = Position(current.x + step.x, current.y + step.y)
            if not walkable(neighbor):
                continue
            new_cost = spent + 1
            if new_cost < cost.get(neighbor, new_cost + 1):
                cost[neighbor] = new_cost
                came_from[neighbor] = current
                heapq.heappush(
                    frontier, (new_cost + estimate(neighbor), new_cost, neighbor.y, neighbor.x)
                )
    return None


def corners(path: Sequence[Position]) -> list[Position]:
    """Só as esquinas e o destino (D1): a UI interpola entre elas."""
    if len(path) < 2:
        return list(path[1:])
    result: list[Position] = []
    for index in range(1, len(path) - 1):
        before, here, after = path[index - 1], path[index], path[index + 1]
        if (here.x - before.x, here.y - before.y) != (after.x - here.x, after.y - here.y):
            result.append(here)
    result.append(path[-1])
    return result
