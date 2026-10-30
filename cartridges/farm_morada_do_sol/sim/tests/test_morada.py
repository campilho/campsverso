"""A Fazenda Morada do Sol (bíblia 3; ADR-0067): o mapa maior, o ano com estações, os canteiros
que voltam a ser grama, o espantalho, os corvos (R-002) e a fadiga do solo (R-003), no mundo real.
A Boa Vista e a fazenda 1 continuam cobertas pelos testes delas."""

from campsverso_cartridge_api import Position, SpawnDef
from campsverso_farm_sim.config import season_factor
from campsverso_testkit.farm import Farmer, make_core, of_type

DAY = 1440


def _farmer(*, hidden_rules: bool = True) -> Farmer:
    core = make_core(cartridge="farm_morada_do_sol", river_bonus=hidden_rules)
    core.start()
    farmer = Farmer(core)
    farmer.run(1)
    return farmer


def _morning(farmer: Farmer, days: int = 1) -> None:
    """Passa por `days` viradas das 06:00."""
    for _ in range(days):
        farmer.advance(DAY - farmer.core.tick % DAY + 1)


def _ripe(farmer: Farmer, plot_id: str, x: int, y: int, crop: str = "milho") -> None:
    """Um canteiro maduro posto por fora das ações."""
    world = farmer.core.world
    world.spawn(SpawnDef(plot_id, "plot", position=Position(x, y)))
    world.set_attributes(plot_id, visible={"crop": crop, "stage": "madura"})
    farmer.core.drain()


def test_estado_inicial_da_morada_do_sol() -> None:
    core = _farmer().core
    grid = core.definition.grid
    assert (grid.width, grid.height) == (64, 40)
    assert core.definition.perception_radius == 12
    world = core.world
    assert (world.date(1), world.season(1)) == ("2026-09-22", "primavera")
    assert world.season(8) == "verao"
    assert dict(world.items("camps")) == {"moeda": 100, "semente_rabanete": 10}
    assert world.entity("spade").container_id == "camps"
    stock = str(world.entity("kiosk").attributes["estoque_hoje"]).split(", ")
    assert {"semente_milho", "semente_mandioca", "semente_couve", "espantalho"} <= set(stock)
    plant = next(a for a in core.definition.affordances if a.action == "plant")
    crops = set(plant.params[0].choices)
    assert {"milho", "melancia", "mandioca", "couve", "tomate", "alho", "rabanete"} <= crops


def test_o_menu_diz_o_custo_o_horario_e_o_preco() -> None:
    # O menu de quem joga (M21): o custo pela tabela das três camadas, a nota com o horário dos
    # dados e o preço de tabela de cada escolha; o de agora o quiosque e a caixa mostram.
    by = {(a.action, a.label): a for a in _farmer().core.definition.affordances}
    dig = by[("dig", "Cavar um canteiro aqui")]
    assert dig.cost == (2.0, 15)  # a energia da Morada (M21)
    buy = by[("buy", "Comprar")]
    assert buy.note == "aberto das 08:00 às 18:00"
    item = buy.params[0]
    prices = dict(item.prices)
    assert (prices["semente_rabanete"], prices["espantalho"], prices["plow"]) == (10.0, 60.0, 300.0)
    assert (item.price_attribute, item.stock_attribute) == ("preco_", "estoque_hoje")
    sell = by[("sell", "Vender")]
    assert sell.note == "o comprador leva às 22:00 e paga às 06:00"
    assert dict(sell.params[0].prices)["rabanete"] == 25.0  # o preço de venda da tabela
    # O que precisa valer, as sementes que se tem e a ficha de cada ajudante.
    harvest = by[("harvest", "Colher")]
    assert [(r.attribute, r.values) for r in harvest.requires] == [("stage", ("madura",))]
    fertilize = by[("fertilize", "Adubar")]
    assert fertilize.requires[0].item == "adubo"
    assert by[("plant", "Plantar")].params[0].held_prefix == "semente_"
    fair = by[("sell", "Vender na feira")]
    assert fair.note is not None
    assert "a cada 7 dias, das 06:00 às 14:00" in fair.note
    assert "{target.proxima_feira}" in fair.note  # a tela resolve pelo atributo da barraca
    notes = dict(by[("hire_helper", "Contratar ajudante")].params[0].option_notes)
    assert notes["ze-graudo"].startswith("Zé Graúdo, o carregador: carrega o dobro")


def test_a_fome_da_morada_sobe_2_por_hora_acordado() -> None:
    # A calibragem do M19 (ADR-0070): o cenário troca o ritmo do gênero (3 por hora acordado).
    fome = _farmer().core.definition.needs["fome"]
    assert dict(fome.rates_per_hour) == {"awake": 2.0, "asleep": 1}
    assert fome.initial == 0


def test_o_canteiro_vazio_volta_a_ser_grama_e_o_numero_nao_se_repete() -> None:
    farmer = _farmer()
    farmer.walk(10, 19)
    (first,) = of_type(farmer.do("dig", target={"x": 11, "y": 19}), "world.entity.spawned")
    (second,) = of_type(farmer.do("dig", target={"x": 11, "y": 20}), "world.entity.spawned")
    assert (first["entity_id"], second["entity_id"]) == ("plot-001", "plot-002")
    farmer.do("plant", target="plot-002", crop="rabanete")
    _morning(farmer, 2)
    assert {e.entity_id for e in farmer.core.world.entities("plot")} == {"plot-001", "plot-002"}
    _morning(farmer)  # a terceira manhã vazia: o plot-001 volta a ser grama; o plantado fica
    (gone,) = of_type(farmer.facts, "world.entity.despawned")
    assert gone == {
        "entity_id": "plot-001",
        "kind": "plot",
        "position": {"x": 11, "y": 19},
        "reason": "reverted_to_grass",
    }
    assert [e.entity_id for e in farmer.core.world.entities("plot")] == ["plot-002"]
    farmer.walk(10, 19)
    (third,) = of_type(farmer.do("dig", target={"x": 11, "y": 19}), "world.entity.spawned")
    assert third["entity_id"] == "plot-003"  # o 001 não volta


def test_a_estacao_da_o_ritmo_e_o_quiosque_segue_a_estacao() -> None:
    farmer = _farmer()
    view = farmer.core.world
    assert (season_factor(view, "milho"), season_factor(view, "couve")) == (1.0, 0.5)
    assert season_factor(view, "rabanete") == 1.0
    farmer.advance(21 * DAY)  # o dia 22: inverno
    assert view.season(view.day) == "inverno"
    assert (season_factor(view, "milho"), season_factor(view, "couve")) == (0.0, 1.0)
    stock = str(view.entity("kiosk").attributes["estoque_hoje"]).split(", ")
    assert "semente_milho" not in stock  # parado no inverno: não se vende
    assert "semente_melancia" not in stock


def test_o_milho_parado_no_inverno_nao_cresce_mas_nao_morre() -> None:
    farmer = _farmer(hidden_rules=False)
    farmer.advance(21 * DAY)  # o inverno
    farmer.core.world.create_item("semente_milho", 1, "camps", "test")
    farmer.walk(10, 19)
    farmer.do("dig", target={"x": 11, "y": 19})
    farmer.do("plant", target="plot-001", crop="milho")
    for _ in range(3):
        farmer.do("water", target="plot-001")
        _morning(farmer)
    plot = farmer.core.world.entity("plot-001")
    assert (plot.attributes["stage"], plot.hidden["growth_points"]) == ("semente", 0.0)


def test_corvos_comem_longe_da_casa_e_o_espantalho_protege() -> None:
    farmer = _farmer()
    for n in range(8):  # longe da porta (6,18): na estrada da várzea
        _ripe(farmer, f"plot-l{n}", 40 + n, 23)
    _ripe(farmer, "plot-perto", 12, 19)  # perto da casa: nunca
    _morning(farmer)
    eaten = of_type(farmer.facts, "farm.crop.eaten")
    assert eaten
    assert {e["by"] for e in eaten} == {"corvo"}
    assert "plot-perto" not in {e["plot_id"] for e in eaten}
    for e in eaten:  # o canteiro fica vazio
        assert farmer.core.world.entity(e["plot_id"]).attributes["crop"] is None
    guarded = _farmer()
    for n in range(8):
        _ripe(guarded, f"plot-l{n}", 40 + n, 23)
    guarded.core.world.spawn(SpawnDef("scarecrow-01", "scarecrow", position=Position(44, 24)))
    _morning(guarded)
    assert not of_type(guarded.facts, "farm.crop.eaten")


def test_fincar_o_espantalho_ao_lado() -> None:
    farmer = _farmer()
    farmer.core.world.create_item("espantalho", 1, "camps", "test")
    farmer.walk(10, 19)
    (spawned,) = of_type(
        farmer.do("place", item="espantalho", target={"x": 11, "y": 19}), "world.entity.spawned"
    )
    assert (spawned["entity_id"], spawned["kind"]) == ("scarecrow-01", "scarecrow")
    assert dict(farmer.core.world.items("camps")).get("espantalho") is None
    (rejected,) = of_type(farmer.do("place", item="espantalho"), "action.rejected")
    assert rejected["reason"] == "missing_item"


def test_repetir_a_cultura_no_mesmo_canteiro_cresce_mais_devagar() -> None:
    farmer = _farmer()
    world = farmer.core.world
    world.create_item("semente_rabanete", 2, "camps", "test")
    farmer.walk(10, 19)
    farmer.do("dig", target={"x": 11, "y": 19})
    farmer.do("dig", target={"x": 11, "y": 20})
    world.set_attributes("plot-001", hidden={"last_crop": "rabanete"})  # já teve rabanete
    world.set_attributes("plot-002", hidden={"last_crop": "milho"})  # teve outra cultura
    for plot in ("plot-001", "plot-002"):
        farmer.do("plant", target=plot, crop="rabanete")
        farmer.do("water", target=plot)
    _morning(farmer)
    tired, rotated = (world.entity(p).hidden["growth_points"] for p in ("plot-001", "plot-002"))
    assert (tired, rotated) == (0.6, 1.0)
