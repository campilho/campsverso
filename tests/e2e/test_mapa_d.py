"""O mapa d da Morada do Sol (ADR-0074, decisão 22): saber vale.

O d é o mapa do M21, que ninguém viu antes da rodada, e o fazendeiro-script 3, que aprende, nunca
roda nele num teste. As réguas que não aprendem, sim: num ano, o oráculo (que sabe as regras)
passa o script 3 fixo (que não sabe e não aprende) pelo que a receita promete, e a fração do valor
de saber capturada tem um denominador de verdade. Em processo, no modo máximo, uns 40 s.
"""

from collections.abc import Mapping
from typing import Any, cast

from campsverso_testkit.pipeline import Pipeline
from campsverso_tools.map_variants import recipes
from campsverso_tools.metrics import Report, compute

SEED = 20261022  # a do mundo farm-morada-do-sol-04, a mesma dos outros três
YEAR = 28


async def _year(script: str) -> Report:
    pipeline = Pipeline(
        SEED, controller="script", cartridge="farm_morada_do_sol", script=script, map_variant="d"
    )
    await pipeline.start()
    await pipeline.run_days(YEAR)
    return compute(pipeline.envelopes)


def _harvests(report: Report) -> int:
    return sum(report.totals()["harvests"].values())


async def test_no_mapa_d_saber_vale() -> None:
    promise = cast(Mapping[str, Any], recipes()["d"]["promete"])["saber_vale"]
    knows, fixed = await _year("oracle"), await _year("farmer3-fixo")
    assert knows.totals()["coins_end"] - fixed.totals()["coins_end"] >= int(promise["moedas"])
    assert _harvests(knows) - _harvests(fixed) >= int(promise["colheitas"])
