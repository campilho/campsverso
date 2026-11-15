"""O passo de tela (ADR-0079): o avatar anda tantos tiles por segundo na tela, em qualquer escala,
e o passo começado termina antes de o avatar virar para o destino novo."""

from collections.abc import Sequence
from dataclasses import dataclass, field
from itertools import count
from pathlib import Path
from typing import Any

import pytest

from campsverso_cartridge_api import (
    CartridgeManifest,
    ClockDef,
    NeedDef,
    Position,
    WorldBuilder,
)
from campsverso_kernel.core import KernelCore, WorldConfig
from campsverso_kernel.definition import DefinitionBuilder
from campsverso_kernel.errors import DefinitionError
from campsverso_kernel.facts import Fact
from campsverso_kernel.loader import build_world
from campsverso_kernel.testing import RULES, START, TILES, LabCartridge, command, control

# Um corredor de 11 tiles: ana anda de (1,1) para o leste; a caixa do laboratório fica embaixo.
LAYOUT = ("#############", "#...........#", "#.###########", "#############")
PACE = 4.0  # tiles por segundo na tela, o passo do escritório


def corridor() -> dict[str, Any]:
    def props(passable: bool) -> list[dict[str, Any]]:
        return [
            {"name": "passable", "type": "bool", "value": passable},
            {"name": "water", "type": "bool", "value": False},
        ]

    def obj(oid: int, name: str, kind: str, x: int, y: int) -> dict[str, Any]:
        blocking = [{"name": "blocking", "type": "bool", "value": True}] if kind == "box" else []
        return {
            "id": oid,
            "name": name,
            "type": kind,
            "x": x * 16,
            "y": y * 16,
            "properties": blocking,
        }

    return {
        "width": len(LAYOUT[0]),
        "height": len(LAYOUT),
        "tilewidth": 16,
        "tileheight": 16,
        "layers": [
            {"type": "tilelayer", "data": [TILES[c] for row in LAYOUT for c in row]},
            {
                "type": "objectgroup",
                "objects": [obj(1, "ana", "avatar", 1, 1), obj(2, "box", "box", 1, 2)],
            },
        ],
        "tilesets": [
            {
                "firstgid": 1,
                "tiles": [
                    {"id": 0, "type": "floor", "properties": props(True)},
                    {"id": 1, "type": "wall", "properties": props(False)},
                    {"id": 2, "type": "water", "properties": props(False)},
                ],
            }
        ],
    }


@dataclass(frozen=True)
class Corridor:
    """O laboratório num tick de 2 s, com o passo de tela, como o escritório."""

    manifest: CartridgeManifest = field(
        default_factory=lambda: CartridgeManifest("lab_corredor", "0.1.0", ("lab",))
    )

    def contribute(self, world: WorldBuilder) -> None:
        world.configure_clock(ClockDef(2, "06:00", (("manha", "06:00"),), default_scale=1))
        # Num tick de 2 s, as taxas precisam render um número inteiro por tick (M23).
        world.define_need(NeedDef("energia", 25, {"asleep": 15}, role="energy"), override=True)
        world.define_need(NeedDef("fome", 79, {"awake": 15, "asleep": 15}), override=True)
        world.set_map(corridor())
        world.set_screen_tiles_per_second(PACE)

    def rules_file(self) -> Path | None:
        return None


_ids = count(1)


def _core(scale: float) -> KernelCore:
    definition = build_world("lab_corredor", {"lab": LabCartridge(), "lab_corredor": Corridor()})
    core = KernelCore(definition, WorldConfig("lab-03", 7, START), RULES, rules_source="test")
    core.configure_clock("continuous", scale, False)
    core.start()
    core.drain()
    return core


def _walk(core: KernelCore, x: int) -> None:
    cmd = command("move", {"target": {"x": x, "y": 1}})
    cmd["id"] = f"cmd-move-{next(_ids)}"
    core.submit(cmd)


def _run(core: KernelCore, ticks: int) -> list[Fact]:
    facts = core.drain()
    for _ in range(ticks):
        core.step()
        facts += core.drain()
    return facts


def _only(facts: Sequence[Fact], event: str) -> list[dict[str, Any]]:
    return [dict(f.data) for f in facts if f.type == f"campsverso.{event}.v1"]


def _ana(core: KernelCore) -> Position | None:
    return core.world.position_of("ana")


def test_o_passo_de_tela_converte_pela_escala_do_momento() -> None:
    core = _core(1)
    assert core.tiles_per_tick() == pytest.approx(8)  # 4 tiles/s num tick de 2 s a 1x
    core.submit(control("clock.set_scale", {"scale": 72, "reason": "teste"}))
    _run(core, 1)
    assert core.tiles_per_tick() == pytest.approx(PACE * 2 / 72)  # um tile a cada 9 ticks


def test_a_72x_o_andar_leva_na_tela_o_tempo_do_passo() -> None:
    core = _core(72)
    _walk(core, 10)
    (moved,) = _only(_run(core, 1), "world.entity.moved")
    assert moved["tiles_per_tick"] == pytest.approx(PACE * 2 / 72)
    ticks = moved["arrival_tick"] - moved["depart_tick"]
    assert ticks == 81  # 9 tiles a 1/9 de tile por tick
    assert ticks * 2 / 72 == pytest.approx(9 / PACE)  # 2,25 s na tela


def test_trocar_o_destino_no_meio_do_passo_termina_o_passo() -> None:
    core = _core(72)
    _walk(core, 10)
    (first,) = _only(_run(core, 1), "world.entity.moved")
    _run(core, 4)  # quatro ticks: 4/9 do primeiro passo
    assert _ana(core) == Position(1, 1)
    _walk(core, 8)
    facts = _run(core, 1)
    (interrupted,) = _only(facts, "world.entity.move_interrupted")
    (moved,) = _only(facts, "world.entity.moved")
    assert interrupted["position"] == {"x": 2, "y": 1}  # o tile em que estava entrando
    assert moved["origin"] == {"x": 2, "y": 1}
    assert moved["depart_tick"] == first["depart_tick"] + 9  # quando chega no tile
    assert _ana(core) == Position(2, 1)


def test_a_seta_segurada_anda_sem_voltar_o_passo() -> None:
    """O teclado manda um destino novo a cada 200 ms, uns 7 ticks a 72x: antes, cada troca voltava
    o avatar para o tile de trás e ele não saía do lugar."""
    core = _core(72)
    for _ in range(9):
        here = _ana(core)
        assert here is not None
        _walk(core, min(11, here.x + 4))
        _run(core, 7)
    here = _ana(core)
    assert here is not None
    assert here.x >= 1 + int(63 * PACE * 2 / 72) - 1  # 63 ticks a 1/9 de tile: uns 7 tiles


def test_o_destino_no_tile_em_que_ja_entrava_para_ali() -> None:
    core = _core(72)
    _walk(core, 10)
    _run(core, 5)
    _walk(core, 2)  # o tile em que está entrando: aceito, e não "already_there"
    facts = _run(core, 1)
    assert not _only(facts, "action.rejected")
    (moved,) = _only(facts, "world.entity.moved")
    assert moved["origin"] == moved["waypoints"][0] == {"x": 2, "y": 1}
    _run(core, 9)
    assert _ana(core) == Position(2, 1)
    assert core.world.avatar_map["ana"].action is None


def test_sem_passo_de_tela_o_andar_segue_o_relogio_do_mundo() -> None:
    definition = build_world("lab", {"lab": LabCartridge()})
    core = KernelCore(definition, WorldConfig("lab-01", 7, START), RULES, rules_source="test")
    core.configure_clock("continuous", 720, False)
    assert (
        core.tiles_per_tick() == 1
    )  # um tile por minuto num tick de um minuto, em qualquer escala


def test_o_passo_de_tela_precisa_ser_positivo() -> None:
    builder = DefinitionBuilder()
    for bad in (0.0, -1.0, float("inf"), float("nan")):
        with pytest.raises(DefinitionError):
            builder.set_screen_tiles_per_second(bad)
