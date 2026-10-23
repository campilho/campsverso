"""O ano acelerado com estações (ADR-0067): a data e a estação no relógio, e a troca de estação."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from campsverso_cartridge_api import (
    AvatarDef,
    CartridgeManifest,
    ClockDef,
    KindDef,
    NeedDef,
    WorldBuilder,
    YearDef,
)
from campsverso_kernel.core import KernelCore, WorldConfig
from campsverso_kernel.errors import DefinitionError
from campsverso_kernel.loader import build_world
from campsverso_kernel.testing import SCRIPT, START, lab_map

DAY = 1440
YEAR = YearDef(
    28,
    "09-22",
    (("primavera", "09-22"), ("verao", "12-21"), ("outono", "03-20"), ("inverno", "06-21")),
)


@dataclass(frozen=True)
class Sol:
    year: YearDef | None = YEAR
    manifest: CartridgeManifest = field(default_factory=lambda: CartridgeManifest("sol", "0.1.0"))

    def contribute(self, world: WorldBuilder) -> None:
        world.configure_clock(
            ClockDef(60, "06:00", (("amanhecer", "06:00"), ("noite", "20:00")), default_scale=72)
        )
        if self.year is not None:
            world.configure_year(self.year)
        world.set_map(lab_map())
        world.define_kind(KindDef("avatar"))
        world.define_kind(KindDef("box", blocking=True))
        world.define_need(NeedDef("energia", 100, {"asleep": 12}, role="energy"))
        world.add_avatar(AvatarDef("ana", SCRIPT))

    def rules_file(self) -> Path | None:
        return None


def _core(cartridge: Sol) -> KernelCore:
    core = KernelCore(
        build_world("sol", {"sol": cartridge}), WorldConfig("sol-01", 7, START), (), "test"
    )
    core.start()
    core.step()  # o tick 0: a primeira fase do dia
    return core


def _facts(core: KernelCore, event: str) -> list[dict[str, Any]]:
    return [dict(f.data) for f in core.drain() if f.type == f"campsverso.{event}.v1"]


def test_a_fase_traz_a_data_e_a_estacao_e_a_estacao_troca_no_dia_8() -> None:
    core = _core(Sol())
    (first, *_) = _facts(core, "world.clock.phase_changed")
    assert first == {"phase": "amanhecer", "day": 1, "date": "2026-09-22", "season": "primavera"}
    core.advance(7 * DAY, jump=True)
    facts = core.drain()
    (changed,) = [dict(f.data) for f in facts if f.type.endswith("season_changed.v1")]
    assert changed == {
        "day": 8,
        "date": "2026-12-22",
        "season": "verao",
        "previous_season": "primavera",
    }
    dawns = [
        dict(f.data)
        for f in facts
        if f.type.endswith("phase_changed.v1") and f.data["phase"] == "amanhecer"
    ]
    assert dawns[-1] == {"phase": "amanhecer", "day": 8, "date": "2026-12-22", "season": "verao"}
    assert core.world.season(8) == "verao"
    assert core.world.date(15) == "2027-03-23"


def test_sem_ano_o_relogio_fica_como_antes() -> None:
    core = _core(Sol(year=None))
    (first, *_) = _facts(core, "world.clock.phase_changed")
    assert first == {"phase": "amanhecer", "day": 1}
    core.advance(8 * DAY, jump=True)
    assert not [f for f in core.drain() if f.type.endswith("season_changed.v1")]
    assert core.world.season(3) is None


@pytest.mark.parametrize(
    ("year", "message"),
    [
        (YearDef(28, "09-22", ()), "estações"),
        (YearDef(2, "09-22", (("a", "01-01"), ("b", "02-01"), ("c", "03-01"))), "estações"),
        (YearDef(28, "09-22", (("a", "01-01"), ("a", "06-01"))), "repetida"),
        (YearDef(28, "13-01", (("a", "01-01"),)), "inválida"),
    ],
)
def test_ano_mal_declarado_e_erro_de_carga(year: YearDef, message: str) -> None:
    with pytest.raises(DefinitionError, match=message):
        build_world("sol", {"sol": Sol(year=year)})
