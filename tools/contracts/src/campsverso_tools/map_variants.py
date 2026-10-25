"""As variantes do mapa da Fazenda Morada do Sol (ADR-0070): receitas sobre o mapa de hoje.

    uv run python -m campsverso_tools.map_variants [--check]   # ou: make mapa-variantes

O mapa de hoje (`map.tmj`) é a variante a e a base de todas: cada receita de `maps/receitas.yaml`
muda a água e a mata dele e grava `maps/<nome>.tmj`, com a casa, o centro, a estrada e a entrada no
lugar. Depois confere o que a receita promete (`problems`): as construções ficam onde estavam e se
alcançam a partir da porta, a grama não muda muito, e a terra boa (a grama perto da água) fica na
distância da porta que a receita diz. Os números das regras vêm dos dados do cartucho. Com
`--check`, só confere se os arquivos gravados estão em dia.
"""

import argparse
import json
import sys
from collections import deque
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from itertools import pairwise
from pathlib import Path
from typing import Any, cast

import yaml

from campsverso_tools.visual_map import render

REPO = Path(__file__).resolve().parents[4]
DATA = REPO / "cartridges/farm_morada_do_sol/sim/src/campsverso_farm_morada_do_sol_sim/data"
BASE = DATA / "map.tmj"
MAPS = DATA / "maps"
RECIPES = MAPS / "receitas.yaml"
GRASS_TOLERANCE = 0.15  # a grama de uma variante fica a menos de 15% da do mapa de hoje

type Grid = list[list[str]]


@dataclass(frozen=True)
class Rules:
    """O que as regras ocultas dizem da geografia (lido dos dados do cartucho)."""

    water_radius: int  # R-001: a grama até esta distância da água cresce mais
    crow_distance: int  # R-002: os corvos só comem além desta distância da porta


def rules() -> Rules:
    flags = cast(Mapping[str, Any], yaml.safe_load((DATA / "rules.yaml").read_text("utf-8")))
    water = cast(Mapping[str, Any], flags["rules"])["river_proximity_bonus"]["params"]["radius"]
    scenario = cast(Mapping[str, Any], yaml.safe_load((DATA / "morada.yaml").read_text("utf-8")))
    return Rules(int(water), int(scenario["crows"]["min_distance"]))


def _types(doc: Mapping[str, Any]) -> tuple[dict[int, str], dict[str, int], dict[str, bool]]:
    """gid -> tipo, tipo -> gid e tipo -> se dá para pisar, do tileset do mapa."""
    tileset = cast(Mapping[str, Any], doc["tilesets"][0])
    first = int(tileset["firstgid"])
    by_gid: dict[int, str] = {}
    passable: dict[str, bool] = {}
    for tile in cast(list[Mapping[str, Any]], tileset["tiles"]):
        name = str(tile["type"])
        by_gid[first + int(tile["id"])] = name
        props = {
            str(p["name"]): p["value"] for p in cast(list[Mapping[str, Any]], tile["properties"])
        }
        passable[name] = bool(props.get("passable", False))
    return by_gid, {name: gid for gid, name in by_gid.items()}, passable


def _terrain(doc: Mapping[str, Any]) -> Mapping[str, Any]:
    return next(layer for layer in doc["layers"] if layer["type"] == "tilelayer")


def grid_of(doc: Mapping[str, Any]) -> Grid:
    by_gid, _, _ = _types(doc)
    width = int(doc["width"])
    data = cast(Sequence[int], _terrain(doc)["data"])
    return [[by_gid[g] for g in data[r : r + width]] for r in range(0, len(data), width)]


def objects_of(doc: Mapping[str, Any]) -> dict[str, tuple[int, int]]:
    """As construções e o avatar do mapa, pelo nome, no tile."""
    tile_w, tile_h = int(doc["tilewidth"]), int(doc["tileheight"])
    layer = next(layer for layer in doc["layers"] if layer["type"] == "objectgroup")
    return {
        str(o["name"]): (int(o["x"]) // tile_w, int(o["y"]) // tile_h)
        for o in cast(list[Mapping[str, Any]], layer["objects"])
    }


def _paint(grid: Grid, x: int, y: int, tile: str, keep: frozenset[str]) -> None:
    if 0 <= y < len(grid) and 0 <= x < len(grid[0]) and grid[y][x] not in keep:
        grid[y][x] = tile


def apply(base: Grid, ops: Sequence[Mapping[str, Any]]) -> Grid:
    """A receita aplicada a uma cópia do terreno, operação por operação."""
    grid = [list(row) for row in base]
    for op in ops:
        tile = str(op["tile"])
        keep = frozenset(str(k) for k in cast(Sequence[Any], op.get("keep") or ()))
        if "fill" in op:
            x0, y0, x1, y1 = (int(v) for v in op["fill"])
            for y in range(y0, y1 + 1):
                for x in range(x0, x1 + 1):
                    _paint(grid, x, y, tile, keep)
        elif "line" in op:
            points = [(int(p[0]), int(p[1])) for p in cast(Sequence[Sequence[Any]], op["line"])]
            wide = int(op.get("width", 1))  # para leste do traço
            for (ax, ay), (bx, by) in pairwise(points):
                steps = max(abs(bx - ax), abs(by - ay), 1)
                for s in range(steps + 1):
                    x = ax + round((bx - ax) * s / steps)
                    y = ay + round((by - ay) * s / steps)
                    for dx in range(wide):
                        _paint(grid, x + dx, y, tile, keep)
        else:
            raise ValueError(f"operação desconhecida na receita: {sorted(op)}")
    return grid


def document(base_doc: Mapping[str, Any], grid: Grid, name: str, title: str) -> dict[str, Any]:
    """O mapa da variante: o de hoje, com o terreno trocado e a origem nas propriedades."""
    _, gid_of, _ = _types(base_doc)
    data = [gid_of[tile] for row in grid for tile in row]
    layers = [
        {**layer, "data": data} if layer["type"] == "tilelayer" else layer
        for layer in cast(list[Mapping[str, Any]], base_doc["layers"])
    ]
    source = f"A variante {name} ({title}): a receita de maps/receitas.yaml sobre o mapa de hoje."
    properties = [{"name": "source", "type": "string", "value": source}]
    return {**base_doc, "layers": layers, "properties": properties}


def _chebyshev(a: tuple[int, int], b: tuple[int, int]) -> int:
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def _thin(grid: Grid, x: int, y: int) -> bool:
    """Um tile de água com terra dos dois lados (leste e oeste, ou norte e sul), dentro do mapa."""

    def land(cx: int, cy: int) -> bool:
        return 0 <= cy < len(grid) and 0 <= cx < len(grid[0]) and grid[cy][cx] != "river"

    return (land(x - 1, y) and land(x + 1, y)) or (land(x, y - 1) and land(x, y + 1))


def fertile(grid: Grid, radius: int) -> list[tuple[int, int]]:
    """A grama a até `radius` tiles (Chebyshev) de um tile de água: onde a R-001 age."""
    water = [(x, y) for y, row in enumerate(grid) for x, tile in enumerate(row) if tile == "river"]
    return [
        (x, y)
        for y, row in enumerate(grid)
        for x, tile in enumerate(row)
        if tile == "grass" and any(_chebyshev((x, y), w) <= radius for w in water)
    ]


def reachable(
    grid: Grid, passable: Mapping[str, bool], start: tuple[int, int]
) -> set[tuple[int, int]]:
    """Os tiles de pisar alcançáveis a partir de `start`, andando nas quatro direções."""
    seen = {start}
    queue = deque([start])
    while queue:
        x, y = queue.popleft()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            inside = 0 <= ny < len(grid) and 0 <= nx < len(grid[0])
            if inside and (nx, ny) not in seen and passable[grid[ny][nx]]:
                seen.add((nx, ny))
                queue.append((nx, ny))
    return seen


def problems(
    base_doc: Mapping[str, Any], grid: Grid, promise: Mapping[str, Any], numbers: Rules
) -> list[str]:
    """O que a variante não cumpre; vazio quando está tudo certo."""
    _, _, passable = _types(base_doc)
    base = grid_of(base_doc)
    found: list[str] = []
    things = objects_of(base_doc)
    door = things["door"]
    walk = reachable(grid, passable, door)
    for name, (x, y) in sorted(things.items()):
        if grid[y][x] != base[y][x]:
            found.append(f"o tile de {name} em ({x}, {y}) mudou")
        around = {(x + dx, y + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)}
        if not around & walk:
            found.append(f"{name} em ({x}, {y}) não se alcança a partir da porta")
    thin = [
        (x, y)
        for y, row in enumerate(grid)
        for x, tile in enumerate(row)
        if tile == "river" and _thin(grid, x, y)
    ]
    if thin:
        found.append(f"água com um tile de largura em {thin[:3]}: a margem não se desenha")
    grass = sum(row.count("grass") for row in grid)
    base_grass = sum(row.count("grass") for row in base)
    if abs(grass - base_grass) > GRASS_TOLERANCE * base_grass:
        found.append(f"grama {grass}, longe da do mapa de hoje ({base_grass})")
    good = fertile(grid, numbers.water_radius)
    if not good:
        return [*found, "a variante não tem terra boa"]
    far = [_chebyshev(tile, door) for tile in good]
    band = cast(Mapping[str, Any], promise.get("fertil_da_porta") or {})
    if "min" in band and min(far) < int(band["min"]):
        found.append(f"terra boa a {min(far)} da porta, menos que {band['min']}")
    if "max" in band and max(far) > int(band["max"]):
        found.append(f"terra boa a {max(far)} da porta, mais que {band['max']}")
    safe = sum(d <= numbers.crow_distance for d in far) / len(far)
    shelter = cast(Mapping[str, Any], promise.get("a_salvo") or {})
    if "min" in shelter and safe < float(shelter["min"]):
        found.append(f"só {safe:.0%} da terra boa a salvo dos corvos, menos que {shelter['min']}")
    if "max" in shelter and safe > float(shelter["max"]):
        found.append(f"{safe:.0%} da terra boa a salvo dos corvos, mais que {shelter['max']}")
    for thing, least in cast(Mapping[str, Any], promise.get("longe_de") or {}).items():
        near = min(_chebyshev(tile, things[str(thing)]) for tile in good)
        if near < int(least):
            found.append(f"terra boa a {near} de {thing}, menos que {least}")
    unreached = [tile for tile in good if tile not in walk]
    if len(unreached) > len(good) // 10:
        found.append(f"{len(unreached)} tiles de terra boa fora do alcance a partir da porta")
    return found


def recipes() -> dict[str, Mapping[str, Any]]:
    raw = cast(Mapping[str, Any], yaml.safe_load(RECIPES.read_text(encoding="utf-8")))
    return {str(name): cast(Mapping[str, Any], recipe) for name, recipe in raw.items()}


def build(name: str, recipe: Mapping[str, Any]) -> tuple[str, list[str]]:
    """O texto do mapa da variante e os problemas dela."""
    base_doc = cast(Mapping[str, Any], json.loads(BASE.read_text(encoding="utf-8")))
    grid = apply(grid_of(base_doc), cast(Sequence[Mapping[str, Any]], recipe["ops"]))
    doc = document(base_doc, grid, name, str(recipe["nome"]))
    promise = cast(Mapping[str, Any], recipe.get("promete") or {})
    return render(doc), problems(base_doc, grid, promise, rules())


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="campsverso_tools.map_variants")
    parser.add_argument("--check", action="store_true", help="só confere se os mapas estão em dia")
    args = parser.parse_args(argv)
    status = 0
    for name, recipe in recipes().items():
        text, found = build(name, recipe)
        out = MAPS / f"{name}.tmj"
        for problem in found:
            print(f"variante {name}: {problem}", file=sys.stderr)
            status = 1
        if args.check:
            if not out.exists() or out.read_text(encoding="utf-8") != text:
                print(
                    f"{out.relative_to(REPO)} desatualizado: rode make mapa-variantes",
                    file=sys.stderr,
                )
                status = 1
            continue
        if not found:
            out.write_text(text, encoding="utf-8")
            print(f"variante {name} gravada em {out.relative_to(REPO)}")
    return status


if __name__ == "__main__":
    sys.exit(main())
