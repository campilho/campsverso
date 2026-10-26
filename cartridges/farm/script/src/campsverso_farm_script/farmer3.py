"""Fazendeiro-script 3 (ADR-0070; plano do M19, §2): planeja o capital e experimenta.

A linha de base honesta: vê o que o LLM vê (a mesma foto, o mesmo catálogo) e não sabe nenhuma
regra oculta. Sobre a base do script 2 (a lembrança, o terreno, a exploração, comer e dormir):

- **O caderno de campo:** anota cada plantio (onde, que cultura, a anterior do canteiro, se foi
  adubado, os dias de rega, quando amadureceu e o que aconteceu) só com o que viu.
- **O modelo** (`knowledge.py`): aprende do caderno o ritmo de cada lugar pelos atributos do mapa
  e a chance de perder a planta madura.
- **A amostragem de Thompson:** a cada manhã sorteia um mundo da crença e planeja para ele: onde
  cavar, o que plantar, que canteiro deixar voltar a ser grama, quando fincar um espantalho.
- **Os pares de teste:** os primeiros canteiros vão em pares, um no melhor lugar que ele conhece
  e outro no lugar em que a crença é mais incerta, com a mesma cultura.
- **A economia:** vende sem afundar o preço (conta o que já está crescendo de cada cultura),
  guarda para a feira, aceita a encomenda que dá para cumprir, faz adubo com os restos.
- **Os ajudantes** (ADR-0072): contrata quando os canteiros que o caixa pede passam dos que ele
  cuida sozinho e o que os canteiros a mais rendem paga a diária, com folga; a diária e quem está
  livre vêm do quadro. Busca no baú a colheita fresca que o ajudante deixa lá, e não aprende
  nada sobre perdas nos dias em que um ajudante trabalhou (não sabe quem colheu).

O oráculo (§3) é este mesmo script com o modelo trocado pela verdade.
"""

import math
import random
from collections import Counter, deque
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

import yaml

from campsverso_farm_script.farmer import Proposal, View, minutes
from campsverso_farm_script.farmer2 import DATA as FARMER2
from campsverso_farm_script.farmer2 import GRASS, Farmer2Script, Turn2, reason_of
from campsverso_farm_script.knowledge import Beliefs, Knowledge, Spot, Tile, Truth, World

DATA = Path(__file__).parent / "data" / "farmer3.yaml"
ORACLE = Path(__file__).parent / "data" / "oracle.yaml"
WATER = frozenset({"river"})
TREES = frozenset({"tree"})
PATHS = frozenset({"path", "entrance"})


def _merged(base: Mapping[str, Any], over: Mapping[str, Any]) -> dict[str, Any]:
    """O arquivo do script 3 por cima do script 2, chave por chave (os dicionários se mesclam)."""
    out = dict(base)
    for key, value in over.items():
        below = out.get(key)
        if isinstance(below, Mapping) and isinstance(value, Mapping):
            out[key] = {**cast(Mapping[str, Any], below), **cast(Mapping[str, Any], value)}
        else:
            out[key] = value
    return out


def load_config(*overlays: Path) -> dict[str, Any]:
    config = cast(dict[str, Any], yaml.safe_load(FARMER2.read_text(encoding="utf-8")))
    for path in (DATA, *overlays):
        config = _merged(config, cast(Mapping[str, Any], yaml.safe_load(path.read_text("utf-8"))))
    return config


@dataclass
class Planting:
    """Uma linha do caderno de campo."""

    plot: str
    tile: Tile
    crop: str
    day: int
    previous: str | None
    fertilized: bool
    test: bool = False
    watered: set[int] = field(default_factory=set[int])
    seen_unripe: int = 0  # o último dia em que foi vista sem estar madura
    ripe_day: int | None = None
    outcome: str | None = None  # colhida, perdida, murcha


@dataclass
class Notebook:
    """O que o script 3 anotou e aprendeu nesta sessão."""

    beliefs: Knowledge
    rng: random.Random
    active: dict[str, Planting] = field(default_factory=dict[str, Planting])
    closed: list[Planting] = field(default_factory=list[Planting])
    last_crop: dict[str, str] = field(default_factory=dict[str, str])
    fertilized: set[str] = field(default_factory=set[str])
    tests: set[str] = field(default_factory=set[str])  # canteiros cavados como teste
    rain_days: set[int] = field(default_factory=set[int])
    storm_days: set[int] = field(default_factory=set[int])
    abandoned: set[str] = field(default_factory=set[str])
    seen: dict[str, int] = field(default_factory=dict[str, int])  # o dia em que viu cada canteiro
    # A comida (nota do usuário, ADR-0070): a fome que cada coisa comida tirou, e a fome de agora.
    meals: dict[str, list[float]] = field(default_factory=dict[str, list[float]])
    hunger: float | None = None
    digs: int = 0
    plantings: int = 0  # os plantios feitos: a cada `test_every`, um canteiro de teste a mais
    pending_tests: int = 0
    world_day: int = 0
    world: World | None = None
    distances: dict[str, dict[Tile, int]] = field(default_factory=dict[str, dict[Tile, int]])
    distances_key: tuple[int, Tile | None] = (0, None)
    # Os ajudantes (ADR-0072): os contratos (quem, o primeiro e o último dia).
    contracts: list[tuple[str, int, int]] = field(default_factory=list[tuple[str, int, int]])

    def helper_on(self, day: int) -> str | None:
        """O ajudante contratado para o dia, se houver."""
        return next((h for h, first, last in self.contracts if first <= day <= last), None)


class Farmer3Script(Farmer2Script):
    """O script 2 com o caderno, o modelo e o planejamento; com `truth` no arquivo, a crença dá
    lugar à verdade (o oráculo)."""

    notes: Notebook  # o caderno da sessão; o script 2 é imutável, e o caderno se troca inteiro

    def __init__(self, config: Mapping[str, Any]) -> None:
        super().__init__(config)
        object.__setattr__(self, "notes", self._fresh())

    @classmethod
    def load(cls) -> Farmer3Script:
        return cls(load_config())

    @classmethod
    def oracle(cls) -> Farmer3Script:
        """O oráculo (ADR-0070, decisão 6): o mesmo script, com a verdade no lugar da crença."""
        return cls(load_config(ORACLE))

    def configured(self, overrides: Mapping[str, Any]) -> Farmer3Script:
        """Uma instância nova, com o arquivo trocado chave por chave (ex.: a contratação forçada
        das medidas de 1, 3 e 7 dias; ADR-0073)."""
        return type(self)(_merged(self.config, overrides))

    def _fresh(self) -> Notebook:
        beliefs = Beliefs(cast(Mapping[str, Any], self.config["model"]))
        truth = cast(Mapping[str, Any] | None, self.config.get("truth"))
        knowledge: Knowledge = beliefs if truth is None else Truth(truth, beliefs)
        return Notebook(knowledge, self._rng())

    def _rng(self) -> random.Random:
        return random.Random(int(self.config["seed"]))

    @property
    def book(self) -> Notebook:
        return self.notes

    def today(self, day: int) -> World:
        """O mundo de hoje: sorteado da crença uma vez por dia (Thompson)."""
        book = self.book
        if book.world is None or book.world_day != day:
            book.world = self.sample(book)
            book.world_day = day
        return book.world

    def sample(self, book: Notebook) -> World:
        return book.beliefs.world(book.rng)

    def decide(self, view: View) -> Proposal:
        tick = int(view["clock"]["tick"])
        if tick < self.bounds.get("tick", 0):  # outra sessão: o caderno recomeça
            object.__setattr__(self, "notes", self._fresh())
        return super().decide(view)

    def _turn(self, view: View, entities: Sequence[Mapping[str, Any]]) -> Turn2:
        """Antes de decidir, anota o que a última ação fez e o que a foto mostra."""
        last = self.last.get("proposal")
        if last is not None:
            self._learn(view, last)
        day = int(view["clock"]["day"])
        for entity in view["entities"]:
            if entity["kind"] == "plot":
                self.book.seen[str(entity["entity_id"])] = day
        return Turn3(self.config, view, [self._today(e, day) for e in entities], self)

    def _today(self, entity: Mapping[str, Any], day: int) -> Mapping[str, Any]:
        """Um canteiro lembrado de outro dia: a rega daquele dia já passou."""
        if entity["kind"] != "plot" or self.book.seen.get(str(entity["entity_id"]), day) >= day:
            return entity
        attributes = {**cast(Mapping[str, Any], entity["attributes"]), "watered_today": False}
        return {**entity, "attributes": attributes}

    # ------------------------------------------------------------- o caderno de campo

    def _learn(self, view: View, last: Proposal) -> None:
        """Anota o que a última ação fez e o que a foto mostra dos canteiros."""
        book = self.book
        day = int(view["clock"]["day"])
        if view["weather"]["condition"] in (self.config["rain"], "storm"):
            book.rain_days.add(day)
        if view["weather"]["condition"] == "storm":
            book.storm_days.add(day)
        done = reason_of(view) == "action_completed"
        params = cast(Mapping[str, Any], last.get("params") or {})
        target = str(params.get("target"))
        near = params.get("near")
        here = {str(e["entity_id"]) for e in view["entities"]}
        if reason_of(view) == "action_rejected" and isinstance(near, str) and near not in here:
            self.memory.pop(
                near, None
            )  # a coisa lembrada sumiu fora da vista (o canteiro virou grama)
        if done and last["action"] == "plant" and target in self.memory:
            tile = _tile(self.memory[target]["position"])
            crop = str(params["crop"])
            book.active[target] = Planting(
                target,
                tile,
                crop,
                day,
                book.last_crop.get(target),
                target in book.fertilized,
                test=target in book.tests,
                seen_unripe=day,
            )
            book.fertilized.discard(target)
            book.last_crop[target] = crop
            book.plantings += 1
            if (
                book.plantings % int(cast(Mapping[str, Any], self.config["model"])["test_every"])
                == 0
            ):
                book.pending_tests += 1
        elif done and last["action"] == "harvest" and target in book.active:
            self._close(book.active.pop(target), "colhida", day)
        elif done and last["action"] == "fertilize":
            book.fertilized.add(target)
        elif done and last["action"] == "clear" and target in book.active:
            self._close(book.active.pop(target), "murcha", day)
        elif done and last["action"] == "hire_helper":
            first = day + 1  # o ajudante chega na manhã seguinte
            book.contracts.append((str(params["helper"]), first, first + int(params["days"]) - 1))
        needs = cast(Mapping[str, float], view["self"]["needs"])
        now = float(needs.get(str(self.config["needs"]["hunger"]), 0))
        if done and last["action"] == "eat" and book.hunger is not None:
            book.meals.setdefault(str(params.get("item")), []).append(book.hunger - now)
        book.hunger = now
        visible = {str(e["entity_id"]): e for e in view["entities"] if e["kind"] == "plot"}
        for plot, planting in list(book.active.items()):
            seen = visible.get(plot)
            if seen is None:
                if plot not in self.memory:  # o canteiro sumiu: a planta se perdeu antes
                    self._close(book.active.pop(plot), "perdida", day)
                continue
            attributes = cast(Mapping[str, Any], seen["attributes"])
            if attributes.get("watered_today"):
                planting.watered.add(day)
            stage = attributes.get("stage")
            if attributes.get("crop") is None:
                self._close(book.active.pop(plot), "perdida", day)
            elif stage == "murcha":
                self._close(book.active.pop(plot), "murcha", day)
            elif stage == self.config["stages"]["ripe"]:
                if planting.ripe_day is None and planting.seen_unripe >= day - 1:
                    planting.ripe_day = day
                    self._measure(planting)
            else:
                planting.seen_unripe = day

    def _close(self, planting: Planting, outcome: str, day: int) -> None:
        book = self.book
        planting.outcome = outcome
        book.closed.append(planting)
        if outcome == "perdida" and day in book.storm_days:
            return  # a tempestade está à vista: não é uma regra do lugar
        if outcome == "perdida" and book.helper_on(day) is not None:
            planting.outcome = "sumiu"  # um ajudante pode ter colhido: não se sabe quem levou
            return
        if outcome in ("colhida", "perdida"):
            door, guard = self.place_of(planting.tile)
            book.beliefs.learn_loss(door, guard, outcome == "perdida")

    def _measure(self, planting: Planting) -> None:
        """O ritmo de um plantio que amadureceu à vista, com todos os dias regados."""
        book = self.book
        assert planting.ripe_day is not None
        days = range(planting.day, planting.ripe_day)
        if any(d not in planting.watered and d not in book.rain_days for d in days):
            return  # um dia sem rega: a medida não diz nada do lugar
        points = float(self.config["crops"][planting.crop]["days"])
        grown = [
            self.pace_on(planting.crop, d) for d in range(planting.day + 1, planting.ripe_day + 1)
        ]
        before, after = sum(grown[:-1]), sum(grown)
        middle = (before + after) / 2 if before > 0 else after * 0.75
        if middle <= 0:
            return
        spot = self.spot(planting.tile, planting.crop, planting.previous, planting.fertilized)
        book.beliefs.learn_growth(spot, math.log(points / middle))

    # ------------------------------------------------------------- o mapa

    def season_on(self, day: int) -> str:
        year = cast(Mapping[str, Any], self.config["year"])
        seasons = cast(Sequence[str], year["seasons"])
        return seasons[((day - 1) // int(year["season_days"])) % len(seasons)]

    def pace_on(self, crop: str, day: int) -> float:
        calendar = cast(Mapping[str, Mapping[str, str]], self.config["calendar"])
        level = calendar.get(crop, {}).get(self.season_on(day))
        return 1.0 if level is None else float(self.config["season_pace"][level])

    def door(self) -> Tile | None:
        found = next((e for e in self.memory.values() if e["kind"] == "door"), None)
        return None if found is None else _tile(found["position"])

    def distance_maps(self) -> dict[str, dict[Tile, int]]:
        """A distância de cada tile conhecido à água, à mata e ao caminho: refeitas quando o
        terreno conhecido cresce (de 50 em 50 tiles) ou a porta aparece."""
        book = self.book
        key = (len(self.terrain) // 50, self.door())
        if key != book.distances_key:
            book.distances = {
                name: _spread(
                    {t for t, (kind, _) in self.terrain.items() if kind in kinds}, self.terrain
                )
                for name, kinds in (("agua", WATER), ("mata", TREES), ("caminho", PATHS))
            }
            book.distances_key = key
        return book.distances

    def spot(self, tile: Tile, crop: str, previous: str | None, fertilized: bool) -> Spot:
        maps = self.distance_maps()
        door = self.door()
        far = 999
        distances: list[int] = []
        for name in cast(Sequence[str], self.config["model"]["distances"]):
            if name == "porta":
                distances.append(far if door is None else _chebyshev(tile, door))
            else:
                distances.append(maps.get(name, {}).get(tile, far))
        return Spot(tuple(distances), previous == crop, fertilized)

    def place_of(self, tile: Tile) -> tuple[int, int | None]:
        """A distância do tile à porta e ao espantalho mais perto (as faixas da perda)."""
        door = self.door()
        guards = [
            _chebyshev(tile, _tile(e["position"]))
            for e in self.memory.values()
            if e["kind"] == self.config["scarecrow"]["kind"] and e.get("position") is not None
        ]
        return (0 if door is None else _chebyshev(tile, door)), min(guards, default=None)


class Turn3(Turn2):
    """Uma decisão do script 3: as prioridades do script 2, com as escolhas do planejamento."""

    script: Farmer3Script  # pyright: ignore[reportIncompatibleVariableOverride]

    def __init__(
        self,
        config: Mapping[str, Any],
        view: View,
        entities: Sequence[Mapping[str, Any]],
        script: Farmer3Script,
    ) -> None:
        super().__init__(config, view, entities, script)
        self.script = script
        self.book = script.book
        self.day = int(view["clock"]["day"])
        # O mundo sorteado (Thompson) escolhe onde cavar: é onde explorar vale. O plano do que
        # plantar e comprar usa o mundo médio da crença, para a comida não depender da sorte.
        self.sampled = script.today(self.day)
        self.world = script.book.beliefs.world()

    def decide(self) -> Proposal:
        for rule in (
            self.sleep,
            self.eat,
            self.harvest,
            self.clear,
            self.refill,
            self.water,
            self.fertilize,
            self.plant,
            self.deliver,
            self.accept,
            self.guard,
            self.compost,
            self.collect,
            self.store,
            self.fetch,
            self.sell,
            self.hire,
            self.buy,
            self.dig,
            self.explore,
        ):
            proposal = rule()
            if proposal is not None:
                return proposal
        ticks = int(self.c["wait_ticks"])
        return {"action": "wait", "params": {"ticks": ticks}, "intent": "esperar"}

    # ------------------------------------------------------------- a conta

    def price(self, crop: str, extra: Mapping[str, int] | None = None) -> float:
        """O preço que a caixa mostra agora, descontado o que já está crescendo da cultura (e o
        que o plano ainda vai plantar)."""
        box = self.nearest(self.of_kind("sell_box"))
        table = float(self.c["crops"][crop]["sale"])
        shown = None if box is None else box["attributes"].get(f"preco_{crop}")
        now = float(shown) if isinstance(shown, int | float) else table
        market = cast(Mapping[str, Any], self.c["market"])
        growing = sum(1 for p in self.book.active.values() if p.crop == crop)
        growing += (extra or {}).get(crop, 0)
        drop = float(market["sell_step"]) * growing / 2
        return now * max(float(market["floor"]), 1.0 - drop)

    def days(self, crop: str, tile: Tile, plot: str | None = None) -> float:
        """Os dias até amadurecer, plantando hoje: o ritmo do mundo de hoje neste lugar, dia a dia
        pelo calendário (a estação que vem conta); infinito se não amadurece em 30 dias."""
        if self._pace(crop) <= 0:
            return math.inf
        previous = None if plot is None else self.book.last_crop.get(plot)
        fertilized = plot is not None and plot in self.book.fertilized
        speed = self.world.speed(self.script.spot(tile, crop, previous, fertilized))
        points = float(self.c["crops"][crop]["days"])
        grown, day = 0.0, self.day
        while grown < points:
            day += 1
            if day > self.day + 30:
                return math.inf
            grown += self.script.pace_on(crop, day) * speed
        return float(day - self.day)

    def value(
        self, crop: str, tile: Tile, plot: str | None = None, extra: Mapping[str, int] | None = None
    ) -> float:
        """O que um plantio rende por dia neste lugar, no mundo de hoje (moedas por dia)."""
        days = self.days(crop, tile, plot)
        if days == math.inf:
            return -math.inf
        info = cast(Mapping[str, Any], self.c["crops"][crop])
        door, guard = self.script.place_of(tile)
        keep = 1.0 - self.world.loss(door, guard)
        energy = float(self.c["energy_price"])
        cycle = 3 * energy  # plantar e colher
        return (self.price(crop, extra) * keep - float(info["price"]) - cycle) / days

    def overhead(self, tile: Tile) -> float:
        """A caminhada diária até o lugar, dividida pelos canteiros que estão juntos."""
        anchors = [_tile(p["position"]) for p in self.of_kind("plot") if p.get("position")]
        well = self.nearest(self.of_kind("well"))
        if well is not None:
            anchors.append(_tile(well["position"]))
        walk = min((_chebyshev(tile, a) for a in anchors), default=0)
        cost = float(self.c["energy_price"]) * float(self.c["walk_energy_per_tile"])
        return cost * 2 * walk / float(self.c["share"])

    def _home(self) -> Tile:
        well = self.nearest(self.of_kind("well"))
        return _tile(well["position"]) if well is not None else _tile(self.pos)

    def worth(self, tile: Tile, crop: str) -> float:
        return self.value(crop, tile) - self.overhead(tile)

    # ------------------------------------------------------------- canteiros

    def active_plots(self) -> list[Mapping[str, Any]]:
        return [p for p in self.of_kind("plot") if p["entity_id"] not in self.book.abandoned]

    def target(self) -> int:
        """Os canteiros que cuida: começa com os do script 2 e cresce com o caixa."""
        rules = cast(Mapping[str, Any], self.c["plots"])
        grown = int(rules["start"]) + self.mine("moeda") // int(rules["coins_per_plot"])
        return min(int(rules["max"]), grown)

    def seeds_held(self) -> int:
        crops = cast(Mapping[str, Mapping[str, Any]], self.c["crops"])
        return sum(self.mine(str(c["seed"])) for c in crops.values())

    def empty_plots(self) -> list[Mapping[str, Any]]:
        return [p for p in self.active_plots() if p["attributes"].get("crop") is None]

    def candidates(self) -> list[Tile]:
        """A grama conhecida onde dá para cavar: livre, alcançável e não marcada sem caminho."""
        taken = {
            _tile(e["position"])
            for e in self.entities
            if e.get("position") is not None and e["entity_id"] != self.me_id
        }
        return sorted(
            t
            for t, (kind, _) in self.script.terrain.items()
            if kind == GRASS and t not in taken and t not in self.script.unreachable
        )

    def dig(self) -> Proposal | None:
        """Cava o próximo canteiro no lugar que o mundo de hoje diz render mais; nos pares de
        teste, um sim e outro não vai para o lugar mais incerto."""
        rules = cast(Mapping[str, Any], self.c["dig"])
        if self.held("spade") is None or self.energy < float(rules["min_energy"]):
            return None
        model = cast(Mapping[str, Any], self.c["model"])
        initial = self.book.digs < 2 * int(model["test_pairs"])
        extra = self.book.pending_tests > 0 and not initial and int(model["test_pairs"]) > 0
        full = len(self.active_plots()) >= self.target()
        if self.now >= minutes(str(rules["until"])) or (full and not extra):
            return None
        if self.view.get("map") is None:
            return None
        if self.seeds_held() <= len(self.empty_plots()):
            return None  # só cava para a semente que já espera: um canteiro vazio volta a ser grama
        crop = self.food_crop()
        tiles = self.candidates()
        if not tiles:
            return None
        digs = self.book.digs
        testing = bool(digs % 2) if initial else extra
        if testing and int(model["test_pairs"]) > 0:
            far = [
                t
                for t in tiles
                if all(_chebyshev(t, _tile(p["position"])) > 4 for p in self.of_kind("plot"))
            ]
            tile = max(far or tiles, key=lambda t: (self.novelty(t, crop), t))
        else:
            mean, self.world = self.world, self.sampled
            try:
                tile = max(tiles, key=lambda t: (self.worth(t, crop), (-t[1], -t[0])))
            finally:
                self.world = mean
        me = _tile(self.pos)
        target = {"x": tile[0], "y": tile[1]}
        if _chebyshev(me, tile) <= 1:
            if testing:
                self.book.tests.add(f"@{tile[0]},{tile[1]}")
                if not initial:
                    self.book.pending_tests -= 1
            self.book.digs += 1
            return {"action": "dig", "params": {"target": target}, "intent": f"cavar em {tile}"}
        return {"action": "move", "params": {"target": target}, "intent": f"ir cavar em {tile}"}

    def novelty(self, tile: Tile, crop: str) -> float:
        """O que um plantio aqui ensinaria: a soma, nos atributos do tile, de quão pouco cada um
        foi medido (o que nunca foi medido vale 1). Vale igual para todos os atributos."""
        beliefs = self.book.beliefs
        spot = self.script.spot(tile, crop, None, False)
        x = Beliefs(cast(Mapping[str, Any], self.c["model"])).features(spot)
        counts = beliefs.counts
        return sum(1.0 / (1 + counts[i]) for i, a in enumerate(x) if a and i > 0)

    def fertilize(self) -> Proposal | None:
        """Aduba o canteiro vazio antes de plantar, quando tem adubo e o mundo de hoje diz que
        vale (o manual diz que faz crescer melhor)."""
        item = str(self.c["fertilizer"]["item"])
        if self.mine(item) < 1:
            return None
        plots = [p for p in self.empty_plots() if p["entity_id"] not in self.book.fertilized]
        plot = self.nearest(plots)
        if plot is None:
            return None
        tile = _tile(plot["position"])
        spot = self.script.spot(tile, "", None, True)
        plain = self.script.spot(tile, "", None, False)
        if self.world.speed(spot) <= self.world.speed(plain) * 1.05:
            return None
        return self.at(plot, "fertilize", f"adubar {plot['entity_id']}", target=plot["entity_id"])

    def plant(self) -> Proposal | None:
        """Planta no canteiro vazio mais perto. As regras de sobrevivência vêm antes (ADR-0070):
        enquanto faltam canteiros de comida (M), a comida da estação, revezando quando o modelo
        aprende que repetir cansa; os outros (N) recebem a semente que mais rende neles. Deixa
        voltar a grama o canteiro que rende bem menos que um lugar novo."""
        if self.now >= minutes(str(self.c["plant_until"])):
            return None
        crops = cast(Mapping[str, Mapping[str, Any]], self.c["crops"])
        held = [c for c in crops if self.mine(str(crops[c]["seed"])) > 0]
        if not held:
            return None
        foods, _ = self.food_plan()
        hungry = self.food_growing() < self.food_plots()
        for plot in sorted(self.empty_plots(), key=lambda p: (self._walk(p), p["entity_id"])):
            pid, tile = str(plot["entity_id"]), _tile(plot["position"])
            self._mark_test(pid, tile)
            food = [c for c in foods if c in held]
            if self.book.digs <= 2 * int(self.c["model"]["test_pairs"]):
                # Os pares de teste: a mesma cultura nos dois lugares, a mais rápida que tem.
                choice = min(held, key=lambda c: (float(crops[c]["days"]), c))
            elif hungry and food:
                choice = self.best_food(food, tile, pid)
            else:
                if self._abandon(pid, tile):
                    continue
                choice = max(held, key=lambda c: (self.value(c, tile, pid), c))
            if choice == self.book.last_crop.get(pid) and self.tired() and self._kiosk_today():
                continue  # repetir cansa o canteiro: espera a semente de outra cultura
            if self.value(choice, tile, pid) == -math.inf:
                continue
            return self.at(plot, "plant", f"plantar {choice} em {pid}", target=pid, crop=choice)
        return None

    # ------------------------------------------------------------- sobreviver (ADR-0070)

    def hunger_per_day(self) -> float:
        """A fome de um dia, pelo ritmo do manual: as horas acordado e as horas dormindo."""
        rules = cast(Mapping[str, Any], self.c["survival"])
        rates = cast(Mapping[str, float], rules["hunger_per_hour"])
        awake = float(rules["awake_hours"])
        return float(rates["awake"]) * awake + float(rates["asleep"]) * (24 - awake)

    def hunger_of(self, crop: str) -> float:
        foods = cast(Mapping[str, Mapping[str, int]], self.c["foods"])
        return float(foods[crop]["hunger"]) if crop in foods else 0.0

    def eat(self) -> Proposal | None:
        """Come com a fome no limite do manual (60): primeiro o prato pronto (dura 2 dias), depois
        o que custa menos por ponto de fome, o preço de venda dividido pela fome que tira (a
        anotada no caderno, quando já comeu; senão a da tabela). Com 2 batatas, a sopa."""
        if self.hunger < float(self.c["hunger_eat_at"]):
            return None
        dishes = [d for d in cast(Sequence[str], self.c["dishes"]) if self.mine(d) > 0]
        if dishes:
            return {"action": "eat", "params": {"item": dishes[0]}, "intent": f"comer {dishes[0]}"}
        soup = cast(Mapping[str, Any], self.c["soup"])
        stove = self.nearest(self.of_kind("stove"))
        if stove is not None and all(
            self.mine(i) >= q for i, q in cast(Mapping[str, int], soup["needs"]).items()
        ):
            recipe = str(soup["recipe"])
            return self.at(
                stove, "cook", f"cozinhar {recipe}", target=stove["entity_id"], recipe=recipe
            )
        foods = sorted(
            cast(Mapping[str, Mapping[str, int]], self.c["foods"]),
            key=lambda f: (self.food_cost(f), f),
        )
        held = [f for f in foods if self.mine(f) > 0]
        if held:
            return {"action": "eat", "params": {"item": held[0]}, "intent": f"comer {held[0]}"}
        chest = self.nearest(self.of_kind("chest"))
        if chest is None:
            return None
        stored = [f for f in foods if self.stock.get(str(chest["entity_id"]), {}).get(f, 0) > 0]
        return (
            None
            if not stored
            else self.at(chest, "withdraw", f"pegar {stored[0]}", item=stored[0], qty=1)
        )

    def food_cost(self, item: str) -> float:
        """Moedas por ponto de fome: o que se deixa de vender para matar a fome."""
        foods = cast(Mapping[str, Mapping[str, int]], self.c["foods"])
        seen = self.book.meals.get(item)
        killed = sum(seen) / len(seen) if seen else float(foods[item]["hunger"])
        return float(foods[item]["sale"]) / max(1.0, killed)

    def _kiosk_today(self) -> bool:
        """Ainda dá para ir ao quiosque hoje."""
        hours = cast(Mapping[str, str], self.c["kiosk_hours"])
        return self.now < minutes(hours["closes"]) - 60

    def feeds(self, crop: str, tile: Tile, plot: str | None = None) -> float:
        """A fome que esta cultura mata por dia neste canteiro, plantando hoje."""
        return self.hunger_of(crop) / self.days(crop, tile, plot)

    def best_food(self, options: Sequence[str], tile: Tile, plot: str | None) -> str:
        """A comida de um canteiro: a que mais mata a fome por dia nele; entre as que ficam a
        menos de 10% disso, a que mais rende (a fome primeiro, o dinheiro no empate)."""
        top = max(self.feeds(c, tile, plot) for c in options)
        close = [c for c in options if self.feeds(c, tile, plot) >= 0.9 * top]
        return max(close, key=lambda c: (self.value(c, tile, plot), c))

    def food_plan(self) -> tuple[list[str], float]:
        """As comidas da estação, da que mais mata a fome por dia de canteiro à que menos, entre
        as de semente barata, e a fome por dia de canteiro da melhor."""
        crops = cast(Mapping[str, Mapping[str, Any]], self.c["crops"])
        rules = cast(Mapping[str, Any], self.c["survival"])
        home = self._home()
        cheap = [
            c
            for c in crops
            if self.hunger_of(c) > 0 and float(crops[c]["price"]) <= float(rules["food_seed_max"])
        ]
        ranked = sorted(
            (c for c in cheap if self.feeds(c, home) > 0), key=lambda c: (-self.feeds(c, home), c)
        )
        return ranked, (self.feeds(ranked[0], home) if ranked else 0.0)

    def food_plots(self) -> int:
        """M, os canteiros que matam a fome de cada dia, com a folga do manual; os outros são N,
        os de vender."""
        _, rate = self.food_plan()
        if rate <= 0:
            return 0
        margin = float(self.c["survival"]["margin"])
        return min(self.target(), math.ceil(self.hunger_per_day() * margin / rate))

    def food_growing(self) -> int:
        foods, _ = self.food_plan()
        return sum(1 for p in self.book.active.values() if p.crop in foods)

    def food_cash(self) -> float:
        """O caixa da semente da próxima leva da comida, que não se investe: a de metade dos
        canteiros de comida (eles não esvaziam todos no mesmo dia)."""
        foods, _ = self.food_plan()
        if not foods:
            return 0.0
        price = float(self.c["crops"][foods[0]]["price"])
        return math.ceil(self.food_plots() / 2) * price

    def tired(self) -> bool:
        """O modelo aprendeu, com 90% de confiança, que repetir a cultura no canteiro atrasa a
        planta."""
        effects = {e.name: e for e in self.book.beliefs.effects()}
        repeat = effects.get("repetida")
        return repeat is not None and repeat.high < float(self.c["rotation"]["below"])

    def _walk(self, plot: Mapping[str, Any]) -> int:
        return _chebyshev(_tile(self.pos), _tile(plot["position"]))

    def _mark_test(self, pid: str, tile: Tile) -> None:
        mark = f"@{tile[0]},{tile[1]}"
        if mark in self.book.tests:
            self.book.tests.discard(mark)
            self.book.tests.add(pid)

    def _abandon(self, pid: str, tile: Tile) -> bool:
        """Com pelo menos 10 plantios medidos, o canteiro que, pelo mundo médio da crença, rende
        menos que 70% do melhor lugar novo fica vazio e volta a ser grama. O mundo médio, e não
        o sorteado: o melhor de mil sorteios é sempre otimista."""
        if pid in self.book.tests or self.book.beliefs.counts[0] < int(
            self.c["move"]["min_measured"]
        ):
            return False
        crop = self.food_crop()
        here = self.value(crop, tile, pid)
        best = max((self.worth(t, crop) for t in self.candidates()), default=-math.inf)
        if best <= 0 or here >= float(self.c["move"]["keep_ratio"]) * best:
            return False
        self.book.abandoned.add(pid)
        return True

    # ------------------------------------------------------------- os ajudantes (ADR-0072)

    def helper_plots(self, helper: str | None) -> int:
        """Os canteiros que a ficha cuida, pela leitura dele das fichas públicas."""
        rules = cast(Mapping[str, Any] | None, self.c.get("helpers"))
        if helper is None or rules is None:
            return 0
        return int(cast(Mapping[str, int], rules["plots"]).get(helper, 0))

    def plot_value(self) -> float:
        """O que um canteiro de vender rende por dia, hoje, no lugar de sempre."""
        crops = [c for c in cast(Mapping[str, Any], self.c["crops"]) if self._pace(c) > 0]
        home = self._home()
        return max((self.value(c, home) for c in crops), default=0.0)

    def helper_gain(self, helper: str) -> float:
        """O que o ajudante rende por dia: os canteiros que o caixa pede e que o Camps não dá
        conta de cuidar sozinho, até os que a ficha cuida, pelo que um canteiro rende."""
        rules = cast(Mapping[str, Any], self.c["helpers"])
        plots = cast(Mapping[str, Any], self.c["plots"])
        grown = int(plots["start"]) + self.mine("moeda") // int(plots["coins_per_plot"])
        wanted = min(int(plots["max"]), grown)
        extra = min(self.helper_plots(helper), max(0, wanted - int(rules["solo"])))
        return extra * max(0.0, self.plot_value())

    def hire(self) -> Proposal | None:
        """Contrata no quadro quando o ajudante rende mais que a diária, com a folga do arquivo,
        e o caixa paga o contrato inteiro sem tocar na reserva, no caixa da comida e na folga de
        investir. Entre as fichas livres e os contratos que cabem no ano, o que mais sobra. Com
        `force`, contrata aquela ficha por aqueles dias sempre que pode (os experimentos)."""
        rules = cast(Mapping[str, Any] | None, self.c.get("helpers"))
        if rules is None or not rules.get("enabled"):
            return None
        board = self.nearest(self.of_kind(str(rules["board_kind"])))
        if board is None or self.book.helper_on(self.day + 1) is not None:
            return None  # sem quadro, ou amanhã já tem ajudante
        if not minutes(str(rules["from"])) <= self.now < minutes(str(rules["until"])):
            return None
        if self.day < int(rules["from_day"]):
            return None  # a primeira semana é a do caixa mais apertado: contratar ali é apostar
        year = cast(Mapping[str, Any], self.c["year"])
        left = int(year["season_days"]) * len(cast(Sequence[str], year["seasons"])) - self.day
        cash = (
            self.mine("moeda")
            - int(self.c["coins_reserve"])
            - self.food_cash()
            - int(self.c["invest_floor"])
        )
        force = cast(Mapping[str, Any] | None, rules.get("force"))
        attributes = cast(Mapping[str, Any], board["attributes"])
        best: tuple[float, str, int] | None = None
        for helper in sorted(cast(Mapping[str, int], rules["plots"])):
            key = helper.replace("-", "_")
            wage = attributes.get(f"diaria_{key}")
            if attributes.get(key) != "livre" or not isinstance(wage, int | float):
                continue
            if force is not None and helper != force["helper"]:
                continue
            gain = self.helper_gain(helper)
            for days in cast(Sequence[int], rules["days"]):
                if days > left or wage * days > cash:
                    continue
                if force is not None:
                    if days == int(force["days"]):
                        best = (0.0, helper, days)
                    continue
                if gain < float(rules["margin"]) * wage:
                    continue
                net = (gain - wage) * days
                if best is None or net > best[0]:
                    best = (net, helper, days)
        if best is None:
            return None
        _, helper, days = best
        return self.at(
            board,
            "hire_helper",
            f"contratar {helper} por {days} dia(s)",
            target=board["entity_id"],
            helper=helper,
            days=days,
        )

    # ------------------------------------------------------------- vender e encomendas

    def fetch(self) -> Proposal | None:
        """Com um ajudante contratado, a colheita fresca que ele deixou no baú (ADR-0072) volta
        para a mão, para vender e entregar como a dele. A comida que vence amanhã fica: é a que
        o script 2 guarda lá, e buscá-la só a faria voltar."""
        chest = self.nearest(self.of_kind("chest"))
        if not self.book.contracts or chest is None:
            return None
        foods = cast(Mapping[str, Mapping[str, int]], self.c["foods"])
        held = cast(Sequence[Mapping[str, Any]], self.view["containers"])
        inside = [c["items"] for c in held if c["container_id"] == chest["entity_id"]]
        stacks = cast(Sequence[Mapping[str, Any]], inside[0] if inside else [])
        fresh: dict[str, int] = {}
        for stack in stacks:
            item, left = str(stack["item"]), stack.get("expires_in_days")
            if item in foods and (not isinstance(left, int) or left > 1):
                fresh[item] = int(stack["qty"])
        for item in sorted(fresh, key=lambda f: (-foods[f]["sale"], f)):
            qty = min(fresh[item], int(self.c["sell"]["fetch_max"]))
            return self.at(
                chest,
                "withdraw",
                f"pegar {qty} {item} no baú",
                target=chest["entity_id"],
                item=item,
                qty=qty,
            )
        return None

    def _fair(self) -> Mapping[str, Any] | None:
        return self.nearest(self.of_kind("fair_stall"))

    def sell(self) -> Proposal | None:
        """Vende o que passa da comida de dois dias: na feira, quando está aberta; na caixa,
        enquanto o preço de agora passa de 70% da tabela ou quando a colheita vai vencer. Na
        véspera da feira, guarda o que aguenta até lá."""
        foods = cast(Mapping[str, Mapping[str, int]], self.c["foods"])
        days = float(self.c["food_days"])
        crops = cast(Mapping[str, Mapping[str, Any]], self.c["crops"])
        cheapest = min(float(c["price"]) for c in crops.values())
        if self.mine("moeda") < 2 * cheapest and self.empty_plots():
            days = 1.0  # sem caixa para a semente: a comida de um dia basta, o resto vira semente
        reserve = days * self.hunger_per_day()
        surplus_points = self._food_points(self.me_id) - reserve
        if surplus_points <= 0:
            return None
        expiring = self._expiring()
        stall = self._fair()
        rules = cast(Mapping[str, Any], self.c["sell"])
        if stall is not None and stall["attributes"].get("open") and self.now < minutes("13:30"):
            units = sum(self.mine(f) for f in foods)
            if units >= int(rules["fair_min_units"]):
                for item in sorted(foods, key=lambda f: (-foods[f]["sale"], f)):
                    amount = self._spare(item, surplus_points)
                    if amount >= 1:
                        return self.at(
                            stall,
                            "sell",
                            f"vender {amount} {item} na feira",
                            target=stall["entity_id"],
                            item=item,
                            qty=amount,
                        )
        fair_tomorrow = (
            stall is not None and stall["attributes"].get("proxima_feira") == self.day + 1
        )
        box = self.nearest(self.of_kind("sell_box"))
        if box is None:
            return None
        for item in sorted(foods, key=lambda f: (-foods[f]["sale"], f)):
            amount = self._spare(item, surplus_points)
            if amount < 1:
                continue
            shown = box["attributes"].get(f"preco_{item}")
            cheap = isinstance(shown, int | float) and float(shown) < float(
                rules["min_price"]
            ) * float(foods[item]["sale"])
            if (cheap or fair_tomorrow) and item not in expiring:
                continue
            return self.at(
                box,
                "sell",
                f"vender {amount} {item}",
                target=box["entity_id"],
                item=item,
                qty=amount,
            )
        return None

    def _spare(self, item: str, surplus_points: float) -> int:
        foods = cast(Mapping[str, Mapping[str, int]], self.c["foods"])
        qty = self.mine(item)
        keep = 0
        while keep < qty and (qty - keep) * float(foods[item]["hunger"]) > surplus_points:
            keep += 1
        return qty - keep

    def _expiring(self) -> set[str]:
        mine = next((c for c in self.view["containers"] if c["container_id"] == self.me_id), None)
        if mine is None:
            return set()
        return {
            str(s["item"])
            for s in mine["items"]
            if isinstance(s.get("expires_in_days"), int) and int(s["expires_in_days"]) <= 1
        }

    def accept(self) -> Proposal | None:
        """Aceita o pedido que o estoque e o que já está crescendo cumprem até o prazo, quando
        paga acima do que a caixa daria."""
        board, orders = self._board_orders()
        rules = cast(Mapping[str, Any], self.c["orders"])
        if board is None or not orders:
            return None
        mine = [o for o in orders if o["attributes"].get("aceita_por") == self.me_id]
        if len(mine) >= int(rules["max_taken"]):
            return None
        promised = {str(o["attributes"]["item"]): int(o["attributes"]["quantidade"]) for o in mine}
        for order in sorted(
            (o for o in orders if o["attributes"].get("aceita_por") is None),
            key=lambda o: (-int(o["attributes"]["pagamento"]), o["entity_id"]),
        ):
            a = order["attributes"]
            item, qty, deadline = str(a["item"]), int(a["quantidade"]), int(a["prazo"])
            crops = cast(Mapping[str, Any], self.c["crops"])
            if item not in crops:
                continue
            box_value = qty * self.price(item)
            if int(a["pagamento"]) < float(rules["min_premium"]) * box_value:
                continue
            coming = sum(
                1
                for p in self.book.active.values()
                if p.crop == item and self._ripe_by(p) <= deadline - 1
            )
            if self.mine(item) + coming - promised.get(item, 0) >= qty:
                return self.at(
                    board,
                    "accept_order",
                    f"aceitar a encomenda de {a['cliente']}",
                    target=board["entity_id"],
                    order=order["entity_id"],
                )
        return None

    def _ripe_by(self, planting: Planting) -> int:
        """O dia em que o plantio deve amadurecer, pelo mundo médio da crença."""
        if planting.ripe_day is not None:
            return planting.ripe_day
        spot = self.script.spot(
            planting.tile, planting.crop, planting.previous, planting.fertilized
        )
        speed = self.script.book.beliefs.world().speed(spot)
        points = float(self.c["crops"][planting.crop]["days"])
        day, grown = planting.day, 0.0
        while grown < points and day < planting.day + 40:
            day += 1
            grown += self.script.pace_on(planting.crop, day) * speed
        return day

    # ------------------------------------------------------------- espantalho, adubo

    def exposed(self) -> list[Mapping[str, Any]]:
        """Os canteiros em que o mundo de hoje diz que a planta madura se perde muito."""
        limit = float(self.c["scarecrow"]["min_loss"])
        found: list[Mapping[str, Any]] = []
        for plot in self.active_plots():
            door, guard = self.script.place_of(_tile(plot["position"]))
            if self.world.loss(door, guard) >= limit and (guard is None or guard > 8):
                found.append(plot)
        return found

    def guard(self) -> Proposal | None:
        """Com um espantalho no inventário, finca no meio dos canteiros expostos."""
        rules = cast(Mapping[str, Any], self.c["scarecrow"])
        item = str(rules["item"])
        if self.mine(item) < 1:
            return None
        exposed = self.exposed()
        if not exposed:
            return None
        xs = sorted(_tile(p["position"])[0] for p in exposed)
        ys = sorted(_tile(p["position"])[1] for p in exposed)
        center = (xs[len(xs) // 2], ys[len(ys) // 2])
        spots = [t for t in self.candidates() if _chebyshev(t, center) <= 2]
        if not spots:
            return None
        me = _tile(self.pos)
        beside = [t for t in spots if _chebyshev(t, me) == 1]
        spot = min(beside or spots, key=lambda t: (_chebyshev(t, center), t))
        target = {"x": spot[0], "y": spot[1]}
        if _chebyshev(me, spot) == 1:
            return {
                "action": "place",
                "params": {"item": item, "target": target},
                "intent": "fincar o espantalho",
            }
        return {"action": "move", "params": {"target": target}, "intent": "ir fincar o espantalho"}

    def wants_scarecrow(self) -> bool:
        group = int(self.c["scarecrow"]["group"])
        return len(self.exposed()) >= group and self.mine(str(self.c["scarecrow"]["item"])) < 1

    def compost(self) -> Proposal | None:
        """Os restos de planta viram adubo na composteira."""
        rules = cast(Mapping[str, Any], self.c["compost"])
        if self.mine(str(rules["item"])) < int(rules["qty"]):
            return None
        bin_ = self.nearest(self.of_kind(str(rules["kind"])))
        if bin_ is None or bin_["attributes"].get("fazendo"):
            return None
        return self.at(
            bin_,
            "process",
            "fazer adubo com os restos",
            target=bin_["entity_id"],
            recipe=str(rules["recipe"]),
            item=str(rules["item"]),
        )

    def collect(self) -> Proposal | None:
        """Pega o adubo pronto na composteira, quando passa por perto."""
        rules = cast(Mapping[str, Any], self.c["compost"])
        bin_ = self.nearest(self.of_kind(str(rules["kind"])))
        item = str(self.c["fertilizer"]["item"])
        if bin_ is None or bin_["entity_id"] not in self.in_view:
            return None
        qty = self.stock.get(str(bin_["entity_id"]), {}).get(item, 0)
        if qty < 1:
            return None
        return self.at(
            bin_, "withdraw", "pegar o adubo", target=bin_["entity_id"], item=item, qty=qty
        )

    # ------------------------------------------------------------- comprar

    def buy(self) -> Proposal | None:
        """A compra pelas regras de sobrevivência (ADR-0070): primeiro a semente dos canteiros de
        comida; depois, com o caixa acima do caixa da comida, a semente que mais rende nos
        outros canteiros (o guloso com orçamento de capital). O espantalho quando o modelo diz
        que há canteiros expostos; o regador grande quando sobra bastante."""
        kiosk = self.nearest(self.of_kind("kiosk"))
        if kiosk is None:
            return None
        crops = cast(Mapping[str, Mapping[str, Any]], self.c["crops"])
        rules = cast(Mapping[str, Any], self.c["scarecrow"])
        coins, reserve = self.mine("moeda"), int(self.c["coins_reserve"])
        visible = kiosk["entity_id"] in self.in_view and bool(kiosk["attributes"].get("open"))
        guard = self.food_cash() + reserve
        scarecrow = self.wants_scarecrow() and coins >= int(rules["price"]) + guard
        if not visible:
            hours = cast(Mapping[str, str], self.c["kiosk_hours"])
            open_now = minutes(hours["opens"]) <= self.now < minutes(hours["closes"]) - 30
            seasonal = [c for c in crops if self._pace(c) > 0]
            if open_now and (scarecrow or self.plan(seasonal)):
                return {
                    "action": "move",
                    "params": {"near": kiosk["entity_id"]},
                    "intent": "ir ao quiosque",
                }
            return None
        if scarecrow:
            return self._buy(kiosk, str(rules["item"]), 1, "um espantalho")
        big = cast(Mapping[str, Any], self.c["big_can"])
        if self.held(str(big["kind"])) is None and coins >= int(big["price"]) + guard + 200:
            return self._buy(kiosk, str(big["item"]), 1, "o regador grande")
        stock = str(kiosk["attributes"].get("estoque_hoje") or "")
        available = stock.split(", ") if stock else []
        market = [
            c
            for c in crops
            if self._pace(c) > 0 and (not available or str(crops[c]["seed"]) in available)
        ]
        wanted = self.plan(market)
        if not wanted:
            return None
        crop, food = wanted[0]
        seed, price = str(crops[crop]["seed"]), int(crops[crop]["price"])
        # A semente da comida (e a do teste) usa o caixa todo: é o meio de produzir. A de vender
        # deixa a reserva, o caixa da comida e a folga de investir.
        spare = coins if food else coins - reserve - self.food_cash() - int(self.c["invest_floor"])
        same = sum(1 for c, f in wanted if c == crop and f == food)
        qty = min(same, self.affordable(kiosk, seed, price, int(spare)))
        return None if qty < 1 else self._buy(kiosk, seed, qty, seed)

    def plan(self, market: Sequence[str]) -> list[tuple[str, bool]]:
        """As sementes que faltam, na ordem da compra, cada uma marcada se é da comida: primeiro
        os canteiros de comida (M) que faltam; depois os outros vazios e os que ainda vai cavar,
        pelo guloso com orçamento de capital (plano macro, §5), só com o caixa acima do caixa da
        comida: quando ele não paga a melhor cultura em todos, escolhe pelo retorno de cada moeda
        por dia; quando paga, pelo que cada canteiro rende."""
        crops = cast(Mapping[str, Mapping[str, Any]], self.c["crops"])
        held = {c: self.mine(str(info["seed"])) for c, info in crops.items()}
        foods, _ = self.food_plan()
        wanted: list[tuple[str, bool]] = []
        food_missing = self.food_plots() - self.food_growing()
        offered = [c for c in foods if c in market]
        slots = [(_tile(p["position"]), str(p["entity_id"])) for p in self.empty_plots()]
        slots += [(self._home(), None)] * max(0, self.target() - len(self.active_plots()))
        if self.book.pending_tests > 0 and offered:
            # O canteiro de teste: uma semente barata, paga como a comida, porque é o que ensina.
            fast = min(offered, key=lambda c: (float(crops[c]["days"]), c))
            if held.get(fast, 0) > 0:
                held[fast] -= 1
            else:
                wanted.append((fast, True))
        # Os canteiros de comida, um a um: a comida que mais mata a fome naquele canteiro, com a
        # cultura de antes dele na conta (quando o modelo aprende que repetir cansa, reveza).
        for tile, plot in slots[: max(0, food_missing)]:
            options = [c for c in foods if held.get(c, 0) > 0] + offered
            if not options:
                break
            choice = self.best_food(options, tile, plot)
            if held.get(choice, 0) > 0:
                held[choice] -= 1
            else:
                wanted.append((choice, True))
        free = max(0, len(slots) - max(food_missing, 0))  # os canteiros de vender
        budget = float(self.mine("moeda") - int(self.c["coins_reserve"])) - self.food_cash()
        budget -= float(self.c["invest_floor"]) + sum(float(crops[c]["price"]) for c, _ in wanted)
        if free <= 0 or budget <= 0:
            return wanted
        home = self._home()
        best = max(market, key=lambda c: (self.value(c, home), c), default=None)
        tight = best is not None and budget < free * float(crops[best]["price"])
        extra: Counter[str] = Counter()
        for tile, plot in slots[-free:]:
            options = [c for c, n in held.items() if n > 0 and c not in foods]
            options += [
                c for c in market if float(crops[c]["price"]) <= budget and c not in options
            ]
            if not options:
                break

            def rank(c: str, tile: Tile = tile, plot: str | None = plot) -> tuple[float, str]:
                value = self.value(c, tile, plot, extra)
                return (value / max(1.0, float(crops[c]["price"])) if tight else value), c

            choice = max(options, key=rank)
            if self.value(choice, tile, plot, extra) <= 0:
                continue
            extra[choice] += 1
            if held.get(choice, 0) > 0:
                held[choice] -= 1
            else:
                wanted.append((choice, False))
                budget -= float(crops[choice]["price"])
        return wanted

    def _buy(self, kiosk: Mapping[str, Any], item: str, qty: int, what: str) -> Proposal:
        return self.at(
            kiosk, "buy", f"comprar {qty} {what}", target=kiosk["entity_id"], item=item, qty=qty
        )


def _tile(position: Mapping[str, Any]) -> Tile:
    return int(position["x"]), int(position["y"])


def _chebyshev(a: Tile, b: Tile) -> int:
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def _spread(sources: set[Tile], known: Mapping[Tile, Any]) -> dict[Tile, int]:
    """A distância (Chebyshev) de cada tile conhecido à fonte mais perto, por uma busca em
    largura em oito direções sobre os tiles conhecidos."""
    found = {t: 0 for t in sources}
    queue = deque(sorted(sources))
    while queue:
        x, y = queue.popleft()
        step = found[(x, y)] + 1
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                n = (x + dx, y + dy)
                if n in known and n not in found:
                    found[n] = step
                    queue.append(n)
    return found
