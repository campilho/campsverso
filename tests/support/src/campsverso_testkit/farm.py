"""Fazenda do Camps para testes: o mundo montado pela cadeia real e um controlador roteirizado.

Não é o fazendeiro-script (M3): só propõe a próxima ação de um roteiro.
"""

import re
from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from typing import Any

from campsverso_adapters import YamlFlags
from campsverso_kernel.core import KernelCore, WorldConfig
from campsverso_kernel.facts import Fact
from campsverso_kernel.loader import build_world, discover
from campsverso_ports import RuleConfig

START = datetime(2026, 10, 10, 6, 0, tzinfo=timezone(timedelta(hours=-3)))  # ADR-0038
WORLD = "farm-camps-01"
SCRIPT_ID = "script/farmer-v1"


def rules(*, river_bonus: bool = True, cartridge: str = "farm_camps") -> tuple[RuleConfig, ...]:
    path = discover()[cartridge].rules_file()
    assert path is not None
    configs = YamlFlags(path).rules()
    return tuple(
        RuleConfig(c.rule, c.impl, c.version, c.hidden, river_bonus, c.params) for c in configs
    )


def make_core(
    seed: int = 20261010, *, river_bonus: bool = True, cartridge: str = "farm_camps"
) -> KernelCore:
    """A Fazenda do Camps por padrão; `cartridge="farm_boavista"` monta a Fazenda Boa Vista."""
    definition = build_world(cartridge)
    world = WORLD if cartridge == "farm_camps" else f"{cartridge.replace('_', '-')}-01"
    core = KernelCore(
        definition,
        WorldConfig(world, seed, START),
        rules(river_bonus=river_bonus, cartridge=cartridge),
        "test",
    )
    return core


class Farmer:
    """Controlador roteirizado: propõe uma ação e espera o avatar ficar ocioso."""

    def __init__(self, core: KernelCore) -> None:
        self.core = core
        self.facts: list[Fact] = []
        self._n = 0
        # O controlador padrão do avatar neste mundo (o script 2 na Boa Vista): é quem propõe.
        self.controller_id = core.world.avatar_map["camps"].default_controller.id

    def _collect(self) -> None:
        self.facts += self.core.drain()

    def run(self, ticks: int) -> None:
        for _ in range(ticks):
            self.core.step()
            self._collect()

    def advance(self, ticks: int, *, jump: bool = True) -> None:
        """Avança `ticks` (saltando o que não acontece) e recolhe os fatos: as viradas do dia."""
        self.core.advance(ticks, jump=jump)
        self._collect()

    def until(self, hhmm: str) -> None:
        self.run(self.core.calendar.ticks_until(self.core.tick, int(hhmm[:2]) * 60 + int(hhmm[3:])))

    def do(self, action: str, **params: Any) -> list[Fact]:
        self._n += 1
        start = len(self.facts)
        self.core.submit(
            {
                "id": f"cmd-{self._n}",
                "type": "campsverso.cmd.action.propose.v1",
                "controllerid": self.controller_id,
                "data": {"avatar_id": "camps", "action": action, "params": params},
            }
        )
        self.run(1)
        avatar = self.core.world.avatar_map["camps"]
        while avatar.action is not None:
            self.run(1)
        return self.facts[start:]

    def walk(self, x: int, y: int) -> list[Fact]:
        return self.do("move", target={"x": x, "y": y})


def event_type(event: str) -> str:
    """`avatar.sleep.ended.v2` vira o tipo completo; sem versão no fim, vale a v1."""
    return f"campsverso.{event}" if re.search(r"\.v\d+$", event) else f"campsverso.{event}.v1"


def of_type(facts: list[Fact], event: str) -> list[Mapping[str, Any]]:
    return [f.data for f in facts if f.type == event_type(event)]
