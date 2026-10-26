"""O fazendeiro-ajudante (ADR-0072): o script de um ajudante contratado, que obedece à ordem do
patrão.

A ordem fica nos atributos do próprio ajudante, à vista dele: `ordem` (cuidar, regar, colher,
plantar, cavar, vender ou parar) e o que ela pede (`ordem_cultura`, `ordem_item`, `ordem_n` e o
ponto `ordem_x`, `ordem_y`). Ele lembra os canteiros que já viu, porque a foto só mostra o que está
no raio dele. Com a fome em 60 ele come do baú; sem comida no baú, vai para casa.

Uma instância por ajudante: o runner pede a fábrica (`helper(avatar_id)`), e cada ajudante tem a
sua lembrança.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

import yaml

DATA = Path(__file__).parent / "data" / "helper.yaml"

type View = Mapping[str, Any]
type Proposal = dict[str, Any]


def load_config() -> dict[str, Any]:
    return cast(dict[str, Any], yaml.safe_load(DATA.read_text(encoding="utf-8")))


def _tile_kind(view: View, x: int, y: int) -> str | None:
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


def _far(a: Mapping[str, int], b: Mapping[str, int]) -> int:
    return max(abs(int(a["x"]) - int(b["x"])), abs(int(a["y"]) - int(b["y"])))


@dataclass
class HelperScript:
    """Um ajudante: a ordem do patrão, a lembrança dos canteiros e o que cavou na ordem atual."""

    avatar_id: str
    config: Mapping[str, Any] = field(default_factory=load_config)
    plots: dict[str, dict[str, Any]] = field(default_factory=dict[str, dict[str, Any]])
    order_key: tuple[Any, ...] = ()
    dug: int = 0
    last: str | None = None  # a ação da última proposta, para saber o que uma recusa recusou

    @property
    def controller_type(self) -> str:
        return "script"

    @property
    def controller_id(self) -> str:
        return f"script/ajudante-{self.avatar_id}"

    def decide(self, view: View) -> Proposal:
        proposal = HelperTurn(self, view).decide()
        self.last = str(proposal["action"])
        return proposal


class HelperTurn:
    def __init__(self, script: HelperScript, view: View) -> None:
        self.s = script
        self.c = script.config
        self.view = view
        me = cast(Mapping[str, Any], view["self"])
        self.me = str(me["entity_id"])
        self.pos = cast(Mapping[str, int], me["position"])
        needs = cast(Mapping[str, float], me["needs"])
        self.hunger = float(needs.get(str(self.c["needs"]["hunger"]), 0))
        self.entities = cast(Sequence[Mapping[str, Any]], view["entities"])
        self.stock = {
            str(c["container_id"]): {str(i["item"]): int(i["qty"]) for i in c["items"]}
            for c in cast(Sequence[Mapping[str, Any]], view["containers"])
        }
        decision = cast(Mapping[str, Any], view.get("decision") or {})
        self.refused = decision.get("reason") == "action_rejected"
        own = next((e for e in self.entities if e.get("entity_id") == self.me), None)
        self.order = cast(Mapping[str, Any], (own or {}).get("attributes") or {})
        self.kinds = cast(Mapping[str, str], self.c["kinds"])
        self._remember()

    # ------------------------------------------------------------- o que se vê e se lembra

    def _remember(self) -> None:
        plot = self.kinds["plot"]
        seen = {str(e["entity_id"]): e for e in self.entities if e.get("kind") == plot}
        for plot_id, entity in seen.items():
            self.s.plots[plot_id] = {
                "position": dict(cast(Mapping[str, int], entity["position"])),
                **dict(cast(Mapping[str, Any], entity.get("attributes") or {})),
            }
        for plot_id in [p for p in self.s.plots if p not in seen]:
            where = cast(Mapping[str, int], self.s.plots[plot_id]["position"])
            if _far(where, self.pos) <= 3:  # devia estar à vista e não está: sumiu
                del self.s.plots[plot_id]

    def one(self, kind: str) -> Mapping[str, Any] | None:
        found = [e for e in self.entities if e.get("kind") == self.kinds[kind]]
        return min(found, key=lambda e: str(e["entity_id"])) if found else None

    def mine(self, item: str) -> int:
        return self.stock.get(self.me, {}).get(item, 0)

    def can(self) -> Mapping[str, Any] | None:
        found = [
            e
            for e in self.entities
            if e.get("kind") == self.kinds["can"] and e.get("container_id") == self.me
        ]
        return found[0] if found else None

    def nearest(self, plots: Sequence[str]) -> str | None:
        if not plots:
            return None
        return min(plots, key=lambda p: (_far(self.s.plots[p]["position"], self.pos), p))

    # ------------------------------------------------------------- as propostas

    def go(self, entity: Mapping[str, Any] | str, intent: str) -> Proposal:
        target = entity if isinstance(entity, str) else str(entity["entity_id"])
        return {"action": "move", "params": {"near": target}, "intent": intent}

    def near(self, where: Mapping[str, int]) -> bool:
        return _far(where, self.pos) <= 1

    def at(self, entity: Mapping[str, Any], action: str, intent: str, **params: Any) -> Proposal:
        """A ação ao lado da coisa, ou ir até ela primeiro."""
        where = cast(Mapping[str, int] | None, entity.get("position"))
        if where is not None and not self.near(where):
            return self.go(entity, f"ir {intent}")
        return {
            "action": action,
            "params": {"target": entity["entity_id"], **params},
            "intent": intent,
        }

    def at_plot(self, plot: str, action: str, intent: str, **params: Any) -> Proposal:
        where = cast(Mapping[str, int], self.s.plots[plot]["position"])
        if not self.near(where):
            return self.go(plot, f"ir {intent}")
        return {"action": action, "params": {"target": plot, **params}, "intent": intent}

    def wait(self, intent: str) -> Proposal:
        return {"action": "wait", "params": {"ticks": int(self.c["wait"])}, "intent": intent}

    # ------------------------------------------------------------- a decisão

    def decide(self) -> Proposal:
        key = tuple(self.order.get(k) for k in ("ordem", "ordem_cultura", "ordem_item", "ordem_n"))
        if key != self.s.order_key:  # ordem nova: recomeça a conta dos canteiros cavados
            self.s.order_key, self.s.dug = key, 0
        elif self.refused and self.s.last == "dig":
            self.s.dug -= 1  # a cova recusada não conta
        food = self.eat()
        if food is not None:
            return food
        task = str(self.order.get("ordem") or "parar")
        chosen = {
            "cuidar": self.care,
            "regar": self.water_only,
            "colher": self.harvest_only,
            "plantar": self.plant,
            "cavar": self.dig,
            "vender": self.sell,
        }.get(task)
        return chosen() if chosen is not None else self.wait("esperar ordem")

    def eat(self) -> Proposal | None:
        if self.hunger < float(self.c["eat_at"]):
            return None
        foods = [str(f) for f in cast(Sequence[Any], self.c["foods"])]
        held = next((f for f in foods if self.mine(f) > 0), None)
        if held is not None:
            return {"action": "eat", "params": {"item": held}, "intent": "comer"}
        chest = self.one("chest")
        stored = None if chest is None else self.stock.get(str(chest["entity_id"]), {})
        there = next((f for f in foods if (stored or {}).get(f, 0) > 0), None)
        if chest is None or there is None:
            return {"action": "go_home", "params": {}, "intent": "sem comida no baú, para casa"}
        return self.at(chest, "withdraw", "pegar comida no baú", item=there, qty=1)

    def store(self) -> Proposal | None:
        """Guarda no baú as colheitas que carrega, quando já são muitas ou o serviço acabou."""
        harvests = [str(h) for h in cast(Sequence[Any], self.c["harvests"])]
        held = [(h, self.mine(h)) for h in harvests if self.mine(h) > 0]
        chest = self.one("chest")
        if not held or chest is None:
            return None
        item, qty = held[0]
        return self.at(chest, "deposit", "guardar a colheita no baú", item=item, qty=qty)

    def ripe(self) -> list[str]:
        return sorted(p for p, a in self.s.plots.items() if a.get("stage") == "madura")

    def dry(self) -> list[str]:
        return sorted(
            p
            for p, a in self.s.plots.items()
            if a.get("crop") is not None
            and a.get("stage") not in ("madura", "murcha")
            and not a.get("watered_today")
        )

    def harvest_one(self) -> Proposal | None:
        plot = self.nearest(self.ripe())
        return None if plot is None else self.at_plot(plot, "harvest", "colher")

    def water_one(self) -> Proposal | None:
        plot = self.nearest(self.dry())
        if plot is None:
            return None
        can = self.can()
        if can is None:
            return None
        charges = cast(Mapping[str, Any], can.get("attributes") or {}).get("charges") or 0
        # Sem carga, ou a rega acabou de ser recusada (a seca pede mais carga): ao poço.
        if int(charges) <= 0 or (self.refused and self.s.last == "water"):
            well = self.one("well")
            return None if well is None else self.at(well, "refill", "encher o regador")
        return self.at_plot(plot, "water", "regar")

    def look(self) -> Proposal | None:
        """Sem canteiro na lembrança: ir ver em volta do poço, onde a fazenda planta."""
        if self.s.plots:
            return None
        well = self.one(str(self.c["look_near"]))
        if well is None or self.near(cast(Mapping[str, int], well["position"])):
            return None
        return self.go(well, "ir ver os canteiros")

    def care(self) -> Proposal:
        carried = sum(self.mine(str(h)) for h in cast(Sequence[Any], self.c["harvests"]))
        if carried >= int(self.c["carry"]):
            stored = self.store()
            if stored is not None:
                return stored
        for step in (self.harvest_one, self.water_one, self.store, self.look):
            proposal = step()
            if proposal is not None:
                return proposal
        return self.wait("tudo cuidado")

    def water_only(self) -> Proposal:
        return self.water_one() or self.look() or self.wait("tudo regado")

    def harvest_only(self) -> Proposal:
        carried = sum(self.mine(str(h)) for h in cast(Sequence[Any], self.c["harvests"]))
        if carried >= int(self.c["carry"]):
            stored = self.store()
            if stored is not None:
                return stored
        return self.harvest_one() or self.store() or self.look() or self.wait("nada maduro")

    def plant(self) -> Proposal:
        crop = str(self.order.get("ordem_cultura") or "")
        seed = f"semente_{crop}"
        empty = sorted(p for p, a in self.s.plots.items() if a.get("crop") is None)
        plot = self.nearest(empty)
        if plot is None:
            return self.look() or self.wait("nenhum canteiro vazio")
        if self.mine(seed) > 0:
            return self.at_plot(plot, "plant", f"plantar {crop}", crop=crop)
        chest = self.one("chest")
        stored = 0 if chest is None else self.stock.get(str(chest["entity_id"]), {}).get(seed, 0)
        if chest is None or stored <= 0:
            return self.wait("sem semente no baú")
        qty = min(stored, len(empty))
        return self.at(chest, "withdraw", f"pegar semente de {crop}", item=seed, qty=qty)

    def dig(self) -> Proposal:
        n = int(self.order.get("ordem_n") or 0)
        x, y = self.order.get("ordem_x"), self.order.get("ordem_y")
        if self.s.dug >= n or not isinstance(x, int) or not isinstance(y, int):
            return self.wait("canteiros cavados")
        taken = {  # onde já há alguma coisa; onde ele mesmo está, ele cava
            (int(where["x"]), int(where["y"]))
            for e in self.entities
            if e.get("entity_id") != self.me
            and (where := cast(Mapping[str, int] | None, e.get("position"))) is not None
        }
        radius = int(self.c["dig_radius"])
        around = range(-radius, radius + 1)
        spots = sorted((max(abs(dx), abs(dy)), x + dx, y + dy) for dx in around for dy in around)
        for _, tx, ty in spots:
            if (tx, ty) in taken or _tile_kind(self.view, tx, ty) != "grass":
                continue
            if _far({"x": tx, "y": ty}, self.pos) <= 1:
                self.s.dug += 1
                return {
                    "action": "dig",
                    "params": {"target": {"x": tx, "y": ty}},
                    "intent": "cavar",
                }
            return {
                "action": "move",
                "params": {"target": {"x": tx, "y": ty}},
                "intent": "ir cavar",
            }
        return self.wait("sem grama livre em volta")

    def sell(self) -> Proposal:
        item = str(self.order.get("ordem_item") or "")
        if self.mine(item) > 0:
            box = self.one("sell_box")
            if box is None:
                return self.wait("sem caixa de vendas à vista")
            return self.at(box, "sell", f"vender {item}", item=item, qty=self.mine(item))
        chest = self.one("chest")
        stored = 0 if chest is None else self.stock.get(str(chest["entity_id"]), {}).get(item, 0)
        if chest is None or stored <= 0:
            return self.wait(f"nada de {item} no baú")
        return self.at(
            chest,
            "withdraw",
            f"pegar {item} para vender",
            item=item,
            qty=min(stored, int(self.c["carry"])),
        )


def helper(avatar_id: str) -> HelperScript:
    """A fábrica do entry point `ajudante`: uma instância por ajudante (ADR-0072)."""
    return HelperScript(avatar_id)
