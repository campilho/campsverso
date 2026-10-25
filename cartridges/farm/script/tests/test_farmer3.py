"""Fazendeiro-script 3 e o oráculo (ADR-0070): a crença que aprende, a verdade do oráculo e as
regras de sobrevivência, em fotos à mão. A corrida de um ano em cada mapa está em
`tests/e2e/test_script3.py`."""

import math
import random
from pathlib import Path
from typing import Any

import yaml

from campsverso_farm_script import Farmer3Script
from campsverso_farm_script.farmer3 import Turn3
from campsverso_farm_script.knowledge import Beliefs, Spot, Truth

REPO = Path(__file__).resolve().parents[4]
MORADA = REPO / "cartridges/farm_morada_do_sol/sim/src/campsverso_farm_morada_do_sol_sim/data"
BOAVISTA = REPO / "cartridges/farm_boavista/sim/src/campsverso_farm_boavista_sim/data"
ROWS = ["GGGGGGGG", "GGGGGGGG", "GGGGWGGG", "GGGGGGGG"]
LEGEND = {
    "G": {"kind": "grass", "properties": {"passable": True, "water": False}},
    "W": {"kind": "well", "properties": {"passable": False, "water": False}},
}


def _yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _model() -> dict[str, Any]:
    return dict(Farmer3Script.load().config["model"])


def test_a_crenca_acha_o_efeito_da_agua_e_o_da_repeticao() -> None:
    # 30 plantios sintéticos: a água a até 4 tiles faz 1,5x, repetir a cultura 0,6x, e as
    # outras distâncias não importam (os distratores).
    beliefs = Beliefs(_model())
    rng = random.Random(1)
    for _ in range(30):
        distances = tuple(rng.choice([1, 3, 6, 12, 30]) for _ in range(4))
        repeat = rng.random() < 0.3
        truth = (1.5 if distances[0] <= 4 else 1.0) * (0.6 if repeat else 1.0)
        days = math.ceil(3 / truth)
        beliefs.learn_growth(Spot(distances, repeat), math.log(3 / (days - 0.5)))
    effects = {e.name: e for e in beliefs.effects()}
    assert effects["agua<=2"].low > 1.0
    assert effects["agua<=4"].low > 1.0
    assert effects["repetida"].high < 0.9
    for name in ("mata<=2", "caminho<=2", "porta<=16", "agua<=16"):
        assert effects[name].low <= 1.0 <= effects[name].high, name
    assert effects["adubada"].measured == 0  # sem dado, a crença é a larga do começo


def test_o_sorteio_varia_e_a_media_nao() -> None:
    beliefs = Beliefs(_model())
    spot = Spot((1, 30, 30, 30))
    mean = beliefs.world().speed(spot)
    assert mean == beliefs.world().speed(spot) == 1.0
    sampled = {round(beliefs.world(random.Random(seed)).speed(spot), 3) for seed in range(5)}
    assert len(sampled) == 5
    beliefs.learn_loss(40, None, lost=True)
    assert beliefs.loss_rates()[(3, 2)] == (0.375, 1)  # Beta(0,5 + 1, 2,5) depois de uma perda


def test_o_oraculo_sabe_os_numeros_do_cartucho() -> None:
    oracle = Farmer3Script.oracle()
    truth = oracle.config["truth"]
    rules = _yaml(MORADA / "rules.yaml")["rules"]
    morada = _yaml(MORADA / "morada.yaml")
    boavista = _yaml(BOAVISTA / "boavista.yaml")
    water = rules["river_proximity_bonus"]["params"]
    assert truth["water"] == {"radius": water["radius"], "multiplier": water["multiplier"]}
    assert truth["fatigue"] == rules["soil_fatigue"]["params"]["multiplier"]
    crows = morada["crows"]
    assert truth["crows"] == {
        "distance": crows["min_distance"],
        "scarecrow_radius": crows["scarecrow_radius"],
        "chance": crows["chance"],
    }
    assert truth["fertilizer_points"] == boavista["fertilizer"]["bonus_points"]
    assert oracle.config["model"]["test_pairs"] == 0


def test_a_verdade_do_oraculo() -> None:
    truth = Truth(Farmer3Script.oracle().config["truth"], Beliefs(_model()))
    assert truth.speed(Spot((4, 30, 30, 30))) == 1.5
    assert truth.speed(Spot((5, 30, 30, 30), repeat=True)) == 0.6
    assert truth.loss(19, None) == 0.5
    assert truth.loss(19, 6) == 0.0
    assert truth.loss(18, None) == 0.0
    effects = {e.name: e.mean for e in truth.effects()}
    assert (effects["agua<=4"], effects["agua<=8"], effects["repetida"]) == (1.5, 1.0, 0.6)


def test_o_script_3_nao_sabe_regra_oculta() -> None:
    # O script justo (ADR-0070): nem o código nem o arquivo dele falam das regras ocultas.
    folder = REPO / "cartridges/farm/script/src/campsverso_farm_script"
    text = " ".join(
        (folder / name).read_text(encoding="utf-8").lower()
        for name in ("farmer3.py", "knowledge.py", "data/farmer3.yaml")
    )
    for phrase in ("r-001", "r-002", "r-003", "várzea", "corvo", "fadiga", "rio"):
        assert f" {phrase} " not in text.replace("(", " ").replace(")", " "), phrase


def _view(**over: Any) -> dict[str, Any]:
    entities: list[dict[str, Any]] = [
        {"entity_id": "door", "kind": "door", "position": {"x": 0, "y": 0}, "attributes": {}},
        {"entity_id": "well", "kind": "well", "position": {"x": 4, "y": 2}, "attributes": {}},
        {
            "entity_id": "spade",
            "kind": "spade",
            "container_id": "camps",
            "attributes": {},
        },
    ]
    doc: dict[str, Any] = {
        "clock": {
            "tick": 0,
            "sim_time": "2026-09-22T09:00:00-03:00",
            "day": 1,
            "phase": "amanhecer",
            "season": "primavera",
        },
        "weather": {"condition": "sun", "day": 1},
        "self": {
            "entity_id": "camps",
            "position": {"x": 1, "y": 1},
            "needs": {"fome": 0, "energia": 100},
            "asleep": False,
        },
        "containers": [{"container_id": "camps", "items": [{"item": "moeda", "qty": 100}]}],
        "entities": entities,
        "map": {"origin": {"x": 0, "y": 0}, "rows": ROWS, "legend": LEGEND},
    }
    return doc | over


def test_as_contas_de_sobrevivencia() -> None:
    # A fome da Morada do Sol: 2 por hora em 16 horas acordado e 1 nas 8 dormindo, 40 por dia. O
    # rabanete na primavera mata uns 8 por dia de canteiro: 7 canteiros pagam o dia com folga.
    script = Farmer3Script.load()
    view = _view()
    script._learn_terrain(view)  # pyright: ignore[reportPrivateUsage]
    turn = Turn3(script.config, view, list(view["entities"]), script)
    assert turn.hunger_per_day() == 40
    foods, rate = turn.food_plan()
    assert foods[0] == "rabanete"
    assert round(rate, 2) == round(25 / 3, 2)
    assert turn.food_plots() == math.ceil(40 * 1.4 / (25 / 3))
    # Sem semente nenhuma, a primeira compra é a da comida.
    assert turn.plan(["rabanete", "tomate", "melancia"])[0] == ("rabanete", True)
