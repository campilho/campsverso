"""Ações e sistemas do gênero farm, exercitados no cenário real (bíblia §6 a §10; ADR-0039)."""

import re

import pytest

from campsverso_contracts import CONTRACT_TYPES
from campsverso_kernel.facts import Fact
from campsverso_kernel.world import to_units
from campsverso_testkit.farm import SCRIPT_ID, Farmer, make_core, of_type


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
    # O grupo vem do mapa (ADR-0054): as métricas separam oeste e leste por ele.
    assert world.entity("plot-w-01").attributes["group"] == "oeste"
    assert world.entity("plot-e-08").attributes["group"] == "leste"


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
    # Plantar 2 + regar 2, e 1/60 por tick acordado desde o começo (ADR-0056).
    assert world.need("camps", "energia") == pytest.approx(96 - farmer.core.tick / 60)


def test_plantar_durante_um_plantio_e_recusado_com_busy() -> None:
    """A partida de 12/out: o segundo plantio cancelava o primeiro. Agora é recusado (ADR-0052)."""
    farmer = _farmer()
    farmer.walk(23, 9)
    start = len(farmer.facts)

    def plant(n: int, target: str) -> None:
        farmer.core.submit(
            {
                "id": f"cmd-busy-{n}",
                "type": "campsverso.cmd.action.propose.v1",
                "controllerid": SCRIPT_ID,
                "data": {
                    "avatar_id": "camps",
                    "action": "plant",
                    "params": {"target": target, "crop": "rabanete"},
                },
            }
        )

    plant(1, "plot-e-01")
    farmer.run(1)
    plant(2, "plot-e-05")
    farmer.run(6)
    facts = farmer.facts[start:]
    (accepted,) = of_type(facts, "action.accepted")
    assert (accepted["params"]["target"], accepted["interrupt"]) == ("plot-e-01", "never")
    (rejected,) = of_type(facts, "action.rejected")
    assert rejected["reason"] == "busy"
    assert of_type(facts, "action.failed") == []
    assert farmer.core.world.entity("plot-e-01").attributes["crop"] == "rabanete"
    assert farmer.core.world.entity("plot-e-05").attributes["crop"] is None


def test_fome_alta_dobra_o_custo_de_energia() -> None:
    farmer = _farmer()
    farmer.walk(23, 9)
    farmer.do("plant", target="plot-e-01", crop="rabanete")
    farmer.core.world.set_need_units("camps", "fome", to_units(85))
    before, tick = farmer.core.world.need("camps", "energia"), farmer.core.tick
    farmer.do("water", target="plot-e-01")
    awake = (farmer.core.tick - tick) / 60  # 1/60 por tick acordado (ADR-0056)
    assert farmer.core.world.need("camps", "energia") == pytest.approx(before - 4 - awake)


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
    # 70 pontos a 12,5/h: 5 h 36 min, mais um minuto pelo 1/60 gasto acordado antes de deitar
    # (ADR-0056): o cochilo arredonda para cima, para acordar cheio.
    assert ticks == 337
    assert ended.data["energy"] == 100.0


def test_cochilo_no_chao_e_mais_longo() -> None:
    farmer = _farmer()
    farmer.walk(12, 9)
    ticks, ended = _nap(farmer, 80)
    assert ticks == 241  # 20 pontos a 5/h: 4 h, mais o minuto acordado antes de deitar (ADR-0056)
    assert ended.data["energy"] == 100.0


def test_cochilo_no_fim_da_tarde_vai_no_maximo_ate_as_6() -> None:
    farmer = _farmer()
    farmer.walk(12, 9)
    farmer.until("19:00")
    ticks, ended = _nap(farmer, 10)  # encher levaria 18 h no chão
    assert ended.tick % 1440 == 0  # acordou às 06:00, a virada do dia agrícola
    # 5/h dormindo, menos 1/60 por tick acordado antes de deitar (ADR-0056).
    assert ended.data["energy"] == pytest.approx(10 - 2 / 60 + 5 * ticks / 60)
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
    # 5/h das 21:01 às 06:00, menos 1/60 por tick acordado antes de deitar (ADR-0056).
    assert ended["energy"] == pytest.approx(40 - 2 / 60 + 5 * 539 / 60)


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


def test_ficar_acordado_custa_um_de_energia_por_hora() -> None:
    """ADR-0056: parado o dia inteiro deixa de ser de graça."""
    farmer = _farmer()
    before = farmer.core.world.need("camps", "energia")
    farmer.run(60)
    assert farmer.core.world.need("camps", "energia") == before - 1


def test_passar_fome_drena_energia_de_hora_em_hora_ate_comer() -> None:
    """ADR-0056: com a fome em 100, 4 de energia por hora acordado, sem morte."""
    farmer = _farmer()
    farmer.core.world.set_need_units("camps", "fome", to_units(100))
    farmer.until("07:05")  # o sistema de hora em hora rodou às 07:00
    awake = farmer.core.tick / 60  # 1 por hora acordado desde o começo (ADR-0056)
    assert farmer.core.world.need("camps", "energia") == pytest.approx(100 - awake - 4)
    farmer.core.world.set_need_units("camps", "fome", to_units(50))  # comeu
    farmer.until("08:05")
    awake = farmer.core.tick / 60
    assert farmer.core.world.need("camps", "energia") == pytest.approx(100 - awake - 4)
    assert not of_type(farmer.facts, "avatar.fainted")


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


# Os parâmetros que cada ação lê (bíblia §8; ações do gênero e do kernel).
ACTION_PARAMS: dict[str, set[str]] = {
    "plant": {"target", "crop"},
    "water": {"target"},
    "harvest": {"target"},
    "clear": {"target"},
    "refill": {"target"},
    "deposit": {"target", "item", "qty"},
    "withdraw": {"target", "item", "qty"},
    "sell": {"target", "item", "qty"},
    "buy": {"target", "item", "qty"},
    "sleep": {"target"},
    "eat": {"item"},
    "wait": {"ticks"},
}


def test_catalogo_de_acoes_bate_com_as_acoes_e_sai_no_session_started() -> None:
    """O menu de quem joga (ADR-0051) só cita ações que existem, com parâmetros que elas leem."""
    farmer = _farmer()
    definition = farmer.core.definition
    kinds = {e.kind for e in farmer.core.world.entities()}
    assert definition.affordances
    for a in definition.affordances:
        assert a.action in definition.actions or a.action in {"move", "wait"}
        names = {p.name for p in a.params} | ({"target"} if a.target else set[str]())
        assert names <= ACTION_PARAMS[a.action], a
        assert set(a.on) <= kinds | {"self"}, a
        for p in a.params:
            assert all(c in definition.items or c in section_crops(farmer) for c in p.choices), p
    (started,) = of_type(farmer.facts, "world.session.started")
    catalog = {(a["action"], a["label"]) for a in started["affordances"]}
    assert ("plant", "Plantar") in catalog
    assert ("sleep", "Dormir aqui") in catalog


def test_rotulos_da_linha_do_tempo_saem_no_session_started_e_citam_campos_do_evento() -> None:
    """Os rótulos (ADR-0068): cada campo entre chaves e cada filtro existem no payload do evento
    (o primeiro nível; `params` é livre)."""
    farmer = _farmer()
    (started,) = of_type(farmer.facts, "world.session.started")
    harvest = {
        "event": "campsverso.world.item.created.v1",
        "where": {"reason": "harvest"},
        "text": "{container_id} colheu {qty} {item}",
    }
    assert harvest in started["labels"]
    for label in started["labels"]:
        fields = set(CONTRACT_TYPES[label["event"]].payload.model_fields)
        cited = [*re.findall(r"\{([a-z0-9_.]+)\}", label["text"]), *label.get("where", {})]
        assert {c.split(".")[0] for c in cited} <= fields, label


def test_catalogo_de_metricas_sai_no_session_started() -> None:
    """As métricas da bíblia §13 (ADR-0054): colheitas agrupadas pelo `group` do canteiro."""
    farmer = _farmer()
    (started,) = of_type(farmer.facts, "world.session.started")
    metrics = {m["id"]: m for m in started["metrics"]}
    assert list(metrics) == ["colheitas", "moedas", "recusas", "murchas", "pico_fome", "desmaios"]
    assert metrics["colheitas"]["by"] == {"field": "params.target", "attribute": "group"}
    assert metrics["moedas"] == {
        "id": "moedas",
        "label": "Moedas no fim do dia",
        "kind": "item",
        "item": "moeda",
    }


def section_crops(farmer: Farmer) -> set[str]:
    return set(farmer.core.world.data("farm")["crops"])


def test_terreno_e_raio_saem_no_session_started() -> None:
    """ADR-0056: o terreno da fazenda com legenda, e o raio nulo (a propriedade inteira)."""
    farmer = _farmer()
    (started,) = of_type(farmer.facts, "world.session.started")
    rows, legend = started["map"]["rows"], started["map"]["legend"]
    assert len(rows) == 18
    assert all(len(row) == 32 for row in rows)
    assert legend["G"] == {"kind": "grass", "properties": {"passable": True, "water": False}}
    assert legend["R"]["properties"]["water"] is True
    assert set("".join(rows)) == set(legend)
    assert started["perception"] == {"radius": None}
