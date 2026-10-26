"""Vários avatares (ADR-0072): um avatar declarado fora do mundo, que entra e sai, a ficha que
distingue o corpo dele (a velocidade, o tempo das ações, o ritmo das necessidades, o gasto de
energia, a capacidade, o desmaio e a visão) e a ação que outro avatar desfaz no meio, num
laboratório próprio."""

import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from campsverso_cartridge_api import (
    Accepted,
    ActionContext,
    AvatarDef,
    AvatarTraits,
    CartridgeManifest,
    ClockDef,
    ControllerRef,
    DailyAt,
    ItemDef,
    KindDef,
    NeedDef,
    Position,
    Rejection,
    SpawnDef,
    SystemContext,
    Validation,
    WorldBuilder,
    WorldOps,
)
from campsverso_kernel.core import KernelCore, WorldConfig
from campsverso_kernel.errors import WorldRuleError
from campsverso_kernel.facts import Fact
from campsverso_kernel.loader import build_world
from campsverso_kernel.testing import SCRIPT, START, LabSystem, command, lab_map

HELPER = ControllerRef("script", "script/bia-v1")
BIA = AvatarTraits(
    speed=0.5,
    action_time={"*": 2.0},
    need_rates={"fome": 2.0},
    energy_cost=1.5,
    capacity=14,
    faints=False,
    vision=2.0,
    night_vision=True,
)


@dataclass(frozen=True)
class Work:
    """Trabalha 4 ticks e gasta 10 de energia."""

    name: str = "work"

    def validate(self, ctx: ActionContext) -> Validation:
        return Accepted(4, "cancel")

    def complete(self, ctx: ActionContext, ops: WorldOps) -> None:
        ops.change_need(ctx.avatar_id, "energia", -10)

    def interrupted(self, ctx: ActionContext, ops: WorldOps, elapsed_ticks: int) -> None:
        pass


@dataclass(frozen=True)
class Take:
    """Pega a pedra da caixa, que é dos dois: confere de novo na conclusão (`Rechecked`)."""

    name: str = "take"

    def validate(self, ctx: ActionContext) -> Validation:
        return self.recheck(ctx) or Accepted(int(ctx.params["ticks"]), "never")

    def recheck(self, ctx: ActionContext) -> Rejection | None:
        return None if ctx.view.items("box").get("pedra") else Rejection("empty")

    def complete(self, ctx: ActionContext, ops: WorldOps) -> None:
        ops.transfer_item("pedra", 1, "box", ctx.avatar_id, "take")

    def interrupted(self, ctx: ActionContext, ops: WorldOps, elapsed_ticks: int) -> None:
        pass


def _arrive(ctx: SystemContext, ops: WorldOps) -> None:
    ops.enter("bia", Position(2, 1), "work_day", {"fome": 0, "energia": 100})


def _go_home(ctx: SystemContext, ops: WorldOps) -> None:
    if ctx.view.present("bia"):
        ops.leave("bia", "end_of_day")


@dataclass(frozen=True)
class Lab3:
    manifest: CartridgeManifest = field(default_factory=lambda: CartridgeManifest("lab3", "0.1.0"))
    bia: AvatarDef = field(default_factory=lambda: AvatarDef("bia", HELPER, BIA, present=False))

    def contribute(self, world: WorldBuilder) -> None:
        world.configure_clock(
            ClockDef(60, "06:00", (("manha", "06:00"), ("noite", "20:00")), default_scale=72)
        )
        world.set_tiles_per_minute(1)
        world.set_map(lab_map())
        world.define_kind(KindDef("avatar", capacity=7))
        world.define_kind(KindDef("box", blocking=True))
        world.define_item(ItemDef("moeda", "moeda"))
        world.define_item(ItemDef("pedra", "recurso", weight=2))
        world.define_need(NeedDef("energia", 100, {"asleep": 12}, role="energy"))
        world.define_need(NeedDef("fome", 10, {"awake": 3, "asleep": 1}))
        world.add_action(Work())
        world.add_action(Take())
        world.add_system(LabSystem("arrive", "scheduled", 10, (DailyAt(("08:00",)),), _arrive))
        world.add_system(LabSystem("home", "scheduled", 10, (DailyAt(("18:00",)),), _go_home))
        world.add_avatar(AvatarDef("ana", SCRIPT))
        world.add_avatar(self.bia)
        world.spawn(SpawnDef("bia", "avatar"))  # fora do mundo: sem posição nem contêiner

    def rules_file(self) -> Path | None:
        return None


def make_core(cartridge: Lab3 | None = None) -> KernelCore:
    definition = build_world("lab3", {"lab3": cartridge or Lab3()})
    core = KernelCore(definition, WorldConfig("lab3-01", 7, START), (), rules_source="test")
    core.start()
    core.drain()
    return core


def _run(core: KernelCore, ticks: int = 1) -> list[Fact]:
    core.drain()
    for _ in range(ticks):
        core.step()
    return core.drain()


def _only(facts: Sequence[Fact], event: str) -> list[dict[str, Any]]:
    wanted = f"campsverso.{event}" if re.search(r"\.v\d+$", event) else f"campsverso.{event}.v1"
    return [dict(f.data) for f in facts if f.type == wanted]


def _as_bia(action: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    proposal = command(action, params, controller=HELPER.id)
    proposal["data"]["avatar_id"] = "bia"
    return proposal


def test_o_ajudante_comeca_fora_do_mundo_e_nao_deve_decisao() -> None:
    core = make_core()
    world = core.world
    assert world.avatars() == ["ana"]
    assert not world.present("bia")
    assert world.position_of("bia") is None
    facts = _run(core, 60)  # a primeira hora: só a Ana decide
    assert {d["avatar_id"] for d in _only(facts, "avatar.decision_requested")} <= {"ana"}
    assert world.needs["bia"] == {"energia": 12000, "fome": 1200}  # paradas, como no começo
    core.submit(_as_bia("work"))
    (rejected,) = _only(_run(core), "action.rejected")
    assert (rejected["avatar_id"], rejected["reason"]) == ("bia", "absent")


def test_entrar_e_sair_com_os_eventos_e_o_pedido_de_decisao() -> None:
    core = make_core()
    facts = _run(core, 121)  # até depois das 08:00
    (entered,) = _only(facts, "avatar.entered")
    assert entered == {"avatar_id": "bia", "position": {"x": 2, "y": 1}, "reason": "work_day"}
    assert core.world.avatars() == ["ana", "bia"]
    requested = [d for d in _only(facts, "avatar.decision_requested") if d["avatar_id"] == "bia"]
    assert [d["reason"] for d in requested] == ["woke_up"]
    assert core.world.need("bia", "fome") == 0.1  # chegou com 0, e um minuto a 6 por hora
    core.submit(_as_bia("work"))
    facts = _run(core, 3)
    (accepted,) = _only(facts, "action.accepted")
    assert accepted["duration_ticks"] == 8  # o tempo dobrado da ficha
    facts = _run(core, 600)  # até as 18:00, com a ação no meio do caminho
    (left,) = _only(facts, "avatar.left")
    assert left == {"avatar_id": "bia", "position": {"x": 2, "y": 1}, "reason": "end_of_day"}
    assert core.world.position_of("bia") is None
    assert not core.lockstep_blocked
    frozen = dict(core.world.needs["bia"])
    _run(core, 60)
    assert core.world.needs["bia"] == frozen  # em casa, as necessidades param


def test_a_ficha_muda_o_corpo() -> None:
    core = make_core()
    world = core.world
    attributes = world.entity("bia").attributes
    assert (attributes["capacity"], attributes["vision"], attributes["night_vision"]) == (
        14,
        2.0,
        True,
    )
    assert world.capacity("bia") == 14
    assert world.capacity("ana") == 7
    assert world.rate("bia", "fome") == 2 * world.rate("ana", "fome")
    _run(core, 121)
    before = world.need("bia", "energia")
    world.change_need("bia", "energia", -10)
    assert world.need("bia", "energia") == before - 15  # 50% a mais de gasto
    world.change_need("bia", "energia", 5)
    assert world.need("bia", "energia") == before - 10  # recuperar não muda
    core.submit(_as_bia("move", {"target": {"x": 1, "y": 2}}))
    (moved,) = _only(_run(core, 3), "world.entity.moved")
    assert moved["tiles_per_tick"] == 0.5 * core.tiles_per_tick
    world.faint("bia", "exhausted", 60, {"energia": 50})
    assert not world.is_asleep("bia")  # a ficha diz que não desmaia


def test_o_snapshot_guarda_quem_esta_fora() -> None:
    core = make_core()
    state = core.export_state()
    (bia,) = [a for a in state["world"]["avatars"] if a["avatar_id"] == "bia"]
    assert bia["present"] is False
    (ana,) = [a for a in state["world"]["avatars"] if a["avatar_id"] == "ana"]
    assert "present" not in ana  # quem está no mundo não muda o snapshot de sempre
    other = make_core()
    other.restore_state(state)
    assert other.world.avatars() == ["ana"]
    assert other.world.position_of("bia") is None


def test_a_definicao_confere_o_avatar_de_fora_e_a_ficha() -> None:
    @dataclass(frozen=True)
    class Placed(Lab3):
        def contribute(self, world: WorldBuilder) -> None:
            super().contribute(world)
            world.spawn(SpawnDef("bia", "avatar", position=Position(2, 1)), override=True)

    with pytest.raises(Exception, match="fora do mundo não tem posição"):
        build_world("lab3", {"lab3": Placed()})
    odd = Lab3(bia=AvatarDef("bia", HELPER, AvatarTraits(need_rates={"fome": 1.3}), False))
    with pytest.raises(WorldRuleError, match="não dá unidades inteiras"):
        make_core(odd)


def test_a_acao_que_outro_avatar_desfez_no_meio_falha_na_conclusao() -> None:
    core = make_core()
    _run(core, 121)  # a Bia chegou
    core.world.create_item("pedra", 1, "box", "test")
    core.submit(command("take", {"ticks": 6}))  # a Ana leva 6 minutos
    core.submit(_as_bia("take", {"ticks": 1}))  # a Bia, 2 (a ficha dobra o tempo)
    facts = _run(core, 8)
    assert len(_only(facts, "action.accepted")) == 2  # as duas valiam na proposta
    (done,) = _only(facts, "action.completed")
    assert done["avatar_id"] == "bia"
    (failed,) = _only(facts, "action.failed")
    assert (failed["avatar_id"], failed["action"], failed["reason"]) == (
        "ana",
        "take",
        "precondition_lost",
    )
    assert core.world.items("bia") == {"pedra": 1}
    asked = [d for d in _only(facts, "avatar.decision_requested") if d["avatar_id"] == "ana"]
    assert asked[-1]["reason"] == "action_interrupted"
