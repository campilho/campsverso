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


def maps_of(scenario: str) -> list[tuple[Path, Path]]:
    """O mapa lógico e o visual do cenário, e os de cada variante do mapa (ADR-0070): a variante
    `maps/b.tmj` vira `map-visual-b.tmj`, ao lado do mapa visual de hoje."""
    base = logic_map(scenario)
    pairs = [(base, visual_map(scenario))]
    for variant in sorted((base.parent / "maps").glob("*.tmj")):
        pairs.append((variant, visual_map(scenario).with_name(f"map-visual-{variant.stem}.tmj")))
    return pairs


LOGIC = logic_map("farm_camps")
OUT = visual_map("farm_camps")
TILESET_IMAGE = "../../farm/art/terrain.png"  # relativo ao mapa visual, para abrir no Tiled
# Árvores LPC por cima da mata (ADR-0067): só nos cenários listados, na folha `trees.png` da
# pasta de arte deles, 4 árvores de 3 x 4 tiles lado a lado. As fazendas 1 e 2 ficam com a cerca.
TREE_SCENARIOS = ("farm_morada_do_sol",)
TREES, TREE_W, TREE_H = 4, 3, 4

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

    if kind in ("grass", "tree"):
        return f"grass-{_variant(x, y, 3)}"
    if kind in PATHS:
        return f"dirt-{_variant(x, y, 3)}"
    if kind == "river":
        # A margem do lado que dá para a terra; fora do mapa conta como água, então o rio que corre
        # na borda (as fazendas 1 e 2, a Morada do Sol) só tem a margem de dentro. As lagoas e o
        # córrego das variantes (ADR-0070) têm margem dos quatro lados.
        def water(cx: int, cy: int) -> bool:
            return not (0 <= cx < width and 0 <= cy < height) or types[cy][cx] == "river"

        return "water-" + _nine(*_sides(water, x, y))
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


def _trees(types: Grid, first: int) -> list[int]:
    """Árvores carimbadas na mata: a cada 3 colunas e 4 linhas, com as linhas desencontradas, onde
    o tronco e os dois lados dele são mata. Uma árvore de 3 x 4 tiles nunca cobre outra."""
    height, width = len(types), len(types[0])
    data = [0] * (width * height)
    for base in range(TREE_H - 1, height, TREE_H):
        shift = (base // TREE_H) % 2
        for x in range(1 + shift, width - 1, TREE_W):
            if not all(types[base][cx] == "tree" for cx in (x - 1, x, x + 1)):
                continue
            tree = _variant(x, base, TREES)
            for row in range(TREE_H):
                for col in range(TREE_W):
                    ty, tx = base - TREE_H + 1 + row, x - 1 + col
                    if 0 <= ty < height:
                        tile = row * TREES * TREE_W + tree * TREE_W + col
                        data[ty * width + tx] = first + tile
    return data


def build(
    logic: Mapping[str, Any], tileset: Mapping[str, Any], *, trees: bool = False
) -> dict[str, Any]:
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
    tilesets: list[dict[str, Any]] = [{"firstgid": 1, **dict(tileset), "image": TILESET_IMAGE}]
    if trees:
        first = 1 + int(tileset["tilecount"])
        layers.append({"name": "trees", "data": _trees(types, first)})
        tilesets.append(
            {
                "firstgid": first,
                "name": "trees",
                "tilewidth": 32,
                "tileheight": 32,
                "tilecount": TREES * TREE_W * TREE_H,
                "columns": TREES * TREE_W,
                "margin": 0,
                "spacing": 0,
                "image": "trees.png",
                "imagewidth": TREES * TREE_W * 32,
                "imageheight": TREE_H * 32,
            }
        )
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
        "tilesets": tilesets,
    }


def render(doc: Mapping[str, Any]) -> str:
    """JSON com uma linha de tiles por linha do mapa, para o diff ficar legível."""
    width = int(doc["width"])
    blocks: dict[str, str] = {}
    layers: list[dict[str, Any]] = []
    for i, layer in enumerate(doc["layers"]):
        if "data" not in layer:  # a camada de objetos do mapa lógico (as variantes, ADR-0070)
            layers.append(dict(layer))
            continue
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
        for source, out in maps_of(scenario):
            if not out.parent.exists():
                continue  # o cenário ainda não tem pasta de arte
            logic = json.loads(source.read_text(encoding="utf-8"))
            text = render(build(logic, tileset, trees=scenario in TREE_SCENARIOS))
            if args.check:
                if not out.exists() or out.read_text(encoding="utf-8") != text:
                    print(
                        f"{out.relative_to(REPO)} desatualizado: rode make mapa-visual",
                        file=sys.stderr,
                    )
                    return 1
                print(f"mapa visual {out.name} de {scenario} em dia")
                continue
            out.write_text(text, encoding="utf-8")
            print(f"mapa visual gravado em {out.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
