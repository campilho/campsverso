"""Kit de testes: um cartucho de laboratório, o mínimo para o kernel sem fazenda (ADR-0025).

Usado pelos testes do kernel e, nos próximos marcos, pelos de percepção e controladores.
"""

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from campsverso_cartridge_api import (
    Accepted,
    ActionContext,
    AvatarDef,
    CartridgeManifest,
    ClockDef,
    ControllerRef,
    DailyAt,
    EntityView,
    ItemDef,
    KindDef,
    NeedDef,
    OnSessionStart,
    OnThreshold,
    Rejection,
    Scalar,
    SystemContext,
    ThresholdDef,
    Trigger,
    Validation,
    WorldBuilder,
    WorldOps,
    WorldView,
)
from campsverso_kernel.core import KernelCore, WorldConfig
from campsverso_kernel.loader import build_world
from campsverso_ports import RuleConfig

START = datetime(2026, 10, 10, 6, 0, tzinfo=timezone(timedelta(hours=-3)))
SCRIPT = ControllerRef("script", "script/lab-v1")
# Mapa 7x4: "#" parede, "~" água, "." chão. Objetos: ana (avatar) em (1,1), box em (4,1).
LAYOUT = ("#######", "#....~#", "#.##..#", "#######")
TILES = {".": 1, "#": 2, "~": 3}


def lab_map() -> dict[str, Any]:
    def props(passable: bool, water: bool = False) -> list[dict[str, Any]]:
        return [
            {"name": "passable", "type": "bool", "value": passable},
            {"name": "water", "type": "bool", "value": water},
        ]

    def obj(oid: int, name: str, kind: str, x: int, y: int, **extra: Scalar) -> dict[str, Any]:
        properties = [{"name": k, "type": "bool", "value": v} for k, v in extra.items()]
        return {
            "id": oid,
            "name": name,
            "type": kind,
            "x": x * 16,
            "y": y * 16,
            "properties": properties,
        }

    return {
        "width": 7,
        "height": 4,
        "tilewidth": 16,
        "tileheight": 16,
        "layers": [
            {"type": "tilelayer", "data": [TILES[c] for row in LAYOUT for c in row]},
            {
                "type": "objectgroup",
                "objects": [
                    obj(1, "ana", "avatar", 1, 1),
                    obj(2, "box", "box", 4, 1, blocking=True),
                ],
            },
        ],
        "tilesets": [
            {
                "firstgid": 1,
                "tiles": [
                    {"id": 0, "type": "floor", "properties": props(True)},
                    {"id": 1, "type": "wall", "properties": props(False)},
                    {"id": 2, "type": "water", "properties": props(False, water=True)},
                ],
            }
        ],
    }


@dataclass(frozen=True)
class Touch:
    """Toca a caixa (adjacente): 2 ticks, custa 10 de energia e rende pedras."""

    name: str = "touch"
    cancellable: bool = True

    def validate(self, ctx: ActionContext) -> Validation:
        me, box = ctx.view.entity(ctx.avatar_id), ctx.view.entity("box")
        assert me.position is not None
        assert box.position is not None
        if me.position.chebyshev(box.position) > 1:
            return Rejection("not_adjacent")
        return Accepted(2)

    def complete(self, ctx: ActionContext, ops: WorldOps) -> None:
        stones = int(ops.apply_rules("stone_yield", "box", 1.0))
        ops.create_item("pedra", stones, ctx.avatar_id, "harvest")
        ops.set_attributes("box", visible={"touched": True})
        ops.change_need(ctx.avatar_id, "energia", -10)
        ops.explain_effects("box")


@dataclass(frozen=True)
class Nap:
    name: str = "nap"
    cancellable: bool = True

    def validate(self, ctx: ActionContext) -> Validation:
        return Accepted(1)

    def complete(self, ctx: ActionContext, ops: WorldOps) -> None:
        ops.start_sleep(ctx.avatar_id, "bed", ctx.view.ticks_until("06:00"))


@dataclass(frozen=True)
class LabSystem:
    name: str
    stage: str
    priority: int
    triggers: tuple[Trigger, ...]
    body: Callable[[SystemContext, WorldOps], None]

    def run(self, ctx: SystemContext, ops: WorldOps) -> None:
        self.body(ctx, ops)


@dataclass(frozen=True)
class WaterBonus:
    name: str = "water_bonus"
    target: str = "stone_yield"

    def apply(
        self, view: WorldView, entity: EntityView, value: float, params: Mapping[str, Scalar]
    ) -> float:
        assert entity.position is not None
        near = any(
            entity.position.chebyshev(t) <= int(params["radius"] or 0)
            for t in view.tiles_with("water")
        )
        return value * float(params["multiplier"] or 1) if near else value


def _collapse(ctx: SystemContext, ops: WorldOps) -> None:
    assert ctx.avatar_id is not None
    ops.faint(ctx.avatar_id, "exhausted", 60, {"energia": 50})


@dataclass(frozen=True)
class LabCartridge:
    manifest: CartridgeManifest = field(default_factory=lambda: CartridgeManifest("lab", "0.1.0"))

    def contribute(self, world: WorldBuilder) -> None:
        world.configure_clock(
            ClockDef(60, "06:00", (("manha", "06:00"), ("noite", "20:00")), default_scale=72)
        )
        world.set_tiles_per_minute(1)
        world.set_map(lab_map())
        world.define_kind(KindDef("avatar"))
        world.define_kind(KindDef("box", blocking=True, attributes={"touched": False}))
        world.define_item(ItemDef("pedra", "recurso"))
        world.define_item(ItemDef("moeda", "moeda"))
        world.define_need(NeedDef("energia", 25, {"asleep": 12}, role="energy"))
        world.define_need(NeedDef("fome", 79, {"awake": 3, "asleep": 1}))
        world.add_threshold(ThresholdDef("fome", 80, "up", requests_decision=True))
        world.add_threshold(ThresholdDef("energia", 20, "down", requests_decision=True))
        world.add_threshold(ThresholdDef("energia", 0, "down", requests_decision=False))
        world.add_action(Touch())
        world.add_action(Nap())
        world.add_system(
            LabSystem(
                "dawn", "scheduled", 10, (OnSessionStart(),), lambda c, o: o.set_weather("sun", 1)
            )
        )
        world.add_system(
            LabSystem(
                "chime",
                "scheduled",
                10,
                (DailyAt(("08:00",)),),
                lambda c, o: o.set_attributes("box", visible={"touched": False}),
            )
        )
        world.add_system(
            LabSystem("collapse", "reactions", 10, (OnThreshold("energia", 0, "down"),), _collapse)
        )
        world.add_rule_impl(WaterBonus())
        world.add_avatar(AvatarDef("ana", SCRIPT))
        world.add_items("ana", "moeda", 5)

    def rules_file(self) -> Path | None:
        return None


RULES = (
    RuleConfig(
        "lab_water",
        "water_bonus",
        "1.0.0",
        hidden=True,
        enabled=True,
        params={"radius": 1, "multiplier": 3},
    ),
)


def make_core(rules: tuple[RuleConfig, ...] = RULES) -> KernelCore:
    definition = build_world("lab", {"lab": LabCartridge()})
    return KernelCore(definition, WorldConfig("lab-01", 7, START), rules, rules_source="test")


def command(
    action: str, params: Mapping[str, Any] | None = None, controller: str = SCRIPT.id
) -> dict[str, Any]:
    return {
        "id": f"cmd-{action}",
        "type": "campsverso.cmd.action.propose.v1",
        "controllerid": controller,
        "data": {"avatar_id": "ana", "action": action, "params": dict(params or {})},
    }


def control(command_type: str, data: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "id": "cmd-control",
        "type": f"campsverso.cmd.{command_type}.v1",
        "actor": "human/operator",
        "data": dict(data),
    }
