"""Os ajudantes da fazenda (ADR-0072): personagens contratáveis, cada um com a sua ficha.

O cenário liga os ajudantes com a seção `helpers`. Cada ajudante é um avatar declarado fora do
mundo, com a ficha nos dados (o nome, a especialidade, o bom e o ruim, a diária, o horário e os
traços do corpo, que o kernel aplica sem saber o que é uma plantadeira). Ele traz as próprias
ferramentas (o regador e a pá) e é controlado por um script que obedece às ordens de quem o
contratou (`script/ajudante-<id>`).

O contrato se faz no quadro de ajudantes, por alguns dias, pago adiantado. No dia de trabalho o
ajudante entra pela entrada da fazenda no horário dele e sai no fim do turno, deixando no baú o
que carrega. O que ele vende vai para o patrão.

Na entidade do ajudante, à vista: a ficha, `patrao`, `dias` (os que faltam) e a ordem (`ordem`,
`ordem_cultura`, `ordem_item`, `ordem_n` e o ponto `ordem_x`, `ordem_y` de onde cavar). No quadro,
à vista, a situação de cada ajudante, com o id em snake_case (`ze_graudo`).
"""

from collections.abc import Mapping, Sequence
from typing import Any, cast

from campsverso_cartridge_api import (
    AvatarDef,
    AvatarTraits,
    ControllerRef,
    EntityView,
    Position,
    SpawnDef,
    SystemContext,
    WorldOps,
    WorldView,
)
from campsverso_farm_sim.config import optional, section

HELPERS = "helpers"
COIN = "moeda"
ORDER = ("ordem", "ordem_cultura", "ordem_item", "ordem_n", "ordem_x", "ordem_y")


# ----------------------------------------------------------------------------- os dados


def roster(data: Mapping[str, Any]) -> Mapping[str, Mapping[str, Any]]:
    return cast(Mapping[str, Mapping[str, Any]], data.get("roster") or {})


def shift_of(data: Mapping[str, Any], helper: str) -> tuple[str, str]:
    """O horário do ajudante: a chegada e a saída (a ficha pode trocar o do cenário)."""
    base = cast(Mapping[str, str], data["shift"])
    own = cast(Mapping[str, str], roster(data)[helper].get("shift") or {})
    return str(own.get("arrive", base["arrive"])), str(own.get("leave", base["leave"]))


def times(data: Mapping[str, Any]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Os horários de chegada e de saída de todas as fichas, para os gatilhos diários."""
    shifts = [shift_of(data, helper) for helper in sorted(roster(data))]
    return tuple(sorted({a for a, _ in shifts})), tuple(sorted({b for _, b in shifts}))


def _factors(raw: object) -> dict[str, float]:
    found = cast(Mapping[str, Any], raw or {})
    return {str(k): float(v) for k, v in found.items()}


def _traits(raw: Mapping[str, Any]) -> AvatarTraits:
    capacity = raw.get("capacity")
    return AvatarTraits(
        speed=float(raw.get("speed", 1.0)),
        action_time=_factors(raw.get("action_time")),
        need_rates=_factors(raw.get("need_rates")),
        energy_cost=float(raw.get("energy_cost", 1.0)),
        capacity=None if capacity is None else float(capacity),
        faints=bool(raw.get("faints", True)),
        vision=float(raw.get("vision", 1.0)),
        night_vision=bool(raw.get("night_vision", False)),
    )


def controller_id(helper: str) -> str:
    return f"script/ajudante-{helper}"


def helper_avatars(data: Mapping[str, Any]) -> list[AvatarDef]:
    """Os ajudantes como avatares fora do mundo, com a ficha no corpo (ADR-0072)."""
    return [
        AvatarDef(
            helper,
            ControllerRef("script", controller_id(helper)),
            _traits(cast(Mapping[str, Any], sheet.get("traits") or {})),
            present=False,
        )
        for helper, sheet in sorted(roster(data).items())
    ]


def helper_spawns(data: Mapping[str, Any]) -> list[SpawnDef]:
    """Os ajudantes, sem posição, com a ficha à vista, e as ferramentas de cada um."""
    found: list[SpawnDef] = []
    tools = cast(Mapping[str, str], data.get("tools") or {})
    for helper, sheet in sorted(roster(data).items()):
        arrive, leave = shift_of(data, helper)
        visible: dict[str, Any] = {
            "nome": str(sheet["nome"]),
            "especialidade": str(sheet["especialidade"]),
            "bom": str(sheet["bom"]),
            "ruim": str(sheet["ruim"]),
            "diaria": int(sheet["diaria"]),
            "horario": f"{arrive}-{leave}",
            "patrao": None,
            "dias": 0,
            "ordem": None,
        }
        hidden: dict[str, Any] = {}
        if sheet.get("seed_loss"):
            hidden["perde_semente"] = float(sheet["seed_loss"])
        if sheet.get("tool_max_weight") is not None:
            hidden["peso_max_ferramenta"] = float(sheet["tool_max_weight"])
        found.append(
            SpawnDef(
                helper, "avatar", display_name=str(sheet["nome"]), attributes=visible, hidden=hidden
            )
        )
        found.extend(
            SpawnDef(f"{helper}-{suffix}", kind, container_id=helper)
            for suffix, kind in sorted(tools.items())
        )
    return found


# ----------------------------------------------------------------------------- no mundo


def config(view: WorldView) -> Mapping[str, Any] | None:
    return optional(view, HELPERS)


def is_helper(view: WorldView, avatar_id: str) -> bool:
    data = config(view)
    return data is not None and avatar_id in roster(data)


def employer(view: WorldView, helper: str) -> str | None:
    value = view.entity(helper).attributes.get("patrao")
    return None if value is None else str(value)


def payee(view: WorldView, avatar_id: str) -> str:
    """Quem recebe pelo que o avatar vende: o patrão, se for um ajudante (ADR-0072)."""
    if is_helper(view, avatar_id):
        return employer(view, avatar_id) or avatar_id
    return avatar_id


def board(view: WorldView, target: object = None) -> EntityView | None:
    data = config(view)
    if data is None:
        return None
    boards = list(view.entities(str(data["board_kind"])))
    if target is None:
        return boards[0] if boards else None
    return next((b for b in boards if b.entity_id == target), None)


def status(view: WorldView, helper: str) -> str:
    """Como o ajudante aparece no quadro."""
    entity = view.entity(helper)
    boss = entity.attributes.get("patrao")
    if boss is None:
        return "livre"
    last = entity.hidden.get("ultimo_dia")
    return f"com {boss} até o dia {last}"


def board_key(helper: str) -> str:
    """O nome do atributo do ajudante no quadro: os atributos são snake_case (`ze_graudo`)."""
    return helper.replace("-", "_")


def show_on_board(view: WorldView, ops: WorldOps, helpers: Sequence[str]) -> None:
    found = board(view)
    if found is not None and helpers:
        visible = {board_key(h): status(view, h) for h in helpers}
        ops.set_attributes(found.entity_id, visible=visible)


def leave_farm(view: WorldView, ops: WorldOps, helper: str, reason: str) -> None:
    """O ajudante deixa no baú o que carrega (o que couber) e vai embora."""
    chest = next(iter(view.entities("chest")), None)
    if chest is not None:
        for item, qty in sorted(view.items(helper).items()):
            fits = next((n for n in range(qty, 0, -1) if view.fits(item, n, chest.entity_id)), 0)
            if fits:
                ops.transfer_item(item, fits, helper, chest.entity_id, "helper_storage")
    ops.leave(helper, reason)


def end_contract(view: WorldView, ops: WorldOps, helper: str) -> None:
    ops.set_attributes(
        helper,
        visible={"patrao": None, "dias": 0, **dict.fromkeys(ORDER, None)},
        hidden={"primeiro_dia": None, "ultimo_dia": None},
    )


def _now(view: WorldView) -> str:
    minute = view.minute_of_day
    return f"{minute // 60:02d}:{minute % 60:02d}"


def _working(view: WorldView, helper: str) -> bool:
    entity = view.entity(helper)
    first = entity.hidden.get("primeiro_dia")
    return (
        entity.attributes.get("patrao") is not None
        and int(cast(int, entity.attributes.get("dias") or 0)) > 0
        and first is not None
        and int(cast(int, first)) <= view.day
    )


def helpers_arrive(ctx: SystemContext, ops: WorldOps) -> None:
    """No horário de chegada: quem tem dia pago entra pela entrada da fazenda, alimentado e
    descansado (dormiu e jantou em casa)."""
    view = ctx.view
    data = section(view, HELPERS)
    spot = cast(Mapping[str, int], data["arrive_at"])
    needs = {str(k): float(v) for k, v in cast(Mapping[str, Any], data["arrival_needs"]).items()}
    now = _now(view)
    for helper in sorted(roster(data)):
        if shift_of(data, helper)[0] != now or view.present(helper) or not _working(view, helper):
            continue
        ops.enter(helper, Position(int(spot["x"]), int(spot["y"])), "work_day", needs)


def helpers_leave(ctx: SystemContext, ops: WorldOps) -> None:
    """No fim do turno: quem está na fazenda vai embora, e o dia conta, mesmo para quem saiu mais
    cedo; o último dia pago encerra o contrato."""
    view = ctx.view
    data = section(view, HELPERS)
    now = _now(view)
    changed: list[str] = []
    for helper in sorted(roster(data)):
        if shift_of(data, helper)[1] != now or not _working(view, helper):
            continue
        if view.present(helper):
            leave_farm(view, ops, helper, "end_of_day")
        left = int(cast(int, view.entity(helper).attributes.get("dias") or 0)) - 1
        ops.set_attributes(helper, visible={"dias": left})
        if left <= 0:
            boss = employer(view, helper)
            end_contract(view, ops, helper)
            ops.emit(
                "campsverso.economy.labor.ended.v1",
                {"helper": helper, "employer": str(boss), "day": view.day},
            )
            changed.append(helper)
    show_on_board(view, ops, changed)


def helpers_board(ctx: SystemContext, ops: WorldOps) -> None:
    """No começo da sessão, o quadro mostra a situação de todos."""
    data = section(ctx.view, HELPERS)
    show_on_board(ctx.view, ops, sorted(roster(data)))
