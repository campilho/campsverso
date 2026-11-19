"""A arte do escritório a partir das folhas do Claude Design (ADR-0082).

    uv run python -m campsverso_tools.office_art [--check]   # ou: make arte-escritorio

As folhas desenhadas em código ficam em `docs/design/escritorio-arte/folhas/`, como chegaram. Daqui
saem, para os cartuchos:

- `cartridges/office/art/terreno.png` e `terreno.tsj`: o tileset do mapa visual, um tile de 32 px
  por nome (o carpete e a faixa de sombra junto ao rodapé, o corredor, as paredes e os cantos, a
  porta, o tapete 3 x 3 e, em duas metades, o que fica pendurado na parede do fundo: o quadro dos
  pedidos em módulos, a janela com a cidade e o relógio);
- as folhas dos móveis, copiadas byte a byte para `cartridges/office/art/`, e uma folha vazia para
  o que o mapa visual ou outra peça já desenha (o quadro na parede, o micro-ondas no balcão); a
  mesinha da copa sai com dois quadros, o segundo com a marmita aberta em cima, para quem come;
- a folha das fichas do quadro dos pedidos, que a tela pendura pelo estado de cada pedido;
- as folhas dos três personagens, copiadas para `cartridges/office_campsverso/art/`;
- as folhas dos balões, dos ícones e da fonte (o pedido de arte de 18/nov), copiadas, e a geometria
  delas em `baloes.json`, que o `art.json` do gênero inclui: as peças, as molduras em nove fatias, o
  fio do progresso, a fonte com a largura de cada glifo e as cores da paleta em hex.

O mapa visual sai depois, por `make mapa-visual`. Com `--check`, só confere se está tudo em dia.
"""

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from campsverso_tools.png import Img, blank, crop, encode_png, paste, paste_over, read_png

REPO = Path(__file__).resolve().parents[4]
SOURCE = REPO / "docs/design/escritorio-arte/folhas"
GENRE = REPO / "cartridges/office/art"
SCENARIO = REPO / "cartridges/office_campsverso/art"
T = 32
COLUMNS = 8
TILESET = "office-terreno"
# Os móveis e as coisas da sala, no gênero; os personagens, no cenário.
FURNITURE = (
    "mesa_dev",
    "cadeira",
    "cadeira_lado",
    "divisoria",
    "arquivo",
    "planta",
    "lixeira",
    "geladeira",
    "balcao_copa",
    "maquina_cafe",
    "bebedouro",
    "sofa_costas",
    "movel_tv",
    "puff",
    "banheiro",
    # A oficina dos robôs (o plano do M24, §4): a bancada e os três robôs de mesa.
    "bancada",
    "robo_testador",
    "robo_revisor",
    "robo_publicador",
)
CHARACTERS = ("camps", "gerente", "vigia")
# Soltas: as fichas do quadro, que a tela pendura pelo estado (10 x 10).
LOOSE = ("fichas",)
# O que fica sobre a cabeça (o pedido de arte de 18/nov): os balões e os ícones, copiados; a fonte
# sai de `font_sheet`, com cada glifo colado à esquerda da célula.
INTERFACE = ("baloes", "icones")
# O que fica na parede do fundo, em módulos de 32 x 64: o nome do tile e o quadro da folha.
WALL_PIECES = (
    ("quadro-comeco", "quadro_pedidos", 0),
    ("quadro-meio", "quadro_pedidos", 1),
    ("quadro-fim", "quadro_pedidos", 2),
    ("janela-comeco", "janela_dia", 0),
    ("janela-meioA", "janela_dia", 1),
    ("janela-meioB", "janela_dia", 2),
    ("janela-fim", "janela_dia", 3),
    # A janela de noite (a luz, das 18:00 em diante) e o relógio em cada hora: a tela troca os
    # tiles pelo relógio do mundo.
    ("janela-noite-comeco", "janela_noite", 0),
    ("janela-noite-meioA", "janela_noite", 1),
    ("janela-noite-meioB", "janela_noite", 2),
    ("janela-noite-fim", "janela_noite", 3),
    *((f"relogio-{hour}", "relogio", hour) for hour in range(12)),
)
# A marmita aberta na mesinha da copa, no quadro de 32 x 64 dela (a prévia: 8 px da esquerda, 30
# do alto).
LUNCHBOX_AT = (8, 30)
VOID = (27, 23, 38, 255)  # o contorno da paleta, fora da sala


def tiles() -> list[tuple[str, Img]]:
    """Os tiles do mapa visual, com nome, na ordem do tileset."""
    cache: dict[str, Img] = {}

    def sheet(name: str) -> Img:
        if name not in cache:
            cache[name] = read_png(SOURCE / f"{name}.png")
        return cache[name]

    def frame(name: str, column: int, row: int = 0, height: int = T) -> Img:
        return crop(sheet(name), column * T, row * height, T, height)

    named: list[tuple[str, Img]] = [("void", blank(T, T, VOID))]
    named += [(f"carpete-{k}", frame("carpete", k)) for k in range(4)]
    named += [("carpete-sombra", frame("carpete", 4)), ("corredor", frame("corredor", 0))]
    named += [("fundo-cima", frame("parede_fundo", 0)), ("fundo-baixo", frame("parede_fundo", 1))]
    sides = ("lado-esq", "lado-dir", "canto-fundo-esq", "canto-fundo-dir")
    sides += ("canto-baixo-esq", "canto-baixo-dir")
    named += [(name, frame("parede_lado", k)) for k, name in enumerate(sides)]
    named += [
        (name, frame("parede_baixo", k))
        for k, name in enumerate(("baixo", "porta-fechada", "porta-aberta"))
    ]
    named += [
        (f"tapete-{row * 3 + col}", frame("tapete", col, row))
        for row in range(3)
        for col in range(3)
    ]
    for name, source, column in WALL_PIECES:
        tall = frame(source, column, height=2 * T)
        named += [(f"{name}-t", crop(tall, 0, 0, T, T)), (f"{name}-b", crop(tall, 0, T, T, T))]
    return named


def tileset() -> tuple[bytes, dict[str, object]]:
    """A imagem do tileset e o `.tsj` que dá o nome de cada tile."""
    named = tiles()
    rows = -(-len(named) // COLUMNS)
    image = blank(COLUMNS * T, rows * T)
    for i, (_, tile) in enumerate(named):
        paste(image, tile, (i % COLUMNS) * T, (i // COLUMNS) * T)
    tsj: dict[str, object] = {
        "type": "tileset",
        "version": "1.10",
        "tiledversion": "1.11.0",
        "name": TILESET,
        "image": "terreno.png",
        "imagewidth": COLUMNS * T,
        "imageheight": rows * T,
        "tilewidth": T,
        "tileheight": T,
        "tilecount": len(named),
        "columns": COLUMNS,
        "margin": 0,
        "spacing": 0,
        "tiles": [{"id": i, "type": name} for i, (name, _) in enumerate(named)],
    }
    return encode_png(image), tsj


def copa_table() -> Img:
    """A mesinha da copa em dois quadros: vazia e com a marmita aberta, enquanto alguém come."""
    table = read_png(SOURCE / "mesa_copa.png")
    box = crop(read_png(SOURCE / "marmita.png"), 16, 0, 16, 16)  # o quadro 1: aberta, com a comida
    sheet = blank(2 * T, 2 * T)
    paste(sheet, table, 0, 0)
    paste(sheet, table, T, 0)
    paste_over(sheet, box, T + LUNCHBOX_AT[0], LUNCHBOX_AT[1])
    return sheet


def bubbles() -> dict[str, object]:
    """A geometria dos balões, dos ícones e da fonte, do `metadados.json` do Claude Design, no
    formato do manifesto de arte (`bubbles`), com as cores da paleta em hex."""
    meta = json.loads((SOURCE / "metadados.json").read_text(encoding="utf-8"))
    palette: dict[str, str] = meta["paleta"]
    sheets = meta["folhas"]
    balloons, icons, glyphs = sheets["baloes"], sheets["icones"], sheets["fonte"]
    pieces = balloons["pecas"]
    font = glyphs["fonte"]

    def frame(name: str, piece: str) -> dict[str, object]:
        style = balloons["molduras"][name]
        return {
            "rect": pieces[piece],
            "slice": balloons["fatia"],
            "color": palette[style["cor"]],
            "margin": style["margem"],
            "line": style["entrelinha"],
            "lines": style["linhasMax"],
        }

    tail = balloons["ponta"]
    progress = balloons["progresso"]
    return {
        "about": (
            "Gerado por make arte-escritorio a partir de docs/design/escritorio-arte/folhas/"
            "metadados.json: não edite à mão. O art.json do gênero o inclui e diz o ícone de "
            "cada ação."
        ),
        "sheets": {
            "baloes": {"image": "baloes.png", "frame_width": 8, "frame_height": 8},
            "icones": {
                "image": "icones.png",
                "frame_width": icons["quadro"][0],
                "frame_height": icons["quadro"][1],
            },
            "fonte": {
                "image": "fonte.png",
                "frame_width": font["celula"][0],
                "frame_height": font["celula"][1],
            },
        },
        "bubbles": {
            "sheet": "baloes",
            "action": {
                "rect": pieces["acao"],
                "anchor": balloons["ancora"],
                "slot": balloons["miolo"],
                "progress": {
                    "x": progress["x"],
                    "y": progress["y"],
                    "width": progress["largura"],
                    "height": progress["altura"],
                    "track": palette[progress["trilho"]],
                    "fill": palette[progress["cheio"]],
                },
                "at_desk": balloons["naMesa"],
            },
            "icons": {"sheet": "icones", "columns": icons["colunas"], "frames": icons["icones"]},
            "label": frame("etiqueta", "etiqueta"),
            "speech": {
                **frame("fala", "fala"),
                "tail": {"rect": pieces[tail["peca"]], "rise": tail["sobe"], "tip": tail["bico"]},
            },
            "font": {
                "sheet": "fonte",
                "cell": font["celula"],
                "columns": glyphs["colunas"],
                "spacing": font["espaco"],
                "glyphs": font["glifos"],
                "widths": font["larguras"],
            },
        },
    }


def font_sheet() -> Img:
    """A folha da fonte com cada glifo começando na coluna 0 da célula, como a tela o recorta (o
    metadados diz assim, mas o "." da folha de 18/nov veio na coluna 1 e sumia)."""
    meta = json.loads((SOURCE / "metadados.json").read_text(encoding="utf-8"))
    width, height = meta["folhas"]["fonte"]["fonte"]["celula"]
    sheet = read_png(SOURCE / "fonte.png")
    out = blank(len(sheet[0]), len(sheet))
    for top in range(0, len(sheet), height):
        for left in range(0, len(sheet[0]), width):
            cell = crop(sheet, left, top, width, height)
            used = [x for row in cell for x, px in enumerate(row) if px[3] > 0]
            shift = min(used, default=0)
            paste(out, crop(cell, shift, 0, width - shift, height), left, top)
    return out


def outputs() -> dict[Path, bytes]:
    """Cada arquivo que esta ferramenta escreve nos cartuchos, com o conteúdo."""
    png, tsj = tileset()
    files: dict[Path, bytes] = {
        GENRE / "terreno.png": png,
        GENRE / "terreno.tsj": (json.dumps(tsj, indent=2, ensure_ascii=False) + "\n").encode(),
        GENRE / "vazio.png": encode_png(blank(T, T)),
    }
    for name in (*FURNITURE, *LOOSE, *INTERFACE):
        files[GENRE / f"{name}.png"] = (SOURCE / f"{name}.png").read_bytes()
    files[GENRE / "fonte.png"] = encode_png(font_sheet())
    text = json.dumps(bubbles(), indent=2, ensure_ascii=False) + "\n"
    files[GENRE / "baloes.json"] = text.encode()
    files[GENRE / "mesa_copa.png"] = encode_png(copa_table())
    for name in CHARACTERS:
        files[SCENARIO / f"{name}.png"] = (SOURCE / f"{name}.png").read_bytes()
    return files


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="campsverso_tools.office_art")
    parser.add_argument("--check", action="store_true", help="só confere se a arte está em dia")
    args = parser.parse_args(argv)
    stale: list[Path] = []
    for path, content in outputs().items():
        if args.check:
            if not path.is_file() or path.read_bytes() != content:
                stale.append(path)
            continue
        path.write_bytes(content)
        print(f"gravado {path.relative_to(REPO)}")
    for path in stale:
        print(f"{path.relative_to(REPO)} desatualizado: rode make arte-escritorio", file=sys.stderr)
    return 1 if stale else 0


if __name__ == "__main__":
    sys.exit(main())
