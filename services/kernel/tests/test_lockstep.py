"""M3 no kernel: move {near}, a espera do lockstep e o at_tick do replay (ADR-0047)."""

import re
from collections.abc import Sequence
from typing import Any

from campsverso_kernel.core import KernelCore
from campsverso_kernel.facts import Fact
from campsverso_kernel.snapshot import decode, document, encode, restore
from campsverso_kernel.testing import SCRIPT, command, control, make_core

REPLAY = {"type": "replay", "id": "replay/teste"}


def _only(facts: Sequence[Fact], event: str) -> list[dict[str, Any]]:
    wanted = f"campsverso.{event}" if re.search(r"\.v\d+$", event) else f"campsverso.{event}.v1"
    return [dict(f.data) for f in facts if f.type == wanted]


def _run(core: KernelCore, ticks: int = 1) -> list[Fact]:
    for _ in range(ticks):
        core.step()
    return core.drain()


def _started(mode: str = "continuous") -> KernelCore:
    core = make_core()
    core.configure_clock("max" if mode == "max" else "continuous", None, False)
    core.start()
    core.drain()
    return core


def _propose(
    action: str, params: dict[str, Any], *, controller: str, at_tick: int | None = None, n: int = 1
) -> dict[str, Any]:
    data: dict[str, Any] = {"avatar_id": "ana", "action": action, "params": params}
    if at_tick is not None:
        data["at_tick"] = at_tick
    return {
        "id": f"cmd-{action}-{n}",
        "type": "campsverso.cmd.action.propose.v1",
        "controllerid": controller,
        "data": data,
    }


# ----------------------------------------------------------------- move {near}


def test_move_near_escolhe_o_tile_livre_mais_perto_da_entidade() -> None:
    core = _started()
    core.submit(command("move", {"near": "box"}))
    facts = _run(core)
    (moved,) = _only(facts, "world.entity.moved")
    assert moved["waypoints"] == [{"x": 3, "y": 1}]  # (4,2) e (5,2) ficam do outro lado da caixa
    _run(core, 3)
    core.submit(command("touch"))
    assert _only(_run(core, 3), "action.completed")[0]["action"] == "touch"


def test_move_near_recusas() -> None:
    core = _started()
    for params, reason in (
        ({"near": "fantasma"}, "invalid_params"),
        ({"near": "box", "target": {"x": 3, "y": 1}}, "invalid_params"),
        ({}, "invalid_params"),
    ):
        core.submit(command("move", params))
        assert _only(_run(core), "action.rejected")[0]["reason"] == reason
    core.submit(command("move", {"near": "box"}))
    _run(core, 4)
    core.submit(command("move", {"near": "box"}))
    assert _only(_run(core), "action.rejected")[0]["reason"] == "already_there"


# ----------------------------------------------------------------- lockstep


def test_modo_maximo_espera_o_script_responder() -> None:
    core = _started("max")
    assert not core.lockstep_blocked
    _run(core)  # tick 0: pedido de decisão (session_started)
    assert core.lockstep_blocked
    core.submit(_propose("wait", {"ticks": 3}, controller=SCRIPT.id))
    assert not core.lockstep_blocked  # a proposta chegou: o relógio pode andar
    _run(core, 3)
    assert not core.lockstep_blocked  # ainda esperando o wait terminar
    _run(core)
    assert core.lockstep_blocked  # wait concluído: novo pedido de decisão


def test_proposta_de_quem_nao_tem_a_posse_nao_destrava() -> None:
    core = _started("max")
    _run(core)
    core.submit(_propose("wait", {"ticks": 1}, controller="script/outro"))
    assert core.lockstep_blocked


def test_no_modo_continuo_ninguem_espera() -> None:
    core = _started()
    _run(core)
    assert core.world.avatar_map["ana"].awaiting
    assert not core.lockstep_blocked


# ----------------------------------------------------------------- at_tick do replay


def _replaying() -> KernelCore:
    core = _started("max")
    core.submit(control("avatar.possess", {"avatar_id": "ana", "controller": REPLAY}))
    core.drain()
    return core


def test_replay_agenda_a_proposta_para_o_tick_pedido() -> None:
    core = _replaying()
    core.submit(_propose("wait", {"ticks": 2}, controller=REPLAY["id"], at_tick=5))
    facts = _run(core, 5)  # ticks 0 a 4: nada acontece com a ana, e o relógio não espera
    assert _only(facts, "action.accepted") == []
    assert not core.lockstep_blocked
    (accepted,) = _only(_run(core), "action.accepted")
    assert accepted["applied_tick"] == 5


def test_at_tick_so_do_replay_e_nunca_no_passado() -> None:
    core = _started("max")
    _run(core, 3)
    core.submit(_propose("wait", {"ticks": 1}, controller=SCRIPT.id, at_tick=3))
    assert _only(_run(core), "action.rejected")[0]["reason"] == "unsupported"
    replay = _replaying()
    _run(replay, 3)
    replay.submit(_propose("wait", {"ticks": 1}, controller=REPLAY["id"], at_tick=1))
    assert _only(_run(replay), "action.rejected")[0]["reason"] == "too_late"


def test_snapshot_guarda_agendados_e_espera() -> None:
    core = _replaying()
    core.submit(_propose("wait", {"ticks": 2}, controller=REPLAY["id"], at_tick=40))
    _run(core, 10)
    data = encode(document(core, {"code": "teste"}, core.log.next_seq))
    copy = restore(core.definition, core.config, decode(data))
    assert copy.export_state() == core.export_state()
    assert _only(_run(copy, 31), "action.accepted")[0]["applied_tick"] == 40
