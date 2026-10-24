"""O tempo na fazenda sobre a biblioteca de clima (ADR-0069): o que cada condição faz com as plantas
e com o mercado. O sorteio é da `libs/climate`; aqui fica a fazenda.

O cenário liga o clima de mundo aberto com a seção `weather`:
- `forecast_at`: a hora em que sai o tempo de amanhã (sem ela, o tempo do dia sai na madrugada);
- `wet`: as condições que regam todas as plantas (a chuva e a tempestade);
- `storm.knock_down`: a chance de cada planta madura ser derrubada na manhã da tempestade;
- `drought`: a rega até `water_by`, ou a planta não cresce no dia, e o regador gasta
  `can_charges` cargas;
- `shock`: depois de uma das `conditions`, a referência das colheitas sobe `magnitude` por `days`.
"""

from collections.abc import Mapping
from typing import Any, cast

from campsverso_cartridge_api import SystemContext, WorldOps, WorldView
from campsverso_farm_sim.config import optional, section


def _weather(view: WorldView) -> Mapping[str, Any]:
    return section(view, "weather")


def wet(view: WorldView, day: int) -> bool:
    """O tempo do dia rega as plantas: a chuva, e o que mais o cenário disser (a tempestade)."""
    conditions = cast(list[str], _weather(view).get("wet") or ["rain"])
    return view.weather(day) in conditions


def drought(view: WorldView) -> Mapping[str, Any] | None:
    """As regras da seca, num dia de seca; nada nos outros dias e nos cenários sem seca."""
    rules = optional(view, "weather", "drought")
    return rules if rules is not None and view.weather(view.day) == "drought" else None


def can_cost(view: WorldView) -> int:
    """As cargas que uma rega gasta hoje: 1, ou mais na seca."""
    rules = drought(view)
    return 1 if rules is None else int(rules.get("can_charges", 1))


def knocked_down(view: WorldView) -> list[tuple[str, str]]:
    """Na manhã de um dia de tempestade: as plantas maduras (que dava para ter colhido ontem) que
    ela derruba, pelo RNG `storm`, em ordem de canteiro."""
    storm = cast(Mapping[str, Any] | None, _weather(view).get("storm"))
    if view.weather(view.day) != "storm" or storm is None:
        return []
    chance = float(storm["knock_down"])
    rng = view.rng("storm")
    fallen: list[tuple[str, str]] = []
    for plot in sorted(view.entities("plot"), key=lambda p: p.entity_id):
        if plot.attributes.get("stage") == "madura" and rng.random() < chance:
            fallen.append((plot.entity_id, str(plot.attributes["crop"])))
    return fallen


def market_shock(view: WorldView, ops: WorldOps) -> None:
    """Depois de uma tempestade ou de uma seca, a referência das colheitas sobe por alguns dias."""
    shock = cast(Mapping[str, Any] | None, _weather(view).get("shock"))
    if shock is None or view.weather(view.day) not in cast(list[str], shock["conditions"]):
        return
    until = view.day + int(shock["days"]) - 1
    for box in view.entities("sell_box"):
        hidden = {"shock": float(shock["magnitude"]), "shock_until": until}
        ops.set_attributes(box.entity_id, hidden=hidden)


def drought_noon(ctx: SystemContext, ops: WorldOps) -> None:
    """Na hora limite da seca: a planta que ainda não foi regada hoje não cresce amanhã, mesmo que
    seja regada à tarde."""
    view = ctx.view
    if drought(view) is None:
        return
    for plot in view.entities("plot"):
        has_plant = plot.attributes.get("crop") is not None
        if has_plant and not plot.attributes.get("watered_today"):
            ops.set_attributes(plot.entity_id, hidden={"parched": True})
