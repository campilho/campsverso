"""Os scripts do escritório (ADR-0078): o dev, o vigia e o gerente dos testes.

Cada um lê a foto da percepção (`perception.delivered.v1`) e devolve uma proposta de ação; o
kernel decide (princípio 2). O dev-script é a linha de base do escritório: pega o pedido mais
antigo do quadro, trabalha na mesa em blocos de um minuto, entrega e avisa, e responde com uma
frase pronta a quem fala com ele (entender o que foi dito é do M24, com a mente). O vigia faz a
ronda no começo de cada hora e passa o resto na cadeira. O gerente-script só existe nos testes e no
soak: escreve os pedidos de um roteiro, cumprimenta o dev e aceita ou devolve o que foi entregue.

Os scripts lembram pouco, por instância (como o ajudante da fazenda lembra os canteiros): o que já
anunciaram e o dia do bom-dia. O resto vem da foto.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

import yaml

DATA = Path(__file__).parent / "data" / "escritorio.yaml"

type View = Mapping[str, Any]
type Proposal = dict[str, Any]

TODO, DOING, DELIVERED = "a_fazer", "fazendo", "entregue"


def load_config() -> dict[str, Any]:
    return cast(dict[str, Any], yaml.safe_load(DATA.read_text(encoding="utf-8")))


def minute_of(view: View) -> int:
    """O minuto do dia na hora da foto (o relógio do mundo, no fuso dele)."""
    hhmm = str(view["clock"]["sim_time"])[11:16]
    return int(hhmm[:2]) * 60 + int(hhmm[3:5])


def minutes(hhmm: str) -> int:
    return int(hhmm[:2]) * 60 + int(hhmm[3:5])


def day_of(view: View) -> int:
    return int(view["clock"]["day"])


def me(view: View) -> str:
    return str(view["self"]["entity_id"])


def position(view: View) -> Mapping[str, int] | None:
    return cast(Mapping[str, int] | None, view["self"].get("position"))


def entities(view: View, kind: str) -> list[Mapping[str, Any]]:
    return [e for e in cast(Sequence[Mapping[str, Any]], view["entities"]) if e["kind"] == kind]


def entity(view: View, entity_id: str) -> Mapping[str, Any] | None:
    found = (
        e
        for e in cast(Sequence[Mapping[str, Any]], view["entities"])
        if e["entity_id"] == entity_id
    )
    return next(found, None)


def present(view: View, avatar_id: str) -> bool:
    found = entity(view, avatar_id)
    return found is not None and found.get("position") is not None


def tickets(view: View) -> list[Mapping[str, Any]]:
    return sorted(entities(view, "ticket"), key=lambda t: int(t["attributes"]["numero"]))


def attrs(item: Mapping[str, Any]) -> Mapping[str, Any]:
    return cast(Mapping[str, Any], item["attributes"])


def adjacent(a: Mapping[str, int] | None, b: Mapping[str, int] | None) -> bool:
    return a is not None and b is not None and max(abs(a["x"] - b["x"]), abs(a["y"] - b["y"])) <= 1


def at(a: Mapping[str, int] | None, x: int, y: int) -> bool:
    return a is not None and a["x"] == x and a["y"] == y


def go_near(entity_id: str, intent: str) -> Proposal:
    return {"action": "move", "params": {"near": entity_id}, "intent": intent}


def go_to(x: int, y: int, intent: str) -> Proposal:
    return {"action": "move", "params": {"target": {"x": x, "y": y}}, "intent": intent}


def wait(seconds: int, intent: str) -> Proposal:
    return {"action": "wait", "params": {"seconds": seconds}, "intent": intent}


def say(text: str, to: str | None, intent: str) -> Proposal:
    params: dict[str, Any] = {"text": text}
    if to is not None:
        params["to"] = to
    return {"action": "say", "params": params, "intent": intent}


def heard_from_others(view: View) -> list[Mapping[str, Any]]:
    """O que disseram com este avatar, ou perto dele, desde a última foto (ADR-0078)."""
    mine = me(view)
    return [
        h
        for h in cast(Sequence[Mapping[str, Any]], view.get("heard") or [])
        if h["avatar_id"] != mine and h.get("listener_id") in (None, mine)
    ]


# ---------------------------------------------------------------------------------- o dev


@dataclass
class DevScript:
    """O dev-script (ADR-0078, decisão 11): o quadro, a mesa, a entrega e as frases prontas."""

    config: Mapping[str, Any]
    sizes: Mapping[str, int]
    announced: set[str] = field(default_factory=set[str])  # os pedidos já anunciados
    greeted: int = 0  # o dia do último bom-dia

    @classmethod
    def load(cls) -> DevScript:
        data = load_config()
        return cls(cast(Mapping[str, Any], data["dev"]), cast(Mapping[str, int], data["sizes"]))

    @property
    def controller_type(self) -> str:
        return "script"

    @property
    def controller_id(self) -> str:
        return str(self.config["id"])

    def _line(self, key: str, ticket: Mapping[str, Any] | None = None) -> str:
        text = str(self.config["lines"][key])
        if ticket is None:
            return text
        return text.format(number=attrs(ticket)["numero"], title=attrs(ticket)["titulo"])

    def decide(self, view: View) -> Proposal:
        mine, here = me(view), position(view)
        speech = heard_from_others(view)
        manager = next(
            (e for e in entities(view, "avatar") if attrs(e).get("papel") == "gerente"), None
        )
        manager_id = None if manager is None else str(manager["entity_id"])
        if speech:
            last = speech[-1]
            hello = "bom dia" in str(last["text"]).lower() and self.greeted != day_of(view)
            if hello:
                self.greeted = day_of(view)
            line = self._line("morning" if hello else "noted")
            return say(line, str(last["avatar_id"]), "responder a quem falou comigo")
        if manager_id is not None and present(view, manager_id) and self.greeted != day_of(view):
            self.greeted = day_of(view)
            return say(self._line("morning"), manager_id, "cumprimentar o gerente")
        board = next(iter(entities(view, "board")), None)
        desk = next((d for d in entities(view, "desk") if attrs(d).get("dono") == mine), None)
        chair = next(iter(entities(view, "chair")), None)
        doing = next(
            (
                t
                for t in tickets(view)
                if attrs(t)["estado"] == DOING and attrs(t).get("dono") == mine
            ),
            None,
        )
        if doing is not None:
            if (
                str(doing["entity_id"]) not in self.announced
                and manager_id
                and present(view, manager_id)
            ):
                self.announced.add(str(doing["entity_id"]))
                return say(self._line("took", doing), manager_id, "avisar o pedido que peguei")
            total = int(self.sizes[str(attrs(doing)["tamanho"])]) * 60
            near_desk = desk is not None and adjacent(here, desk.get("position"))
            if not near_desk:
                return self._sit(chair, desk, "ir para a mesa trabalhar")
            if int(attrs(doing).get("trabalho", 0)) >= total:
                return {"action": "deliver", "params": {}, "intent": "entregar o pedido"}
            chunk = int(self.config["chunk_seconds"])
            return {
                "action": "work",
                "params": {"seconds": chunk},
                "intent": f"trabalhar no pedido {attrs(doing)['numero']}",
            }
        delivered = [
            t
            for t in tickets(view)
            if attrs(t)["estado"] == DELIVERED
            and attrs(t).get("dono") == mine
            and f"entregue:{t['entity_id']}:{attrs(t).get('comentario')}" not in self.announced
        ]
        if delivered and manager_id and present(view, manager_id):
            done = delivered[0]
            self.announced.add(f"entregue:{done['entity_id']}:{attrs(done).get('comentario')}")
            return say(self._line("delivered", done), manager_id, "avisar a entrega")
        todo = [t for t in tickets(view) if attrs(t)["estado"] == TODO]
        if todo and board is not None:
            if not adjacent(here, board.get("position")):
                return go_near(str(board["entity_id"]), "ir ao quadro pegar um pedido")
            first = todo[0]
            return {
                "action": "take_ticket",
                "params": {"target": first["entity_id"]},
                "intent": f"pegar o pedido {attrs(first)['numero']}",
            }
        if chair is not None and not at(here, *_xy(chair)):
            return self._sit(chair, desk, "voltar para a mesa")
        return wait(int(self.config["wait_seconds"]), "esperar um pedido no quadro")

    def _sit(
        self, chair: Mapping[str, Any] | None, desk: Mapping[str, Any] | None, intent: str
    ) -> Proposal:
        if chair is not None:
            x, y = _xy(chair)
            return go_to(x, y, intent)
        assert desk is not None
        return go_near(str(desk["entity_id"]), intent)


def _xy(item: Mapping[str, Any]) -> tuple[int, int]:
    spot = cast(Mapping[str, int], item["position"])
    return int(spot["x"]), int(spot["y"])


# ---------------------------------------------------------------------------------- o vigia


@dataclass
class GuardScript:
    """O vigia: a ronda nos primeiros minutos de cada hora, e a cadeira no resto."""

    config: Mapping[str, Any]

    @property
    def controller_type(self) -> str:
        return "script"

    @property
    def controller_id(self) -> str:
        return str(self.config["id"])

    def decide(self, view: View) -> Proposal:
        now, here = minute_of(view), position(view)
        points = [tuple(cast(Sequence[int], p)) for p in self.config["points"]]
        if now % 60 < int(self.config["round_minutes"]):
            x, y = points[(now // 2) % len(points)]
            if not at(here, x, y):
                return go_to(x, y, "fazer a ronda")
        chair = cast(Sequence[int], self.config["chair"])
        if not at(here, int(chair[0]), int(chair[1])):
            return go_to(int(chair[0]), int(chair[1]), "voltar para a cadeira")
        return wait(int(self.config["wait_seconds"]), "vigiar")


# ---------------------------------------------------------------------------------- o gerente


@dataclass
class ManagerScript:
    """O gerente-script, só para os testes e o soak (ADR-0078, decisão 17): o roteiro do dia."""

    config: Mapping[str, Any]
    greeted: int = 0

    @property
    def controller_type(self) -> str:
        return "script"

    @property
    def controller_id(self) -> str:
        return str(self.config["id"])

    def decide(self, view: View) -> Proposal:
        now, here = minute_of(view), position(view)
        dev = next((e for e in entities(view, "avatar") if attrs(e).get("papel") == "dev"), None)
        dev_id = None if dev is None else str(dev["entity_id"])
        if dev_id is not None and present(view, dev_id) and self.greeted != day_of(view):
            self.greeted = day_of(view)
            return say(str(self.config["greeting"]), dev_id, "cumprimentar o dev")
        board = next(iter(entities(view, "board")), None)
        if board is None:
            return wait(int(self.config["wait_seconds"]), "sem quadro")
        near_board = adjacent(here, board.get("position"))
        written_today = self._written_today(view)
        script = cast(Sequence[Mapping[str, Any]], self.config["tickets"])
        due = [t for t in script if minutes(str(t["at"])) <= now]
        delivered = [t for t in tickets(view) if attrs(t)["estado"] == DELIVERED]
        if delivered or len(due) > written_today:
            if not near_board:
                return go_near(str(board["entity_id"]), "ir ao quadro")
            if delivered:
                return self._review(delivered[0])
            plan = due[written_today]
            title = f"{plan['title']} (dia {day_of(view)})"
            return {
                "action": "write_ticket",
                "params": {
                    "title": title,
                    "description": str(plan["description"]),
                    "acceptance": str(plan["acceptance"]),
                    "size": str(plan["size"]),
                },
                "intent": "escrever um pedido",
            }
        return wait(int(self.config["wait_seconds"]), "esperar")

    def _written_today(self, view: View) -> int:
        suffix = f"(dia {day_of(view)})"
        return sum(1 for t in tickets(view) if str(attrs(t)["titulo"]).endswith(suffix))

    def _review(self, ticket: Mapping[str, Any]) -> Proposal:
        """Devolve um de cada três, na primeira entrega; aceita o resto."""
        number = int(attrs(ticket)["numero"])
        first = attrs(ticket).get("comentario") is None
        if first and number % int(self.config["return_every"]) == 0:
            return {
                "action": "return_ticket",
                "params": {
                    "target": ticket["entity_id"],
                    "comment": str(self.config["return_comment"]),
                },
                "intent": f"devolver o pedido {number}",
            }
        return {
            "action": "accept_ticket",
            "params": {"target": ticket["entity_id"]},
            "intent": f"aceitar o pedido {number}",
        }


def staff(avatar_id: str) -> GuardScript | ManagerScript:
    """A fábrica do entry point `escritorio`: o vigia ou o gerente-script, pelo id do avatar."""
    data = load_config()
    if avatar_id == "gerente":
        return ManagerScript(cast(Mapping[str, Any], data["gerente"]))
    return GuardScript(cast(Mapping[str, Any], data["vigia"]))
