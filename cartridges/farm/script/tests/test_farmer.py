"""Fazendeiro-script: cada prioridade da bíblia §11, a partir de fotos montadas à mão."""

from typing import Any

import pytest

from campsverso_farm_script import FarmerScript

SCRIPT = FarmerScript.load()


def plot(pid: str, x: int, y: int, **attrs: Any) -> dict[str, Any]:
    base: dict[str, Any] = {"crop": None, "stage": None, "watered_today": False}
    return {
        "entity_id": pid,
        "kind": "plot",
        "position": {"x": x, "y": y},
        "attributes": base | attrs,
    }


def thing(eid: str, kind: str, x: int, y: int, **attrs: Any) -> dict[str, Any]:
    return {"entity_id": eid, "kind": kind, "position": {"x": x, "y": y}, "attributes": attrs}


def view(
    *,
    at: tuple[int, int] = (10, 10),
    time: str = "10:00",
    hunger: float = 0,
    energy: float = 100,
    rain: bool = False,
    mine: dict[str, int] | None = None,
    chest: dict[str, int] | None = None,
    charges: int = 10,
    plots: list[dict[str, Any]] | None = None,
    kiosk_open: bool = False,
) -> dict[str, Any]:
    stocks = {"camps": mine if mine is not None else {"moeda": 100}, "chest": chest or {}}
    entities = [
        thing("bed", "bed", 3, 3),
        thing("chest", "chest", 7, 4),
        thing("sell-box", "sell_box", 8, 6),
        thing("well", "well", 17, 10),
        thing("kiosk", "kiosk", 16, 15, open=kiosk_open),
        {
            "entity_id": "watering-can",
            "kind": "watering_can",
            "container_id": "camps",
            "attributes": {"charges": charges, "capacity": 10},
        },
        *(plots or []),
    ]
    return {
        "clock": {"tick": 0, "sim_time": f"2026-10-10T{time}:00-03:00", "day": 1, "phase": "x"},
        "weather": {"condition": "rain" if rain else "sun", "day": 1},
        "self": {
            "entity_id": "camps",
            "position": {"x": at[0], "y": at[1]},
            "needs": {"fome": hunger, "energia": energy},
            "asleep": False,
        },
        "containers": [
            {"container_id": c, "items": [{"item": i, "qty": q} for i, q in sorted(s.items())]}
            for c, s in stocks.items()
            if s
        ],
        "entities": entities,
    }


def decide(**kwargs: Any) -> tuple[str, dict[str, Any]]:
    proposal = SCRIPT.decide(view(**kwargs))
    return proposal["action"], proposal["params"]


def test_nada_a_fazer_espera_15_minutos() -> None:
    assert decide(plots=[]) == ("wait", {"ticks": 15})


def test_dormir_na_cama_depois_das_21_30() -> None:
    assert decide(time="21:30", at=(10, 10)) == ("move", {"near": "bed"})
    assert decide(time="21:30", at=(4, 4)) == ("sleep", {"target": "bed"})


def test_energia_baixa_so_dorme_depois_das_20() -> None:
    assert decide(time="19:00", energy=5, plots=[]) == ("wait", {"ticks": 15})
    assert decide(time="20:00", energy=5, at=(4, 4)) == ("sleep", {"target": "bed"})


def test_tarde_demais_para_andar_dorme_no_chao() -> None:
    assert decide(time="01:45", at=(30, 20)) == ("sleep", {})


def test_com_fome_come_o_mais_barato_ou_busca_no_bau() -> None:
    assert decide(hunger=70, mine={"batata": 1, "rabanete": 1}) == ("eat", {"item": "rabanete"})
    assert decide(hunger=70, mine={}, chest={"rabanete": 2}, at=(7, 5)) == (
        "withdraw",
        {"item": "rabanete", "qty": 1},
    )


def test_colhe_a_madura_mais_perto_desempatando_pelo_id() -> None:
    plots = [
        plot("plot-b", 12, 10, crop="rabanete", stage="madura"),
        plot("plot-a", 8, 10, crop="rabanete", stage="madura"),
    ]
    assert decide(plots=plots) == ("move", {"near": "plot-a"})  # mesma distância: menor id
    assert decide(plots=plots, at=(9, 10)) == ("harvest", {"target": "plot-a"})


def test_regador_vazio_enche_no_poco_se_alguem_precisa_de_agua() -> None:
    thirsty = [plot("plot-a", 11, 10, crop="rabanete", stage="broto")]
    assert decide(plots=thirsty, charges=0) == ("move", {"near": "well"})
    assert decide(plots=thirsty, charges=0, at=(16, 10)) == ("refill", {})
    assert decide(plots=thirsty, charges=0, rain=True) == ("wait", {"ticks": 15})


def test_rega_e_planta() -> None:
    growing = [plot("plot-a", 11, 10, crop="rabanete", stage="broto")]
    assert decide(plots=growing) == ("water", {"target": "plot-a"})
    empty = [plot("plot-a", 11, 10)]
    assert decide(plots=empty, mine={"semente_rabanete": 2}) == (
        "plant",
        {"target": "plot-a", "crop": "rabanete"},
    )


def test_vende_o_que_passa_da_reserva_de_comida() -> None:
    assert decide(mine={"rabanete": 5}, at=(8, 5)) == ("sell", {"item": "rabanete", "qty": 2})
    assert decide(mine={"rabanete": 3}, plots=[]) == ("wait", {"ticks": 15})


def test_compra_sementes_para_os_canteiros_vazios() -> None:
    empty = [plot(f"plot-{i}", 11 + i, 10) for i in range(3)]
    proposal = decide(plots=empty, mine={"moeda": 25}, kiosk_open=True, at=(16, 14))
    assert proposal == ("buy", {"item": "semente_rabanete", "qty": 2})
    assert decide(plots=empty, mine={"moeda": 25}, kiosk_open=False) == ("wait", {"ticks": 15})


@pytest.mark.parametrize("stage", ["madura", "murcha"])
def test_planta_madura_ou_murcha_nao_e_regada(stage: str) -> None:
    plots = [plot("plot-a", 30, 30, crop="rabanete", stage=stage)]
    action, _ = decide(plots=plots, charges=0)
    assert action != "refill"
