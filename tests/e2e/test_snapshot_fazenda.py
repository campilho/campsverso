"""Snapshot da Fazenda do Camps em momentos difíceis: o mundo restaurado segue igual ao original."""

import json

from campsverso_kernel.core import KernelCore
from campsverso_kernel.snapshot import decode, document, encode, restore
from campsverso_testkit.farm import Farmer, make_core, of_type


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


def _farmer(cartridge: str = "farm_camps") -> Farmer:
    core = make_core(cartridge=cartridge)
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
    # A 30 tiles por minuto (ADR-0057) qualquer trajeto cabe num tick: depois do primeiro passo a
    # caminhada está em curso, com a trajetória no estado, e termina no passo seguinte.
    farmer.run(1)
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


def test_boa_vista_canteiro_cavado_ferramenta_no_bau_lotes_e_ensopado() -> None:
    """ADR-0062: o que a Fazenda Boa Vista acrescenta ao estado (canteiro criado em tempo de
    execução, entidade guardada no baú, lotes com validade, modificador de necessidade e o peso)
    sobrevive ao snapshot e segue igual."""
    farmer = _farmer("farm_boavista")
    world = farmer.core.world
    for item in ("batata", "cenoura", "alho", "adubo"):
        world.create_item(item, 1, "camps", "test")
    farmer.core.drain()
    farmer.walk(4, 8)
    farmer.do("dig", target={"x": 5, "y": 8})
    farmer.do("fertilize", target="plot-01")
    farmer.do("plant", target="plot-01", crop="rabanete")
    farmer.do("water", target="plot-01")
    farmer.walk(4, 4)  # dentro da casa, ao lado do fogão
    assert of_type(farmer.do("cook", target="stove", recipe="ensopado"), "action.completed")
    assert of_type(farmer.do("eat", item="ensopado"), "action.completed")  # saciedade por 8 h
    assert "ensopado" not in world.items("camps")
    world.move_entity("spade", "chest")  # uma entidade guardada noutro contêiner
    farmer.core.drain()
    assert world.entity("spade").container_id == "chest"
    assert world.entity("plot-01").attributes["crop"] == "rabanete"
    farmer.until("08:00")  # a virada ainda vai estragar, crescer a planta e soltar a saciedade
    _same_future(farmer.core)
