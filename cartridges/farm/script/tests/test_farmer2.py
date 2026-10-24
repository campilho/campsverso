"""Fazendeiro-script 2 (bíblia 2, §11): as prioridades da Fazenda Boa Vista, em fotos à mão."""

from typing import Any

from campsverso_farm_script import Farmer2Script

SCRIPT = Farmer2Script.load()
ROWS = ["GGGGGGGG", "GGGPGGGG", "GGGGWGGG", "GGGGGGGG"]  # G grama, P caminho, W o poço (não pisa)
LEGEND = {
    "G": {"kind": "grass", "properties": {"passable": True, "water": False}},
    "P": {"kind": "path", "properties": {"passable": True, "water": False}},
    "W": {"kind": "well", "properties": {"passable": False, "water": False}},
}


def thing(eid: str, kind: str, x: int, y: int, **attrs: Any) -> dict[str, Any]:
    return {"entity_id": eid, "kind": kind, "position": {"x": x, "y": y}, "attributes": attrs}


def plot(pid: str, x: int, y: int, **attrs: Any) -> dict[str, Any]:
    base: dict[str, Any] = {"crop": None, "stage": None, "watered_today": False}
    return thing(pid, "plot", x, y, **(base | attrs))


def held(eid: str, kind: str, **attrs: Any) -> dict[str, Any]:
    return {"entity_id": eid, "kind": kind, "container_id": "camps", "attributes": attrs}


def view(
    *,
    at: tuple[int, int] = (1, 1),
    time: str = "10:00",
    hunger: float = 0,
    energy: float = 100,
    mine: dict[str, int] | None = None,
    stacks: list[dict[str, Any]] | None = None,
    plots: list[dict[str, Any]] | None = None,
    tools: list[dict[str, Any]] | None = None,
    kiosk_open: bool = False,
    stock: str = "semente_rabanete, semente_batata, adubo",
    prices: dict[str, int] | None = None,
    terrain: bool = True,
) -> dict[str, Any]:
    items = stacks or [{"item": item, "qty": qty} for item, qty in (mine or {"moeda": 100}).items()]
    box_prices = {f"preco_{k}": v for k, v in (prices or {}).items()}
    entities = [
        thing("bed", "bed", 0, 0),
        thing("chest", "chest", 7, 0),
        thing("sell-box", "sell_box", 7, 3, **box_prices),
        thing("well", "well", 4, 2),
        thing("kiosk", "kiosk", 0, 3, open=kiosk_open, estoque_hoje=stock),
        thing("stove", "stove", 2, 0),
        *(
            tools
            if tools is not None
            else [
                held("spade", "spade"),
                held("watering-can", "watering_can", charges=10, capacity=10),
            ]
        ),
        *(plots or []),
    ]
    doc: dict[str, Any] = {
        "clock": {
            "tick": 0,
            "sim_time": f"2026-10-10T{time}:00-03:00",
            "day": 1,
            "phase": "amanhecer",
        },
        "weather": {"condition": "sun", "day": 1},
        "self": {
            "entity_id": "camps",
            "position": {"x": at[0], "y": at[1]},
            "needs": {"fome": hunger, "energia": energy},
            "asleep": False,
        },
        "containers": [{"container_id": "camps", "items": items}],
        "entities": entities,
    }
    if terrain:
        doc["map"] = {"origin": {"x": 0, "y": 0}, "rows": ROWS, "legend": LEGEND}
    return doc


def test_cava_na_grama_mais_perto_do_poco_e_so_com_a_pa() -> None:
    far = SCRIPT.decide(view(at=(0, 2)))  # nenhuma grama boa ao lado: anda até a melhor
    assert far["action"] == "move"
    assert far["params"] == {"target": {"x": 3, "y": 2}}  # grama colada ao poço; empate por x, y
    beside = SCRIPT.decide(view(at=(4, 1)))  # ao lado do poço: cava o tile bom mais perto dele
    assert beside == {
        "action": "dig",
        "params": {"target": {"x": 3, "y": 2}},
        "intent": "cavar em 3,2",
    }
    nearby = SCRIPT.decide(view())  # de (1, 1), a grama (2, 2) a 2 do poço já está ao lado
    assert nearby["params"] == {"target": {"x": 2, "y": 2}}
    no_spade = SCRIPT.decide(
        view(at=(4, 1), tools=[held("watering-can", "watering_can", charges=10, capacity=10)])
    )
    assert no_spade["action"] != "dig"


def test_para_de_cavar_com_dezesseis_canteiros() -> None:
    plots = [plot(f"plot-{i:02d}", i % 8, 3, crop="rabanete", stage="madura") for i in range(16)]
    proposal = SCRIPT.decide(view(at=(0, 3), plots=plots))
    assert proposal["action"] == "harvest"


def test_planta_a_melhor_conta_que_tem_semente() -> None:
    seeds = {"moeda": 10, "semente_rabanete": 1, "semente_tomate": 1, "semente_cenoura": 2}
    # Com os 16 canteiros cavados, plantar passa a valer (antes, cavar tem prioridade).
    plots = [plot("plot-01", 2, 1)] + [
        plot(f"plot-{i:02d}", i, 3, crop="rabanete", stage="semente", watered_today=True)
        for i in range(2, 17)
    ]
    proposal = SCRIPT.decide(view(at=(2, 2), mine=seeds, plots=plots))
    assert proposal["action"] == "plant"
    assert proposal["params"]["crop"] == "tomate"  # 10 por canteiro-dia, contra 5 e 1,25
    only_carrot = SCRIPT.decide(view(at=(2, 2), mine={"semente_cenoura": 1}, plots=plots))
    assert only_carrot["params"]["crop"] == "cenoura"


def test_vende_so_o_que_passa_de_dois_dias_de_comida_e_so_a_bom_preco() -> None:
    plots = [
        plot(f"plot-{i:02d}", i, 3, crop="rabanete", stage="semente", watered_today=True)
        for i in range(16)
    ]
    mine = {"moeda": 10, "rabanete": 10}  # 250 pontos de fome; a reserva é 112
    proposal = SCRIPT.decide(view(at=(6, 3), mine=mine, plots=plots, prices={"rabanete": 25}))
    assert proposal["action"] == "sell"
    assert proposal["params"] == {
        "target": "sell-box",
        "item": "rabanete",
        "qty": 5,
    }  # sobram 5 (125 pontos)
    cheap = SCRIPT.decide(view(at=(6, 3), mine=mine, plots=plots, prices={"rabanete": 19}))
    assert cheap["action"] != "sell"  # 19 < 80% de 25


def test_compra_o_regador_grande_quando_sobra_e_sementes_do_estoque_do_dia() -> None:
    planted = [
        plot(f"plot-{i:02d}", i, 3, crop="rabanete", stage="semente", watered_today=True)
        for i in range(3, 17)
    ]
    plots = [plot("plot-01", 1, 3), plot("plot-02", 2, 3), *planted]  # 14 com rabanete, 2 vazios
    rich = SCRIPT.decide(view(at=(1, 3), mine={"moeda": 400}, plots=plots, kiosk_open=True))
    assert rich["params"]["item"] == "watering_can_large"  # 150 + 10 + 160 de sementes: sobra
    with_big = [
        held("spade", "spade"),
        held("watering-can", "watering_can", charges=10, capacity=10),
        held("watering-can-large-1", "watering_can-large", charges=25, capacity=25),
    ]
    stock = "semente_rabanete, semente_batata, adubo"
    poor = SCRIPT.decide(
        view(
            at=(1, 3), mine={"moeda": 60}, plots=plots, kiosk_open=True, tools=with_big, stock=stock
        )
    )
    assert poor["action"] == "buy"
    assert (poor["params"]["item"], poor["params"]["qty"]) == (
        "semente_rabanete",
        2,
    )  # pobre: só a base
    upgrade = SCRIPT.decide(
        view(
            at=(1, 3),
            mine={"moeda": 300},
            plots=plots,
            kiosk_open=True,
            tools=with_big,
            stock=stock,
        )
    )
    assert upgrade["action"] == "buy"
    assert (
        upgrade["params"]["item"] == "semente_batata"
    )  # com capital e a base plantada, a melhor conta do dia
    closed = SCRIPT.decide(
        view(at=(1, 3), mine={"moeda": 200}, plots=plots, kiosk_open=False, tools=with_big)
    )
    assert closed["action"] != "buy"


def test_com_fome_cozinha_a_sopa_antes_de_comer_cru_e_come_o_prato_pronto() -> None:
    cook = SCRIPT.decide(view(at=(2, 1), hunger=75, mine={"batata": 2}))
    assert (cook["action"], cook["params"]["recipe"]) == ("cook", "sopa_de_batata")
    ready = SCRIPT.decide(view(at=(2, 1), hunger=75, mine={"batata": 2, "sopa_de_batata": 1}))
    assert ready == {
        "action": "eat",
        "params": {"item": "sopa_de_batata"},
        "intent": "comer sopa_de_batata",
    }
    raw = SCRIPT.decide(view(at=(2, 1), hunger=75, mine={"batata": 1, "rabanete": 1}))
    assert raw["params"]["item"] == "rabanete"  # o de menor valor


def test_guarda_no_bau_a_comida_que_vence_amanha() -> None:
    plots = [
        plot(f"plot-{i:02d}", i, 3, crop="rabanete", stage="semente", watered_today=True)
        for i in range(16)
    ]
    stacks = [{"item": "moeda", "qty": 10}, {"item": "morango", "qty": 3, "expires_in_days": 1}]
    proposal = SCRIPT.decide(view(at=(7, 1), stacks=stacks, plots=plots))
    assert proposal["action"] == "deposit"
    assert proposal["params"] == {"target": "chest", "item": "morango", "qty": 2}


def test_dorme_na_cama_a_noite() -> None:
    proposal = SCRIPT.decide(view(at=(1, 0), time="21:40"))
    assert proposal == {"action": "sleep", "params": {"target": "bed"}, "intent": "dormir na cama"}


def test_com_o_regador_grande_na_mao_guarda_o_pequeno() -> None:
    plots = [
        plot(f"plot-{i:02d}", i, 3, crop="rabanete", stage="semente", watered_today=True)
        for i in range(16)
    ]
    both = [
        held("spade", "spade"),
        held("watering-can", "watering_can", charges=10, capacity=10),
        held("watering-can-large-1", "watering_can_large", charges=25, capacity=25),
    ]
    proposal = SCRIPT.decide(view(at=(7, 1), plots=plots, tools=both))
    assert proposal["action"] == "deposit"
    assert proposal["params"] == {"target": "chest", "item": "watering-can", "qty": 1}


def test_com_raio_lembra_o_que_viu_e_esquece_o_que_sumiu_a_vista() -> None:
    """Morada do Sol (ADR-0067): a foto mostra só um recorte; o script lembra o canteiro de fora."""
    script = Farmer2Script.load()  # a lembrança é de cada instância
    can = [held("watering-can", "watering_can", charges=10, capacity=10)]  # sem a pá: não cava
    ripe = plot("plot-far", 6, 3, crop="rabanete", stage="madura")
    script.decide(view(at=(1, 3), tools=can, plots=[ripe]))
    second = view(at=(1, 3), tools=can)
    second["map"] = {"origin": {"x": 0, "y": 0}, "rows": [r[:4] for r in ROWS], "legend": LEGEND}
    proposal = script.decide(second)  # o canteiro maduro ficou fora do recorte: vai até ele
    assert (proposal["action"], proposal["params"]) == ("move", {"near": "plot-far"})
    third = script.decide(view(at=(1, 3), tools=can))  # à vista e ausente: esqueceu
    assert third["params"] != {"near": "plot-far"}


def test_com_estacao_nao_planta_a_cultura_parada() -> None:
    """No inverno o milho para (calendário do manual): o script planta o que cresce."""
    can = [held("watering-can", "watering_can", charges=10, capacity=10)]
    seeds = {"semente_milho": 3, "semente_couve": 3}
    winter = view(at=(1, 3), tools=can, mine=seeds, plots=[plot("plot-01", 2, 3)])
    winter["clock"]["season"] = "inverno"
    proposal = SCRIPT.decide(winter)
    assert (proposal["action"], proposal["params"]["crop"]) == ("plant", "couve")
    summer = view(at=(1, 3), tools=can, mine=seeds, plots=[plot("plot-01", 2, 3)])
    summer["clock"]["season"] = "verao"
    assert SCRIPT.decide(summer)["params"]["crop"] == "milho"


def test_sem_nada_para_fazer_explora_ate_a_fronteira_do_que_viu() -> None:
    """ADR-0067: com a foto recortada, o script anda até um tile já visto que dá para o não visto.
    Com a foto começando no canto (o mapa inteiro, como na Boa Vista), não explora."""
    script = Farmer2Script.load()
    can = [held("watering-can", "watering_can", charges=10, capacity=10)]  # sem a pá: não cava
    cut = view(at=(5, 2), tools=can)
    cut["map"] = {"origin": {"x": 2, "y": 1}, "rows": ROWS, "legend": LEGEND}
    proposal = script.decide(cut)
    assert proposal == {
        "action": "move",
        "params": {"target": {"x": 4, "y": 1}},  # o mais perto; empate pela linha e pela coluna
        "intent": "explorar a fazenda",
    }
    tired = view(at=(5, 2), tools=can, energy=20)
    tired["map"] = cut["map"]
    assert script.decide(tired)["action"] == "wait"  # cansado: não explora
    whole = Farmer2Script.load()
    assert whole.decide(view(at=(5, 2), tools=can))["action"] == "wait"
