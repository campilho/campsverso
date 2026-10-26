"""O fazendeiro-ajudante (ADR-0072): a ordem do patrão, em fotos à mão."""

from typing import Any

from campsverso_farm_script import HelperScript, helper

ROWS = ["GGGGGGGG", "GGGGGGGG", "GGGGWGGG", "GGGGGGGG"]  # G grama, W o poço
LEGEND = {
    "G": {"kind": "grass", "properties": {"passable": True, "water": False}},
    "W": {"kind": "well", "properties": {"passable": False, "water": False}},
}


def thing(eid: str, kind: str, x: int, y: int, **attrs: Any) -> dict[str, Any]:
    return {"entity_id": eid, "kind": kind, "position": {"x": x, "y": y}, "attributes": attrs}


def plot(pid: str, x: int, y: int, **attrs: Any) -> dict[str, Any]:
    base: dict[str, Any] = {"crop": None, "stage": None, "watered_today": False}
    return thing(pid, "plot", x, y, **(base | attrs))


def view(
    *,
    at: tuple[int, int] = (1, 1),
    order: dict[str, Any] | None = None,
    hunger: float = 0,
    mine: dict[str, int] | None = None,
    chest: dict[str, int] | None = None,
    plots: list[dict[str, Any]] | None = None,
    charges: int = 10,
    refused: bool = False,
    day: int = 2,
) -> dict[str, Any]:
    me = {
        "entity_id": "dita",
        "kind": "avatar",
        "position": {"x": at[0], "y": at[1]},
        "attributes": {"nome": "Dita", "patrao": "camps", "ordem": "cuidar", **(order or {})},
    }
    containers = [
        {"container_id": cid, "items": [{"item": i, "qty": q} for i, q in sorted(stock.items())]}
        for cid, stock in (("chest", chest or {}), ("dita", mine or {}))
        if stock
    ]
    can = {
        "entity_id": "dita-regador",
        "kind": "watering_can",
        "container_id": "dita",
        "attributes": {"charges": charges, "capacity": 10},
    }
    doc: dict[str, Any] = {
        "clock": {"tick": 0, "sim_time": "2026-09-23T10:00:00-03:00", "day": day, "phase": "manha"},
        "weather": {"condition": "sol", "day": 2},
        "self": {
            "entity_id": "dita",
            "position": {"x": at[0], "y": at[1]},
            "needs": {"fome": hunger, "energia": 100},
            "asleep": False,
        },
        "containers": containers,
        "entities": [
            me,
            can,
            thing("chest", "chest", 7, 0),
            thing("sell-box", "sell_box", 7, 3),
            thing("well", "well", 4, 2),
            *(plots or []),
        ],
        "map": {"origin": {"x": 0, "y": 0}, "rows": ROWS, "legend": LEGEND},
    }
    if refused:
        doc["decision"] = {"reason": "action_rejected", "controller": {"id": "x"}}
    return doc


def test_a_fabrica_da_um_script_por_ajudante() -> None:
    dita, nina = helper("dita"), helper("nina")
    assert (dita.controller_type, dita.controller_id) == ("script", "script/ajudante-dita")
    assert nina.controller_id == "script/ajudante-nina"
    assert dita.plots is not nina.plots  # cada um com a sua lembrança


def test_cuidar_colhe_o_maduro_e_rega_o_seco_e_vai_ver_quando_nao_lembra() -> None:
    script = helper("dita")
    looking = script.decide(view(at=(0, 0)))  # nenhum canteiro na lembrança: ir ver no poço
    assert looking == {
        "action": "move",
        "params": {"near": "well"},
        "intent": "ir ver os canteiros",
    }
    plots = [
        plot("plot-01", 1, 2, crop="rabanete", stage="broto"),
        plot("plot-02", 2, 2, crop="rabanete", stage="madura"),
    ]
    first = script.decide(view(plots=plots))
    assert (first["action"], first["params"]) == ("harvest", {"target": "plot-02"})
    plots[1] = plot("plot-02", 2, 2)
    second = script.decide(view(plots=plots))
    assert (second["action"], second["params"]) == ("water", {"target": "plot-01"})
    drought = script.decide(view(plots=plots, refused=True))  # a seca recusou a rega: ao poço
    assert drought == {
        "action": "move",
        "params": {"near": "well"},
        "intent": "ir encher o regador",
    }
    dry = script.decide(view(at=(3, 1), plots=plots, charges=0))
    assert (dry["action"], dry["params"]) == ("refill", {"target": "well"})


def test_cuidar_guarda_a_colheita_no_bau() -> None:
    script = helper("dita")
    full = script.decide(view(at=(6, 0), mine={"rabanete": 6}))
    assert full == {
        "action": "deposit",
        "params": {"target": "chest", "item": "rabanete", "qty": 6},
        "intent": "guardar a colheita no baú",
    }


def test_plantar_pega_a_semente_do_bau_e_planta_o_canteiro_vazio() -> None:
    script = helper("dita")
    order = {"ordem": "plantar", "ordem_cultura": "rabanete"}
    plots = [plot("plot-01", 6, 1), plot("plot-02", 1, 3, crop="batata", stage="broto")]
    none = script.decide(view(at=(6, 0), order=order, plots=plots))
    assert none["intent"] == "sem semente no baú"
    take = script.decide(view(at=(6, 0), order=order, plots=plots, chest={"semente_rabanete": 5}))
    assert take["params"] == {"target": "chest", "item": "semente_rabanete", "qty": 1}
    plant = script.decide(view(at=(6, 0), order=order, plots=plots, mine={"semente_rabanete": 1}))
    assert (plant["action"], plant["params"]) == (
        "plant",
        {"target": "plot-01", "crop": "rabanete"},
    )


def test_cavar_faz_os_canteiros_pedidos_em_volta_do_ponto_e_a_recusa_nao_conta() -> None:
    script = helper("dita")
    order = {"ordem": "cavar", "ordem_n": 2, "ordem_x": 1, "ordem_y": 1}
    first = script.decide(view(order=order))
    assert first["params"] == {"target": {"x": 1, "y": 1}}  # onde ela está, ela cava
    taken = [plot("plot-01", 1, 1)]
    second = script.decide(view(order=order, plots=taken, refused=True))  # a primeira, recusada
    assert second["action"] == "dig"
    third = script.decide(view(order=order, plots=taken))
    assert third["action"] == "dig"
    done = script.decide(view(order=order, plots=taken))
    assert done["intent"] == "canteiros cavados"


def test_vender_leva_do_bau_para_a_caixa() -> None:
    script = helper("dita")
    order = {"ordem": "vender", "ordem_item": "abobora"}
    take = script.decide(view(at=(6, 0), order=order, chest={"abobora": 9}))
    assert take["params"] == {"target": "chest", "item": "abobora", "qty": 6}
    sell = script.decide(view(at=(6, 3), order=order, mine={"abobora": 6}))
    assert sell["params"] == {"target": "sell-box", "item": "abobora", "qty": 6}


def test_parar_espera_e_sem_comida_no_bau_vai_para_casa() -> None:
    script = HelperScript("dita")
    assert script.decide(view(order={"ordem": "parar"}))["action"] == "wait"
    assert script.decide(view(order={"ordem": None}))["action"] == "wait"  # sem ordem, espera
    hungry = script.decide(view(at=(6, 0), hunger=60, chest={"batata": 2}))
    assert hungry["params"] == {"target": "chest", "item": "batata", "qty": 1}
    eats = script.decide(view(hunger=60, mine={"batata": 1}))
    assert eats == {"action": "eat", "params": {"item": "batata"}, "intent": "comer"}
    home = script.decide(view(hunger=60))
    assert home["action"] == "go_home"


def test_o_canteiro_lembrado_de_ontem_perdeu_a_rega_e_ela_vai_ver() -> None:
    script = helper("dita")
    watered = [plot("plot-01", 6, 3, crop="rabanete", stage="broto", watered_today=True)]
    assert script.decide(view(at=(6, 2), plots=watered))["intent"] == "tudo cuidado"
    tomorrow = script.decide(view(at=(0, 0), day=3))  # longe, sem o canteiro à vista
    assert tomorrow == {"action": "move", "params": {"near": "plot-01"}, "intent": "ir regar"}


def test_sem_canteiro_na_lembranca_vai_ate_o_patrao_quando_o_ve() -> None:
    script = helper("dita")
    camps = {"entity_id": "camps", "kind": "avatar", "position": {"x": 7, "y": 3}, "attributes": {}}
    seen = view(at=(0, 0))
    seen["entities"].append(camps)
    assert script.decide(seen) == {
        "action": "move",
        "params": {"near": "camps"},
        "intent": "ir até o patrão",
    }


def test_o_canteiro_lembrado_que_sumiu_e_esquecido_na_recusa() -> None:
    script = helper("dita")
    watered = [plot("plot-01", 7, 3, crop="rabanete", stage="broto", watered_today=True)]
    script.decide(view(at=(6, 2), plots=watered))
    going = script.decide(view(at=(0, 0), day=3))
    assert going["params"] == {"near": "plot-01"}
    refused = script.decide(view(at=(0, 0), day=3, refused=True))  # não existe mais
    assert "plot-01" not in script.plots
    assert refused["intent"] == "ir ver os canteiros"  # volta a procurar
