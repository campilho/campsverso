"""Cartucho office_campsverso, o escritório do Campsverso: estende o gênero office (ADR-0078)."""

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

import yaml

from campsverso_cartridge_api import (
    AvatarDef,
    CartridgeManifest,
    ControllerRef,
    ControllerType,
    Position,
    SpawnDef,
    WorldBuilder,
)

DATA = Path(__file__).parent / "data"
ROBOT_NAME = re.compile(r"[a-z][a-z0-9_]{0,23}")
ROBOT_MODULE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*")
BENCH_SLOTS = 3  # os apoios da bancada: um por tile da pegada dela
RESERVE_ARGS = 8  # os argumentos do script de reserva (`reserva`), no máximo
RESERVE_ARG = re.compile(r"[^\s]{1,200}")  # um caminho, sem espaço: a lista vai num atributo só


def bench_of(tmj: Mapping[str, Any]) -> Position:
    """O tile da bancada no mapa: o meio dela, que bloqueia."""
    tile = int(tmj["tilewidth"])
    for layer in cast(list[Mapping[str, Any]], tmj["layers"]):
        for item in cast(list[Mapping[str, Any]], layer.get("objects") or ()):
            if item.get("type") == "bench":
                return Position(int(item["x"]) // tile, int(item["y"]) // tile)
    raise ValueError("o mapa do escritório não tem bancada")


def reserve_args(name: str, raw: object) -> list[str]:
    """Os argumentos com que o dev-script, o script de reserva, chama o robô antes de entregar
    (`reserva`): uma lista de caminhos sem espaço. Os atributos de uma entidade são escalares, então
    eles viajam juntos, separados por espaço."""
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise ValueError(f"robos: {name}: a reserva é uma lista de argumentos")
    given = [str(a) for a in cast(list[object], raw)]
    if len(given) > RESERVE_ARGS or not all(RESERVE_ARG.fullmatch(a) for a in given):
        raise ValueError(
            f"robos: {name}: a reserva tem até {RESERVE_ARGS} argumentos, sem espaço, de até 200"
        )
    return given


def robots(raw: object, bench: Position) -> list[SpawnDef]:
    """Os robôs do registro, sobre a bancada: um por apoio, na ordem (o plano do M24, §4)."""
    entries = cast(list[Mapping[str, Any]], raw or [])
    if len(entries) > BENCH_SLOTS:
        raise ValueError(
            f"robos: a bancada tem {BENCH_SLOTS} apoios, e o registro tem {len(entries)}"
        )
    found: list[SpawnDef] = []
    names: set[str] = set()
    for slot, entry in enumerate(entries):
        name, module = str(entry.get("nome", "")), str(entry.get("modulo", ""))
        if not ROBOT_NAME.fullmatch(name) or name in names:
            raise ValueError(f"robos: nome inválido ou repetido: {name!r}")
        if not ROBOT_MODULE.fullmatch(module):
            raise ValueError(f"robos: {name}: o módulo {module!r} não é um módulo Python")
        names.add(name)
        attributes: dict[str, Any] = {
            "nome": name,
            "modulo": module,
            "descricao": " ".join(str(entry.get("descricao", "")).split())[:300],
        }
        reserve = reserve_args(name, entry.get("reserva"))
        if reserve:
            attributes["reserva"] = " ".join(reserve)
        found.append(
            SpawnDef(
                f"robo-{name}",
                "robot",
                position=Position(bench.x - 1 + slot, bench.y),
                display_name=name.capitalize(),
                attributes=attributes,
            )
        )
    return found


@dataclass(frozen=True)
class OfficeCampsversoCartridge:
    manifest: CartridgeManifest = field(
        default_factory=lambda: CartridgeManifest("office_campsverso", "0.1.0", extends=("office",))
    )

    def contribute(self, world: WorldBuilder) -> None:
        tmj = cast(dict[str, Any], json.loads((DATA / "map.tmj").read_text(encoding="utf-8")))
        world.set_map(tmj)
        state = cast(
            dict[str, Any], yaml.safe_load((DATA / "escritorio.yaml").read_text(encoding="utf-8"))
        )
        bench = robots(state.get("robos"), bench_of(tmj))
        for robot in bench:
            world.spawn(robot)
        # O registro também vai aos dados: o sistema da bancada põe no mundo retomado o robô que o
        # registro ganhou numa versão nova, e tira o que saiu (o briefing do PR #2, 21/nov).
        world.merge_data(
            "office",
            {
                "bench_robots": [
                    {
                        "id": r.entity_id,
                        "x": r.position.x if r.position else 0,
                        "y": r.position.y if r.position else 0,
                        "name": r.display_name or r.entity_id,
                        "attributes": dict(r.attributes),
                    }
                    for r in bench
                ]
            },
        )
        office = cast(Mapping[str, Any], state["office"])
        world.merge_data("office", office)
        door = Position(int(office["door"]["x"]), int(office["door"]["y"]))
        for member in cast(list[Mapping[str, Any]], state["cast"]):
            controller = cast(Mapping[str, str], member["controller"])
            avatar_id = str(member["id"])
            if member.get("on_call"):  # o acordo de convocação próprio do dev (a parte 5 do M25)
                world.merge_data("office", {"agreements": {avatar_id: member["on_call"]}})
            # Todos começam fora: o expediente põe o dev e o vigia; o gerente entra ao ser assumido.
            world.spawn(
                SpawnDef(
                    avatar_id,
                    "avatar",
                    display_name=str(member["name"]),
                    attributes={"papel": str(member["role"])},
                )
            )
            world.add_avatar(
                AvatarDef(
                    avatar_id,
                    ControllerRef(cast(ControllerType, controller["type"]), controller["id"]),
                    present=False,
                    controllers=frozenset(str(kind) for kind in member["accepts"]),
                    enters_at=door if member.get("enters_at_door") else None,
                )
            )

    def rules_file(self) -> Path | None:
        return None
