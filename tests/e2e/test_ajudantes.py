"""Os ajudantes no ciclo inteiro (ADR-0072): kernel, percepção, o script do Camps e um runner por
ajudante, como o processo `helpers`. O contrato entra direto no mundo (a ação de contratar tem os
testes dela no cenário); aqui se vê o ajudante chegar, obedecer à ordem e ir embora. As ordens que
dependem do que o Camps faz na fazenda (plantar, regar, colher) têm testes de unidade no script."""

from typing import Any

from campsverso_testkit.pipeline import DAY, Pipeline

MORADA = "farm_morada_do_sol"
SHIFT = 12 * 60  # das 06:00 às 18:00


async def _hired(helper: str, days: int, **order: Any) -> Pipeline:
    """A Morada do Sol com um ajudante contratado desde a manhã seguinte, com a ordem dada."""
    pipeline = Pipeline(cartridge=MORADA)
    await pipeline.start()
    world = pipeline.core.world
    first = world.day + 1
    world.set_attributes(
        helper,
        visible={"patrao": "camps", "dias": days, "ordem": "cuidar", **order},
        hidden={"primeiro_dia": first, "ultimo_dia": first + days - 1},
    )
    return pipeline


def _done(pipeline: Pipeline, avatar: str) -> list[str]:
    return [
        a["action"] for a in pipeline.of_type("action.completed.v1") if a["avatar_id"] == avatar
    ]


async def test_o_ajudante_chega_cuida_e_vai_embora_ate_o_fim_do_contrato() -> None:
    pipeline = await _hired("dita", 2)
    await pipeline.run_days(3)
    entered = [e for e in pipeline.of_type("avatar.entered.v1") if e["avatar_id"] == "dita"]
    left = [e for e in pipeline.of_type("avatar.left.v1") if e["avatar_id"] == "dita"]
    assert [e["reason"] for e in entered] == ["work_day", "work_day"]
    assert [e["reason"] for e in left] == ["end_of_day", "end_of_day"]
    (ended,) = pipeline.of_type("economy.labor.ended.v1")
    assert (ended["helper"], ended["employer"]) == ("dita", "camps")
    proposals = pipeline.of_type("cmd.action.propose.v1")
    mine = [p for p in proposals if p["avatar_id"] == "dita"]
    assert mine
    assert all(p["action"] != "go_home" for p in mine)
    others = {p["avatar_id"] for p in proposals} - {"camps", "dita"}
    assert others == set()  # quem não foi contratado não sai de casa


async def test_a_ordem_de_cavar_faz_os_canteiros_pedidos_e_para() -> None:
    pipeline = await _hired("ze-graudo", 1, ordem="cavar", ordem_n=2, ordem_x=33, ordem_y=36)
    await pipeline.run_until(DAY + SHIFT)
    assert _done(pipeline, "ze-graudo").count("dig") == 2


async def test_a_ordem_de_vender_paga_o_patrao() -> None:
    pipeline = await _hired("nina", 1, ordem="vender", ordem_item="rabanete")
    world = pipeline.core.world
    world.create_item("rabanete", 3, "chest", "test")
    await pipeline.run_until(DAY + SHIFT)
    assert "sell" in _done(pipeline, "nina")
    assert world.items("nina").get("moeda", 0) == 0  # a moeda foi para o Camps


async def test_parar_so_espera() -> None:
    pipeline = await _hired("seu-bento", 1, ordem="parar")
    await pipeline.run_until(DAY + SHIFT)
    mine = [p for p in pipeline.of_type("cmd.action.propose.v1") if p["avatar_id"] == "seu-bento"]
    assert mine
    assert {p["action"] for p in mine} == {"wait"}
