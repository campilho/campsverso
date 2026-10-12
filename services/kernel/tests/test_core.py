import re
from collections.abc import Sequence
from typing import Any

import pytest

from campsverso_cartridge_api import Position
from campsverso_kernel.core import KernelCore
from campsverso_kernel.facts import Fact
from campsverso_kernel.testing import RULES, command, control, make_core


def _types(facts: Sequence[Fact]) -> list[str]:
    return [f.type.removeprefix("campsverso.") for f in facts]


def _only(facts: Sequence[Fact], event: str) -> list[dict[str, Any]]:
    wanted = f"campsverso.{event}" if re.search(r"\.v\d+$", event) else f"campsverso.{event}.v1"
    return [dict(f.data) for f in facts if f.type == wanted]


def _run(core: KernelCore, ticks: int = 1) -> list[Fact]:
    core.drain()
    for _ in range(ticks):
        core.step()
    return core.drain()


def test_inicio_da_sessao_publica_mundo_regras_entidades_e_pede_decisao() -> None:
    core = make_core()
    core.start()
    started = _types(core.drain())
    assert started[:2] == ["world.session.started.v1", "rules.loaded.v1"]
    assert started.count("world.entity.spawned.v1") == 2
    assert "avatar.possessed.v1" in started
    assert "world.weather.changed.v1" in started
    first_tick = core.drain() or _run(core)
    (decision,) = _only(first_tick, "avatar.decision_requested")
    assert decision["reason"] == "session_started"
    assert decision["needs"] == {"energia": 25.0, "fome": 79.05}


def test_mover_aceita_publica_trajeto_e_conclui_no_tempo(core: KernelCore) -> None:
    _run(core)
    core.submit(command("move", {"target": {"x": 3, "y": 1}}))
    facts = _run(core)
    (accepted,) = _only(facts, "action.accepted")
    (moved,) = _only(facts, "world.entity.moved")
    assert accepted["duration_ticks"] == 2
    assert accepted["interrupt"] == "cancel"  # andar se cancela (ADR-0052)
    assert moved["waypoints"] == [{"x": 3, "y": 1}]
    assert moved["arrival_tick"] == moved["depart_tick"] + 2
    later = _run(core, 2)
    assert _only(later, "action.completed")[0]["action"] == "move"
    assert core.world.position_of("ana") == Position(3, 1)
    assert _only(later, "avatar.decision_requested")[0]["reason"] == "action_completed"


@pytest.mark.parametrize(
    ("target", "reason"),
    [
        ({"x": 1, "y": 1}, "already_there"),
        ({"x": 2, "y": 2}, "not_passable"),
        ({"x": 5, "y": 2}, "unreachable"),
        ({"x": "a", "y": 1}, "invalid_params"),
    ],
)
def test_mover_recusa_com_motivo_legivel(
    core: KernelCore, target: dict[str, Any], reason: str
) -> None:
    core.submit(command("move", {"target": target}))
    (rejected,) = _only(_run(core), "action.rejected")
    assert rejected["reason"] == reason


def test_comando_de_quem_nao_tem_a_posse_e_recusado(core: KernelCore) -> None:
    core.submit(command("wait", {"ticks": 5}, controller="human/intruso"))
    (rejected,) = _only(_run(core), "action.rejected")
    assert rejected["reason"] == "not_in_control"


def test_acao_desconhecida_e_recusada(core: KernelCore) -> None:
    core.submit(command("fly"))
    assert _only(_run(core), "action.rejected")[0]["reason"] == "unknown_action"


def test_nova_proposta_cancela_o_movimento_na_posicao_real(core: KernelCore) -> None:
    _run(core)
    core.submit(command("move", {"target": {"x": 3, "y": 1}}))
    _run(core)
    core.submit(command("wait", {"ticks": 3}))
    facts = _run(core)
    (interrupted,) = _only(facts, "world.entity.move_interrupted")
    (failed,) = _only(facts, "action.failed")
    (accepted,) = _only(facts, "action.accepted")
    assert interrupted["position"] == {"x": 2, "y": 1}
    assert failed["reason"] == "cancelled"
    assert accepted["replaces"] == failed["action_id"]


def test_proposta_recusada_nao_cancela_a_acao_em_andamento(core: KernelCore) -> None:
    core.submit(command("wait", {"ticks": 10}))
    _run(core)
    core.submit(command("touch"))
    facts = _run(core)
    assert _only(facts, "action.rejected")[0]["reason"] == "not_adjacent"
    assert _only(facts, "action.failed") == []
    assert core.world.avatar_map["ana"].action is not None


def _walk_to_box(core: KernelCore) -> None:
    _run(core)
    core.submit(command("move", {"target": {"x": 3, "y": 1}}))
    _run(core, 3)


# ------------------------------------------------------------- política de interrupção (ADR-0052)


def test_acao_never_recusa_comando_novo_com_busy_e_termina(core: KernelCore) -> None:
    _walk_to_box(core)
    core.submit(command("touch"))
    (accepted,) = _only(_run(core), "action.accepted")
    assert accepted["interrupt"] == "never"
    core.submit(command("wait", {"ticks": 3}))
    facts = _run(core, 2)
    (rejected,) = _only(facts, "action.rejected")
    assert rejected["reason"] == "busy"
    assert rejected["detail"] == f"touch termina no tick {accepted['applied_tick'] + 2}"
    assert _only(facts, "action.failed") == []
    assert [c["action"] for c in _only(facts, "action.completed")] == ["touch"]


def test_acao_partial_guarda_o_trabalho_e_continua_mais_curta(core: KernelCore) -> None:
    _walk_to_box(core)
    core.submit(command("dig"))
    (accepted,) = _only(_run(core), "action.accepted")
    assert (accepted["interrupt"], accepted["duration_ticks"]) == ("partial", 8)
    _run(core, 4)
    core.submit(command("wait", {"ticks": 1}))
    facts = _run(core)
    (failed,) = _only(facts, "action.failed")
    (waiting,) = _only(facts, "action.accepted")
    done = failed["elapsed_ticks"] // 2
    assert failed["reason"] == "cancelled"
    assert done >= 2
    assert waiting["replaces"] == failed["action_id"]
    assert core.world.entity_map["box"].attributes["dug"] == done
    _run(core, 2)
    core.submit(command("dig"))
    (again,) = _only(_run(core), "action.accepted")
    assert again["duration_ticks"] == (4 - done) * 2


def test_retomar_a_mesma_acao_partial_desconta_o_que_foi_feito(core: KernelCore) -> None:
    _walk_to_box(core)
    core.submit(command("dig"))
    _run(core, 4)
    core.submit({**command("dig"), "id": "cmd-dig-2"})
    facts = _run(core)
    (failed,) = _only(facts, "action.failed")
    (accepted,) = _only(facts, "action.accepted")
    assert accepted["duration_ticks"] == (4 - failed["elapsed_ticks"] // 2) * 2


def test_desmaio_interrompe_a_acao_partial_e_guarda_o_trabalho(core: KernelCore) -> None:
    _walk_to_box(core)
    core.submit(command("dig"))
    _run(core, 5)
    core.world.faint("ana", "exhausted", 60, {"energia": 50})
    (failed,) = _only(core.drain(), "action.failed")
    assert failed["reason"] == "fainted"
    assert core.world.entity_map["box"].attributes["dug"] == failed["elapsed_ticks"] // 2


def test_acao_do_cartucho_aplica_regra_oculta_e_explica_o_efeito(core: KernelCore) -> None:
    _walk_to_box(core)
    core.submit(command("touch"))
    facts = _run(core, 3)
    (created,) = _only(facts, "world.item.created")
    (effect,) = _only(facts, "rules.effect_applied")
    (explained,) = _only(facts, "action.effects_explained")
    assert created["qty"] == 3  # caixa a 1 tile da água: x3 pela regra oculta
    assert effect == {
        "rule": "lab_water",
        "version": "1.0.0",
        "entity_id": "box",
        "property": "stone_yield",
        "base": 1.0,
        "applied": 3.0,
    }
    assert explained["rules_applied"] == [
        {"rule": "lab_water", "version": "1.0.0", "hidden": True, "multiplier": 3.0}
    ]
    assert _only(facts, "world.entity.state_changed")[0]["changes"] == {"touched": True}


def test_regra_desligada_a_quente_deixa_de_contribuir(core: KernelCore) -> None:
    core.submit(
        control("rules.toggle", {"rule": "lab_water", "enabled": False, "reason": "experimento"})
    )
    toggled = _only(core.drain(), "rules.toggled")
    assert toggled[0]["enabled"] is False
    _walk_to_box(core)
    core.submit(command("touch"))
    facts = _run(core, 3)
    assert _only(facts, "world.item.created")[0]["qty"] == 1
    assert _only(facts, "action.effects_explained") == []


def test_necessidade_cruza_limiar_e_pede_decisao() -> None:
    core = make_core()
    core.start()
    facts = _run(core, 20)  # fome 79 + 3/h: chega a 80 no 20º tick
    (crossed,) = _only(facts, "world.need.threshold_crossed")
    assert crossed == {
        "avatar_id": "ana",
        "need": "fome",
        "threshold": 80,
        "direction": "up",
        "value": 80.0,
    }
    assert [d["reason"] for d in _only(facts, "avatar.decision_requested")][-1] == "need_threshold"


def test_energia_zero_desmaia_e_acorda_com_energia_de_desmaio(core: KernelCore) -> None:
    _walk_to_box(core)
    facts: list[Fact] = []
    for _ in range(3):  # 25 -> 15 -> 5 -> 0
        core.submit(command("touch"))
        facts += _run(core, 3)
    (fainted,) = _only(facts, "avatar.fainted")
    (slept,) = _only(facts, "avatar.sleep.started.v2")
    assert fainted["reason"] == "exhausted"
    assert slept["cause"] == "faint"
    core.submit(command("wait", {"ticks": 1}))
    assert _only(_run(core), "action.rejected")[0]["reason"] == "busy"
    woke = _run(core, 60)
    (ended,) = _only(woke, "avatar.sleep.ended.v2")
    assert ended == {"avatar_id": "ana", "cause": "faint", "energy": 50.0}
    assert _only(woke, "avatar.decision_requested")[-1]["reason"] == "woke_up"


def test_dormir_ate_a_virada_do_dia(core: KernelCore) -> None:
    core.submit(command("nap"))
    facts = _run(core, 2)
    (slept,) = _only(facts, "avatar.sleep.started.v2")
    assert slept["cause"] == "voluntary"
    assert "bed_id" not in slept  # dormiu onde estava (ADR-0041)
    assert slept["wake_at_tick"] == 1440  # 06:00 do dia 2
    assert core.world.rate("ana", "energia") == 24  # 12/h da necessidade: 24 unidades por tick
    core.advance(1440 - core.tick + 1)
    assert core.world.avatar_map["ana"].asleep is False


def test_a_cama_troca_a_taxa_de_recuperacao_so_durante_o_sono(core: KernelCore) -> None:
    _walk_to_box(core)
    core.submit(command("nap", {"bed": "box"}))
    (slept,) = _only(_run(core, 2), "avatar.sleep.started.v2")
    assert slept["bed_id"] == "box"
    assert core.world.rate("ana", "energia") == 48  # 24/h passados pela ação
    core.advance(1440 - core.tick + 1)
    woke = core.drain()
    (ended,) = _only(woke, "avatar.sleep.ended.v2")
    assert ended["bed_id"] == "box"
    assert ended["energy"] == 100.0
    assert core.world.rate("ana", "energia") == 0  # acordada, sem taxa


def test_relogio_pausa_avanca_passo_a_passo_e_retoma(core: KernelCore) -> None:
    core.submit(control("clock.step", {"ticks": 2}))
    assert _only(core.drain(), "world.command.rejected")[0]["reason"] == "not_paused"
    core.submit(control("clock.pause", {"reason": "debug"}))
    core.submit(control("clock.step", {"ticks": 3}))
    core.submit(control("clock.resume", {}))
    facts = core.drain()
    assert _types(facts)[0] == "world.clock.paused.v1"
    assert _only(facts, "world.clock.stepped")[0] == {"ticks": 3, "from_tick": 0, "to_tick": 3}
    assert _types(facts)[-1] == "world.clock.resumed.v1"


def test_posse_modo_maximo_e_devolucao(core: KernelCore) -> None:
    human = {"type": "human", "id": "human/camps-browser"}
    core.submit(control("clock.set_mode", {"mode": "max"}))
    core.submit(control("avatar.possess", {"avatar_id": "ana", "controller": human}))
    facts = core.drain()
    assert _only(facts, "world.clock.mode_changed")[0]["mode"] == "max"
    assert _only(facts, "world.command.rejected")[0]["reason"] == "mode_not_allowed"
    core.submit(control("clock.set_mode", {"mode": "continuous"}))
    core.submit(control("avatar.possess", {"avatar_id": "ana", "controller": human}))
    assert _only(core.drain(), "avatar.possessed")[0]["controller"] == human
    core.submit(command("wait", {"ticks": 1}))
    assert _only(_run(core), "action.rejected")[0]["reason"] == "not_in_control"
    core.submit(control("avatar.release", {"avatar_id": "ana"}))
    released = _only(core.drain(), "avatar.released")
    assert released[0]["controller"] == {"type": "script", "id": "script/lab-v1"}


def _scripted_run(jump: bool) -> list[tuple[int, str, Any]]:
    core = make_core(RULES)
    core.start()
    plan = {
        30: command("move", {"target": {"x": 3, "y": 1}}),
        200: command("touch"),
        900: command("nap"),
    }
    tick = 0
    for at, cmd in sorted(plan.items()):
        core.advance(at - tick, jump=jump)
        core.submit(cmd)
        tick = at
    core.advance(2 * 1440 - tick, jump=jump)
    return [
        (f.tick, f.type, f.data)
        for f in core.drain()
        if f.type != "campsverso.world.clock.jumped.v1"
    ]


def test_salto_de_tempo_produz_os_mesmos_fatos_que_tick_a_tick() -> None:
    assert _scripted_run(jump=True) == _scripted_run(jump=False)


def test_mesma_seed_e_mesmos_comandos_dao_os_mesmos_fatos() -> None:
    first, second = _scripted_run(jump=False), _scripted_run(jump=False)
    assert first == second
    assert len(first) > 50


def test_ordem_efetiva_do_tick_e_visivel() -> None:
    core = make_core()
    assert core.describe_order("08:00") == [
        "scheduled: chime(10)",
        "clock: kernel",
        "needs: kernel",
        "wake: kernel",
        "actions: kernel",
        "commands: kernel",
        "reactions: -",
        "decisions: kernel",
    ]
    assert "clock: kernel, fase:noite" in core.describe_order("20:00")
