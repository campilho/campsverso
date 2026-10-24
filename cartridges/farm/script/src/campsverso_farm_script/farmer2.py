"""Fazendeiro-script 2 (bíblia 2, §11): a linha de base competente e cega da Fazenda Boa Vista.

Como o fazendeiro-script da v0.1, decide pela foto da percepção, com empates por distância e por
id. Segue o manual com regras boas (cava perto do poço, planta a melhor conta visível que o
dinheiro permite, cozinha a sopa, vende enquanto o preço do dia compensa, compra o regador grande
quando sobra) e não sabe nenhuma regra oculta: nunca o arado, nunca o adubo, rega tudo, inclusive
o alho.

Na Morada do Sol (ADR-0067) ele vê só um raio em volta; por isso lembra o último estado de cada
coisa que viu e vai até ela quando precisa (os canteiros, o que não é construção fixa), e lembra
o terreno que já viu. O que estava à vista e sumiu, ele esquece. Sem nada para fazer, de dia, com
energia e sem fome, explora: anda até a fronteira do que conhece, até ter visto o mapa inteiro.
Com a estação na foto, segue o calendário de plantio do manual: não planta nem compra a cultura
parada e conta a fraca como mais lenta. Com o mapa inteiro à vista (a Boa Vista), a lembrança e a
exploração nunca mudam nada.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

import yaml

from campsverso_farm_script.farmer import Proposal, View, adjacent, distance, minutes

DATA = Path(__file__).parent / "data" / "farmer2.yaml"
GRASS = "grass"


@dataclass(frozen=True)
class Farmer2Script:
    config: Mapping[str, Any]
    # O último estado visto de cada coisa com posição, para quem vê só um raio (ADR-0067).
    memory: dict[str, Mapping[str, Any]] = field(default_factory=dict[str, Mapping[str, Any]])
    # O terreno já visto: (x, y) -> (classe, passável); e o que se sabe do tamanho do mapa.
    terrain: dict[tuple[int, int], tuple[str, bool]] = field(
        default_factory=dict[tuple[int, int], tuple[str, bool]]
    )
    bounds: dict[str, int] = field(default_factory=dict[str, int])
    unreachable: set[tuple[int, int]] = field(default_factory=set[tuple[int, int]])
    # A última proposta, para não repetir uma que acabou de ser recusada (ADR-0069).
    last: dict[str, Proposal] = field(default_factory=dict[str, Proposal])

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
        tick = int(view["clock"]["tick"])
        if tick < self.bounds.get("tick", 0):  # o relógio voltou: outra sessão, outra lembrança
            self.memory.clear()
            self.terrain.clear()
            self.bounds.clear()
            self.unreachable.clear()
            self.last.clear()
        self.bounds["tick"] = tick
        self._learn_terrain(view)
        turn = _Turn(self.config, view, self._remember(view), self)
        proposal = turn.decide()
        if _reason(view) == "action_rejected" and proposal == self.last.get("proposal"):
            # A mesma proposta acabou de ser recusada (um preço que subiu, um custo que mudou):
            # esperar um pouco em vez de repetir, e o mundo anda.
            proposal = {
                "action": "wait",
                "params": {"ticks": int(self.config["wait_ticks"])},
                "intent": "esperar depois de uma recusa",
            }
        self.last["proposal"] = proposal
        self.bounds["exploring"] = int(proposal.get("intent") == EXPLORE)
        return proposal

    def _learn_terrain(self, view: View) -> None:
        """Guarda o recorte de terreno da foto e deduz as bordas do mapa. O recorte é centrado no
        avatar e cortado nas bordas: o raio sai de um lado esquerdo ou de cima que não foi cortado,
        e um lado direito ou de baixo mais curto que o raio é a borda. Sem raio conhecido (a foto
        sempre começa no canto: o mapa inteiro), não há o que explorar. Uma exploração recusada
        marca o alvo como sem caminho."""
        terrain = cast(Mapping[str, Any] | None, view.get("map"))
        if terrain is None:
            return
        if self.bounds.get("exploring") and _reason(view) == "action_rejected":
            target = self.bounds.get("target_x"), self.bounds.get("target_y")
            if target[0] is not None and target[1] is not None:
                self.unreachable.add((target[0], target[1]))
        origin = cast(Mapping[str, int], terrain.get("origin") or {"x": 0, "y": 0})
        rows = cast(Sequence[str], terrain["rows"])
        legend = cast(Mapping[str, Mapping[str, Any]], terrain["legend"])
        x0, y0 = int(origin["x"]), int(origin["y"])
        for dy, row in enumerate(rows):
            for dx, code in enumerate(row):
                entry = legend.get(code) or {}
                passable = bool(
                    cast(Mapping[str, Any], entry.get("properties") or {}).get("passable")
                )
                self.terrain[(x0 + dx, y0 + dy)] = (str(entry.get("kind")), passable)
        width = max((len(r) for r in rows), default=0)
        me = cast(Mapping[str, int], view["self"]["position"])
        cx, cy = int(me["x"]), int(me["y"])
        if x0 > 0:
            self.bounds["reach"] = cx - x0
        elif y0 > 0:
            self.bounds["reach"] = cy - y0
        reach = self.bounds.get("reach")
        if reach is None:
            return
        if x0 + width - 1 < cx + reach:
            self.bounds["width"] = x0 + width
        if y0 + len(rows) - 1 < cy + reach:
            self.bounds["height"] = y0 + len(rows)

    def frontier(self, me: Mapping[str, int]) -> tuple[int, int] | None:
        """O tile passável já visto mais perto, com um vizinho ainda não visto dentro do mapa."""
        if "reach" not in self.bounds:
            return None  # o mapa inteiro à vista
        width, height = self.bounds.get("width"), self.bounds.get("height")

        def unseen(x: int, y: int) -> bool:
            inside = x >= 0 and y >= 0 and (width is None or x < width)
            return inside and (height is None or y < height) and (x, y) not in self.terrain

        here = (int(me["x"]), int(me["y"]))
        best: tuple[int, tuple[int, int]] | None = None
        for (x, y), (_, passable) in self.terrain.items():
            if not passable or (x, y) in self.unreachable or (x, y) == here:
                continue
            if any(unseen(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                key = (max(abs(x - here[0]), abs(y - here[1])), (y, x))
                if best is None or key < best:
                    best = key
        if best is None:
            return None
        y, x = best[1]
        return x, y

    def _remember(self, view: View) -> list[Mapping[str, Any]]:
        """As coisas à vista e as lembradas fora da vista. Sem o terreno na foto, só as à vista."""
        current = cast(Sequence[Mapping[str, Any]], view["entities"])
        box = _visible_box(view)
        if box is None:
            return list(current)
        here = {str(e["entity_id"]) for e in current}
        for entity in current:
            if entity.get("position") is not None:
                self.memory[str(entity["entity_id"])] = entity
        for entity_id in sorted(self.memory):
            if entity_id not in here and _inside(box, self.memory[entity_id]["position"]):
                del self.memory[entity_id]  # estava à vista e sumiu: virou grama, foi comida...
        return [*current, *(e for i, e in sorted(self.memory.items()) if i not in here)]


EXPLORE = "explorar a fazenda"


def _reason(view: View) -> str:
    return str(cast(Mapping[str, Any], view.get("decision") or {}).get("reason", ""))


def _visible_box(view: View) -> tuple[int, int, int, int] | None:
    """O retângulo do terreno da foto: o que está à vista agora."""
    terrain = cast(Mapping[str, Any] | None, view.get("map"))
    if terrain is None:
        return None
    origin = cast(Mapping[str, int], terrain.get("origin") or {"x": 0, "y": 0})
    rows = cast(Sequence[str], terrain["rows"])
    width = max((len(r) for r in rows), default=0)
    return int(origin["x"]), int(origin["y"]), width, len(rows)


def _inside(box: tuple[int, int, int, int], where: Mapping[str, int]) -> bool:
    x0, y0, width, height = box
    return x0 <= int(where["x"]) < x0 + width and y0 <= int(where["y"]) < y0 + height


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
    def __init__(
        self,
        config: Mapping[str, Any],
        view: View,
        entities: Sequence[Mapping[str, Any]],
        script: Farmer2Script | None = None,
    ) -> None:
        self.c = config
        self.view = view
        self.script = script
        me = view["self"]
        self.me_id = str(me["entity_id"])
        self.pos: Mapping[str, int] = me["position"]
        needs = cast(Mapping[str, float], me["needs"])
        self.hunger = float(needs.get(config["needs"]["hunger"], 0))
        self.energy = float(needs.get(config["needs"]["energy"], 100))
        self.now = minutes(str(view["clock"]["sim_time"])[11:16])
        self.raining = view["weather"]["condition"] == config["rain"]
        self.entities = entities
        self.in_view = {str(e["entity_id"]) for e in view["entities"]}
        self.season = cast(str | None, view["clock"].get("season"))
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

    def water_cost(self) -> int:
        """As cargas de uma rega hoje: 1, ou o que a seca pede (ADR-0069)."""
        drought = cast(Mapping[str, Any] | None, self.c.get("drought"))
        if drought is not None and self.view["weather"]["condition"] == drought["condition"]:
            return int(drought["can_charges"])
        return 1

    def affordable(self, kiosk: Mapping[str, Any], seed: str, price: int, budget: int) -> int:
        """Quantas sementes cabem no orçamento, com o preço do quiosque subindo a cada unidade
        num mercado que lembra (ADR-0069); conta para cima, para não ser recusado."""
        shown = kiosk["attributes"].get(f"preco_{seed}")
        base = float(shown) if isinstance(shown, int | float) else float(price)
        step = float(cast(Mapping[str, Any], self.c.get("market") or {}).get("buy_step", 0.0))
        if step == 0.0 and not isinstance(shown, int | float):
            return max(0, budget // price)
        qty, spent = 0, 0
        while True:
            unit = int(base * (1.0 + step * qty)) + 1
            if spent + unit > budget:
                return qty
            spent += unit
            qty += 1

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
            self.deliver,
            self.accept,
            self.store,
            self.sell,
            self.buy,
            self.explore,
        ):
            proposal = rule()
            if proposal is not None:
                return proposal
        ticks = int(self.c["wait_ticks"])
        return {"action": "wait", "params": {"ticks": ticks}, "intent": "esperar"}

    def explore(self) -> Proposal | None:
        """Sem nada para fazer: de dia, com energia e sem fome, vai até a fronteira do que conhece
        (ADR-0067). Com o mapa inteiro à vista, nunca há fronteira."""
        rules = cast(Mapping[str, Any] | None, self.c.get("explore"))
        if self.script is None or rules is None:
            return None
        daytime = minutes(str(rules["from"])) <= self.now < minutes(str(rules["until"]))
        rested = self.energy >= float(rules["min_energy"])
        if not daytime or not rested or self.hunger >= float(rules["max_hunger"]):
            return None
        target = self.script.frontier(self.pos)
        if target is None:
            return None
        self.script.bounds["target_x"], self.script.bounds["target_y"] = target
        return {
            "action": "move",
            "params": {"target": {"x": target[0], "y": target[1]}},
            "intent": EXPLORE,
        }

    def food_crop(self) -> str:
        """A cultura da base de comida: a de sempre, ou, com estação na foto, a primeira da lista
        que cresce no ritmo cheio nesta estação (o rabanete fica fraco no verão)."""
        usual = str(self.c["food_crop"])
        if self.season is None:
            return usual
        options = [str(c) for c in cast(Sequence[Any], self.c.get("food_crops") or [usual])]
        return next((c for c in options if self._pace(c) >= 1.0), usual)

    def kind_at(self, x: int, y: int) -> str | None:
        """A classe do tile: pela foto, ou pelo terreno lembrado."""
        seen = _tile_kind(self.view, x, y)
        if seen is not None or self.script is None:
            return seen
        remembered = self.script.terrain.get((x, y))
        return None if remembered is None else remembered[0]

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
        cuida: um tile bom ao lado, cava; senão anda até o melhor. Sem a pá, não cava."""
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
            if (x, y) not in taken and self.kind_at(x, y) == GRASS
        ]
        if not candidates:
            if well["entity_id"] in self.in_view:
                return None
            near = {"near": well["entity_id"]}  # o terreno de lá não está à vista: vai ver
            return {"action": "move", "params": near, "intent": "ir para o poço cavar"}

        def closest_to_well(tile: tuple[int, int]) -> tuple[int, tuple[int, int]]:
            return abs(tile[0] - wx) + abs(tile[1] - wy), tile

        me = (self.pos["x"], self.pos["y"])
        near = [t for t in candidates if max(abs(t[0] - me[0]), abs(t[1] - me[1])) <= 1]
        if near:  # um tile bom ao lado (ou o seu): cava ali, como se rega
            x, y = min(near, key=closest_to_well)
            target = {"x": x, "y": y}
            return {"action": "dig", "params": {"target": target}, "intent": f"cavar em {x},{y}"}
        x, y = min(candidates, key=closest_to_well)
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
        if self.can_charges() >= self.water_cost() or not self.thirsty():
            return None
        well = self.nearest(self.of_kind("well"))
        return None if well is None else self.at(well, "refill", "encher o regador")

    def water(self) -> Proposal | None:
        plot = self.nearest(self.thirsty())
        if plot is None or self.can_charges() < self.water_cost():
            return None
        return self.at(plot, "water", f"regar {plot['entity_id']}", target=plot["entity_id"])

    def _pace(self, crop: str) -> float:
        """O ritmo da cultura na estação, pelo calendário do manual; 1 sem estação na foto."""
        if self.season is None:
            return 1.0
        calendar = cast(Mapping[str, Mapping[str, str]], self.c.get("calendar", {}))
        level = calendar.get(crop, {}).get(self.season)
        return 1.0 if level is None else float(self.c["season_pace"][level])

    def _best_crops(self) -> list[str]:
        """As culturas pela conta visível, da melhor à pior: (venda - semente) / dias, com os dias
        esticados pela estação; a cultura parada na estação fica de fora."""
        crops = cast(Mapping[str, Mapping[str, Any]], self.c["crops"])

        def gain(name: str) -> float:
            c = crops[name]
            return (float(c["sale"]) - float(c["price"])) * self._pace(name) / float(c["days"])

        return sorted((n for n in crops if self._pace(n) > 0), key=lambda n: (-gain(n), n))

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
        if kiosk is None:
            return None
        if kiosk["entity_id"] not in self.in_view:  # lembrado: vai até lá no horário do manual
            hours = cast(Mapping[str, str] | None, self.c.get("kiosk_hours"))
            opens = hours is not None and minutes(hours["opens"]) <= self.now
            if opens and hours is not None and self.now < minutes(hours["closes"]) - 30:
                return self._kiosk_errand(kiosk)
            return None
        if not kiosk["attributes"].get("open"):
            return None
        coins, reserve = self.mine("moeda"), int(self.c["coins_reserve"])
        crops = cast(Mapping[str, Mapping[str, Any]], self.c["crops"])
        food = self.food_crop()
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
            qty = min(food_missing, self.affordable(kiosk, food_seed, food_price, coins - reserve))
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
            qty = min(missing, self.affordable(kiosk, seed, price, coins - reserve))
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

    def _board_orders(self) -> tuple[Mapping[str, Any] | None, list[Mapping[str, Any]]]:
        """O quadro de encomendas e os pedidos à vista dentro dele: só perto do quadro se leem."""
        board = self.nearest(self.of_kind("order_board"))
        if board is None:
            return None, []
        kind = self.c["kinds"].get("order", "order")
        orders = [
            e
            for e in self.entities
            if e["kind"] == kind and e.get("container_id") == board["entity_id"]
        ]
        return board, sorted(orders, key=lambda e: e["entity_id"])

    def deliver(self) -> Proposal | None:
        """Entrega o pedido aceito quando tem os itens (ADR-0069)."""
        board, orders = self._board_orders()
        for order in orders:
            a = order["attributes"]
            if a.get("aceita_por") == self.me_id and self.mine(str(a["item"])) >= int(
                a["quantidade"]
            ):
                return self.at(
                    cast(Mapping[str, Any], board),
                    "deliver_order",
                    f"entregar a encomenda {order['entity_id']}",
                    target=cast(Mapping[str, Any], board)["entity_id"],
                    order=order["entity_id"],
                )
        return None

    def accept(self) -> Proposal | None:
        """Aceita, perto do quadro, o pedido aberto que já dá para cumprir com o que carrega: o
        script 2 não planta para encomenda (isso é do script 3)."""
        board, orders = self._board_orders()
        limits = cast(Mapping[str, Any] | None, self.c.get("orders"))
        if board is None or limits is None or not orders:
            return None
        mine = [o for o in orders if o["attributes"].get("aceita_por") == self.me_id]
        if len(mine) >= int(limits["max_taken"]):
            return None
        best = sorted(
            (o for o in orders if o["attributes"].get("aceita_por") is None),
            key=lambda o: (-int(o["attributes"]["pagamento"]), o["entity_id"]),
        )
        for order in best:
            a = order["attributes"]
            if self.mine(str(a["item"])) >= int(a["quantidade"]):
                return self.at(
                    board,
                    "accept_order",
                    f"aceitar a encomenda de {a['cliente']}",
                    target=board["entity_id"],
                    order=order["entity_id"],
                )
        return None

    def _kiosk_errand(self, kiosk: Mapping[str, Any]) -> Proposal | None:
        """Vai ao quiosque lembrado quando faltam sementes para os canteiros vazios."""
        crops = cast(Mapping[str, Mapping[str, Any]], self.c["crops"])
        held = sum(self.mine(str(c["seed"])) for c in crops.values())
        food_price = int(crops[self.food_crop()]["price"])
        if len(self.plots(None)) <= held or self.mine("moeda") < food_price + int(
            self.c["coins_reserve"]
        ):
            return None
        return {
            "action": "move",
            "params": {"near": kiosk["entity_id"]},
            "intent": "ir ao quiosque comprar sementes",
        }
