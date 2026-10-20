"""Fazendeiro-script 2 (bíblia 2, §11): a linha de base competente e cega da Fazenda Boa Vista.

Como o fazendeiro-script da v0.1, é uma função pura da foto da percepção para uma proposta, com
empates por distância e por id. Segue o manual com regras boas (cava perto do poço, planta a
melhor conta visível que o dinheiro permite, cozinha a sopa, vende enquanto o preço do dia
compensa, compra o regador grande quando sobra) e não sabe nenhuma regra oculta: nunca o arado,
nunca o adubo, rega tudo, inclusive o alho.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import yaml

from campsverso_farm_script.farmer import Proposal, View, adjacent, distance, minutes

DATA = Path(__file__).parent / "data" / "farmer2.yaml"
GRASS = "grass"


@dataclass(frozen=True)
class Farmer2Script:
    config: Mapping[str, Any]

    @classmethod
    def load(cls) -> Farmer2Script:
        return cls(cast(dict[str, Any], yaml.safe_load(DATA.read_text(encoding="utf-8"))))

    @property
    def controller_type(self) -> str:
        return "script"

    @property
    def controller_id(self) -> str:
        return str(self.config["id"])

    def decide(self, view: View) -> Proposal:
        return _Turn(self.config, view).decide()


def _tile_kind(view: View, x: int, y: int) -> str | None:
    """A classe do tile pelo terreno da foto (ADR-0056): `rows` e `legend`, com `origin`."""
    terrain = cast(Mapping[str, Any] | None, view.get("map"))
    if terrain is None:
        return None
    origin = cast(Mapping[str, int], terrain.get("origin") or {"x": 0, "y": 0})
    rows = cast(Sequence[str], terrain["rows"])
    row, col = y - int(origin["y"]), x - int(origin["x"])
    if not (0 <= row < len(rows) and 0 <= col < len(rows[row])):
        return None
    legend = cast(Mapping[str, Mapping[str, Any]], terrain["legend"])
    entry = legend.get(rows[row][col])
    return None if entry is None else str(entry.get("kind"))


class _Turn:
    def __init__(self, config: Mapping[str, Any], view: View) -> None:
        self.c = config
        self.view = view
        me = view["self"]
        self.me_id = str(me["entity_id"])
        self.pos: Mapping[str, int] = me["position"]
        needs = cast(Mapping[str, float], me["needs"])
        self.hunger = float(needs.get(config["needs"]["hunger"], 0))
        self.energy = float(needs.get(config["needs"]["energy"], 100))
        self.now = minutes(str(view["clock"]["sim_time"])[11:16])
        self.raining = view["weather"]["condition"] == config["rain"]
        self.entities = cast(Sequence[Mapping[str, Any]], view["entities"])
        self.stock: dict[str, dict[str, int]] = {
            str(c["container_id"]): {str(i["item"]): int(i["qty"]) for i in c["items"]}
            for c in view["containers"]
        }

    # ------------------------------------------------------------- leitura

    def mine(self, item: str) -> int:
        return self.stock.get(self.me_id, {}).get(item, 0)

    def of_kind(self, kind: str) -> list[Mapping[str, Any]]:
        return [e for e in self.entities if e["kind"] == self.c["kinds"].get(kind, kind)]

    def held(self, kind: str) -> Mapping[str, Any] | None:
        return next(
            (e for e in self.entities if e["kind"] == kind and e.get("container_id") == self.me_id),
            None,
        )

    def nearest(self, candidates: Sequence[Mapping[str, Any]]) -> Mapping[str, Any] | None:
        placed = [e for e in candidates if e.get("position") is not None]
        return min(
            placed, key=lambda e: (distance(self.pos, e["position"]), e["entity_id"]), default=None
        )

    def at(self, thing: Mapping[str, Any], action: str, intent: str, /, **params: Any) -> Proposal:
        if adjacent(self.pos, thing["position"]):
            return {"action": action, "params": params, "intent": intent}
        near = {"near": thing["entity_id"]}
        return {"action": "move", "params": near, "intent": f"ir para {thing['entity_id']}"}

    def plots(self, *stages: str | None) -> list[Mapping[str, Any]]:
        return [p for p in self.of_kind("plot") if p["attributes"].get("stage") in stages]

    def can_charges(self) -> int:
        """O regador que carrega, o grande se tiver."""
        big = self.held(str(self.c["big_can"]["kind"]))
        can = big or self.held(str(self.c["small_can"]))
        return int(can["attributes"].get("charges") or 0) if can else 0

    # ------------------------------------------------------------- prioridades (bíblia 2, §11)

    def decide(self) -> Proposal:
        for rule in (
            self.sleep,
            self.eat,
            self.dig,
            self.harvest,
            self.clear,
            self.refill,
            self.water,
            self.plant,
            self.store,
            self.sell,
            self.buy,
        ):
            proposal = rule()
            if proposal is not None:
                return proposal
        ticks = int(self.c["wait_ticks"])
        return {"action": "wait", "params": {"ticks": ticks}, "intent": "esperar"}

    def _night(self, since: str) -> bool:
        return self.now >= minutes(since) or self.now < minutes(self.c["sleep"]["wake_at"])

    def sleep(self) -> Proposal | None:
        rules = self.c["sleep"]
        tired = self.energy < float(rules["low_energy"])
        if not (tired or self._night(rules["at"])):
            return None
        bed = self.nearest(self.of_kind(rules["bed_kind"]))
        late = minutes(rules["ground_after"]) <= self.now < minutes(rules["wake_at"])
        if bed is None or (late and not adjacent(self.pos, bed["position"])):
            return {"action": "sleep", "params": {}, "intent": "dormir onde está"}
        return self.at(bed, "sleep", "dormir na cama", target=bed["entity_id"])

    def _food_value(self, item: str) -> int:
        foods = cast(Mapping[str, Mapping[str, int]], self.c["foods"])
        return int(foods[item]["sale"]) if item in foods else 0

    def eat(self) -> Proposal | None:
        if self.hunger < float(self.c["hunger_eat_at"]):
            return None
        dishes = [d for d in cast(Sequence[str], self.c["dishes"]) if self.mine(d) > 0]
        if dishes:
            return {"action": "eat", "params": {"item": dishes[0]}, "intent": f"comer {dishes[0]}"}
        soup = cast(Mapping[str, Any], self.c["soup"])
        needs = cast(Mapping[str, int], soup["needs"])
        stove = self.nearest(self.of_kind("stove"))
        if stove is not None and all(self.mine(i) >= q for i, q in needs.items()):
            recipe = str(soup["recipe"])
            return self.at(
                stove, "cook", f"cozinhar {recipe}", target=stove["entity_id"], recipe=recipe
            )
        foods = cast(Mapping[str, Mapping[str, int]], self.c["foods"])
        by_value = sorted(foods, key=lambda f: (foods[f]["sale"], f))
        held = [f for f in by_value if self.mine(f) > 0]
        if held:
            return {"action": "eat", "params": {"item": held[0]}, "intent": f"comer {held[0]}"}
        chest = self.nearest(self.of_kind("chest"))
        if chest is None:
            return None
        stored = [f for f in by_value if self.stock.get(chest["entity_id"], {}).get(f, 0) > 0]
        if not stored:
            return None
        return self.at(chest, "withdraw", f"pegar {stored[0]}", item=stored[0], qty=1)

    def dig(self) -> Proposal | None:
        """Cava os canteiros nos tiles de grama mais perto do poço, até o número que o script
        cuida; sem a pá, não cava."""
        digging = cast(Mapping[str, Any], self.c["digging"])
        if len(self.of_kind("plot")) >= int(digging["plots"]) or self.held("spade") is None:
            return None
        well = self.nearest(self.of_kind(str(digging["near"])))
        if well is None or self.view.get("map") is None:
            return None
        taken = {
            (e["position"]["x"], e["position"]["y"])
            for e in self.entities
            if e.get("position") is not None and e["entity_id"] != self.me_id
        }
        wx, wy = int(well["position"]["x"]), int(well["position"]["y"])
        radius = int(digging.get("radius", 2))
        candidates = [
            (x, y)
            for x in range(wx - radius, wx + radius + 1)
            for y in range(wy - radius, wy + radius + 1)
            if (x, y) not in taken and _tile_kind(self.view, x, y) == GRASS
        ]
        if not candidates:
            return None
        if (self.pos["x"], self.pos["y"]) in candidates:  # já está num tile bom: cava aqui
            return {"action": "dig", "params": {}, "intent": "cavar um canteiro"}
        x, y = min(candidates, key=lambda t: (abs(t[0] - wx) + abs(t[1] - wy), t))
        target = {"x": x, "y": y}
        return {"action": "move", "params": {"target": target}, "intent": f"ir cavar em {x},{y}"}

    def thirsty(self) -> list[Mapping[str, Any]]:
        if self.raining:
            return []
        stages = self.c["stages"]
        return [
            p
            for p in self.of_kind("plot")
            if p["attributes"].get("crop") is not None
            and p["attributes"].get("stage") not in (stages["ripe"], stages["withered"])
            and not p["attributes"].get("watered_today")
        ]

    def harvest(self) -> Proposal | None:
        plot = self.nearest(self.plots(self.c["stages"]["ripe"]))
        if plot is None:
            return None
        return self.at(plot, "harvest", f"colher {plot['entity_id']}", target=plot["entity_id"])

    def clear(self) -> Proposal | None:
        plot = self.nearest(self.plots(self.c["stages"]["withered"]))
        if plot is None:
            return None
        return self.at(plot, "clear", f"limpar {plot['entity_id']}", target=plot["entity_id"])

    def refill(self) -> Proposal | None:
        if self.can_charges() > 0 or not self.thirsty():
            return None
        well = self.nearest(self.of_kind("well"))
        return None if well is None else self.at(well, "refill", "encher o regador")

    def water(self) -> Proposal | None:
        plot = self.nearest(self.thirsty())
        if plot is None or self.can_charges() < 1:
            return None
        return self.at(plot, "water", f"regar {plot['entity_id']}", target=plot["entity_id"])

    def _best_crops(self) -> list[str]:
        """As culturas pela conta visível, da melhor à pior: (venda - semente) / dias."""
        crops = cast(Mapping[str, Mapping[str, Any]], self.c["crops"])

        def gain(name: str) -> float:
            c = crops[name]
            return (float(c["sale"]) - float(c["price"])) / float(c["days"])

        return sorted(crops, key=lambda n: (-gain(n), n))

    def plant(self) -> Proposal | None:
        plot = self.nearest(self.plots(None))
        if plot is None:
            return None
        crops = cast(Mapping[str, Mapping[str, Any]], self.c["crops"])
        for crop in self._best_crops():
            seed = str(crops[crop]["seed"])
            if self.mine(seed) > 0:
                return self.at(
                    plot,
                    "plant",
                    f"plantar {crop} em {plot['entity_id']}",
                    target=plot["entity_id"],
                    crop=crop,
                )
        return None

    def _food_points(self, container: str) -> float:
        foods = cast(Mapping[str, Mapping[str, int]], self.c["foods"])
        stock = self.stock.get(container, {})
        return sum(float(foods[f]["hunger"]) * stock.get(f, 0) for f in foods)

    def store(self) -> Proposal | None:
        """Com o regador grande na mão, o pequeno vai para o baú (pesa e não serve); e comida que
        vence amanhã vai para o baú (o manual diz que ele guarda bem), menos uma unidade, para
        comer."""
        chest = self.nearest(self.of_kind("chest"))
        if chest is None:
            return None
        small = self.held(str(self.c["small_can"]))
        if small is not None and self.held(str(self.c["big_can"]["kind"])) is not None:
            return self.at(
                chest,
                "deposit",
                "guardar o regador pequeno",
                target=chest["entity_id"],
                item=small["entity_id"],
                qty=1,
            )
        foods = cast(Mapping[str, Mapping[str, int]], self.c["foods"])
        mine = self.stock.get(self.me_id, {})
        for container in self.view["containers"]:
            if container["container_id"] != self.me_id:
                continue
            for stack in sorted(container["items"], key=lambda s: str(s["item"])):
                item, expires = str(stack["item"]), stack.get("expires_in_days")
                qty = mine.get(item, 0)
                if item in foods and isinstance(expires, int) and expires <= 1 and qty > 1:
                    return self.at(
                        chest,
                        "deposit",
                        f"guardar {item}",
                        target=chest["entity_id"],
                        item=item,
                        qty=qty - 1,
                    )
        return None

    def sell(self) -> Proposal | None:
        """Vende o que passa da comida de dois dias, enquanto o preço do dia compensa."""
        box = self.nearest(self.of_kind("sell_box"))
        if box is None:
            return None
        foods = cast(Mapping[str, Mapping[str, int]], self.c["foods"])
        reserve = float(self.c["food_days"]) * float(self.c["hunger_per_day"])
        surplus_points = self._food_points(self.me_id) - reserve
        if surplus_points <= 0:
            return None
        floor = float(self.c["sell_floor"])
        for item in sorted(foods, key=lambda f: (-foods[f]["sale"], f)):  # o mais caro primeiro
            qty = self.mine(item)
            if qty < 1:
                continue
            price = box["attributes"].get(f"preco_{item}")
            if isinstance(price, int | float) and float(price) < floor * float(foods[item]["sale"]):
                continue
            keep = 0
            while keep < qty and (qty - keep) * float(foods[item]["hunger"]) > surplus_points:
                keep += 1
            amount = qty - keep
            if amount >= 1:
                return self.at(
                    box,
                    "sell",
                    f"vender {amount} {item}",
                    target=box["entity_id"],
                    item=item,
                    qty=amount,
                )
        return None

    def buy(self) -> Proposal | None:
        """Enquanto é pobre, a cultura barata que se come para todos os canteiros; com capital,
        metade fica com ela e o resto vai para a melhor conta visível que o dinheiro permite,
        guardando uma reserva. O regador grande só quando sobra depois de semear a fazenda."""
        kiosk = self.nearest(self.of_kind("kiosk"))
        if kiosk is None or not kiosk["attributes"].get("open"):
            return None
        coins, reserve = self.mine("moeda"), int(self.c["coins_reserve"])
        crops = cast(Mapping[str, Mapping[str, Any]], self.c["crops"])
        food = str(self.c["food_crop"])
        food_seed, food_price = str(crops[food]["seed"]), int(crops[food]["price"])
        all_plots = len(self.of_kind("plot"))
        big = cast(Mapping[str, Any], self.c["big_can"])
        seeds_for_all = all_plots * food_price  # o que custa semear a fazenda inteira
        if (
            self.held(str(big["kind"])) is None
            and coins >= int(big["price"]) + reserve + seeds_for_all
        ):
            return self.at(
                kiosk,
                "buy",
                "comprar o regador grande",
                target=kiosk["entity_id"],
                item=str(big["item"]),
                qty=1,
            )
        empty = len(self.plots(None))
        stock = str(kiosk["attributes"].get("estoque_hoje") or "")
        available = stock.split(", ") if stock else []
        seeds_held = {name: self.mine(str(c["seed"])) for name, c in crops.items()}
        missing = empty - sum(seeds_held.values())
        if missing <= 0:
            return None
        poor = coins < int(self.c["upgrade_from"])
        food_plots = all_plots if poor else int(self.c["food_plots"])
        planted_food = sum(1 for p in self.of_kind("plot") if p["attributes"].get("crop") == food)
        food_missing = min(missing, food_plots - planted_food - seeds_held[food])
        if food_missing > 0 and (not available or food_seed in available):
            qty = min(food_missing, (coins - reserve) // food_price)
            if qty >= 1:
                return self.at(
                    kiosk,
                    "buy",
                    f"comprar {qty} {food_seed}",
                    target=kiosk["entity_id"],
                    item=food_seed,
                    qty=qty,
                )
        for crop in self._best_crops():
            seed, price = str(crops[crop]["seed"]), int(crops[crop]["price"])
            if available and seed not in available:
                continue
            qty = min(missing, (coins - reserve) // price)
            if qty >= 1:
                return self.at(
                    kiosk,
                    "buy",
                    f"comprar {qty} {seed}",
                    target=kiosk["entity_id"],
                    item=seed,
                    qty=qty,
                )
        return None
