"""O escritório no kernel (M23, ADR-0078): o expediente, o pedido no quadro e quem pode o quê."""

import json
import re
from collections.abc import Sequence
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest
import yaml

from campsverso_cartridge_api import Position
from campsverso_kernel.core import KernelCore, WorldConfig
from campsverso_kernel.facts import Fact
from campsverso_kernel.loader import build_world
from campsverso_office_campsverso_sim.cartridge import robots

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
    assert not core.world.avatar_map["tiago"].present
    facts = _until(core, "09:00")
    assert _only(facts, "avatar.entered") == [
        {"avatar_id": "tiago", "position": {"x": 9, "y": 15}, "reason": "expediente"}
    ]
    assert _only(facts, "avatar.left")[0]["avatar_id"] == "vigia"
    assert not _only(_until(core, "12:00"), "avatar.left")  # o almoço é na copa (ADR-0080)
    assert core.world.avatar_map["tiago"].present
    assert not core.world.avatar_map["vigia"].present  # o vigia não vem no almoço
    facts = _until(core, "18:00")
    assert _only(facts, "avatar.left")[0] == {
        "avatar_id": "tiago",
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
    assert not core.world.avatar_map["tiago"].present
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
    # Sem escolha na prancheta, o pedido é o de antes do M26: o padrão do mundo programa.
    assert "maos" not in ticket.attributes
    assert "modelo" not in ticket.attributes


def test_a_prancheta_escolhe_quem_programa_e_o_modelo() -> None:
    """ADR-0089: as mãos e o modelo do pedido, entre os que o cartucho oferece."""
    core = _core()
    _until(core, "09:00")
    _manager_in(core)
    _act(core, "gerente", "move", {"near": "quadro"}, HUMAN["id"])
    chosen = {"title": "Conector do Codex", "harness": "claude_code", "model": "claude-opus-5-5"}
    facts = _act(core, "gerente", "write_ticket", chosen, HUMAN["id"])
    (created,) = _only(facts, "office.ticket.created")
    assert (created["harness"], created["model"]) == ("claude_code", "claude-opus-5-5")
    attributes = core.world.entity_map["pedido-001"].attributes
    assert (attributes["maos"], attributes["modelo"]) == ("claude_code", "claude-opus-5-5")
    # Vazio é o padrão do mundo; o que o cartucho não oferece, o kernel recusa.
    empty = _act(core, "gerente", "write_ticket", {"title": "x", "harness": ""}, HUMAN["id"])
    assert "harness" not in _only(empty, "office.ticket.created")[0]
    for wrong in ({"harness": "codex"}, {"model": "gpt-qualquer"}, {"harness": 3}):
        refused = _act(core, "gerente", "write_ticket", {"title": "x", **wrong}, HUMAN["id"])
        assert _only(refused, "action.rejected")[0]["reason"] == "invalid_params"


def test_a_tela_mostra_as_escolhas_que_o_cartucho_oferece() -> None:
    """As escolhas da prancheta no locale do gênero são as do office.yaml, na mesma ordem."""
    office = Path(__file__).parents[3] / "office"
    config = yaml.safe_load(
        (office / "sim/src/campsverso_office_sim/data/office.yaml").read_text(encoding="utf-8")
    )
    locale = json.loads((office / "locale/pt-BR.json").read_text(encoding="utf-8"))
    assert list(locale["choices"]["hands"]) == config["ticket"]["hands"]
    assert list(locale["choices"]["models"]) == config["ticket"]["models"]


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
    _act(core, "tiago", "move", {"near": "quadro"}, DEV)
    wrote = _act(core, "tiago", "write_ticket", {"title": "x"}, DEV)
    assert _only(wrote, "action.rejected")[0]["reason"] == "not_allowed"


def test_nenhum_humano_assume_o_dev() -> None:
    core = _core()
    core.submit(
        {
            "id": "cmd-dev",
            "type": "campsverso.cmd.avatar.possess.v1",
            "actor": "human/operator",
            "data": {"avatar_id": "tiago", "controller": HUMAN},
        }
    )
    assert _only(core.drain(), "world.command.rejected")[0]["reason"] == "controller_not_allowed"


def test_pegar_trabalhar_parar_para_o_almoco_na_copa_e_entregar() -> None:
    core = _core()
    _until(core, "11:40")
    _manager_in(core)
    _write(core, size="P")  # 15 minutos de trabalho
    _act(core, "tiago", "move", {"near": "quadro"}, DEV)
    (taken,) = _only(_act(core, "tiago", "take_ticket", {}, DEV), "office.ticket.taken")
    assert taken["number"] == 1
    _act(core, "tiago", "move", {"target": {"x": 4, "y": 5}}, DEV)  # a cadeira, junto da mesa
    core.submit(
        {
            "id": "cmd-work",
            "type": "campsverso.cmd.action.propose.v1",
            "controllerid": DEV,
            "data": {"avatar_id": "tiago", "action": "work", "params": {}},
        }
    )
    for _ in range(5 * 60 * TICKS_PER_SECOND):  # cinco minutos de trabalho
        core.step()
    _act(core, "tiago", "move", {"near": "mesa-copa-1"}, DEV)  # para: o trabalho fica guardado
    worked = core.world.entity_map["pedido-001"].attributes["trabalho"]
    assert isinstance(worked, int)
    assert 0 < worked < 900
    _until(core, "12:00")
    (lunch,) = _only(_act(core, "tiago", "lunch", {}, DEV), "action.accepted")
    assert lunch["duration_ticks"] == TICKS_PER_HOUR - 5 * 60 * TICKS_PER_SECOND  # até 12:55
    _act(core, "tiago", "move", {"target": {"x": 4, "y": 5}}, DEV)
    early = _act(core, "tiago", "deliver", {}, DEV)
    assert _only(early, "action.rejected")[0]["reason"] == "not_done"
    (rest,) = _only(_act(core, "tiago", "work", {}, DEV), "action.accepted")
    assert rest["duration_ticks"] == (900 - worked) * TICKS_PER_SECOND  # só o que faltava
    (delivered,) = _only(_act(core, "tiago", "deliver", {}, DEV), "office.ticket.delivered")
    assert delivered["worked_seconds"] == 900


def test_as_pausas_da_rotina_ao_lado_de_cada_coisa() -> None:
    """ADR-0080: ilustrativas, de qualquer um, ao lado da coisa; o almoço só na hora dele."""
    core = _core()
    _until(core, "09:00")
    far = _act(core, "tiago", "coffee", {}, DEV)
    assert _only(far, "action.rejected")[0]["reason"] == "not_adjacent"
    for thing, action, seconds in (
        ("bebedouro", "drink", 30),
        ("maquina-cafe", "coffee", 120),
        ("geladeira", "fridge", 15),
        ("micro-ondas", "microwave", 90),
        ("lixeira", "trash", 5),
        ("porta-banheiro", "restroom", 240),
    ):
        _act(core, "tiago", "move", {"near": thing}, DEV)
        facts = _act(core, "tiago", action, {}, DEV)
        (accepted,) = _only(facts, "action.accepted")
        assert accepted["duration_ticks"] == seconds * TICKS_PER_SECOND
        assert _only(facts, "action.completed")
    _act(core, "tiago", "move", {"near": "mesa-copa-1"}, DEV)
    early = _act(core, "tiago", "lunch", {}, DEV)
    assert _only(early, "action.rejected")[0]["reason"] == "invalid_params"  # fora da hora


def test_o_banheiro_fica_fora_da_sala() -> None:
    """ADR-0082: as portas do banheiro dão para o corredor. Da mesa, o dev sai pela porta da sala,
    vai pelo corredor até a porta do banheiro e volta pelo mesmo caminho."""
    core = _core()
    _until(core, "09:00")
    _act(core, "tiago", "move", {"target": {"x": 4, "y": 5}}, DEV)
    facts = _act(core, "tiago", "move", {"near": "porta-banheiro"}, DEV)
    (moved,) = _only(facts, "world.entity.moved")
    corners = [(p["x"], p["y"]) for p in moved["waypoints"]]
    assert (9, 13) in corners or any(y >= 14 for _, y in corners)  # pela porta, pelo corredor
    here = core.world.position_of("tiago")
    assert here is not None
    assert here.y == 14  # no corredor, diante da porta do banheiro
    assert _only(_act(core, "tiago", "restroom", {}, DEV), "action.completed")


def test_o_trabalho_em_blocos_soma_cada_bloco() -> None:
    core = _core()
    _until(core, "09:00")
    _manager_in(core)
    _write(core, size="P")
    _act(core, "tiago", "move", {"near": "quadro"}, DEV)
    _act(core, "tiago", "take_ticket", {}, DEV)
    _act(core, "tiago", "move", {"target": {"x": 4, "y": 5}}, DEV)
    for done in (60, 120, 180):
        _act(core, "tiago", "work", {"seconds": 60}, DEV)
        assert core.world.entity_map["pedido-001"].attributes["trabalho"] == done


def test_o_gerente_aceita_ou_devolve_com_o_comentario() -> None:
    core = _core()
    _until(core, "09:00")
    _manager_in(core)
    _write(core, size="P")
    _act(core, "tiago", "move", {"near": "quadro"}, DEV)
    _act(core, "tiago", "take_ticket", {}, DEV)
    _act(core, "tiago", "move", {"target": {"x": 4, "y": 5}}, DEV)
    _act(core, "tiago", "work", {}, DEV)
    _act(core, "tiago", "deliver", {}, DEV)
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
    rejected = _only(again, "action.rejected")[0]
    assert (rejected["reason"], rejected["detail"]) == (
        "wrong_state",
        "o pedido 1 ainda não foi entregue",
    )


def test_aceitar_de_novo_diz_que_ja_foi_aceito() -> None:
    """Dois cliques em aceitar saíam juntos da fila da tela, e o segundo dizia "não foi entregue"
    (achado do usuário em 18/nov)."""
    core = _core()
    _until(core, "09:00")
    _manager_in(core)
    _write(core, size="P")
    _act(core, "tiago", "move", {"near": "quadro"}, DEV)
    _act(core, "tiago", "take_ticket", {}, DEV)
    _act(core, "tiago", "move", {"target": {"x": 4, "y": 5}}, DEV)
    _act(core, "tiago", "work", {}, DEV)
    _act(core, "tiago", "deliver", {}, DEV)
    accepted = _act(core, "gerente", "accept_ticket", {"target": "pedido-001"}, HUMAN["id"])
    assert _only(accepted, "office.ticket.accepted")
    again = _act(core, "gerente", "accept_ticket", {"target": "pedido-001"}, HUMAN["id"])
    rejected = _only(again, "action.rejected")[0]
    assert (rejected["reason"], rejected["detail"]) == ("wrong_state", "o pedido 1 já foi aceito")


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


def test_a_entrega_com_o_patch_da_oficina() -> None:
    """ADR-0080: a entrega leva o resumo do patch; o pedido guarda a referência, para o quadro."""
    core = _core()
    _until(core, "09:00")
    _manager_in(core)
    _write(core, size="P")
    _act(core, "tiago", "move", {"near": "quadro"}, DEV)
    _act(core, "tiago", "take_ticket", {}, DEV)
    _act(core, "tiago", "move", {"target": {"x": 4, "y": 5}}, DEV)
    _act(core, "tiago", "work", {}, DEV)
    patch = {
        "ref": "office-teste/pedido-001/x.patch",
        "base": "a" * 40,
        "files": ["docs/oficina/pedido-001.md"],
        "added": 7,
        "removed": 0,
    }
    facts = _act(core, "tiago", "deliver", {"patch": patch}, DEV)
    (delivered,) = _only(facts, "office.ticket.delivered")
    assert delivered["patch"] == patch
    assert core.world.entity_map["pedido-001"].attributes["patch"] == patch["ref"]


def test_o_sofa_a_marmita_e_o_menu_de_pausas() -> None:
    """ADR-0082: a TV e o videogame no sofá, do tapete logo acima ou abaixo dele; a marmita na mão
    entre a geladeira e o lixo; e o menu das pausas para quem está no escritório."""
    core = KernelCore(
        build_world("office_campsverso"), WorldConfig("office-teste", 1, MONDAY), (), "test"
    )
    core.start()
    (session,) = _only(core.drain(), "world.session.started.v2")
    menu = {a["action"]: a["on"] for a in session["affordances"]}
    assert menu["videogame"] == ["sofa", "tv"]
    assert set(menu) >= {"drink", "coffee", "fridge", "microwave", "lunch", "trash", "restroom"}
    _until(core, "09:00")
    _act(core, "tiago", "move", {"target": {"x": 12, "y": 6}}, DEV)
    far = _act(core, "tiago", "videogame", {}, DEV)
    assert _only(far, "action.rejected")[0]["reason"] == "not_adjacent"
    _act(core, "tiago", "move", {"target": {"x": 16, "y": 6}}, DEV)
    (played,) = _only(_act(core, "tiago", "videogame", {}, DEV), "action.accepted")
    assert played["duration_ticks"] == 15 * 60 * TICKS_PER_SECOND
    _act(core, "tiago", "move", {"near": "geladeira"}, DEV)
    _act(core, "tiago", "fridge", {}, DEV)
    assert core.world.entity_map["tiago"].attributes["carregando"] == "marmita"
    _act(core, "tiago", "move", {"near": "lixeira"}, DEV)
    _act(core, "tiago", "trash", {}, DEV)
    assert core.world.entity_map["tiago"].attributes.get("carregando") is None


# ------------------------------------------------------------------ a bancada (o plano do M24, §4)


def test_a_bancada_fica_no_cubiculo_ao_lado_do_dev_com_o_testador() -> None:
    core = _core()
    bench = core.world.entity_map["bancada"]
    assert (bench.kind, core.world.position_of("bancada")) == ("bench", Position(8, 4))
    assert "cadeira-2" not in core.world.entity_map  # a cadeira do cubículo saiu
    # O primeiro robô, a criação do dev no pedido 1 (18/nov), no primeiro apoio.
    on_bench = [e for e in core.world.entity_map.values() if e.kind == "robot"]
    # O briefing veio depois, no segundo apoio.
    assert {e.entity_id: core.world.position_of(e.entity_id) for e in on_bench} == {
        "robo-testador": Position(7, 4),
        "robo-briefing": Position(8, 4),
    }


def test_os_robos_do_registro_vao_para_os_apoios_da_bancada() -> None:
    entries = [
        {"nome": "testador", "modulo": "tools.robos.testador", "descricao": "Roda os testes."},
        {"nome": "revisor", "modulo": "tools.robos.revisor", "descricao": "Lê o patch."},
    ]
    spawned = robots(entries, Position(8, 4))
    assert [(r.entity_id, r.position) for r in spawned] == [
        ("robo-testador", Position(7, 4)),
        ("robo-revisor", Position(8, 4)),
    ]
    assert spawned[0].attributes == {
        "nome": "testador",
        "modulo": "tools.robos.testador",
        "descricao": "Roda os testes.",
    }
    assert not spawned[0].blocking
    for bad in (
        [{"nome": "Testador", "modulo": "tools.x"}],  # maiúscula
        [{"nome": "t", "modulo": "tools.x; rm -rf /"}],  # não é um módulo
        [{"nome": "t", "modulo": "a"}, {"nome": "t", "modulo": "b"}],  # repetido
        [{"nome": f"r{i}", "modulo": "a"} for i in range(4)],  # a bancada tem três apoios
        [{"nome": "t", "modulo": "a", "reserva": "tools/robos/tests"}],  # não é uma lista
        [{"nome": "t", "modulo": "a", "reserva": ["com espaco ruim"]}],  # um caminho com espaço
        [{"nome": "t", "modulo": "a", "reserva": [f"p{i}" for i in range(9)]}],  # até oito
    ):
        with pytest.raises(ValueError, match="robos"):
            robots(bad, Position(8, 4))


def test_a_reserva_do_registro_vai_no_robo_para_o_dev_script() -> None:
    """Os argumentos com que o script de reserva chama o robô: num atributo só, separados por
    espaço (os atributos de uma entidade são escalares)."""
    entry = {"nome": "testador", "modulo": "tools.robos.testador", "reserva": ["a/tests", "b"]}
    assert robots([entry], Position(8, 4))[0].attributes["reserva"] == "a/tests b"
    core = _core()
    assert core.world.entity_map["robo-testador"].attributes["reserva"] == "tools/robos/tests"
