"""A luz da sala (ADR-0088): o interruptor na parede à direita da porta, o temporizador do prédio e
quem acende e apaga ao lado dele."""

import re
from collections.abc import Sequence
from datetime import datetime, timedelta, timezone
from typing import Any

from campsverso_cartridge_api import Position
from campsverso_kernel.core import KernelCore, WorldConfig
from campsverso_kernel.facts import Fact
from campsverso_kernel.loader import build_world

SAO_PAULO = timezone(timedelta(hours=-3))
SATURDAY = datetime(2026, 11, 21, 10, 0, tzinfo=SAO_PAULO)
HUMAN = {"type": "human", "id": "human/camps-browser"}
TICKS_PER_MINUTE = 240  # o tick de 250 ms (ADR-0081)
SWITCHED = "campsverso.office.light.switched.v1"


def _core(start: datetime = SATURDAY) -> KernelCore:
    core = KernelCore(
        build_world("office_campsverso"), WorldConfig("office-teste", 1, start), (), "test"
    )
    core.start()
    core.drain()
    return core


def _only(facts: Sequence[Fact], event: str) -> list[dict[str, Any]]:
    wanted = event if re.search(r"\.v\d+$", event) else f"campsverso.{event}.v1"
    return [dict(f.data) for f in facts if f.type == wanted]


def _minutes(core: KernelCore, count: float) -> list[Fact]:
    facts: list[Fact] = []
    for _ in range(round(count * TICKS_PER_MINUTE)):
        core.step()
        facts += core.drain()
    return facts


def _jump(core: KernelCore, minutes: int) -> list[Fact]:
    core.advance(minutes * TICKS_PER_MINUTE, jump=True)
    return core.drain()


def _lit(core: KernelCore) -> object:
    return core.world.entity_map["interruptor"].attributes.get("acesa")


def _propose(core: KernelCore, action: str, params: dict[str, Any] | None = None) -> None:
    core.submit(
        {
            "id": f"cmd-gerente-{action}-{core.tick}",
            "type": "campsverso.cmd.action.propose.v1",
            "controllerid": HUMAN["id"],
            "data": {"avatar_id": "gerente", "action": action, "params": params or {}},
        }
    )


def _enter(core: KernelCore) -> None:
    core.submit(
        {
            "id": f"cmd-assumir-{core.tick}",
            "type": "campsverso.cmd.avatar.possess.v1",
            "actor": "human/operator",
            "data": {"avatar_id": "gerente", "controller": HUMAN},
        }
    )
    _minutes(core, 0.1)


def test_o_interruptor_entra_na_parede_apagado_de_dia_e_o_temporizador_acende_e_apaga() -> None:
    core = _core()
    assert core.world.position_of("interruptor") == Position(10, 13)
    assert _lit(core) is False
    on = _only(_jump(core, 8 * 60 + 1), SWITCHED)  # 18:01: passou das 18:00
    assert on == [{"switch_id": "interruptor", "on": True}]  # sem `by`: o temporizador
    assert _lit(core) is True
    off = _only(_jump(core, 3 * 60), SWITCHED)  # 21:01
    assert off == [{"switch_id": "interruptor", "on": False}]
    assert _lit(core) is False
    assert _only(_jump(core, 60), SWITCHED) == []  # 22:01: nada


def test_num_mundo_que_comeca_as_19h_o_interruptor_entra_aceso() -> None:
    core = _core(SATURDAY.replace(hour=19))
    assert _lit(core) is True


def test_o_gerente_acende_e_apaga_ao_lado_do_interruptor_e_de_longe_e_recusado() -> None:
    core = _core(SATURDAY.replace(hour=22))
    assert _lit(core) is False
    _enter(core)  # o gerente entra pelo corredor, na frente da porta (9, 15)
    _propose(core, "light_on")
    (far,) = _only(_minutes(core, 0.1), "action.rejected")
    assert far["detail"] == "longe do interruptor"
    _propose(core, "move", {"target": {"x": 10, "y": 14}})
    _minutes(core, 0.5)
    assert core.world.position_of("gerente") == Position(10, 14)
    _propose(core, "light_on")
    facts = _minutes(core, 0.1)
    assert _only(facts, SWITCHED) == [{"switch_id": "interruptor", "on": True, "by": "gerente"}]
    assert _lit(core) is True
    _propose(core, "light_on")
    (again,) = _only(_minutes(core, 0.1), "action.rejected")
    assert again["detail"] == "a luz já está acesa"
    _propose(core, "light_off")
    assert _only(_minutes(core, 0.1), SWITCHED)[0]["on"] is False
    assert _lit(core) is False
