"""Fazendeiro-script (bíblia §11): a primeira prioridade aplicável vence.

Uma função pura do instantâneo da percepção para uma proposta de ação. Empates são decididos por
menor distância (Manhattan) e depois por menor id, para ser determinístico. Para chegar perto de
alguma coisa, usa `move {near}` e deixa o kernel escolher onde pisar (ADR-0047).
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import yaml

DATA = Path(__file__).parent / "data" / "farmer.yaml"

type View = Mapping[str, Any]
type Proposal = dict[str, Any]


def _minutes(hhmm: str) -> int:
    return int(hhmm[:2]) * 60 + int(hhmm[3:5])


def _distance(a: Mapping[str, int], b: Mapping[str, int]) -> int:
    return abs(a["x"] - b["x"]) + abs(a["y"] - b["y"])


def _adjacent(a: Mapping[str, int], b: Mapping[str, int]) -> bool:
    return max(abs(a["x"] - b["x"]), abs(a["y"] - b["y"])) <= 1


@dataclass(frozen=True)
class FarmerScript:
    config: Mapping[str, Any]

    @classmethod
    def load(cls) -> FarmerScript:
        return cls(cast(dict[str, Any], yaml.safe_load(DATA.read_text(encoding="utf-8"))))

    @property
    def controller_type(self) -> str:
        return "script"

    @property
    def controller_id(self) -> str:
        return str(self.config["id"])

    # ------------------------------------------------------------- leitura da foto

    def decide(self, view: View) -> Proposal:
        """Recebe a `view` de `perception.delivered.v1` e devolve {action, params, intent}."""
        return _Turn(self.config, view).decide()


class _Turn:
    """Uma decisão: a foto, já organizada para as perguntas da bíblia."""

    def __init__(self, config: Mapping[str, Any], view: View) -> None:
        self.c = config
        me = view["self"]
        self.me_id = str(me["entity_id"])
        self.pos: Mapping[str, int] = me["position"]
        needs = cast(Mapping[str, float], me["needs"])
        self.hunger = float(needs.get(config["needs"]["hunger"], 0))
        self.energy = float(needs.get(config["needs"]["energy"], 100))
        self.now = _minutes(str(view["clock"]["sim_time"])[11:16])
        self.raining = view["weather"]["condition"] == config["rain"]
        self.entities = cast(Sequence[Mapping[str, Any]], view["entities"])
        self.stock: dict[str, dict[str, int]] = {
            str(c["container_id"]): {str(i["item"]): int(i["qty"]) for i in c["items"]}
            for c in view["containers"]
        }

    def mine(self, item: str) -> int:
        return self.stock.get(self.me_id, {}).get(item, 0)

    def of_kind(self, kind: str) -> list[Mapping[str, Any]]:
        return [e for e in self.entities if e["kind"] == self.c["kinds"].get(kind, kind)]

    def nearest(self, candidates: Sequence[Mapping[str, Any]]) -> Mapping[str, Any] | None:
        placed = [e for e in candidates if e.get("position") is not None]
        return min(
            placed, key=lambda e: (_distance(self.pos, e["position"]), e["entity_id"]), default=None
        )

    def at(self, thing: Mapping[str, Any], action: str, intent: str, /, **params: Any) -> Proposal:
        """Age se estiver ao lado; senão, anda até lá."""
        if _adjacent(self.pos, thing["position"]):
            return {"action": action, "params": params, "intent": intent}
        near = {"near": thing["entity_id"]}
        return {"action": "move", "params": near, "intent": f"ir para {thing['entity_id']}"}

    # ------------------------------------------------------------- prioridades (bíblia §11)

    def decide(self) -> Proposal:
        for rule in (
            self.sleep,
            self.eat,
            self.harvest,
            self.clear,
            self.refill,
            self.water,
            self.plant,
            self.sell,
            self.buy,
        ):
            proposal = rule()
            if proposal is not None:
                return proposal
        ticks = int(self.c["wait_ticks"])
        return {"action": "wait", "params": {"ticks": ticks}, "intent": "esperar"}

    def _night(self, since: str) -> bool:
        return self.now >= _minutes(since) or self.now < _minutes(self.c["sleep"]["wake_at"])

    def sleep(self) -> Proposal | None:
        rules = self.c["sleep"]
        tired = self.energy < float(rules["low_energy"]) and self._night(rules["allowed_from"])
        if not (tired or self._night(rules["at"])):
            return None
        bed = self.nearest(self.of_kind(rules["bed_kind"]))
        late = _minutes(rules["ground_after"]) <= self.now < _minutes(rules["wake_at"])
        if bed is None or (late and not _adjacent(self.pos, bed["position"])):
            return {"action": "sleep", "params": {}, "intent": "dormir onde está"}
        return self.at(bed, "sleep", "dormir na cama", target=bed["entity_id"])

    def eat(self) -> Proposal | None:
        if self.hunger < float(self.c["hunger_eat_at"]):
            return None
        foods = cast(Mapping[str, int], self.c["foods"])
        by_value = sorted(foods, key=lambda f: (foods[f], f))
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

    def plots(self, *stages: str | None) -> list[Mapping[str, Any]]:
        return [p for p in self.of_kind("plot") if p["attributes"].get("stage") in stages]

    def thirsty(self) -> list[Mapping[str, Any]]:
        if self.raining:
            return []
        growing = [p for p in self.of_kind("plot") if p["attributes"].get("crop") is not None]
        stages = self.c["stages"]
        return [
            p
            for p in growing
            if p["attributes"].get("stage") not in (stages["ripe"], stages["withered"])
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

    def can_charges(self) -> int:
        cans = [e for e in self.of_kind("can") if e.get("container_id") == self.me_id]
        return int(cans[0]["attributes"].get("charges") or 0) if cans else 0

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

    def plant(self) -> Proposal | None:
        seed, crop = str(self.c["seed"]), str(self.c["crop"])
        plot = self.nearest(self.plots(None))
        if plot is None or self.mine(seed) < 1:
            return None
        return self.at(
            plot, "plant", f"plantar em {plot['entity_id']}", target=plot["entity_id"], crop=crop
        )

    def sell(self) -> Proposal | None:
        foods = cast(Mapping[str, int], self.c["foods"])
        held = {f: self.mine(f) for f in sorted(foods) if self.mine(f) > 0}
        surplus = sum(held.values()) - int(self.c["food_reserve"])
        box = self.nearest(self.of_kind("sell_box"))
        if surplus <= 0 or box is None:
            return None
        item = max(held, key=lambda f: (held[f], f))
        qty = min(held[item], surplus)
        return self.at(box, "sell", f"vender {qty} {item}", item=item, qty=qty)

    def buy(self) -> Proposal | None:
        kiosk = self.nearest(self.of_kind("kiosk"))
        seed, price = str(self.c["seed"]), int(self.c["seed_price"])
        missing = len(self.plots(None)) - self.mine(seed)
        coins = self.mine("moeda")
        if kiosk is None or not kiosk["attributes"].get("open") or missing <= 0 or coins < price:
            return None
        qty = min(missing, coins // price)
        return self.at(kiosk, "buy", f"comprar {qty} {seed}", item=seed, qty=qty)
