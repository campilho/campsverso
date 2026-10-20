"""As quatro primitivas genéricas da Fazenda Boa Vista (ADR-0062), num laboratório próprio: peso e
capacidade, entidade criada em tempo de execução, lotes com validade e modificadores de
necessidade."""

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
    CartridgeManifest,
    ClockDef,
    ItemDef,
    KindDef,
    NeedDef,
    Position,
    Rejection,
    SpawnDef,
    Validation,
    WorldBuilder,
    WorldOps,
)
from campsverso_kernel.core import KernelCore, WorldConfig
from campsverso_kernel.errors import WorldRuleError
from campsverso_kernel.facts import Fact
from campsverso_kernel.loader import build_world
from campsverso_kernel.testing import SCRIPT, START, command, lab_map

DAY = 1440


@dataclass(frozen=True)
class Grab:
    """Pega pedras do chão (pesam 2 cada): recusa `too_heavy` quando não cabem."""

    name: str = "grab"

    def validate(self, ctx: ActionContext) -> Validation:
        qty = int(ctx.params.get("qty", 1))
        if not ctx.view.fits("pedra", qty, ctx.avatar_id):
            return Rejection("too_heavy")
        return Accepted(1)

    def complete(self, ctx: ActionContext, ops: WorldOps) -> None:
        ops.create_item("pedra", int(ctx.params.get("qty", 1)), ctx.avatar_id, "grab")

    def interrupted(self, ctx: ActionContext, ops: WorldOps, elapsed_ticks: int) -> None:
        pass


@dataclass(frozen=True)
class Stash:
    """Guarda itens na caixa."""

    name: str = "stash"

    def validate(self, ctx: ActionContext) -> Validation:
        item, qty = str(ctx.params["item"]), int(ctx.params.get("qty", 1))
        if ctx.view.items(ctx.avatar_id).get(item, 0) < qty:
            return Rejection("missing_item")
        if not ctx.view.fits(item, qty, "box"):
            return Rejection("too_heavy")
        return Accepted(1)

    def complete(self, ctx: ActionContext, ops: WorldOps) -> None:
        ops.transfer_item(
            str(ctx.params["item"]), int(ctx.params.get("qty", 1)), ctx.avatar_id, "box", "stash"
        )

    def interrupted(self, ctx: ActionContext, ops: WorldOps, elapsed_ticks: int) -> None:
        pass


@dataclass(frozen=True)
class Pick:
    """Colhe maçãs (validade de 2 dias)."""

    name: str = "pick"

    def validate(self, ctx: ActionContext) -> Validation:
        return Accepted(1)

    def complete(self, ctx: ActionContext, ops: WorldOps) -> None:
        ops.create_item("maca", int(ctx.params.get("qty", 1)), ctx.avatar_id, "harvest")

    def interrupted(self, ctx: ActionContext, ops: WorldOps, elapsed_ticks: int) -> None:
        pass


@dataclass(frozen=True)
class Eat:
    """Come uma maçã; `stew: true` é o ensopado, que segura a fome pela metade por 120 ticks."""

    name: str = "eat"

    def validate(self, ctx: ActionContext) -> Validation:
        if ctx.view.items(ctx.avatar_id).get("maca", 0) < 1:
            return Rejection("missing_item")
        return Accepted(1)

    def complete(self, ctx: ActionContext, ops: WorldOps) -> None:
        ops.consume_item("maca", 1, ctx.avatar_id, "eat")
        if ctx.params.get("stew"):
            ops.add_need_modifier(ctx.avatar_id, "fome", 0.5, 120, "satisfeito_ate")

    def interrupted(self, ctx: ActionContext, ops: WorldOps, elapsed_ticks: int) -> None:
        pass


@dataclass(frozen=True)
class Dig:
    """Cava um canteiro no tile pedido: uma entidade nova em tempo de execução."""

    name: str = "dig"

    def validate(self, ctx: ActionContext) -> Validation:
        return Accepted(2)

    def complete(self, ctx: ActionContext, ops: WorldOps) -> None:
        number = len(ctx.view.entities("plot")) + 1
        target = ctx.params["target"]
        ops.spawn(
            SpawnDef(
                f"plot-{number:02d}",
                "plot",
                position=Position(int(target["x"]), int(target["y"])),
                attributes={"dug": True},
            )
        )

    def interrupted(self, ctx: ActionContext, ops: WorldOps, elapsed_ticks: int) -> None:
        pass


@dataclass(frozen=True)
class Stow:
    """Guarda a pá na caixa, ou pega de volta (`back: true`): uma entidade muda de contêiner."""

    name: str = "stow"

    def validate(self, ctx: ActionContext) -> Validation:
        target = ctx.avatar_id if ctx.params.get("back") else "box"
        if not ctx.view.fits_entity("spade", target):
            return Rejection("too_heavy")
        return Accepted(1)

    def complete(self, ctx: ActionContext, ops: WorldOps) -> None:
        ops.move_entity("spade-1", ctx.avatar_id if ctx.params.get("back") else "box")

    def interrupted(self, ctx: ActionContext, ops: WorldOps, elapsed_ticks: int) -> None:
        pass


@dataclass(frozen=True)
class Lab2:
    manifest: CartridgeManifest = field(default_factory=lambda: CartridgeManifest("lab2", "0.1.0"))

    def contribute(self, world: WorldBuilder) -> None:
        world.configure_clock(ClockDef(60, "06:00", (("manha", "06:00"),), default_scale=72))
        world.set_tiles_per_minute(1)
        world.set_map(lab_map())
        world.define_kind(KindDef("avatar", capacity=7))
        world.define_kind(KindDef("box", blocking=True, capacity=100, shelf_life_factor=2))
        world.define_kind(KindDef("plot", attributes={"dug": False}))
        world.define_kind(KindDef("spade", weight=3))
        world.set_movement_cost("energia", 0.05)  # 1 de energia a cada 20 tiles (ADR-0062)
        world.define_item(ItemDef("moeda", "moeda"))
        world.define_item(ItemDef("pedra", "recurso", weight=2))
        world.define_item(ItemDef("maca", "comida", weight=0.5, shelf_life_days=2))
        world.define_need(NeedDef("energia", 100, {"asleep": 12}, role="energy"))
        world.define_need(NeedDef("fome", 10, {"awake": 3, "asleep": 1}))
        for action in (Grab(), Stash(), Pick(), Eat(), Dig(), Stow()):
            world.add_action(action)
        world.add_avatar(AvatarDef("ana", SCRIPT))
        world.spawn(SpawnDef("spade-1", "spade", container_id="ana"))
        world.add_items("ana", "moeda", 5)

    def rules_file(self) -> Path | None:
        return None


def make_core() -> KernelCore:
    definition = build_world("lab2", {"lab2": Lab2()})
    core = KernelCore(definition, WorldConfig("lab2-01", 7, START), (), rules_source="test")
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


def _do(core: KernelCore, action: str, params: dict[str, Any] | None = None) -> list[Fact]:
    core.submit(command(action, params))
    return _run(core, 3)


# ----------------------------------------------------------------- peso e capacidade


def test_peso_e_capacidade() -> None:
    core = make_core()
    assert core.world.entity("ana").attributes["capacity"] == 7
    assert core.world.weight("ana") == 3.0  # a pá, uma entidade guardada, pesa pelo tipo
    facts = _do(core, "grab", {"qty": 2})
    assert _only(facts, "action.completed")
    changes = [c["changes"] for c in _only(facts, "world.entity.state_changed")]
    assert {"weight": 7.0} in changes
    assert core.world.weight("ana") == 7.0
    assert not core.world.fits("pedra", 1, "ana")
    (rejected,) = _only(_do(core, "grab", {"qty": 1}), "action.rejected")
    assert rejected["reason"] == "too_heavy"
    facts = _do(core, "stash", {"item": "pedra", "qty": 2})
    assert _only(facts, "world.item.transferred")[0]["qty"] == 2
    assert (core.world.weight("ana"), core.world.weight("box")) == (3.0, 4.0)
    assert core.world.entity("box").attributes["weight"] == 4.0
    assert core.world.capacity("box") == 100


def test_o_kernel_trata_nao_caber_como_violacao() -> None:
    core = make_core()
    with pytest.raises(WorldRuleError, match="too_heavy"):
        core.world.create_item("pedra", 3, "ana", "test")  # 3 da pá + 6 > 7
    core.world.spawn(SpawnDef("spade-2", "spade", container_id="ana"))  # 3 + 3 = 6: cabe
    with pytest.raises(WorldRuleError, match="too_heavy"):
        core.world.create_item("pedra", 1, "ana", "test")  # 6 + 2 > 7
    with pytest.raises(WorldRuleError, match="too_heavy"):
        core.world.spawn(SpawnDef("spade-3", "spade", container_id="ana"))  # 6 + 3 > 7


def test_guardar_a_ferramenta_na_caixa_e_pegar_de_volta() -> None:
    core = make_core()
    facts = _do(core, "stow")
    (stored,) = _only(facts, "world.entity.stored")
    assert stored == {
        "entity_id": "spade-1",
        "from_container": "ana",
        "to_container": "box",
        "action_id": stored["action_id"],
    }
    assert core.world.entity("spade-1").container_id == "box"
    assert (core.world.weight("ana"), core.world.weight("box")) == (0.0, 3.0)
    _do(core, "grab", {"qty": 3})  # sem a pá cabem 3 pedras (6 de 7)
    (rejected,) = _only(_do(core, "stow", {"back": True}), "action.rejected")
    assert rejected["reason"] == "too_heavy"
    _do(core, "stash", {"item": "pedra", "qty": 2})
    assert _only(_do(core, "stow", {"back": True}), "world.entity.stored")
    assert core.world.entity("spade-1").container_id == "ana"
    assert core.world.weight("ana") == 5.0


def test_andar_gasta_energia_por_tile() -> None:
    core = make_core()
    before = core.world.need("ana", "energia")
    core.submit(command("move", {"target": {"x": 3, "y": 1}}))  # de (1,1) a (3,1): 2 tiles
    _run(core, 4)
    assert core.world.entity("ana").position == Position(3, 1)
    assert core.world.need("ana", "energia") == pytest.approx(before - 2 * 0.05)


# ----------------------------------------------------------------- entidade em tempo de execução


def test_cavar_cria_uma_entidade_que_sobrevive_ao_snapshot() -> None:
    core = make_core()
    facts = _do(core, "dig", {"target": {"x": 2, "y": 1}})
    (spawned,) = _only(facts, "world.entity.spawned")
    assert spawned == {
        "entity_id": "plot-01",
        "kind": "plot",
        "blocking": False,
        "position": {"x": 2, "y": 1},
        "attributes": {"dug": True},
        "action_id": spawned["action_id"],
    }
    assert core.world.entity("plot-01").position == Position(2, 1)
    assert core.world.walkable(Position(2, 1))  # não bloqueia
    state = core.export_state()
    other = KernelCore(
        build_world("lab2", {"lab2": Lab2()}), WorldConfig("lab2-01", 7, START), (), "test"
    )
    other.restore_state(state)
    assert other.world.entity("plot-01").attributes == {"dug": True}
    assert [e.entity_id for e in other.world.entities("plot")] == ["plot-01"]
    with pytest.raises(WorldRuleError, match="já existe"):
        core.world.spawn(SpawnDef("plot-01", "plot", position=Position(3, 1)))


# ----------------------------------------------------------------- lotes e validade


def test_lotes_vencem_pela_validade_e_o_contêiner_conserva() -> None:
    core = make_core()
    (created,) = _only(_do(core, "pick", {"qty": 2}), "world.item.created")
    assert (created["expires_day"], core.world.day) == (3, 1)
    (moved,) = _only(_do(core, "stash", {"item": "maca", "qty": 1}), "world.item.transferred")
    assert moved["expires_day"] == 3
    core.advance(2 * DAY - core.tick + 1, jump=True)  # passa pelas 06:00 do dia 3
    spoiled = _only(core.drain(), "world.item.consumed")
    assert spoiled == [
        {
            "item": "maca",
            "qty": 1,
            "container_id": "ana",
            "reason": "spoiled",
            "expires_day": 3,
        }
    ]
    assert core.world.items("ana") == {"moeda": 5}
    assert core.world.items("box") == {"maca": 1}  # a caixa dobra a validade
    core.advance(2 * DAY, jump=True)  # passa pelas 06:00 do dia 5
    (spoiled_box,) = _only(core.drain(), "world.item.consumed")
    assert (spoiled_box["container_id"], spoiled_box["reason"]) == ("box", "spoiled")
    assert core.world.items("box") == {}


def test_comer_tira_do_lote_mais_velho() -> None:
    core = make_core()
    _do(core, "pick", {"qty": 1})
    core.advance(DAY - core.tick, jump=True)  # dia 2
    _do(core, "pick", {"qty": 1})
    (eaten,) = _only(_do(core, "eat"), "world.item.consumed")
    assert (eaten["reason"], eaten["expires_day"]) == ("eat", 3)
    assert core.world.lots["ana"]["maca"] == [[2, 1]]


# ----------------------------------------------------------------- modificadores de necessidade


def _hunger(core: KernelCore) -> float:
    return core.world.need("ana", "fome")


def test_o_ensopado_segura_a_fome_pela_metade_e_vence() -> None:
    core = make_core()
    _do(core, "pick")
    facts = _do(core, "eat", {"stew": True})
    changes = [c["changes"] for c in _only(facts, "world.entity.state_changed")]
    assert any("satisfeito_ate" in c for c in changes)
    until_label = core.world.entity("ana").attributes["satisfeito_ate"]
    assert isinstance(until_label, str)
    assert re.fullmatch(r"\d\d:\d\d", until_label)
    (modifier,) = core.world.avatar_map["ana"].modifiers
    until, start, base = int(modifier["until_tick"]), core.tick, _hunger(core)
    _run(core, 60)  # a fome sobe 3 por hora, 0,05 por tick; pela metade, 0,025
    assert _hunger(core) == pytest.approx(base + 60 * 0.025)
    _run(core, 120)  # já venceu: a taxa volta ao normal e o atributo se apaga
    active = until - start
    assert _hunger(core) == pytest.approx(base + active * 0.025 + (180 - active) * 0.05)
    assert core.world.entity("ana").attributes["satisfeito_ate"] is None
    assert core.world.avatar_map["ana"].modifiers == []


def test_o_salto_de_tempo_integra_o_modificador_por_trechos() -> None:
    stepped, jumped = make_core(), make_core()
    for core in (stepped, jumped):
        _do(core, "pick")
        _do(core, "eat", {"stew": True})
    stepped.advance(300)
    jumped.advance(300, jump=True)
    assert _hunger(stepped) == _hunger(jumped)
    assert stepped.world.avatar_map["ana"].modifiers == jumped.world.avatar_map["ana"].modifiers


def test_o_modificador_sobrevive_ao_snapshot() -> None:
    core = make_core()
    _do(core, "pick", {"qty": 2})
    _do(core, "eat", {"stew": True})
    state = core.export_state()
    other = KernelCore(
        build_world("lab2", {"lab2": Lab2()}), WorldConfig("lab2-01", 7, START), (), "test"
    )
    other.restore_state(state)
    assert other.world.avatar_map["ana"].modifiers == core.world.avatar_map["ana"].modifiers
    assert other.world.lots == core.world.lots
    core.advance(200)
    other.advance(200)
    assert _hunger(core) == _hunger(other)


def test_um_fator_que_nao_da_unidade_inteira_e_recusado() -> None:
    core = make_core()
    with pytest.raises(WorldRuleError, match="unidades inteiras"):
        core.world.add_need_modifier("ana", "fome", 0.3, 10, "x")
