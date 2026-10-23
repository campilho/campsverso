"""O mapa visual da Fazenda do Camps, montado a partir do mapa lógico (ADR-0053, decisão 4).

    uv run python -m campsverso_tools.visual_map [--check]   # ou: make mapa-visual

O mapa lógico (`map.tmj` do cenário) é a verdade do kernel: 9 tipos de tile. Este arquivo só diz
como desenhá-lo com os tiles LPC do gênero (`cartridges/farm/art/terrain.tsj`, onde cada tile tem
um nome): bordas do rio, da terra do caminho e da cerca viva, a terra arada dos canteiros, o chão e
as paredes da casa sem telhado. O kernel nunca lê o resultado.

Ajustes pedidos depois vão nas regras daqui; rodar de novo regrava `map-visual.tmj`. Com `--check`,
só confere se o arquivo gravado está em dia.
"""

import argparse
import json
import sys
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[4]
TILESET = REPO / "cartridges/farm/art/terrain.tsj"
SCENARIOS = ("farm_camps", "farm_boavista", "farm_morada_do_sol")  # os cenários com mapa próprio


def logic_map(scenario: str) -> Path:
    return REPO / f"cartridges/{scenario}/sim/src/campsverso_{scenario}_sim/data/map.tmj"


def visual_map(scenario: str) -> Path:
    return REPO / f"cartridges/{scenario}/art/map-visual.tmj"


LOGIC = logic_map("farm_camps")
OUT = visual_map("farm_camps")
TILESET_IMAGE = "../../farm/art/terrain.png"  # relativo ao mapa visual, para abrir no Tiled

PATHS = {"path", "entrance"}
HOUSE = {"wall", "floor", "door"}
# Tipo lógico -> prefixo do tile desenhado no chão (o teste de coerência usa a mesma tabela)
GROUND = {
    "grass": "grass-",
    "tree": "grass-",
    "path": "dirt",
    "entrance": "dirt",
    "river": "water-",
    "soil": "soil-",
    "wall": "floor",  # a parede é uma faixa fina por cima do chão (camada over)
    "floor": "floor",
    "door": "floor",
}

type Grid = list[list[str]]


def logical_types(logic: Mapping[str, Any]) -> Grid:
    names = {
        int(ts["firstgid"]) + int(t["id"]): str(t.get("type") or t.get("class") or "")
        for ts in logic["tilesets"]
        for t in ts.get("tiles", [])
    }
    layer = next(
        layer
        for layer in logic["layers"]
        if layer["type"] == "tilelayer" and layer["name"] == "terrain"
    )
    width = int(logic["width"])
    data = [names.get(int(gid), "") for gid in layer["data"]]
    return [data[y * width : (y + 1) * width] for y in range(int(logic["height"]))]


def _variant(x: int, y: int, count: int) -> int:
    return (x * 7 + y * 13) % count  # variação estável, sem sorteio


def _sides(is_kind: Callable[[int, int], bool], x: int, y: int) -> tuple[bool, bool, bool, bool]:
    return is_kind(x, y - 1), is_kind(x + 1, y), is_kind(x, y + 1), is_kind(x - 1, y)


def _nine(n: bool, e: bool, s: bool, w: bool) -> str:
    """O pedaço de um bloco 3x3 do LPC pela vizinhança do mesmo tipo (norte, leste, sul, oeste)."""
    vertical = "t" if not n else ("b" if not s else "")
    horizontal = "l" if not w else ("r" if not e else "")
    return (vertical + horizontal) or "c"


def _ground(types: Grid, x: int, y: int) -> str:
    kind = types[y][x]
    height, width = len(types), len(types[0])

    def same(cx: int, cy: int) -> bool:
        return 0 <= cx < width and 0 <= cy < height and types[cy][cx] == kind

    if kind in ("grass", "tree"):
        return f"grass-{_variant(x, y, 3)}"
    if kind in PATHS:
        return f"dirt-{_variant(x, y, 3)}"
    if kind == "river":
        return "water-c" if same(x - 1, y) else "water-l"
    if kind == "soil":
        # Terra arada inteira em cada canteiro: as bordas do pacote têm grama dentro do tile, e a
        # planta ficaria em cima da grama.
        return "soil-c"
    return "floor"  # wall, floor e door: tábuas contínuas


def _overlays(types: Grid, x: int, y: int) -> list[str]:
    """O que vai por cima do chão: a cerca viva nas árvores e a terra que transborda do caminho."""
    kind = types[y][x]
    height, width = len(types), len(types[0])

    def tree(cx: int, cy: int) -> bool:  # fora do mapa conta como mata
        return not (0 <= cx < width and 0 <= cy < height) or types[cy][cx] == "tree"

    def path(cx: int, cy: int) -> bool:
        return 0 <= cx < width and 0 <= cy < height and types[cy][cx] in PATHS

    if kind == "tree":
        return ["hedge-" + _nine(*_sides(tree, x, y))]
    if kind == "wall":
        # Parede fina: a faixa de pedra fica na borda que dá para fora da casa.
        def outside(cx: int, cy: int) -> bool:
            inside = 0 <= cx < width and 0 <= cy < height and types[cy][cx] in HOUSE
            return not inside

        n, e, s, w = _sides(outside, x, y)
        sides = ("t" if n else "b" if s else "") + ("l" if w else "r" if e else "")
        return [f"wall-{sides}"] if sides else []
    if kind != "grass":
        return []
    n, e, s, w = _sides(path, x, y)
    edges = [piece for side, piece in ((e, "l"), (w, "r"), (s, "t"), (n, "b")) if side]
    if not edges:
        corners = (
            (path(x + 1, y + 1), "tl"),
            (path(x - 1, y + 1), "tr"),
            (path(x + 1, y - 1), "bl"),
            (path(x - 1, y - 1), "br"),
        )
        edges = [piece for side, piece in corners if side]
    return [f"dirt-edge-{piece}" for piece in edges]


def build(logic: Mapping[str, Any], tileset: Mapping[str, Any]) -> dict[str, Any]:
    types = logical_types(logic)
    height, width = len(types), len(types[0])
    gid = {str(t["type"]): int(t["id"]) + 1 for t in tileset["tiles"]}
    ground = [gid[_ground(types, x, y)] for y in range(height) for x in range(width)]
    stacks = [_overlays(types, x, y) for y in range(height) for x in range(width)]
    depth = max((len(s) for s in stacks), default=0)
    layers: list[dict[str, Any]] = [{"name": "ground", "data": ground}]
    for level in range(depth):
        data = [gid[s[level]] if level < len(s) else 0 for s in stacks]
        layers.append({"name": f"over-{level + 1}", "data": data})
    return {
        "type": "map",
        "version": "1.10",
        "tiledversion": "1.11.0",
        "orientation": "orthogonal",
        "renderorder": "right-down",
        "width": width,
        "height": height,
        "tilewidth": 32,
        "tileheight": 32,
        "infinite": False,
        "nextlayerid": len(layers) + 1,
        "nextobjectid": 1,
        "properties": [
            {
                "name": "generated_by",
                "type": "string",
                "value": "campsverso_tools.visual_map (make mapa-visual)",
            }
        ],
        "layers": [
            {
                "type": "tilelayer",
                "id": i + 1,
                "name": layer["name"],
                "x": 0,
                "y": 0,
                "width": width,
                "height": height,
                "opacity": 1,
                "visible": True,
                "data": layer["data"],
            }
            for i, layer in enumerate(layers)
        ],
        "tilesets": [{"firstgid": 1, **dict(tileset), "image": TILESET_IMAGE}],
    }


def render(doc: Mapping[str, Any]) -> str:
    """JSON com uma linha de tiles por linha do mapa, para o diff ficar legível."""
    width = int(doc["width"])
    blocks: dict[str, str] = {}
    layers: list[dict[str, Any]] = []
    for i, layer in enumerate(doc["layers"]):
        data: Sequence[int] = layer["data"]
        rows = [", ".join(str(v) for v in data[r : r + width]) for r in range(0, len(data), width)]
        mark = f"__layer_{i}__"
        blocks[f'"{mark}"'] = "[\n        " + ",\n        ".join(rows) + "\n      ]"
        layers.append({**layer, "data": mark})
    text = json.dumps({**doc, "layers": layers}, indent=2, ensure_ascii=False)
    for mark, block in blocks.items():
        text = text.replace(mark, block)
    return text + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="campsverso_tools.visual_map")
    parser.add_argument("--check", action="store_true", help="só confere se o arquivo está em dia")
    parser.add_argument("--scenario", choices=SCENARIOS, help="um cenário só (padrão: todos)")
    args = parser.parse_args(argv)
    tileset = json.loads(TILESET.read_text(encoding="utf-8"))
    for scenario in [args.scenario] if args.scenario else SCENARIOS:
        source, out = logic_map(scenario), visual_map(scenario)
        if not out.parent.exists():
            continue  # o cenário ainda não tem pasta de arte
        text = render(build(json.loads(source.read_text(encoding="utf-8")), tileset))
        if args.check:
            if not out.exists() or out.read_text(encoding="utf-8") != text:
                print(
                    f"{out.relative_to(REPO)} desatualizado: rode make mapa-visual", file=sys.stderr
                )
                return 1
            print(f"mapa visual de {scenario} em dia")
            continue
        out.write_text(text, encoding="utf-8")
        print(f"mapa visual gravado em {out.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
