"""Ações e sistemas do gênero farm, exercitados no cenário real (bíblia §6 a §10; ADR-0039)."""

import pytest

from campsverso_kernel.facts import Fact
from campsverso_kernel.world import to_units
from campsverso_testkit.farm import Farmer, make_core, of_type


def _farmer(*, river_bonus: bool = True, seed: int = 20261010) -> Farmer:
    core = make_core(seed, river_bonus=river_bonus)
    core.start()
    farmer = Farmer(core)
    farmer.run(1)
    return farmer


def _last_rejection(farmer: Farmer) -> str:
    return str(of_type(farmer.facts, "action.rejected")[-1]["reason"])


def test_estado_inicial_da_biblia() -> None:
    world = _farmer().core.world
    assert dict(world.items("camps")) == {"moeda": 100, "semente_rabanete": 10}
    assert dict(world.items("chest")) == {"rabanete": 5}
    assert world.entity("watering-can").attributes["charges"] == 10
    assert world.entity("kiosk").attributes["open"] is False


def test_plantar_regar_e_os_custos_de_energia() -> None:
    farmer = _farmer()
    farmer.walk(23, 9)  # ao lado de plot-e-01 (24,9) e plot-e-05 (24,10)
    planted = farmer.do("plant", target="plot-e-01", crop="rabanete")
    changes = of_type(planted, "world.entity.state_changed")[0]["changes"]
    assert changes["crop"] == "rabanete"
    assert changes["stage"] == "semente"
    farmer.do("water", target="plot-e-01")
    world = farmer.core.world
    assert world.entity("plot-e-01").attributes["watered_today"] is True
    assert world.entity("watering-can").attributes["charges"] == 9
    assert world.need("camps", "energia") == 96  # plantar 2 + regar 2


def test_fome_alta_dobra_o_custo_de_energia() -> None:
    farmer = _farmer()
    farmer.walk(23, 9)
    farmer.do("plant", target="plot-e-01", crop="rabanete")
    farmer.core.world.set_need_units("camps", "fome", to_units(85))
    before = farmer.core.world.need("camps", "energia")
    farmer.do("water", target="plot-e-01")
    assert farmer.core.world.need("camps", "energia") == before - 4


def test_recusas_com_motivo_legivel() -> None:
    farmer = _farmer()
    farmer.do("plant", target="plot-e-01", crop="rabanete")
    assert _last_rejection(farmer) == "not_adjacent"
    farmer.walk(23, 9)
    farmer.do("water", target="plot-e-01")
    assert _last_rejection(farmer) == "no_plant"
    farmer.do("harvest", target="plot-e-01")
    assert _last_rejection(farmer) == "not_ripe"
    farmer.do("plant", target="plot-e-01", crop="milho")
    assert _last_rejection(farmer) == "invalid_params"
    farmer.do("eat", item="moeda")
    assert _last_rejection(farmer) == "not_edible"
    farmer.do("sleep", target="bed")
    assert _last_rejection(farmer) == "not_adjacent"


def test_quiosque_abre_as_oito_e_vende_sementes() -> None:
    farmer = _farmer()
    farmer.walk(17, 15)  # ao lado do quiosque (16,15)
    farmer.do("buy", item="semente_batata", qty=1)
    assert _last_rejection(farmer) == "closed"
    farmer.until("08:00")
    farmer.run(1)
    farmer.do("buy", item="semente_batata", qty=2)
    world = farmer.core.world
    assert world.items("camps")["moeda"] == 60
    assert world.items("camps")["semente_batata"] == 2
    farmer.do("buy", item="semente_abobora", qty=2)
    assert _last_rejection(farmer) == "insufficient_funds"


def test_comer_do_bau_reduz_a_fome() -> None:
    farmer = _farmer()
    farmer.walk(7, 3)  # ao lado do baú (7,4)
    farmer.do("withdraw", item="rabanete", qty=2)
    farmer.core.world.set_need_units("camps", "fome", to_units(60))
    farmer.do("eat", item="rabanete")
    assert farmer.core.world.need("camps", "fome") == 35.55  # a fome sobe nos 11 ticks da refeição
    assert farmer.core.world.items("camps")["rabanete"] == 1
    assert farmer.core.world.items("chest")["rabanete"] == 3


def test_venda_recolhida_as_22_e_paga_as_6() -> None:
    farmer = _farmer()
    farmer.walk(7, 3)
    farmer.do("withdraw", item="rabanete", qty=2)
    farmer.walk(8, 5)  # ao lado da caixa de vendas (8,6)
    farmer.do("sell", item="rabanete", qty=2)
    farmer.until("22:00")
    farmer.run(1)
    assert of_type(farmer.facts, "world.item.consumed")[-1]["reason"] == "buyer_collect"
    farmer.until("06:00")
    farmer.run(1)
    (paid,) = of_type(farmer.facts, "farm.buyer.paid")
    assert paid["total"] == 50
    assert paid["container_id"] == "camps"
    assert farmer.core.world.items("camps")["moeda"] == 150


def test_a_noite_dorme_na_cama_ate_as_6() -> None:
    farmer = _farmer()
    farmer.walk(4, 3)  # ao lado da cama (3,3)
    farmer.until("21:00")
    farmer.core.world.set_need_units("camps", "energia", to_units(40))
    farmer.do("sleep", target="bed")
    world = farmer.core.world
    assert world.is_asleep("camps")
    farmer.until("06:00")
    farmer.run(1)
    (ended,) = of_type(farmer.facts, "avatar.sleep.ended.v2")
    assert (ended["cause"], ended["bed_id"]) == ("voluntary", "bed")
    assert ended["energy"] == 100.0  # 40 + 12,5/h por 9 h, no teto
    assert of_type(farmer.facts, "avatar.fainted") == []


def _nap(farmer: Farmer, energy: float, **params: str) -> tuple[int, Fact]:
    """Cochila agora com a energia dada; devolve quantos ticks durou e o fim do sono."""
    farmer.core.world.set_need_units("camps", "energia", to_units(energy))
    farmer.do("sleep", **params)
    (started,) = [f for f in farmer.facts if f.type.endswith("avatar.sleep.started.v2")]
    while farmer.core.world.is_asleep("camps"):
        farmer.run(1)
    (ended,) = [f for f in farmer.facts if f.type.endswith("avatar.sleep.ended.v2")]
    return ended.tick - started.tick, ended


def test_cochilo_de_dia_na_cama_acorda_com_a_energia_cheia() -> None:
    """De dia, dormir é cochilo: acaba quando a energia enche (ADR-0049)."""
    farmer = _farmer()
    farmer.walk(4, 3)
    farmer.until("10:00")
    ticks, ended = _nap(farmer, 30, target="bed")
    assert ticks == 336  # 70 pontos a 12,5/h: 5 h 36 min
    assert ended.data["energy"] == 100.0


def test_cochilo_no_chao_e_mais_longo() -> None:
    farmer = _farmer()
    farmer.walk(12, 9)
    ticks, ended = _nap(farmer, 80)
    assert ticks == 240  # 20 pontos a 5/h: 4 h
    assert ended.data["energy"] == 100.0


def test_cochilo_no_fim_da_tarde_vai_no_maximo_ate_as_6() -> None:
    farmer = _farmer()
    farmer.walk(12, 9)
    farmer.until("19:00")
    ticks, ended = _nap(farmer, 10)  # encher levaria 18 h no chão
    assert ended.tick % 1440 == 0  # acordou às 06:00, a virada do dia agrícola
    assert ended.data["energy"] == pytest.approx(10 + 5 * ticks / 60)
    assert of_type(farmer.facts, "avatar.fainted") == []


def test_com_energia_cheia_nao_ha_cochilo() -> None:
    farmer = _farmer()
    farmer.do("sleep")
    assert _last_rejection(farmer) == "not_tired"
    assert not farmer.core.world.is_asleep("camps")


def test_dormir_no_chao_recupera_menos() -> None:
    """Sem alvo, dorme onde está, mesmo ao lado da cama: 5/h em vez de 12,5/h (ADR-0041)."""
    farmer = _farmer()
    farmer.walk(12, 9)  # no meio da fazenda, longe da cama
    farmer.until("21:00")
    farmer.core.world.set_need_units("camps", "energia", to_units(40))
    farmer.do("sleep")
    (started,) = of_type(farmer.facts, "avatar.sleep.started.v2")
    assert "bed_id" not in started
    assert started["position"] == {"x": 12, "y": 9}
    farmer.until("06:00")
    farmer.run(1)
    (ended,) = of_type(farmer.facts, "avatar.sleep.ended.v2")
    assert ended["energy"] == pytest.approx(40 + 5 * 539 / 60)  # 5/h das 21:01 às 06:00


def test_dormir_exige_cama_de_verdade_e_ao_lado() -> None:
    farmer = _farmer()
    farmer.walk(12, 9)
    farmer.until("21:00")
    farmer.do("sleep", target="chest")
    assert _last_rejection(farmer) == "invalid_params"
    farmer.do("sleep", target="bed")
    assert _last_rejection(farmer) == "not_adjacent"


def test_quem_fica_acordado_desmaia_as_2_e_acorda_com_50() -> None:
    farmer = _farmer()
    farmer.until("02:00")
    farmer.run(1)
    (fainted,) = of_type(farmer.facts, "avatar.fainted")
    assert fainted["reason"] == "late_night"
    farmer.until("06:00")
    farmer.run(1)
    (ended,) = of_type(farmer.facts, "avatar.sleep.ended.v2")
    assert (ended["cause"], ended["energy"]) == ("faint", 50.0)


def test_energia_zero_desmaia_na_hora() -> None:
    farmer = _farmer()
    farmer.walk(17, 9)  # ao lado do poço (17,10)
    farmer.core.world.set_need_units("camps", "energia", to_units(1))
    farmer.do("refill")  # custa 1
    (fainted,) = of_type(farmer.facts, "avatar.fainted")
    assert fainted["reason"] == "exhausted"


def _grow(river_bonus: bool) -> Farmer:
    """Planta e rega um canteiro no leste (perto do rio) e um no oeste, todo dia."""
    farmer = _farmer(river_bonus=river_bonus)
    for _ in range(3):
        farmer.walk(23, 9)
        for plot in ("plot-e-01",):
            if farmer.core.world.entity(plot).attributes["crop"] is None:
                farmer.do("plant", target=plot, crop="rabanete")
            if farmer.core.world.entity(plot).attributes["stage"] != "madura":
                farmer.do("water", target=plot)
        farmer.walk(12, 9)
        if farmer.core.world.entity("plot-w-04").attributes["crop"] is None:
            farmer.do("plant", target="plot-w-04", crop="rabanete")
        if farmer.core.world.entity("plot-w-04").attributes["stage"] != "madura":
            farmer.do("water", target="plot-w-04")
        farmer.walk(17, 9)
        farmer.do("refill")
        farmer.until("06:00")
        farmer.run(1)
    return farmer


def test_regra_oculta_faz_o_leste_amadurecer_antes() -> None:
    """Prévia do A11: com a R-001, o rabanete do leste amadurece em 2 dias; o do oeste, em 3."""
    farmer = _grow(river_bonus=True)
    matured = {m["plot_id"]: m["days"] for m in of_type(farmer.facts, "farm.crop.matured")}
    assert matured == {"plot-e-01": 2, "plot-w-04": 3}
    effects = of_type(farmer.facts, "rules.effect_applied")
    assert {e["entity_id"] for e in effects} == {"plot-e-01"}


def test_sem_a_regra_oculta_os_dois_lados_levam_3_dias() -> None:
    farmer = _grow(river_bonus=False)
    matured = {m["plot_id"]: m["days"] for m in of_type(farmer.facts, "farm.crop.matured")}
    assert matured == {"plot-e-01": 3, "plot-w-04": 3}
    assert of_type(farmer.facts, "rules.effect_applied") == []


def test_colheita_explica_a_regra_oculta_so_em_evento_internal() -> None:
    farmer = _grow(river_bonus=True)
    farmer.walk(23, 9)
    harvested = farmer.do("harvest", target="plot-e-01")
    (explained,) = of_type(harvested, "action.effects_explained")
    assert explained["rules_applied"][0]["rule"] == "river_proximity_bonus"
    assert explained["rules_applied"][0]["hidden"] is True
    assert farmer.core.world.items("camps")["rabanete"] == 1


def test_planta_sem_agua_por_duas_viradas_murcha() -> None:
    farmer = _farmer()
    farmer.walk(23, 9)
    farmer.do("plant", target="plot-e-01", crop="rabanete")
    for _ in range(2):
        farmer.until("06:00")
        farmer.run(1)
    weather = farmer.core.world.weather_by_day
    if any(weather.get(day) == "rain" for day in (1, 2)):
        return  # a chuva rega sozinha; a seed fixa deste teste não traz chuva nesses dias
    (withered,) = of_type(farmer.facts, "farm.crop.withered")
    assert withered["dry_days"] == 2
    farmer.walk(23, 9)
    farmer.do("clear", target="plot-e-01")
    assert farmer.core.world.entity("plot-e-01").attributes["crop"] is None


def test_clima_sorteado_as_5_para_o_dia_seguinte_com_chuva_de_cerca_de_20_por_cento() -> None:
    farmer = _farmer()
    farmer.run(40 * 1440)
    days = farmer.core.world.weather_by_day
    assert sorted(days) == list(range(1, 42))
    rain = sum(1 for c in days.values() if c == "rain") / len(days)
    assert 0.05 < rain < 0.40
