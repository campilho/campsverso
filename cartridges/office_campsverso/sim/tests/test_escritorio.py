"""O escritório no kernel (M23, ADR-0078): o expediente, o pedido no quadro e quem pode o quê."""

import re
from collections.abc import Sequence
from datetime import datetime, timedelta, timezone
from typing import Any

import pytest

from campsverso_kernel.core import KernelCore, WorldConfig
from campsverso_kernel.facts import Fact
from campsverso_kernel.loader import build_world

SAO_PAULO = timezone(timedelta(hours=-3))
MONDAY = datetime(2026, 11, 16, tzinfo=SAO_PAULO)
HUMAN = {"type": "human", "id": "human/camps-browser"}
DEV = "script/dev"
TICKS_PER_SECOND = 4  # o tick de 250 ms (ADR-0081)
TICKS_PER_HOUR = 3600 * TICKS_PER_SECOND


def _core(start: datetime = MONDAY) -> KernelCore:
    core = KernelCore(
        build_world("office_campsverso"), WorldConfig("office-teste", 1, start), (), "test"
    )
    core.start()
    return core


def _only(facts: Sequence[Fact], event: str) -> list[dict[str, Any]]:
    wanted = f"campsverso.{event}" if re.search(r"\.v\d+$", event) else f"campsverso.{event}.v1"
    return [dict(f.data) for f in facts if f.type == wanted]


def _until(core: KernelCore, hhmm: str) -> list[Fact]:
    """Salta até o próximo HH:MM do relógio do mundo e roda esse tick: os fatos do caminho."""
    core.drain()
    core.advance(core.world.ticks_until(hhmm) + 1, jump=True)
    return core.drain()


def _act(
    core: KernelCore, avatar: str, action: str, params: dict[str, Any], controller: str
) -> list[Fact]:
    """Propõe a ação e roda até ela acabar (ou ser recusada)."""
    facts = core.drain()
    core.submit(
        {
            "id": f"cmd-{avatar}-{action}-{core.tick}",
            "type": "campsverso.cmd.action.propose.v1",
            "controllerid": controller,
            "data": {"avatar_id": avatar, "action": action, "params": params},
        }
    )
    for _ in range(4 * TICKS_PER_HOUR):
        core.step()
        facts += core.drain()
        if core.world.avatar_map[avatar].action is None:
            break
    return facts


def _manager_in(core: KernelCore) -> None:
    core.submit(
        {
            "id": "cmd-assumir",
            "type": "campsverso.cmd.avatar.possess.v1",
            "actor": "human/operator",
            "data": {"avatar_id": "gerente", "controller": HUMAN},
        }
    )
    core.drain()


def _write(core: KernelCore, title: str = "Busca por nome", size: str = "P") -> list[Fact]:
    _act(core, "gerente", "move", {"near": "quadro"}, HUMAN["id"])
    params = {
        "title": title,
        "description": "Achar um arquivo.",
        "acceptance": "Acha o CLAUDE.md.",
        "size": size,
    }
    return _act(core, "gerente", "write_ticket", params, HUMAN["id"])


# ------------------------------------------------------------------ o expediente


def test_o_dia_util_do_dev_e_do_vigia() -> None:
    core = _core()
    assert core.world.avatar_map["vigia"].present  # meia-noite de segunda: o plantão
    assert not core.world.avatar_map["camps"].present
    facts = _until(core, "09:00")
    assert _only(facts, "avatar.entered") == [
        {"avatar_id": "camps", "position": {"x": 9, "y": 15}, "reason": "expediente"}
    ]
    assert _only(facts, "avatar.left")[0]["avatar_id"] == "vigia"
    assert not _only(_until(core, "12:00"), "avatar.left")  # o almoço é na copa (ADR-0080)
    assert core.world.avatar_map["camps"].present
    assert not core.world.avatar_map["vigia"].present  # o vigia não vem no almoço
    facts = _until(core, "18:00")
    assert _only(facts, "avatar.left")[0] == {
        "avatar_id": "camps",
        "reason": "expediente",
        "position": {"x": 9, "y": 15},
    }
    assert _only(facts, "avatar.entered")[0]["avatar_id"] == "vigia"


@pytest.mark.parametrize(
    "day", [datetime(2026, 11, 21, tzinfo=SAO_PAULO), datetime(2026, 11, 20, tzinfo=SAO_PAULO)]
)
def test_no_fim_de_semana_e_no_feriado_o_dev_nao_vem(day: datetime) -> None:
    """Um sábado, e a sexta-feira da Consciência Negra."""
    core = _core(day)
    _until(core, "10:00")
    assert not core.world.avatar_map["camps"].present
    assert core.world.avatar_map["vigia"].present


# ------------------------------------------------------------------ o pedido


def test_o_gerente_escreve_o_pedido_no_quadro() -> None:
    core = _core()
    _until(core, "09:00")
    _manager_in(core)
    facts = _write(core)
    (created,) = _only(facts, "office.ticket.created")
    assert created == {
        "ticket_id": "pedido-001",
        "number": 1,
        "title": "Busca por nome",
        "description": "Achar um arquivo.",
        "acceptance": "Acha o CLAUDE.md.",
        "size": "P",
        "author": "gerente",
    }
    ticket = core.world.entity_map["pedido-001"]
    assert ticket.container_id == "quadro"
    assert ticket.attributes["estado"] == "a_fazer"


def test_cada_papel_faz_o_que_e_dele_e_perto_do_lugar_certo() -> None:
    core = _core()
    _until(core, "09:00")
    _manager_in(core)
    # Da porta, longe do quadro.
    far = _act(core, "gerente", "write_ticket", {"title": "x"}, HUMAN["id"])
    assert _only(far, "action.rejected")[0]["reason"] == "not_adjacent"
    _write(core)
    taken = _act(core, "gerente", "take_ticket", {}, HUMAN["id"])
    assert _only(taken, "action.rejected")[0]["reason"] == "not_allowed"
    _act(core, "camps", "move", {"near": "quadro"}, DEV)
    wrote = _act(core, "camps", "write_ticket", {"title": "x"}, DEV)
    assert _only(wrote, "action.rejected")[0]["reason"] == "not_allowed"


def test_nenhum_humano_assume_o_dev() -> None:
    core = _core()
    core.submit(
        {
            "id": "cmd-dev",
            "type": "campsverso.cmd.avatar.possess.v1",
            "actor": "human/operator",
            "data": {"avatar_id": "camps", "controller": HUMAN},
        }
    )
    assert _only(core.drain(), "world.command.rejected")[0]["reason"] == "controller_not_allowed"


def test_pegar_trabalhar_parar_para_o_almoco_na_copa_e_entregar() -> None:
    core = _core()
    _until(core, "11:40")
    _manager_in(core)
    _write(core, size="P")  # 15 minutos de trabalho
    _act(core, "camps", "move", {"near": "quadro"}, DEV)
    (taken,) = _only(_act(core, "camps", "take_ticket", {}, DEV), "office.ticket.taken")
    assert taken["number"] == 1
    _act(core, "camps", "move", {"target": {"x": 5, "y": 7}}, DEV)  # a cadeira, junto da mesa
    core.submit(
        {
            "id": "cmd-work",
            "type": "campsverso.cmd.action.propose.v1",
            "controllerid": DEV,
            "data": {"avatar_id": "camps", "action": "work", "params": {}},
        }
    )
    for _ in range(5 * 60 * TICKS_PER_SECOND):  # cinco minutos de trabalho
        core.step()
    _act(core, "camps", "move", {"near": "mesa-copa"}, DEV)  # para: o trabalho fica guardado
    worked = core.world.entity_map["pedido-001"].attributes["trabalho"]
    assert isinstance(worked, int)
    assert 0 < worked < 900
    _until(core, "12:00")
    (lunch,) = _only(_act(core, "camps", "lunch", {}, DEV), "action.accepted")
    assert lunch["duration_ticks"] == TICKS_PER_HOUR  # até as 13h
    _act(core, "camps", "move", {"target": {"x": 5, "y": 7}}, DEV)
    early = _act(core, "camps", "deliver", {}, DEV)
    assert _only(early, "action.rejected")[0]["reason"] == "not_done"
    (rest,) = _only(_act(core, "camps", "work", {}, DEV), "action.accepted")
    assert rest["duration_ticks"] == (900 - worked) * TICKS_PER_SECOND  # só o que faltava
    (delivered,) = _only(_act(core, "camps", "deliver", {}, DEV), "office.ticket.delivered")
    assert delivered["worked_seconds"] == 900


def test_as_pausas_da_rotina_ao_lado_de_cada_coisa() -> None:
    """ADR-0080: ilustrativas, de qualquer um, ao lado da coisa; o almoço só na hora dele."""
    core = _core()
    _until(core, "09:00")
    far = _act(core, "camps", "coffee", {}, DEV)
    assert _only(far, "action.rejected")[0]["reason"] == "not_adjacent"
    for thing, action, seconds in (
        ("bebedouro", "drink", 30),
        ("balcao-copa", "coffee", 120),
        ("porta-banheiro", "restroom", 240),
    ):
        _act(core, "camps", "move", {"near": thing}, DEV)
        facts = _act(core, "camps", action, {}, DEV)
        (accepted,) = _only(facts, "action.accepted")
        assert accepted["duration_ticks"] == seconds * TICKS_PER_SECOND
        assert _only(facts, "action.completed")
    _act(core, "camps", "move", {"near": "mesa-copa"}, DEV)
    early = _act(core, "camps", "lunch", {}, DEV)
    assert _only(early, "action.rejected")[0]["reason"] == "invalid_params"  # fora da hora


def test_o_trabalho_em_blocos_soma_cada_bloco() -> None:
    core = _core()
    _until(core, "09:00")
    _manager_in(core)
    _write(core, size="P")
    _act(core, "camps", "move", {"near": "quadro"}, DEV)
    _act(core, "camps", "take_ticket", {}, DEV)
    _act(core, "camps", "move", {"target": {"x": 5, "y": 7}}, DEV)
    for done in (60, 120, 180):
        _act(core, "camps", "work", {"seconds": 60}, DEV)
        assert core.world.entity_map["pedido-001"].attributes["trabalho"] == done


def test_o_gerente_aceita_ou_devolve_com_o_comentario() -> None:
    core = _core()
    _until(core, "09:00")
    _manager_in(core)
    _write(core, size="P")
    _act(core, "camps", "move", {"near": "quadro"}, DEV)
    _act(core, "camps", "take_ticket", {}, DEV)
    _act(core, "camps", "move", {"target": {"x": 5, "y": 7}}, DEV)
    _act(core, "camps", "work", {}, DEV)
    _act(core, "camps", "deliver", {}, DEV)
    empty = _act(
        core, "gerente", "return_ticket", {"target": "pedido-001", "comment": " "}, HUMAN["id"]
    )
    assert _only(empty, "action.rejected")[0]["reason"] == "invalid_params"
    comment = "Falta achar sem diferenciar maiúsculas."
    returned = _act(
        core, "gerente", "return_ticket", {"target": "pedido-001", "comment": comment}, HUMAN["id"]
    )
    assert _only(returned, "office.ticket.returned")[0]["comment"] == comment
    attributes = core.world.entity_map["pedido-001"].attributes
    assert (attributes["estado"], attributes["dono"], attributes["trabalho"]) == (
        "a_fazer",
        None,
        0,
    )
    again = _act(core, "gerente", "accept_ticket", {"target": "pedido-001"}, HUMAN["id"])
    assert _only(again, "action.rejected")[0]["reason"] == "wrong_state"


def test_um_mundo_que_comeca_fora_de_uma_troca_de_fase_ja_sabe_a_fase() -> None:
    core = _core(datetime(2026, 11, 16, 8, 59, tzinfo=SAO_PAULO))
    phases = _only(core.drain(), "world.clock.phase_changed")
    assert phases == [{"phase": "manha", "day": 1}]


def test_a_sessao_do_escritorio_vai_na_v2_com_o_tick_de_250_ms() -> None:
    """ADR-0081: o tick menor que um segundo vai em milissegundos, no `session.started.v2`, com o
    passo de tela para o teclado da tela; a 1x, o avatar anda um tile por tick."""
    core = KernelCore(
        build_world("office_campsverso"), WorldConfig("office-teste", 1, MONDAY), (), "test"
    )
    core.start()
    (session,) = _only(core.drain(), "world.session.started.v2")
    assert (session["tick_ms"], session["screen_tiles_per_second"]) == (250, 4)
    assert "tick_seconds" not in session
    assert core.scale == 1
    assert core.tiles_per_tick() == 1.0
