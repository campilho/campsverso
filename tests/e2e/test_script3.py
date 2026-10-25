"""O fazendeiro-script 3 e o oráculo um ano inteiro na Morada do Sol (ADR-0070, decisão 15).

Em processo, no modo máximo, uns 15 s por ano. O script 3 não sabe nenhuma regra oculta e tem de
descobrir pelo caderno de campo; o oráculo é o mesmo código sabendo as regras; o script 2 é a
régua cega. Com as regras do arquivo desligadas (`river_bonus=False`: a água e a fadiga), o
script 3 não pode "descobrir" o que não existe.
"""

from collections.abc import Mapping

from campsverso_farm_script import controller3
from campsverso_farm_script.knowledge import Effect
from campsverso_testkit.pipeline import Pipeline
from campsverso_tools.metrics import Report, compute

SEED = 20261022  # a do mundo farm-morada-do-sol-01
YEAR = 28
_BLIND: list[Report] = []  # o ano do script 2: o mesmo nos três mapas (ele nunca sai do poço)


async def _year(script: str, variant: str | None, *, rules: bool = True) -> Report:
    pipeline = Pipeline(
        SEED,
        controller="script",
        cartridge="farm_morada_do_sol",
        script=script,
        map_variant=variant,
        river_bonus=rules,
    )
    await pipeline.start()
    await pipeline.run_days(YEAR)
    return compute(pipeline.envelopes)


async def _blind() -> Report:
    if not _BLIND:
        _BLIND.append(await _year("farmer2", "c"))
    return _BLIND[0]


def _effects() -> Mapping[str, Effect]:
    return {e.name: e for e in controller3.book.beliefs.effects()}


def _hungry(report: Report) -> int:
    return sum(1 for day in report.days if day.hunger_peak >= 100)


def _harvests(report: Report) -> int:
    return sum(report.totals()["harvests"].values())


async def test_o_script_3_aprende_a_fadiga_e_a_agua_e_colhe_mais_que_o_script_2() -> None:
    # Nos mapas a e b; no c (as lagoas longe) ele ainda passa fome, e o ano dele fica para a
    # rodada de verificação (o plano do M19, §9).
    blind = await _blind()
    for variant in (None, "b"):
        report = await _year("farmer3", variant)
        effects = _effects()
        assert effects["repetida"].high < 0.9, variant  # repetir a cultura atrasa: aprendeu
        assert max(effects["agua<=2"].low, effects["agua<=4"].low) > 1.0, variant  # a água ajuda
        assert _harvests(report) > _harvests(blind), variant
        assert _hungry(report) < _hungry(blind), variant


async def test_sem_as_regras_o_script_3_nao_descobre_o_que_nao_existe() -> None:
    await _year("farmer3", None, rules=False)
    effects = _effects()
    for name in ("agua<=2", "agua<=4", "agua<=8"):
        effect = effects[name]
        assert effect.low <= 1.0 <= effect.high, (name, effect)
    assert effects["repetida"].low > 0.9  # sem a fadiga, repetir não atrasa


async def test_o_oraculo_atravessa_o_ano_das_lagoas_sem_quase_passar_fome() -> None:
    blind = await _blind()
    report = await _year("oracle", "c")
    assert _hungry(report) <= 5 < _hungry(blind)
    assert report.totals()["coins_end"] > blind.totals()["coins_end"]
