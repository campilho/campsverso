"""O PR do dev no mundo (ADR-0083, ADR-0084): o vigia do GitHub relata cada mudança num PR, e o
cartucho do escritório confere e muda o pedido. O aceite é mesclar."""

import re
from collections.abc import Sequence
from datetime import datetime, timedelta, timezone
from typing import Any

from campsverso_kernel.core import KernelCore, WorldConfig
from campsverso_kernel.facts import Fact
from campsverso_kernel.loader import build_world

SAO_PAULO = timezone(timedelta(hours=-3))
MONDAY = datetime(2026, 11, 16, tzinfo=SAO_PAULO)
HUMAN = {"type": "human", "id": "human/camps-browser"}
DEV = "script/dev"
REPORT = "campsverso.cmd.office.pull_request.report.v1"
URL = "https://github.com/campilho/campsverso/pull/12"
HEAD = "7c6b8ac0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6"


def _only(facts: Sequence[Fact], event: str) -> list[dict[str, Any]]:
    wanted = f"campsverso.{event}" if re.search(r"\.v\d+$", event) else f"campsverso.{event}.v1"
    return [dict(f.data) for f in facts if f.type == wanted]


def _act(core: KernelCore, avatar: str, action: str, params: dict[str, Any], who: str) -> None:
    core.submit(
        {
            "id": f"cmd-{avatar}-{action}-{core.tick}",
            "type": "campsverso.cmd.action.propose.v1",
            "controllerid": who,
            "data": {"avatar_id": avatar, "action": action, "params": params},
        }
    )
    for _ in range(4 * 3600 * 4):
        core.step()
        if core.world.avatar_map[avatar].action is None:
            break


def _delivered() -> KernelCore:
    """Um pedido escrito pelo gerente e entregue pelo dev-script, às 9 da segunda."""
    core = KernelCore(
        build_world("office_campsverso"), WorldConfig("office-teste", 1, MONDAY), (), "test"
    )
    core.start()
    core.advance(core.world.ticks_until("09:00") + 1, jump=True)
    core.submit(
        {
            "id": "cmd-assumir",
            "type": "campsverso.cmd.avatar.possess.v1",
            "actor": "human/operator",
            "data": {"avatar_id": "gerente", "controller": HUMAN},
        }
    )
    _act(core, "gerente", "move", {"near": "quadro"}, HUMAN["id"])
    ticket = {"title": "Briefing", "description": "Montar.", "acceptance": "Passa.", "size": "P"}
    _act(core, "gerente", "write_ticket", ticket, HUMAN["id"])
    _act(core, "tiago", "move", {"near": "quadro"}, DEV)
    _act(core, "tiago", "take_ticket", {}, DEV)
    _act(core, "tiago", "move", {"target": {"x": 4, "y": 5}}, DEV)
    _act(core, "tiago", "work", {}, DEV)
    _act(core, "tiago", "deliver", {}, DEV)
    core.drain()
    return core


def _report(core: KernelCore, state: str, n: int = 12, **extra: Any) -> list[Fact]:
    core.submit(
        {
            "id": f"cmd-pr-{state}-{core.tick}-{len(extra)}",
            "type": REPORT,
            "data": {"ticket_id": "pedido-001", "pull_request": n, "state": state, **extra},
        }
    )
    return core.drain()


def _opened(core: KernelCore) -> list[Fact]:
    return _report(core, "opened", url=URL, branch="dev/pedido-1", head=HEAD)


def test_o_pr_aberto_fica_no_pedido_e_o_aceite_no_quadro_vira_mesclar() -> None:
    core = _delivered()
    facts = _opened(core)
    (opened,) = _only(facts, "office.ticket.pr_opened")
    assert opened == {
        "ticket_id": "pedido-001",
        "number": 1,
        "pull_request": 12,
        "url": URL,
        "branch": "dev/pedido-1",
        "head": HEAD,
    }
    attributes = core.world.entity_map["pedido-001"].attributes
    pr = (attributes["pr"], attributes["pr_estado"], attributes["pr_ci"])
    assert pr == (12, "aberto", "pending")
    # O gerente não aceita no quadro um pedido com PR aberto: o aceite é mesclar.
    _act(core, "gerente", "move", {"near": "quadro"}, HUMAN["id"])
    core.drain()
    _act(core, "gerente", "accept_ticket", {"target": "pedido-001"}, HUMAN["id"])
    (rejected,) = _only(core.drain(), "action.rejected")
    assert (rejected["reason"], rejected["detail"]) == (
        "pr_open",
        "o pedido 1 se aceita mesclando o PR #12",
    )


def test_o_ci_e_o_merge_aceitam_o_pedido() -> None:
    core = _delivered()
    _opened(core)
    (updated,) = _only(_report(core, "updated", ci="success"), "office.ticket.pr_updated")
    assert updated == {"ticket_id": "pedido-001", "number": 1, "pull_request": 12, "ci": "success"}
    assert core.world.entity_map["pedido-001"].attributes["pr_ci"] == "success"
    facts = _report(core, "merged")
    assert _only(facts, "office.ticket.pr_merged") == [
        {"ticket_id": "pedido-001", "number": 1, "pull_request": 12}
    ]
    # O aceite sai como se o gerente aceitasse: a memória e o quadro leem o mesmo fato.
    assert _only(facts, "office.ticket.accepted") == [
        {"ticket_id": "pedido-001", "number": 1, "by": "gerente"}
    ]
    attributes = core.world.entity_map["pedido-001"].attributes
    assert (attributes["estado"], attributes["pr_estado"]) == ("aceito", "mesclado")
    # Mesclado não volta a mudar.
    (rejected,) = _only(_report(core, "updated", ci="failure"), "world.command.rejected")
    assert rejected["reason"] == "pr_not_open"


def test_fechar_sem_mesclar_devolve_o_pedido() -> None:
    core = _delivered()
    _opened(core)
    facts = _report(core, "closed")
    assert _only(facts, "office.ticket.pr_closed")
    (returned,) = _only(facts, "office.ticket.returned.v2")
    assert returned["comment"] == "O PR #12 foi fechado sem mesclar."
    attributes = core.world.entity_map["pedido-001"].attributes
    assert (attributes["estado"], attributes["dono"], attributes["pr_estado"]) == (
        "a_fazer",
        None,
        "fechado",
    )


def test_o_kernel_recusa_o_relato_que_nao_confere() -> None:
    core = _delivered()
    rejected = _only(_report(core, "merged"), "world.command.rejected")
    assert rejected[0]["reason"] == "other_pr"  # nenhum PR aberto ainda
    _opened(core)
    again = _only(_opened(core), "world.command.rejected")
    assert again[0]["reason"] == "pr_exists"
    other = _only(_report(core, "updated", n=99, ci="success"), "world.command.rejected")
    assert other[0]["reason"] == "other_pr"
    empty = _only(_report(core, "updated"), "world.command.rejected")
    assert empty[0]["reason"] == "nothing_changed"
    assert core.world.entity_map["pedido-001"].attributes["estado"] == "entregue"


def test_o_relato_fica_no_diario_e_o_mesmo_comando_da_o_mesmo_fato() -> None:
    """O comando é aplicado na hora, com o comando como causa: o replay o refaz do diário."""
    first, second = _delivered(), _delivered()
    assert [(f.type, dict(f.data)) for f in _opened(first)] == [
        (f.type, dict(f.data)) for f in _opened(second)
    ]
