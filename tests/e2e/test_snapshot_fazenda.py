"""Snapshot da Fazenda do Camps em momentos difíceis: o mundo restaurado segue igual ao original."""

import json

from campsverso_kernel.core import KernelCore
from campsverso_kernel.snapshot import decode, document, encode, restore
from campsverso_testkit.farm import Farmer, make_core


def _copy(core: KernelCore) -> KernelCore:
    data = encode(document(core, {"code": "teste"}, core.log.next_seq))
    return restore(core.definition, core.config, decode(data))


def _continue(core: KernelCore, ticks: int) -> list[tuple[int, int, str, str]]:
    facts: list[tuple[int, int, str, str]] = []
    for _ in range(ticks):
        core.step()
        facts += [(f.seq, f.tick, f.type, json.dumps(f.data, sort_keys=True)) for f in core.drain()]
    return facts


def _same_future(core: KernelCore, ticks: int = 2 * 1440) -> None:
    copy = _copy(core)
    assert copy.export_state() == core.export_state()
    assert _continue(copy, ticks) == _continue(core, ticks)
    assert copy.export_state() == core.export_state()


def _farmer() -> Farmer:
    core = make_core()
    core.start()
    farmer = Farmer(core)
    farmer.run(1)
    return farmer


def test_canteiros_plantados_e_regra_oculta_contribuindo() -> None:
    farmer = _farmer()
    farmer.walk(23, 9)
    for plot in ("plot-e-01", "plot-e-05"):
        farmer.do("plant", target=plot, crop="rabanete")
        farmer.do("water", target=plot)
    farmer.until("07:00")  # o crescimento do dia 2 ainda vai aplicar a R-001
    _same_future(farmer.core)


def test_no_meio_de_um_trajeto() -> None:
    farmer = _farmer()
    farmer.core.submit(
        {
            "id": "cmd-andar",
            "type": "campsverso.cmd.action.propose.v1",
            "controllerid": "script/farmer-v1",
            "data": {
                "avatar_id": "camps",
                "action": "move",
                "params": {"target": {"x": 23, "y": 9}},
            },
        }
    )
    farmer.run(3)
    assert farmer.core.world.avatar_map["camps"].action is not None
    _same_future(farmer.core)


def test_dormindo_na_cama() -> None:
    farmer = _farmer()
    farmer.walk(4, 3)
    farmer.until("21:00")
    farmer.do("sleep", target="bed")
    farmer.run(30)
    assert farmer.core.world.is_asleep("camps")
    _same_future(farmer.core)
