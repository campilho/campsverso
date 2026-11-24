"""Os scripts do escritório (ADR-0078): o dev, o vigia e o gerente dos testes.

Cada um lê a foto da percepção (`perception.delivered.v1`) e devolve uma proposta de ação; o
kernel decide (princípio 2). O dev-script é a linha de base do escritório: pega o pedido mais
antigo do quadro, trabalha na mesa em blocos de um minuto, entrega e avisa, e responde com uma
frase pronta a quem fala com ele (entender o que foi dito é do M24, com a mente). O vigia faz a
ronda no começo de cada hora e passa o resto na cadeira. O gerente-script só existe nos testes e no
soak: escreve os pedidos de um roteiro, cumprimenta o dev e aceita ou devolve o que foi entregue.

A rotina (ADR-0080) é o que o dev faz quando não há pedido: almoça na copa, faz as pausas do dia
(água, café, banheiro) e fica sentado na mesa. As pausas são ilustrativas e não custam nada; os
horários saem de um sorteio pelo dia, o mesmo sempre que o dia se repete. O dev-script usa a rotina
quando não tem pedido, e a mente com rotina (M24) a usa quando o modelo não tem trabalho.

Os scripts lembram pouco, por instância (como o ajudante da fazenda lembra os canteiros): o que já
anunciaram, o dia do bom-dia e as pausas feitas. O resto vem da foto.
"""

import random
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

import yaml

DATA = Path(__file__).parent / "data" / "escritorio.yaml"

type View = Mapping[str, Any]
type Proposal = dict[str, Any]

TODO, DOING, DELIVERED = "a_fazer", "fazendo", "entregue"
PR_OPEN = "aberto"  # o PR do pedido, no GitHub (ADR-0083)
# As coisas da copa e das pausas (os tipos do gênero office; ADR-0080, ADR-0082).
COOLER, COFFEE, COPA_TABLE, COPA_CHAIR, RESTROOM = (
    "water_cooler",
    "coffee_machine",
    "copa_table",
    "copa_chair",
    "restroom_door",
)
FRIDGE, MICROWAVE, TRASH, SOFA = "fridge", "microwave", "trash", "sofa"
BREAK_PLACES = {"drink": COOLER, "coffee": COFFEE, "restroom": RESTROOM, "videogame": SOFA}
# O passo da sessão que chama um robô da bancada, com o nome da ferramenta da mente (ADR-0080).
ROBOT_STEP = "chamar_robo"
# O almoço em etapas (ADR-0082): a geladeira, o micro-ondas, a mesinha e o lixo da copa.
LUNCH_STEPS = (
    ("fridge", FRIDGE, "pegar o almoço na geladeira"),
    ("microwave", MICROWAVE, "esquentar o almoço"),
    ("lunch", COPA_TABLE, "almoçar na copa"),
    ("trash", TRASH, "jogar fora o resto"),
)


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
class Routine:
    """A rotina do dev (ADR-0080): o almoço na copa, as pausas do dia e a mesa. De graça."""

    config: Mapping[str, Any]
    done: dict[int, set[int]] = field(default_factory=dict[int, set[int]])  # pausas feitas, por dia
    lunched: dict[int, int] = field(default_factory=dict[int, int])  # etapas do almoço, por dia

    def plan(self, me: str, day: int) -> list[tuple[int, str]]:
        """As pausas do dia, em minutos do dia: o sorteio pelo avatar e pelo dia, sempre igual."""
        rng = random.Random(f"rotina:{me}:{day}")
        spread = int(self.config["spread_minutes"])
        start, end = minutes(str(self.config["start"])), minutes(str(self.config["end"]))

        def jitter(minute: int) -> int:
            return max(start, min(end, minute + rng.randint(-spread, spread)))

        pauses = [(jitter(minutes(str(at))), "coffee") for at in self.config["coffee"]]
        every = int(self.config["water_every_minutes"])
        pauses += [(jitter(at), "drink") for at in range(start + every // 2, end, every)]
        pauses += [
            (rng.randint(start, end), "restroom")
            for _ in range(int(self.config["restroom_per_day"]))
        ]
        # O videogame no sofá (ADR-0082), à tarde, depois do almoço.
        after = minutes(str(self.config["lunch"][1]))
        pauses += [
            (rng.randint(after, end), "videogame")
            for _ in range(int(self.config.get("videogame_per_day", 0)))
        ]
        return sorted(pauses)

    def lunch(self, view: View) -> Proposal | None:
        """Na hora do almoço, as etapas na copa (ADR-0082): pegar na geladeira, esquentar no
        micro-ondas, comer sentado na mesinha e jogar fora. Cada etapa vai até a coisa e a faz;
        depois da última, a rotina volta à mesa."""
        start, end = (minutes(str(hhmm)) for hhmm in self.config["lunch"])
        if not start <= minute_of(view) < end:
            return None
        day = day_of(view)
        step = self.lunched.get(day, 0)
        while step < len(LUNCH_STEPS):
            action, kind, label = LUNCH_STEPS[step]
            thing = next(iter(entities(view, kind)), None)
            if thing is None:  # a coisa não está no escritório: a etapa fica de fora
                step += 1
                self.lunched[day] = step
                continue
            if action == "lunch":
                seat = chair_by(view, thing, COPA_CHAIR)
                if seat is not None and not at(position(view), *_xy(seat)):
                    return go_to(*_xy(seat), f"rotina: ir {label}")
            if not adjacent(position(view), thing.get("position")):
                return go_near(str(thing["entity_id"]), f"rotina: ir {label}")
            self.lunched[day] = step + 1
            return {"action": action, "params": {}, "intent": f"rotina: {label}"}
        return None

    def pause(self, view: View) -> Proposal | None:
        """A próxima pausa vencida: ir até a coisa e fazer a pausa. O dev convocado fora do
        expediente veio trabalhar e não faz pausa nenhuma; num dia normal, a pausa com mais de
        `stale_minutes` de atraso fica para outro dia. Antes, o dev que chegava à noite fazia as
        pausas do dia que tinham ficado para trás, o videogame de 15 minutos com elas, antes de
        olhar o quadro (o primeiro pedido do dev convocado, 21/nov)."""
        mine, day, now = me(view), day_of(view), minute_of(view)
        myself = entity(view, mine)
        if myself is not None and attrs(myself).get("convocado_por") is not None:
            return None
        stale = int(self.config.get("stale_minutes", 60))
        done = self.done.setdefault(day, set())
        for index, (minute, action) in enumerate(self.plan(mine, day)):
            if index in done or minute > now:
                continue
            if now - minute > stale:
                done.add(index)
                continue
            thing = next(iter(entities(view, BREAK_PLACES[action])), None)
            if thing is None:
                done.add(index)
                continue
            if action == "videogame":  # no tapete, logo abaixo do sofá
                spot = cast(Mapping[str, int], thing.get("position") or {})
                below = (int(spot.get("x", 0)), int(spot.get("y", 0)) + 1)
                if not at(position(view), *below):
                    return go_to(*below, f"rotina: ir {LABELS[action]}")
            elif not adjacent(position(view), thing.get("position")):
                return go_near(str(thing["entity_id"]), f"rotina: ir {LABELS[action]}")
            done.add(index)
            return {"action": action, "params": {}, "intent": f"rotina: {LABELS[action]}"}
        return None

    def decide(
        self, view: View, desk_chair: Mapping[str, Any] | None, wait_seconds: int
    ) -> Proposal:
        """O que a rotina faz agora: o almoço, uma pausa vencida, ou a mesa."""
        found = self.lunch(view) or self.pause(view)
        if found is not None:
            return found
        if desk_chair is not None and not at(position(view), *_xy(desk_chair)):
            return go_to(*_xy(desk_chair), "rotina: voltar para a mesa")
        return wait(wait_seconds, "rotina: esperar um pedido no quadro")


LABELS = {
    "drink": "beber água",
    "coffee": "tomar um café",
    "restroom": "ao banheiro",
    "videogame": "jogar videogame",
}


def chair_by(
    view: View, thing: Mapping[str, Any] | None, kind: str = "chair"
) -> Mapping[str, Any] | None:
    """A cadeira ao lado da coisa (a mesa do dev; na copa, a cadeira de lado da mesinha)."""
    spot = None if thing is None else thing.get("position")
    return next((c for c in entities(view, kind) if adjacent(c.get("position"), spot)), None)


def bench_calls(view: View) -> list[dict[str, Any]]:
    """Os robôs da bancada que o script de reserva chama antes de entregar: os que o registro do
    cenário deu argumentos para ele (`reserva`, os caminhos separados por espaço), na ordem dos
    apoios. Sem modelo, ele não escolhe o que testar: o cenário escolhe."""
    calls: list[dict[str, Any]] = []
    for robot in sorted(entities(view, "robot"), key=lambda e: str(e["entity_id"])):
        a = attrs(robot)
        given = str(a.get("reserva") or "").split()
        if given and a.get("modulo"):
            calls.append(
                {
                    "tool": ROBOT_STEP,
                    "args": {
                        "robo": str(robot["entity_id"]),
                        "modulo": str(a["modulo"]),
                        "argumentos": given,
                    },
                }
            )
    return calls


def workshop_session(ticket: Mapping[str, Any], view: View | None = None) -> dict[str, Any]:
    """A sessão do dev-script na oficina (ADR-0080), o script de reserva: sem modelo, ele registra o
    pedido num arquivo, chama os robôs da bancada que têm argumentos para ele e entrega. O
    controlador a roda pela porta da oficina antes de propor a entrega, e a tira da proposta num
    mundo sem oficina."""
    a = attrs(ticket)
    number = int(a["numero"])
    lines = [
        f"# Pedido {number}: {a.get('titulo', '')}",
        "",
        str(a.get("descricao") or ""),
        "",
        f"**Teste de aceite:** {a.get('aceite') or '(nenhum)'}",
        "",
        "Registrado pelo dev-script na oficina, sem modelo: o script de reserva do escritório.",
        "",
    ]
    return {
        "ticket_id": str(ticket["entity_id"]),
        "steps": [
            {"tool": "ler", "args": {"path": "README.md", "start": 1, "end": 20}},
            {
                "tool": "escrever",
                "args": {
                    "path": f"docs/oficina/pedido-{number:03d}.md",
                    "content": "\n".join(lines),
                },
            },
            *([] if view is None else bench_calls(view)),
            {"tool": "ver_mudancas", "args": {}},
            {"tool": "pronto", "args": {}},
        ],
    }


# Quantos minutos antes do almoço o dev avisa: o bloco de trabalho é de um minuto, então dois
# minutos garantem uma decisão na janela.
LUNCH_NOTICE_MINUTES = 2


@dataclass
class DevScript:
    """O dev-script (ADR-0078, decisão 11): o quadro, a mesa, a entrega e as frases prontas."""

    config: Mapping[str, Any]
    sizes: Mapping[str, int]
    announced: set[str] = field(default_factory=set[str])  # os pedidos já anunciados
    greeted: int = 0  # o dia do último bom-dia
    lunched: int = 0  # o dia do último aviso do almoço
    routine: Routine | None = None
    # O que o dev prometeu na conversa e a rotina cumpre (ADR-0093, decisão 10): uma ação de
    # `WISHES`, que a mente põe aqui; a rotina anda até a coisa e faz, e o desejo some.
    wish: str | None = None

    def __post_init__(self) -> None:
        if self.routine is None:
            self.routine = Routine(cast(Mapping[str, Any], self.config["routine"]))

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
        if self.wish is not None:
            promised, done = wish_step(view, self.wish)
            if done:
                self.wish = None
            if promised is not None:
                return promised
        if manager_id is not None and present(view, manager_id) and self.greeted != day_of(view):
            self.greeted = day_of(view)
            return say(self._line("morning"), manager_id, "cumprimentar o gerente")
        # O aviso do almoço, nos minutos antes da saída: sem ele, o dev sumia da sala ao meio-dia
        # (a primeira partida do usuário no escritório).
        lunch = minutes(str(self.config["lunch_at"]))
        if lunch - LUNCH_NOTICE_MINUTES <= minute_of(view) < lunch and self.lunched != day_of(view):
            self.lunched = day_of(view)
            listener = manager_id if manager_id is not None and present(view, manager_id) else None
            return say(self._line("lunch"), listener, "avisar que vou almoçar")
        board = next(iter(entities(view, "board")), None)
        desk = next((d for d in entities(view, "desk") if attrs(d).get("dono") == mine), None)
        chair = chair_by(view, desk)
        assert self.routine is not None
        lunch = self.routine.lunch(view)  # o almoço vem antes do trabalho simulado
        if lunch is not None:
            return lunch
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
                return {
                    "action": "deliver",
                    "params": {},
                    "intent": "entregar o pedido",
                    "workshop": workshop_session(doing, view),
                }
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
        # Só o pedido dele ou o de ninguém (ADR-0093, decisão 8).
        todo = [
            t
            for t in tickets(view)
            if attrs(t)["estado"] == TODO and attrs(t).get("para") in (None, mine)
        ]
        if todo and board is not None:
            if not adjacent(here, board.get("position")):
                return go_near(str(board["entity_id"]), "ir ao quadro pegar um pedido")
            first = todo[0]
            return {
                "action": "take_ticket",
                "params": {"target": first["entity_id"]},
                "intent": f"pegar o pedido {attrs(first)['numero']}",
            }
        return self.routine.decide(view, chair, int(self.config["wait_seconds"]))

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


LIGHT_SWITCH = "light_switch"  # o interruptor da sala (ADR-0088)


def light_request(text: str) -> bool | None:
    """O que pediram da luz numa fala: acender (`True`), apagar (`False`), ou nada."""
    low = text.lower()
    if "luz" not in low:
        return None
    return not any(word in low for word in ("apag", "deslig"))


@dataclass
class GuardScript:
    """O vigia: a ronda nos primeiros minutos de cada hora, e a cadeira no resto. Na ronda, ele
    fica em cada ponto até a vez do próximo: antes, chegando ao ponto, voltava à cadeira e ia ao
    ponto de novo, e em tempo real ficava indo e vindo da porta a cada segundo (21/nov).

    A luz (ADR-0088): quem fala com ele sobre a luz (com a menção, ou dizendo "vigia") ouve a
    resposta, e ele vai ao interruptor acender ou apagar. Na ronda, apaga a sala vazia."""

    config: Mapping[str, Any]
    wanted: bool | None = None  # a luz que pediram, até ele chegar ao interruptor

    @property
    def controller_type(self) -> str:
        return "script"

    @property
    def controller_id(self) -> str:
        return str(self.config["id"])

    def decide(self, view: View) -> Proposal:
        now, here = minute_of(view), position(view)
        light = self._light(view, now, here)
        if light is not None:
            return light
        points = [tuple(cast(Sequence[int], p)) for p in self.config["points"]]
        if now % 60 < int(self.config["round_minutes"]):
            x, y = points[(now // 2) % len(points)]
            if not at(here, x, y):
                return go_to(x, y, "fazer a ronda")
            return wait(int(self.config.get("look_seconds", 30)), "olhar a sala")
        chair = cast(Sequence[int], self.config["chair"])
        if not at(here, int(chair[0]), int(chair[1])):
            return go_to(int(chair[0]), int(chair[1]), "voltar para a cadeira")
        return wait(int(self.config["wait_seconds"]), "vigiar")

    def _light(self, view: View, now: int, here: Mapping[str, int] | None) -> Proposal | None:
        """O pedido da luz, a ida ao interruptor e a sala vazia apagada na ronda; nada, senão."""
        mine = me(view)
        lines = cast(Mapping[str, str], self.config.get("lines") or {})
        switch = next(iter(entities(view, LIGHT_SWITCH)), None)
        for heard in reversed(heard_from_others(view)):
            text = str(heard["text"])
            asked = light_request(text)
            if asked is None or (heard.get("listener_id") != mine and "vigia" not in text.lower()):
                continue
            speaker = str(heard["avatar_id"])
            if switch is None:
                missing = lines.get("no_switch", "Aqui não tem interruptor.")
                return say(missing, speaker, "responder")
            self.wanted = asked
            line = lines.get("light_on" if asked else "light_off", "Já vou.")
            return say(line, speaker, "responder sobre a luz")
        if switch is None:
            return None
        lit = bool(attrs(switch).get("acesa"))
        others = [
            e
            for e in entities(view, "avatar")
            if e["entity_id"] != mine and e.get("position") is not None
        ]
        on_round = now % 60 < int(self.config["round_minutes"])
        if self.wanted is None and lit and not others and on_round:
            self.wanted = False  # na ronda, a sala vazia não fica acesa
        if self.wanted is None:
            return None
        if lit == self.wanted:
            self.wanted = None
            return None
        if not adjacent(here, cast(Mapping[str, int] | None, switch.get("position"))):
            return go_near(str(switch["entity_id"]), "ir ao interruptor")
        on, self.wanted = self.wanted, None
        return {
            "action": "light_on" if on else "light_off",
            "params": {},
            "intent": "acender a luz" if on else "apagar a luz",
        }


# ---------------------------------------------------------------------------------- o desejo

# O que o dev pode prometer na conversa e cumprir na hora (ADR-0093, decisão 10): a ação do kernel
# e a coisa da sala onde ela se faz (sem coisa, ali mesmo).
WISHES: Mapping[str, str | None] = {
    "go_home": None,
    "coffee": COFFEE,
    "tv": SOFA,
    "videogame": SOFA,
    "light_on": LIGHT_SWITCH,
    "light_off": LIGHT_SWITCH,
}
WISH_LABELS = {
    "go_home": "ir para casa",
    "coffee": "tomar um café",
    "tv": "ver TV",
    "videogame": "jogar videogame",
    "light_on": "acender a luz",
    "light_off": "apagar a luz",
}


def wish_step(view: View, wish: str) -> tuple[Proposal | None, bool]:
    """O passo do que o dev prometeu na conversa: andar até a coisa e fazer. Devolve a proposta e
    se ela é a última (a própria ação); sem a coisa na sala, ou um desejo que não existe, nada."""
    if wish not in WISHES:
        return None, True
    kind = WISHES[wish]
    label = WISH_LABELS[wish]
    done: Proposal = {"action": wish, "params": {}, "intent": f"prometi: {label}"}
    if kind is None:
        return done, True
    thing = next(iter(entities(view, kind)), None)
    if thing is None:
        return None, True
    here = position(view)
    if kind == SOFA:  # no tapete, logo abaixo do sofá, como as pausas da rotina
        spot = cast(Mapping[str, int], thing.get("position") or {})
        below = (int(spot.get("x", 0)), int(spot.get("y", 0)) + 1)
        if not at(here, *below):
            return go_to(*below, f"prometi: {label}"), False
    elif not adjacent(here, thing.get("position")):
        return go_near(str(thing["entity_id"]), f"prometi: {label}"), False
    return done, True


# ---------------------------------------------------------------------------------- o gerente


@dataclass
class ManagerScript:
    """O gerente-script, só para os testes e o soak (ADR-0078, decisão 17): o roteiro do dia."""

    config: Mapping[str, Any]
    greeted: int = 0  # o dia dos bons-dias de `greeted_devs`
    dev_came: int = 0  # o último dia em que um dev veio: sem ele, não é dia de escrever pedido
    # Os devs que já ganharam bom-dia hoje (ADR-0093: com vários devs, um bom-dia para cada).
    greeted_devs: set[str] = field(default_factory=set[str])

    @property
    def controller_type(self) -> str:
        return "script"

    @property
    def controller_id(self) -> str:
        return str(self.config["id"])

    def decide(self, view: View) -> Proposal:
        now, here = minute_of(view), position(view)
        here_devs = [
            str(e["entity_id"])
            for e in entities(view, "avatar")
            if attrs(e).get("papel") == "dev" and present(view, str(e["entity_id"]))
        ]
        if here_devs:
            self.dev_came = day_of(view)
        if self.greeted != day_of(view):
            self.greeted, self.greeted_devs = day_of(view), set()
        # Um bom-dia para cada dev que chega, uma vez por dia (ADR-0093).
        hello = next((d for d in sorted(here_devs) if d not in self.greeted_devs), None)
        if hello is not None:
            self.greeted_devs.add(hello)
            return say(str(self.config["greeting"]), hello, "cumprimentar o dev")
        board = next(iter(entities(view, "board")), None)
        if board is None:
            return wait(int(self.config["wait_seconds"]), "sem quadro")
        near_board = adjacent(here, board.get("position"))
        written_today = self._written_today(view)
        script = cast(Sequence[Mapping[str, Any]], self.config["tickets"])
        # Só nos dias em que o dev veio: no feriado e no fim de semana, o gerente também não escreve
        # (o soak de 5 dias do M23 caiu num feriado, 20/11, e três pedidos ficaram para segunda).
        workday = self.dev_came == day_of(view)
        due = [t for t in script if workday and minutes(str(t["at"])) <= now]
        # Com o PR aberto (ADR-0083), o pedido se decide no GitHub: quem mescla é o humano.
        delivered = [
            t
            for t in tickets(view)
            if attrs(t)["estado"] == DELIVERED and attrs(t).get("pr_estado") != PR_OPEN
        ]
        if delivered or len(due) > written_today:
            if not near_board:
                return go_near(str(board["entity_id"]), "ir ao quadro")
            if delivered:
                return self._review(delivered[0])
            plan = due[written_today]
            title = f"{plan['title']} (dia {day_of(view)})"
            params: dict[str, Any] = {
                "title": title,
                "description": str(plan["description"]),
                "acceptance": str(plan["acceptance"]),
                "size": str(plan["size"]),
            }
            # Quem programa e o modelo (ADR-0089), e para quem (ADR-0093), quando o roteiro escolhe.
            for key in ("harness", "model", "assignee"):
                if plan.get(key):
                    params[key] = str(plan[key])
            if plan.get("everyone"):
                params["everyone"] = True
            return {"action": "write_ticket", "params": params, "intent": "escrever um pedido"}
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
