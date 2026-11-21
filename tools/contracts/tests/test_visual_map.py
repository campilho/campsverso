"""Mapa visual e manifestos de arte (ADR-0053): coerentes com o mapa lógico e com os arquivos."""

import json
import struct
from pathlib import Path
from typing import Any

from campsverso_tools import visual_map
from campsverso_tools.visual_map import (
    GROUND,
    LOGIC,
    OUT,
    REPO,
    TILESET,
    build,
    logical_types,
    render,
)

ART = {"farm": REPO / "cartridges/farm/art", "farm_camps": REPO / "cartridges/farm_camps/art"}


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _png_size(path: Path) -> tuple[int, int]:
    width, height = struct.unpack(">II", path.read_bytes()[16:24])
    return width, height


def test_o_mapa_visual_gravado_esta_em_dia() -> None:
    assert OUT.read_text(encoding="utf-8") == render(build(_json(LOGIC), _json(TILESET)))
    assert visual_map.main(["--check"]) == 0


def test_cada_tile_desenhado_combina_com_o_tipo_logico() -> None:
    logic = logical_types(_json(LOGIC))
    visual = _json(OUT)
    names = {t["id"] + 1: t["type"] for t in visual["tilesets"][0]["tiles"]}
    assert (visual["width"], visual["height"]) == (len(logic[0]), len(logic))
    ground, *over = visual["layers"]
    width = int(visual["width"])
    for i, gid in enumerate(ground["data"]):
        kind = logic[i // width][i % width]
        assert names[gid].startswith(GROUND[kind]), (i % width, i // width, kind, names[gid])
    for layer in over:
        for i, gid in enumerate(layer["data"]):
            kind = logic[i // width][i % width]
            if gid:
                expected = {"tree": "hedge-", "grass": "dirt-edge-", "wall": "wall-"}
                assert kind in expected
                assert names[gid].startswith(expected[kind])


def test_manifestos_apontam_para_arquivos_e_quadros_que_existem() -> None:
    sheets: dict[str, tuple[Path, int, int]] = {}
    for layer, folder in ART.items():
        manifest = _json(folder / "art.json")
        assert manifest["version"] == 1, layer
        assert (folder / manifest["credits"]).is_file(), layer
        if "visual_map" in manifest:
            assert (folder / manifest["visual_map"]).is_file()
        for name, sheet in manifest.get("sheets", {}).items():
            width, height = _png_size(folder / sheet["image"])
            columns, rows = width // sheet["frame_width"], height // sheet["frame_height"]
            sheets[name] = (folder / sheet["image"], columns, rows)
    terrain = _json(TILESET)
    assert (TILESET.parent / terrain["image"]).is_file()
    farm = _json(ART["farm"] / "art.json")
    for kind, art in farm["kinds"].items():
        for look in [art, *(v["look"] for v in art.get("variants", []))]:
            if "sheet" in look:
                _, columns, rows = sheets[look["sheet"]]
                assert look["frame"] < columns * rows, (kind, look)
    camps = _json(ART["farm_camps"] / "art.json")["avatars"]["camps"]
    _, columns, rows = sheets[camps["sheet"]]
    for name, animation in camps["animations"].items():
        last_row = animation["row"] + (0 if animation.get("single") else 3)
        assert last_row < rows, name
        assert max(animation["frames"]) < columns, name
    for target in [camps["idle"], camps["asleep"], *camps["actions"].values()]:
        assert target in camps["animations"]


def test_toda_cultura_e_estagio_da_fazenda_tem_arte() -> None:
    import yaml

    data = yaml.safe_load(
        (REPO / "cartridges/farm/sim/src/campsverso_farm_sim/data/farm.yaml").read_text()
    )
    farm = _json(ART["farm"] / "art.json")
    variants = farm["kinds"]["plot"]["variants"]
    stages = ("broto", "crescendo", "madura", "murcha")
    for crop in data["crops"]:
        for stage in stages:
            assert any(v["when"] == {"crop": crop, "stage": stage} for v in variants), (crop, stage)
    assert any(v["when"] == {"stage": "semente"} for v in variants)


OFFICE_ART = {
    "office": REPO / "cartridges/office/art",
    "office_campsverso": REPO / "cartridges/office_campsverso/art",
}


def test_o_mapa_visual_do_escritorio_combina_com_o_mapa_logico() -> None:
    """O escritório (ADR-0078; a arte nova, ADR-0082): cada tile do chão cabe no tipo lógico, a
    parede do fundo tem duas linhas de face sobre a sala, a faixa de sombra fica junto ao rodapé, o
    tapete fecha o 3 x 3 nos cantos, e o que fica pendurado vai na parede do fundo."""
    scenario = "office_campsverso"
    logic = _json(visual_map.logic_map(scenario))
    tileset = _json(visual_map.OFFICE_TILESET)
    decor = _json(visual_map.decor_file(scenario))
    out = visual_map.visual_map(scenario)
    assert out.read_text(encoding="utf-8") == render(visual_map.build_office(logic, tileset, decor))
    assert (visual_map.OFFICE_TILESET.parent / tileset["image"]).is_file()
    types = logical_types(logic)
    visual = _json(out)
    names = {t["id"] + 1: t["type"] for t in tileset["tiles"]}
    ground, over = visual["layers"]
    width = int(visual["width"])
    for i, gid in enumerate(ground["data"]):
        x, y = i % width, i // width
        assert names[gid] in visual_map.OFFICE_GROUND[types[y][x]], (x, y, names[gid])
        if names[gid] == "fundo-baixo":
            assert types[y + 1][x] in visual_map.ROOM
        if names[gid] == "carpete-sombra":
            assert names[ground["data"][i - width]] == "fundo-baixo", (x, y)
    rug = [
        (i % width, i // width)
        for i, t in enumerate(ground["data"])
        if names[t].startswith("tapete")
    ]
    corners = {names[ground["data"][y * width + x]] for x, y in rug if (x, y) in _corners(rug)}
    assert corners == {"tapete-0", "tapete-2", "tapete-6", "tapete-8"}
    hung = [i for i, gid in enumerate(over["data"]) if gid]
    assert len(hung) == 2 * len(decor["pieces"])  # cada peça em duas metades
    for i in hung:
        under = names[ground["data"][i]]
        assert under.startswith("fundo-"), (i % width, i // width, under)


def _corners(tiles: list[tuple[int, int]]) -> set[tuple[int, int]]:
    xs, ys = [x for x, _ in tiles], [y for _, y in tiles]
    return {(x, y) for x in (min(xs), max(xs)) for y in (min(ys), max(ys))}


def test_a_arte_do_escritorio_esta_em_dia_com_as_folhas_do_design() -> None:
    """As folhas dos cartuchos são cópias das de `docs/design/escritorio-arte/folhas/`, e o tileset
    sai delas igual a cada rodada (`make arte-escritorio`; ADR-0082)."""
    from campsverso_tools import office_art

    for path, content in office_art.outputs().items():
        assert path.read_bytes() == content, path.relative_to(REPO)


def test_os_manifestos_do_escritorio_apontam_para_quadros_que_existem() -> None:
    sheets: dict[str, tuple[int, int]] = {}
    manifests = {layer: _json(folder / "art.json") for layer, folder in OFFICE_ART.items()}
    for layer, manifest in manifests.items():
        folder = OFFICE_ART[layer]
        assert (folder / manifest["credits"]).is_file(), layer
        for name, sheet in manifest.get("sheets", {}).items():
            width, height = _png_size(folder / sheet["image"])
            sheets[name] = (width // sheet["frame_width"], height // sheet["frame_height"])
    scenario = manifests["office_campsverso"]
    assert (OFFICE_ART["office_campsverso"] / scenario["visual_map"]).is_file()
    # O tileset do mapa visual é desenhado pela folha de mesmo nome (a tela procura assim).
    assert _json(visual_map.OFFICE_TILESET)["name"] in manifests["office"]["sheets"]
    for kind, art in manifests["office"]["kinds"].items():
        if "sheet" in art:
            columns, rows = sheets[art["sheet"]]
            frames: list[Any] = [
                art["frame"],
                *(v["look"].get("frame", 0) for v in art.get("variants", [])),
            ]
            in_use: Any = art.get("in_use", [])  # a TV tem uma lista: o jogo e o telejornal
            uses: list[Any] = [in_use] if "actions" in in_use else in_use
            for use in uses:
                frames += use["frames"]
            frames += art.get("loop", {}).get("frames", [])
            frames += [art["front"]] if "front" in art else []
            assert max(frames) < columns * rows, kind
    for name, prop in manifests["office"]["tile_props"].items():
        columns, rows = sheets[prop["sheet"]]
        assert columns * rows >= (16 if prop.get("autotile") == "mask4" else 1), name
    assert manifests["office"]["kinds"]["chair"]["seat"] == "up"
    # Cada tipo de entidade do mapa lógico tem arte (ADR-0082): nada vira um quadrado de cor.
    logic = _json(visual_map.logic_map("office_campsverso"))
    objects = next(layer for layer in logic["layers"] if layer["type"] == "objectgroup")
    assert {o["type"] for o in objects["objects"]} <= set(manifests["office"]["kinds"])
    cast = scenario["avatars"]
    assert set(cast) == {"camps", "gerente", "vigia"}
    for name, avatar in cast.items():
        columns, rows = sheets[avatar["sheet"]]
        for animation in avatar["animations"].values():
            directions = 1 if animation.get("single") else len(animation.get("facings", "1234"))
            assert animation["row"] + directions - 1 < rows, name
            assert max(animation["frames"]) < columns, name
        targets = [avatar["idle"], avatar["asleep"], avatar["seated"], *avatar["actions"].values()]
        targets += avatar.get("seated_actions", {}).values()
        targets += [a for carried in avatar.get("carry", {}).values() for a in carried.values()]
        assert all(target in avatar["animations"] for target in targets), name
        # Quem senta no sofá para ver TV ou jogar senta numa coisa que existe no mapa.
        placed = {o["type"] for o in objects["objects"]}
        assert set(avatar.get("sit_on", {}).values()) <= placed, name
    # A luz da noite, a janela e o relógio, e as fichas do quadro (ADR-0082).
    names = {t["type"] for t in _json(visual_map.OFFICE_TILESET)["tiles"]}
    timed = manifests["office"]["time_tiles"]
    for day, night in timed["night"].items():
        assert {f"{day}-t", f"{day}-b", f"{night}-t", f"{night}-b"} <= names, day
    assert {f"{timed['clock']}-{hour}-{half}" for hour in range(12) for half in "tb"} <= names
    lights = scenario["lights"]
    assert lights["lantern"]["avatar"] in cast
    width, height = int(logic["width"]), int(logic["height"])
    assert all(0 <= x < width and 0 <= y < height for x, y in lights["lamps"])
    cards = scenario["cards"]
    columns, rows = sheets[cards["sheet"]]
    frames = [cards["frame"], *cards["state_frames"].values(), *cards["size_frames"].values()]
    assert max(frames) < columns * rows
    assert set(cards["columns"]) == {"a_fazer", "fazendo", "entregue", "aceito"}
    # O selo do PR nas fichas e a placa da versão na parede (ADR-0083).
    badge = cards["badge"]
    columns, rows = sheets[badge["sheet"]]
    assert set(badge["frames"]) == {"pr", "ci_verde", "ci_vermelho", "mesclado"}
    assert max(badge["frames"].values()) < columns * rows
    plaque = scenario["plaque"]
    columns, rows = sheets[plaque["sheet"]]
    assert plaque["frame"] < columns * rows
    # A placa numa linha (ADR-0087): o texto cabe no quadro, e o quadro, na parede.
    frame_width = manifests["office"]["sheets"][plaque["sheet"]]["frame_width"]
    text = plaque["text"]
    assert set(text) == {"x", "y", "width", "color"}
    assert text["x"] + text["width"] <= frame_width
    assert 0 <= plaque["x"] <= width * 32 - frame_width
