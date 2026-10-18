"""O mapa do Tiled bate com a bíblia §4, e a ordem do tick fica travada (ADR-0037)."""

from campsverso_testkit.farm import make_core

BIBLIA = """
TTTTTTTTTTTTTTTTTTTTTTTTTTTTRRRR
T...........................RRRR
T.CCCCC.....................RRRR
T.Cb.mC.....................RRRR
T.C...CB....................RRRR
T.CCPCC.....................RRRR
T...=...V...................RRRR
T...=.......................RRRR
T...=.......................RRRR
T...=...HHHH............HHHHRRRR
T...=...HHHH.....W......HHHHRRRR
T...=.......................RRRR
T...=.......................RRRR
T...========================RRRR
T..............=............RRRR
T..............=S...........RRRR
T..............=............RRRR
TTTTTTTTTTTTTTTEETTTTTTTTTTTRRRR
""".strip().splitlines()

TERRAIN = {"grass": ".", "floor": ".", "path": "=", "tree": "T", "river": "R", "wall": "C",
           "door": "P", "soil": "H", "entrance": "E"}  # fmt: skip
OBJECTS = {"bed": "b", "table": "m", "chest": "B", "sell_box": "V", "well": "W", "kiosk": "S",
           "door": "P", "plot": "H"}  # fmt: skip


def test_mapa_do_tiled_reproduz_o_mapa_da_biblia() -> None:
    definition = make_core().definition
    grid = definition.grid
    rows = [[TERRAIN[grid.tile_kinds[y][x]] for x in range(grid.width)] for y in range(grid.height)]
    for spawn in definition.spawns.values():
        if spawn.position is not None and spawn.kind in OBJECTS:
            rows[spawn.position.y][spawn.position.x] = OBJECTS[spawn.kind]
    assert ["".join(r) for r in rows] == BIBLIA


def _position(name: str) -> tuple[int, int]:
    position = make_core().definition.spawns[name].position
    assert position is not None
    return position.x, position.y


def test_ids_dos_canteiros_seguem_a_adr_0019() -> None:
    assert _position("plot-w-01") == (8, 9)
    assert _position("plot-w-08") == (11, 10)
    assert _position("plot-e-04") == (27, 9)


def test_rio_marcado_como_agua_e_canteiros_do_leste_a_ate_4_tiles() -> None:
    definition = make_core().definition
    water = definition.grid.tiles_with("water")
    assert {p.x for p in water} == {28, 29, 30, 31}
    for name, spawn in definition.spawns.items():
        if spawn.kind == "plot" and spawn.position is not None:
            near = min(spawn.position.chebyshev(w) for w in water)
            assert (near <= 4) == name.startswith("plot-e")


ORDEM = {
    "02:00": ["scheduled: faint_late_night(10), starving(40)", "clock: kernel"],
    "05:00": ["scheduled: weather(10), starving(40)", "clock: kernel"],
    "06:00": [
        "scheduled: crop_growth(10), buyer_pay(20), new_day(30), starving(40)",
        "clock: kernel, fase:amanhecer",
    ],
    "22:00": ["scheduled: buyer_collect(10), starving(40)", "clock: kernel"],
}


def test_ordem_efetiva_nos_horarios_chave() -> None:
    core = make_core()
    for hhmm, first_lines in ORDEM.items():
        order = core.describe_order(hhmm)
        assert order[:2] == first_lines, hhmm
        assert order[2:] == [
            "needs: kernel",
            "wake: kernel",
            "actions: kernel",
            "commands: kernel",
            "reactions: -",  # o desmaio por energia 0 é disparado por limiar, não por horário
            "decisions: kernel",
        ]
