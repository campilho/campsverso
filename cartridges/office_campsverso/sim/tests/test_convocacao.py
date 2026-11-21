"""A convocação do dev fora do expediente (a parte 5 do M25): ao entrar, pelo botão, a dispensa, a
saída do gerente, o teto, a janela do dia e o expediente que assume."""

import re
from collections.abc import Sequence
from datetime import datetime, timedelta, timezone
from typing import Any

from campsverso_kernel.core import KernelCore, WorldConfig
from campsverso_kernel.facts import Fact
from campsverso_kernel.loader import build_world

SAO_PAULO = timezone(timedelta(hours=-3))
SATURDAY = datetime(2026, 11, 21, 10, 0, tzinfo=SAO_PAULO)
HUMAN = {"type": "human", "id": "human/camps-browser"}
TICKS_PER_MINUTE = 240  # o tick de 250 ms (ADR-0081)


def _core(start: datetime = SATURDAY) -> KernelCore:
    core = KernelCore(
        build_world("office_campsverso"), WorldConfig("office-teste", 1, start), (), "test"
    )
    core.start()
    core.drain()
    return core


def _only(facts: Sequence[Fact], event: str) -> list[dict[str, Any]]:
    wanted = f"campsverso.{event}" if re.search(r"\.v\d+$", event) else f"campsverso.{event}.v1"
    return [dict(f.data) for f in facts if f.type == wanted]


def _minutes(core: KernelCore, count: float) -> list[Fact]:
    """Roda tantos minutos, tick a tick, conferindo que o dev e o vigia nunca estão juntos."""
    facts: list[Fact] = []
    for _ in range(round(count * TICKS_PER_MINUTE)):
        core.step()
        facts += core.drain()
        inside = {a for a in ("camps", "vigia") if core.world.avatar_map[a].present}
        assert inside != {"camps", "vigia"}, f"os dois no escritório no tick {core.tick}"
    return facts


def _jump(core: KernelCore, minutes: int) -> list[Fact]:
    core.advance(minutes * TICKS_PER_MINUTE, jump=True)
    return core.drain()


def _possess(core: KernelCore) -> None:
    core.submit(
        {
            "id": f"cmd-assumir-{core.tick}",
            "type": "campsverso.cmd.avatar.possess.v1",
            "actor": "human/operator",
            "data": {"avatar_id": "gerente", "controller": HUMAN},
        }
    )


def _release(core: KernelCore) -> None:
    core.submit(
        {
            "id": f"cmd-devolver-{core.tick}",
            "type": "campsverso.cmd.avatar.release.v1",
            "actor": "human/operator",
            "data": {"avatar_id": "gerente"},
        }
    )


def _propose(core: KernelCore, action: str) -> None:
    core.submit(
        {
            "id": f"cmd-gerente-{action}-{core.tick}",
            "type": "campsverso.cmd.action.propose.v1",
            "controllerid": HUMAN["id"],
            "data": {"avatar_id": "gerente", "action": action, "params": {}},
        }
    )


def _present(core: KernelCore, avatar: str) -> bool:
    return core.world.avatar_map[avatar].present


def test_o_gerente_entra_no_sabado_e_o_camps_vem_pelo_chamado() -> None:
    core = _core()
    assert _present(core, "vigia")
    _possess(core)
    facts = _minutes(core, 1.1)
    (summoned,) = _only(facts, "office.staff.summoned")
    assert (summoned["avatar_id"], summoned["by"], summoned["origin"]) == (
        "camps",
        "gerente",
        "entrada",
    )
    assert summoned["arrives_tick"] - core.tick <= 2 * TICKS_PER_MINUTE  # o deslocamento
    assert summoned["until_tick"] - summoned["arrives_tick"] == 6 * 60 * TICKS_PER_MINUTE - (
        2 * TICKS_PER_MINUTE
    )
    assert not _present(core, "camps")  # ainda a caminho
    facts = _minutes(core, 2)
    entered = [d for d in _only(facts, "avatar.entered") if d["avatar_id"] == "camps"]
    assert [d["reason"] for d in entered] == ["convocacao"]
    left = _only(facts, "avatar.left")
    assert [(d["avatar_id"], d["reason"]) for d in left] == [("vigia", "plantao")]
    assert _present(core, "camps")
    assert not _present(core, "vigia")


def test_dispensado_ele_vai_embora_e_so_o_botao_o_chama_de_novo() -> None:
    core = _core()
    _possess(core)
    _minutes(core, 3.1)
    assert _present(core, "camps")
    _propose(core, "dismiss")
    facts = _minutes(core, 1.1)
    (dismissed,) = _only(facts, "office.staff.dismissed")
    assert dismissed == {"avatar_id": "camps", "reason": "dispensado", "by": "gerente"}
    assert [(d["avatar_id"], d["reason"]) for d in _only(facts, "avatar.left")] == [
        ("camps", "convocacao")
    ]
    assert _present(core, "vigia")  # o vigia volta
    _jump(core, 30)
    assert not _present(core, "camps")  # com o gerente lá, ele não volta sozinho
    _propose(core, "summon")
    facts = _minutes(core, 3.1)
    (summoned,) = _only(facts, "office.staff.summoned")
    assert summoned["origin"] == "gerente"
    assert _present(core, "camps")
    _propose(core, "summon")  # de novo: já está convocado
    (rejected,) = _only(_minutes(core, 0.1), "action.rejected")
    assert "já foi convocado" in rejected["detail"]


def test_o_gerente_sai_e_a_convocacao_acaba() -> None:
    core = _core()
    _possess(core)
    _minutes(core, 3.1)
    _release(core)
    facts = _minutes(core, 1.1)
    assert _only(facts, "office.staff.dismissed") == [{"avatar_id": "camps", "reason": "saida"}]
    assert not _present(core, "camps")
    assert _present(core, "vigia")
    _possess(core)  # a visita nova chama de novo, mesmo depois de uma dispensa
    _minutes(core, 3.1)
    assert _present(core, "camps")


def test_o_teto_de_horas_encerra_a_convocacao() -> None:
    core = _core(datetime(2026, 11, 21, 8, 0, tzinfo=SAO_PAULO))
    _possess(core)
    _minutes(core, 3.1)
    facts = _jump(core, 6 * 60)
    assert _only(facts, "office.staff.dismissed") == [{"avatar_id": "camps", "reason": "teto"}]
    assert not _present(core, "camps")
    _jump(core, 60)
    assert not _present(core, "camps")  # o teto não chama de novo sozinho


def test_a_janela_do_dia_comeca_as_8_e_acaba_as_23() -> None:
    core = _core(datetime(2026, 11, 21, 22, 50, tzinfo=SAO_PAULO))
    _possess(core)
    _minutes(core, 3.1)
    assert _present(core, "camps")
    facts = _jump(core, 10)
    assert _only(facts, "office.staff.dismissed") == [{"avatar_id": "camps", "reason": "janela"}]
    assert not _present(core, "camps")
    _propose(core, "summon")
    (rejected,) = _only(_minutes(core, 0.1), "action.rejected")
    assert rejected["detail"] == "a convocação vale das 08:00 às 23:00"
    late = _core(datetime(2026, 11, 22, 6, 0, tzinfo=SAO_PAULO))  # domingo cedo, fora da janela
    _possess(late)
    _minutes(late, 3.1)
    assert not _present(late, "camps")


def test_no_dia_util_o_botao_espera_o_fim_do_expediente_e_o_expediente_assume() -> None:
    weekday = _core(datetime(2026, 11, 23, 10, 0, tzinfo=SAO_PAULO))  # segunda, no expediente
    _possess(weekday)
    _jump(weekday, 1)
    _propose(weekday, "summon")
    (rejected,) = _only(_minutes(weekday, 0.1), "action.rejected")
    assert rejected["detail"] == "o Camps está no expediente"
    early = _core(datetime(2026, 11, 23, 8, 0, tzinfo=SAO_PAULO))  # segunda cedo
    _possess(early)
    _minutes(early, 3.1)
    assert _present(early, "camps")
    facts = _jump(early, 60)  # as 09:00: o expediente assume, e o dev fica
    assert _only(facts, "office.staff.dismissed") == [
        {"avatar_id": "camps", "reason": "expediente"}
    ]
    assert not [d for d in _only(facts, "avatar.left") if d["avatar_id"] == "camps"]
    assert _present(early, "camps")
