"""A memória da mente (ADR-0060): episódios sem chamada ao modelo, o caderno, o bloco que abre
cada janela e a reflexão de fim de dia.

Tudo o que a mente escreve na memória vem das entregas da percepção e das próprias propostas; o
que ela devolve ao modelo é texto montado só com isso, determinístico, para a fita reproduzir.
"""

import copy
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from typing import Any, cast

from campsverso_mind.compare import COMPARE, COMPARE_INSTRUCTIONS, COMPARE_TOOL, Columns, Comparison
from campsverso_mind.mind import Mind
from campsverso_mind.notebook import FieldNotebook
from campsverso_ports import (
    Belief,
    BeliefRevision,
    Effort,
    Episode,
    Experiment,
    MemoryPort,
    ModelRequest,
    ModelResponse,
    Note,
    Place,
    Reflection,
    Tile,
    request_sha256,
)

NOTE = "note"
NOTE_DESCRIPTION = (
    'Algo que vale lembrar amanhã (uma observação, um número, uma dúvida), ou "" se nada.'
)
NOTE_MAX = 500
REFLECT = "reflect"
# Marcação de ferramenta que o modelo às vezes escreve dentro de um texto da reflexão, com o plano
# repetido depois (`</summary> <parameter name="plan">`; ADR-0070): o texto acaba antes dela.
TOOL_MARKUP = re.compile(r"</|<(?:parameter|invoke|function_calls)\b")
MAX_ATTEMPTS = 2  # reflexões tentadas por dia: a da noite e, se falhar, uma de manhã

# A importância por tabela (decisão 4): sem chamada ao modelo, e a mesma em qualquer execução.
IMPORTANCE_BY_TYPE: Mapping[str, int] = {
    "campsverso.avatar.fainted.v1": 10,
    "campsverso.farm.crop.matured.v1": 7,
    "campsverso.farm.crop.withered.v1": 7,
    "campsverso.action.rejected.v1": 6,
    "campsverso.action.failed.v1": 6,
    "campsverso.world.clock.phase_changed.v1": 2,
    "campsverso.world.weather.changed.v1": 2,
    "campsverso.avatar.sleep.started.v2": 2,
    "campsverso.avatar.sleep.ended.v2": 2,
    "campsverso.avatar.possessed.v1": 2,
    "campsverso.avatar.released.v1": 2,
}
IMPORTANCE_BY_ACTION: Mapping[str, int] = {
    "harvest": 7,
    "buy": 4,
    "sell": 4,
    "eat": 4,
    "plant": 3,
    "water": 3,
    "refill": 3,
    "clear": 3,
    "deposit": 3,
    "withdraw": 3,
    "sleep": 2,
    "move": 1,
    "wait": 1,
}
DEFAULT_IMPORTANCE = 1
# O que não vira episódio: ou repete a proposta, ou é ruído de cada tick.
SKIPPED_PREFIXES = (
    "campsverso.action.accepted.",
    "campsverso.world.entity.moved.",
    "campsverso.world.need.",
    "campsverso.world.entity.attributes",
    "campsverso.perception.",
    "campsverso.avatar.decision_requested.",
)
_ID_KEYS = ("avatar_id", "entity_id", "plot_id", "container_id", "target", "near", "bed_id")


@dataclass(frozen=True, slots=True)
class MemorySettings:
    enabled: bool = True
    block_beliefs: int = 20
    block_notes: int = 20
    block_salient: int = 10
    block_places: int = 25  # lugares fora de vista que o bloco lista (ADR-0067)
    reflection_model: str | None = None  # None: o modelo das decisões
    reflection_effort: Effort | None = "medium"
    reflection_max_tokens: int = (
        16384  # o raciocínio adaptativo gasta daqui; 8 mil cortaram uma noite
    )
    reflection_episodes: int = 200  # linhas do dia que a reflexão lê, as mais recentes
    # O caderno de campo e o experimento da noite (ADR-0070): ligados pela mente do cenário.
    field_notebook: bool = False
    experiments: bool = False
    block_plantings: int = 12  # plantios que o bloco de abertura mostra, os mais recentes
    hunger_need: str = "fome"  # a necessidade que a comida mata, para a tabela da comida
    # A ferramenta de comparação na reflexão (ADR-0074): ligada só no braço; pede o caderno.
    compare: bool = False


@dataclass(frozen=True, slots=True)
class Clock:
    tick: int
    day: int
    sim_time: str
    season: str | None = None  # num mundo com ano (ADR-0067)

    def at(self, tick: int) -> str:
        """A hora de um tick passado, a partir da hora desta entrega (HH:MM)."""
        try:
            now = datetime.fromisoformat(self.sim_time)
        except ValueError:
            return f"t{tick}"
        return (now - timedelta(minutes=self.tick - tick)).strftime("%H:%M")


def clock_of(delivery: Mapping[str, Any]) -> Clock:
    raw = cast(
        Mapping[str, Any], delivery.get("clock") or delivery.get("view", {}).get("clock") or {}
    )
    season = raw.get("season")
    return Clock(
        int(raw.get("tick", delivery.get("as_of_tick", 0))),
        int(raw.get("day", 1)),
        str(raw.get("sim_time", "")),
        None if season is None else str(season),
    )


def _clean(text: object, limit: int) -> str:
    """Um texto da reflexão numa linha, cortado na primeira marcação de ferramenta e no tamanho."""
    flat = " ".join(str(text).split())
    found = TOOL_MARKUP.search(flat)
    return (flat if found is None else flat[: found.start()].rstrip())[:limit]


def _box(terrain: Mapping[str, Any] | None) -> tuple[int, int, int, int] | None:
    """O recorte de terreno da foto (origem e tamanho): o que está à vista."""
    if terrain is None:
        return None
    origin = cast(Mapping[str, int], terrain.get("origin") or {"x": 0, "y": 0})
    rows = cast(Sequence[str], terrain.get("rows") or ())
    width = max((len(r) for r in rows), default=0)
    return int(origin["x"]), int(origin["y"]), width, len(rows)


def _inside(box: tuple[int, int, int, int], x: int, y: int) -> bool:
    x0, y0, width, height = box
    return x0 <= x < x0 + width and y0 <= y < y0 + height


def _place_line(clock: Clock, place: Place) -> str:
    hhmm = place.sim_time[11:16] or clock.at(place.tick)
    when = hhmm if place.day == clock.day else f"dia {place.day}, {hhmm}"
    attributes = ", ".join(f"{k} {v}" for k, v in place.attributes if v not in ("null", "false"))
    detail = f": {attributes}" if attributes else ""
    return f"- {place.entity_id} ({place.kind}) em ({place.x},{place.y}){detail}; visto {when}"


def _short(event_type: str) -> str:
    return event_type.removeprefix("campsverso.").rsplit(".v", 1)[0]


def _compact(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _tags(data: Mapping[str, Any]) -> tuple[str, ...]:
    found: list[str] = []
    params = cast(Mapping[str, Any], data.get("params") or {})
    for key in _ID_KEYS:
        for source in (data, params):
            value = source.get(key)
            if isinstance(value, str) and value and value not in found:
                found.append(value)
    return tuple(found)


def _line(clock: Clock, event: Mapping[str, Any]) -> tuple[str, int]:
    """Uma linha legível e a importância de um evento percebido."""
    kind = str(event.get("type", ""))
    data = cast(Mapping[str, Any], event.get("data") or {})
    when = clock.at(int(event.get("tick", clock.tick)))
    action = str(data.get("action", ""))
    params = _compact(data.get("params") or {})
    if kind == "campsverso.action.completed.v1":
        return f"{when} fiz {action} {params}", IMPORTANCE_BY_ACTION.get(action, 3)
    if kind == "campsverso.action.rejected.v1":
        detail = f" ({data['detail']})" if data.get("detail") else ""
        return f"{when} recusado {action} {params}: {data.get('reason')}{detail}", 6
    if kind == "campsverso.action.failed.v1":
        return f"{when} falhou {action} {params}: {data.get('reason')}", 6
    if kind == "campsverso.avatar.fainted.v1":
        return f"{when} desmaiei ({data.get('reason')})", 10
    if kind == "campsverso.world.clock.phase_changed.v1":
        return f"{when} fase do dia: {data.get('phase')}", 2
    if kind == "campsverso.world.weather.changed.v1":
        return f"{when} clima do dia {data.get('day')}: {data.get('condition')}", 2
    if kind == "campsverso.farm.crop.matured.v1":
        return f"{when} {data.get('plot_id')} amadureceu em {data.get('days')} dias", 7
    if kind == "campsverso.farm.crop.withered.v1":
        return f"{when} {data.get('plot_id')} murchou", 7
    if kind.startswith("campsverso.avatar.sleep."):
        verb = "dormi" if "started" in kind else "acordei"
        return f"{when} {verb} ({data.get('cause')})", 2
    rest = {k: v for k, v in data.items() if k not in ("avatar_id", "action_id")}
    return f"{when} {_short(kind)} {_compact(rest)}", IMPORTANCE_BY_TYPE.get(
        kind, DEFAULT_IMPORTANCE
    )


REFLECT_TOOL: dict[str, Any] = {
    "name": REFLECT,
    "description": (
        "Feche o dia: o que aconteceu, o que você aprendeu sobre como esta fazenda funciona e o "
        "que pretende amanhã."
    ),
    "strict": True,
    "input_schema": {
        "type": "object",
        "properties": {
            "summary": {
                "type": "string",
                "description": "O dia em 3 a 5 linhas, em português, em primeira pessoa.",
            },
            "plan": {
                "type": "string",
                "description": 'O que você pretende amanhã, em 1 a 3 linhas; ou "".',
            },
            "beliefs": {
                "type": "array",
                "description": (
                    "A lista inteira de crenças, revisada: as que continuam (confirmed), as que "
                    "mudaram de confiança (confirmed ou weakened), as que você abandona "
                    "(retracted) e as novas (new). Uma crença é o que você acredita sobre como "
                    "a fazenda funciona, tirado do que você viu."
                ),
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "string",
                            "description": 'O id da crença existente (bel-0001), ou "" se nova.',
                        },
                        "statement": {"type": "string", "description": "A crença, em uma frase."},
                        "confidence": {
                            "type": "number",
                            "description": "Quanto você acredita, de 0 a 1.",
                        },
                        "evidence": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "O que você viu que sustenta isso: horas e fatos.",
                        },
                        "status": {
                            "type": "string",
                            "enum": ["new", "confirmed", "weakened", "retracted"],
                        },
                        "reason": {
                            "type": "string",
                            "description": 'Por que, em uma frase; ou "".',
                        },
                    },
                    "required": ["id", "statement", "confidence", "evidence", "status", "reason"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["summary", "plan", "beliefs"],
        "additionalProperties": False,
    },
}

EXPERIMENT_RESULTS = ("cumpriu", "falhou", "inconclusivo")


def reflect_tool(experiments: bool) -> dict[str, Any]:
    """A ferramenta da reflexão; com experimentos (ADR-0070), o experimento de amanhã e o veredito
    do de ontem."""
    if not experiments:
        return REFLECT_TOOL
    tool = copy.deepcopy(REFLECT_TOOL)
    schema = cast(dict[str, Any], tool["input_schema"])
    properties = cast(dict[str, Any], schema["properties"])
    text = {"type": "string"}
    properties["experiment"] = {
        "type": "object",
        "description": (
            'Um experimento barato para amanhã, sobre algo que você ainda não sabe; ou os três "".'
        ),
        "properties": {
            "hypothesis": {**text, "description": "O que você acha que acontece, em uma frase."},
            "test": {**text, "description": "O que fazer amanhã para ver, e com o que comparar."},
            "prediction": {**text, "description": "O que deve acontecer se a hipótese for certa."},
        },
        "required": ["hypothesis", "test", "prediction"],
        "additionalProperties": False,
    }
    properties["experiment_result"] = {
        "type": "string",
        "enum": [*EXPERIMENT_RESULTS, ""],
        "description": 'Se a previsão do experimento de ontem se cumpriu; "" se não havia.',
    }
    schema["required"] = [*cast(list[str], schema["required"]), "experiment", "experiment_result"]
    return tool


EXPERIMENT_INSTRUCTIONS = """\
Proponha também um experimento barato para amanhã, sobre algo que você ainda não sabe de como a \
fazenda funciona: a hipótese, o teste (o que fazer amanhã, e com o que comparar) e a previsão (o \
que deve acontecer se a hipótese estiver certa). Se havia um experimento de ontem, diga em \
`experiment_result` se a previsão se cumpriu, falhou ou ficou inconclusiva."""

REFLECTION_INSTRUCTIONS = """\
## A reflexão da noite

O dia acabou. Você recebe o que aconteceu hoje (uma linha por acontecimento, na ordem), o que \
você mesmo anotou e as crenças que já tinha. Responda com a ferramenta `reflect`, e só com ela: \
o resumo do dia, o plano para amanhã e a lista inteira de crenças revisada. Uma crença é uma \
regra que você acha que vale nesta fazenda, tirada do que viu, com a confiança que a evidência \
sustenta: confirme o que se repetiu, enfraqueça o que não se repetiu, abandone o que o dia \
desmentiu, e forme crenças novas só com evidência. Cite as horas e os fatos. Seja econômico: \
até 12 crenças, cada uma com até três evidências de uma linha curta, e o resumo em 3 a 5 linhas."""


class Memory:
    """A memória de um avatar na mente: escreve episódios e anotações, monta o bloco de abertura e
    conduz a reflexão; os eventos para o operador saem por `drain_events`."""

    def __init__(
        self, port: MemoryPort, avatar_id: str, settings: MemorySettings | None = None
    ) -> None:
        self.port = port
        self.avatar_id = avatar_id
        self.settings = settings or MemorySettings()
        self._events: list[dict[str, Any]] = []
        self.last_proposal: str | None = None
        self.reflect_due: Clock | None = None
        self.attempts: dict[int, int] = {}  # tentativas de reflexão por dia; o teto evita o laço
        self.fresh = False  # há uma reflexão nova que a próxima entrega precisa mostrar
        self.in_view: set[str] = set()  # o que a última entrega mostrou (ADR-0067)
        self.clock: Clock | None = None  # o relógio da última entrega (a prova do fim, ADR-0070)
        self.notebook = FieldNotebook(port, avatar_id, self.settings.hunger_need)
        self.columns: Columns | None = None  # o que a comparação mede (ADR-0074)
        self.known: set[tuple[int, int]] = set()  # os tiles que a porta já guarda
        self.comparisons = 0  # as vezes que a reflexão usou a comparação

    def adopt(self, mind: Mind) -> None:
        """O caderno de campo e o experimento da noite, se a mente do cenário os usa (ADR-0070);
        e as colunas da comparação, quando a corrida a liga (ADR-0074)."""
        self.settings = replace(
            self.settings,
            field_notebook=self.settings.field_notebook or mind.field_notebook,
            experiments=self.settings.experiments or mind.experiments,
        )
        if self.settings.compare:
            if mind.columns is None or not self.settings.field_notebook:
                raise ValueError(f"a mente {mind.name} não tem caderno de campo e colunas")
            self.columns = mind.columns
            self.known = {(t.x, t.y) for t in self.port.terrain()}

    # ------------------------------------------------------------- registrar

    def _places(self, clock: Clock, delivery: Mapping[str, Any]) -> None:
        """O último estado visto de cada coisa com posição (ADR-0067). A foto mostra tudo o que
        está à vista: o que era lembrado dentro do recorte dela e não está mais lá, sumiu. O delta
        traz o que mudou, o que saiu do raio (`out_of_view`, que se lembra) e o que deixou de
        existir à vista (`gone`, que se esquece)."""
        view = cast(Mapping[str, Any] | None, delivery.get("view"))
        seen = cast(
            Sequence[Mapping[str, Any]],
            (view or {}).get("entities") if view is not None else delivery.get("entities") or (),
        )
        mine = {self.avatar_id}
        places = [
            Place(
                str(e["entity_id"]),
                str(e["kind"]),
                int(e["position"]["x"]),
                int(e["position"]["y"]),
                tuple(
                    (str(k), _compact(v))
                    for k, v in sorted(cast(Mapping[str, Any], e.get("attributes") or {}).items())
                ),
                clock.tick,
                clock.day,
                clock.sim_time,
            )
            for e in seen
            if e.get("position") is not None and str(e["entity_id"]) not in mine
        ]
        if places:
            self.port.remember(places)
        ids = {p.entity_id for p in places}
        if view is not None:
            self.in_view = {str(e["entity_id"]) for e in seen}
            self._terrain(cast(Mapping[str, Any] | None, view.get("map")))
            box = _box(cast(Mapping[str, Any] | None, view.get("map")))
            if box is not None:
                stale = [
                    p.entity_id
                    for p in self.port.places()
                    if p.entity_id not in self.in_view and _inside(box, p.x, p.y)
                ]
                if stale:
                    self.port.forget(stale)
            return
        gone = [str(i) for i in cast(Sequence[Any], delivery.get("gone") or ())]
        away = {str(i) for i in cast(Sequence[Any], delivery.get("out_of_view") or ())}
        if gone:
            self.port.forget(gone)
        self.in_view = (self.in_view | ids) - away - set(gone)

    def _terrain(self, terrain: Mapping[str, Any] | None) -> None:
        """Os tiles da foto que a comparação mede (a água, a mata...), os que ainda não estavam
        guardados (ADR-0074)."""
        if self.columns is None or terrain is None:
            return
        kinds = frozenset[str]().union(*self.columns.terrain.values())
        legend = cast(Mapping[str, Mapping[str, Any]], terrain.get("legend") or {})
        origin = cast(Mapping[str, int], terrain.get("origin") or {"x": 0, "y": 0})
        x0, y0 = int(origin["x"]), int(origin["y"])
        fresh: list[Tile] = []
        for dy, row in enumerate(cast(Sequence[str], terrain.get("rows") or ())):
            for dx, code in enumerate(row):
                kind = str((legend.get(code) or {}).get("kind"))
                tile = (x0 + dx, y0 + dy)
                if kind in kinds and tile not in self.known:
                    fresh.append(Tile(tile[0], tile[1], kind))
                    self.known.add(tile)
        if fresh:
            self.port.see(fresh)

    def observe(self, delivery: Mapping[str, Any]) -> Clock:
        """O que aconteceu desde a última entrega vira episódios; a foto não (é estado). As coisas
        vistas viram lugares lembrados (ADR-0067)."""
        clock = clock_of(delivery)
        self.clock = clock
        self._places(clock, delivery)
        if self.settings.field_notebook:
            places = {p.entity_id: p for p in self.port.places()}
            self.notebook.observe(clock.day, delivery, places, self.in_view, clock.season)
        reason = str(cast(Mapping[str, Any], delivery.get("decision") or {}).get("reason", ""))
        if reason in ("session_started", "possessed"):
            text = "assumi o corpo" if reason == "possessed" else "a sessão começou"
            self.port.record(
                Episode(
                    clock.tick,
                    clock.day,
                    f"{clock.at(clock.tick)} {text}",
                    2,
                    reason,
                    (),
                    clock.sim_time,
                )
            )
        for event in cast(Sequence[Mapping[str, Any]], delivery.get("events") or ()):
            kind = str(event.get("type", ""))
            if kind.startswith(SKIPPED_PREFIXES):
                continue
            text, importance = _line(clock, event)
            data = cast(Mapping[str, Any], event.get("data") or {})
            self.port.record(
                Episode(
                    int(event.get("tick", clock.tick)),
                    clock.day,
                    text,
                    importance,
                    _short(kind),
                    _tags(data),
                    clock.sim_time,
                )
            )
        return clock

    def proposed(self, clock: Clock, proposal: Mapping[str, Any], note: object) -> None:
        action = str(proposal.get("action", ""))
        intent = str(proposal.get("intent", ""))
        params = _compact(proposal.get("params") or {})
        text = f"{clock.at(clock.tick)} propus {action} {params}: {intent}"
        self.port.record(
            Episode(
                clock.tick,
                clock.day,
                text,
                IMPORTANCE_BY_ACTION.get(action, 2),
                "proposal",
                _tags(proposal),
                clock.sim_time,
            )
        )
        self.last_proposal = f"{action} {_compact(proposal.get('params') or {})}: {intent}"
        written = " ".join(str(note).split()) if isinstance(note, str) else ""
        if written:
            written = written[:NOTE_MAX]
            self.port.note(Note(clock.tick, clock.day, written, clock.sim_time))
            self._events.append(
                {
                    "type": "campsverso.memory.noted.v1",
                    "data": {"avatar_id": self.avatar_id, "day": clock.day, "text": written},
                }
            )
        if action == "sleep":
            self.reflect_due = clock

    def drain_events(self) -> list[dict[str, Any]]:
        events, self._events = self._events, []
        return events

    # ------------------------------------------------------------- lembrar

    def block(self, clock: Clock) -> str:
        """O que o agente lembra, na abertura de uma janela (decisão 6)."""
        s = self.settings
        lines: list[str] = ["## O que você lembra"]
        last = self.port.last_reflection()
        if last is not None:
            lines.append(f"Dia {last.day}, ao dormir: {last.summary}")
            if last.plan:
                lines.append(f"Plano: {last.plan}")
        beliefs = self.port.beliefs()[: s.block_beliefs]
        if beliefs:
            lines.append("Crenças (confiança de 0 a 1):")
            lines.extend(f"- {b.belief_id} ({b.confidence:.2f}): {b.statement}" for b in beliefs)
        notes = self.port.notes(clock.day)[-s.block_notes :]
        if notes:
            lines.append(f"Anotações de hoje (dia {clock.day}):")
            lines.extend(f"- {clock.at(n.tick)} {n.text}" for n in notes)
        salient = self.port.salient(clock.day, now_tick=clock.tick, limit=s.block_salient)
        if salient:
            lines.append("Momentos de hoje:")
            lines.extend(f"- {e.text}" for e in salient)
        away = [p for p in self.port.places() if p.entity_id not in self.in_view]
        if away:
            lines.append("Fora de vista, pelo que você viu por último:")
            lines.extend(_place_line(clock, p) for p in away[: s.block_places])
        if s.field_notebook:
            lines.extend(self.notebook.lines(s.block_plantings))
        trial = self.open_experiment()
        if s.experiments and trial is not None:
            lines.append(
                f"Experimento em teste (proposto na noite do dia {trial.day}): hipótese: "
                f"{trial.hypothesis}; teste: {trial.test}; previsão: {trial.prediction}"
            )
        if self.last_proposal:
            lines.append(f"Última ação: {self.last_proposal}")
        if len(lines) == 1:
            lines.append("O caderno ainda está vazio: é o seu primeiro dia.")
        return "\n".join(lines)

    # ------------------------------------------------------------- refletir

    def open_experiment(self) -> Experiment | None:
        """O último experimento proposto que ainda não teve veredito."""
        if not self.settings.experiments:
            return None
        found = [e for e in self.port.experiments() if e.result is None]
        return found[-1] if found else None

    def pending_day(self, clock: Clock) -> int | None:
        """Um dia anterior com episódios e sem reflexão: a noite passou sem dormir (desmaio).
        No máximo `MAX_ATTEMPTS` tentativas por dia: uma reflexão que falha de manhã não pode
        ser tentada de novo a cada entrega, cobrando cada tentativa."""
        previous = clock.day - 1
        if (
            previous < 1
            or self.port.has_reflection(previous)
            or self.attempts.get(previous, 0) >= MAX_ATTEMPTS
            or not self.port.episodes(previous, limit=1)
        ):
            return None
        return previous

    def attempted(self, day: int) -> int:
        """Conta uma tentativa de refletir o dia; devolve quantas já foram."""
        self.attempts[day] = self.attempts.get(day, 0) + 1
        return self.attempts[day]

    def reflect_request(self, system: str, clock: Clock, day: int, model: str) -> ModelRequest:
        s = self.settings
        episodes = self.port.episodes(day, limit=s.reflection_episodes)
        notes = self.port.notes(day)
        beliefs = self.port.beliefs()
        parts = [f"Dia {day}. O que aconteceu, na ordem:"]
        parts.extend(f"- {e.text}" for e in episodes) if episodes else parts.append(
            "- (nada registrado)"
        )
        parts.append("O que você anotou:")
        parts.extend(f"- {clock.at(n.tick)} {n.text}" for n in notes) if notes else parts.append(
            "- (nada)"
        )
        parts.append("As crenças que você já tinha:")
        parts.extend(
            f"- {b.belief_id} ({b.confidence:.2f}): {b.statement}" for b in beliefs
        ) if beliefs else parts.append("- (nenhuma)")
        trial = self.open_experiment()
        if trial is not None and trial.day < day:
            parts.append(
                f"O experimento que você propôs na noite do dia {trial.day}: hipótese: "
                f"{trial.hypothesis}; teste: {trial.test}; previsão: {trial.prediction}. Diga se a "
                "previsão se cumpriu."
            )
        parts.append("Feche o dia com a ferramenta reflect.")
        return ModelRequest(
            model=s.reflection_model or model,
            messages=[{"role": "user", "content": [{"type": "text", "text": "\n".join(parts)}]}],
            system=[
                {
                    "type": "text",
                    "text": f"{system}\n\n{self._instructions()}",
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            tools=[COMPARE_TOOL, reflect_tool(s.experiments)]
            if self.columns is not None
            else [reflect_tool(s.experiments)],
            max_tokens=s.reflection_max_tokens,
            effort=s.reflection_effort,
            purpose="reflection",
            avatar_id=self.avatar_id,
        )

    def _instructions(self) -> str:
        parts = [REFLECTION_INSTRUCTIONS]
        if self.settings.experiments:
            parts.append(EXPERIMENT_INSTRUCTIONS)
        if self.columns is not None:
            parts.append(COMPARE_INSTRUCTIONS)
        return "\n\n".join(parts)

    def compared(
        self, request: ModelRequest, response: ModelResponse, day: int
    ) -> ModelRequest | None:
        """A reflexão pediu a comparação (ADR-0074): o pedido seguinte, com a resposta e o
        resultado da ferramenta; `None` quando ela não pediu (fechou o dia, ou parou)."""
        uses = response.tool_uses()
        names = {str(t.get("name")) for t in uses}
        if self.columns is None or COMPARE not in names or REFLECT in names:
            return None
        if response.stop_reason == "max_tokens":
            return None
        comparison = Comparison(
            self.columns, self.port.plantings(), self.port.terrain(), self.port.places()
        )
        results: list[dict[str, Any]] = []
        for use in uses:
            given = cast(Mapping[str, Any], use.get("input") or {})
            if use.get("name") == COMPARE:
                self.comparisons += 1
                text = comparison.text(str(given.get("crop") or ""), day)
                results.append({"type": "tool_result", "tool_use_id": use["id"], "content": text})
            else:
                results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": use["id"],
                        "content": "Ferramenta desconhecida na reflexão.",
                        "is_error": True,
                    }
                )
        messages = [
            *request.messages,
            {"role": "assistant", "content": [dict(b) for b in response.content]},
            {"role": "user", "content": results},
        ]
        return replace(request, messages=messages)

    def _experiment(self, given: Mapping[str, Any], day: int, data: dict[str, Any]) -> None:
        """O veredito do experimento de ontem e o experimento de amanhã (ADR-0070)."""
        verdict = str(given.get("experiment_result") or "")
        trial = self.open_experiment()
        if trial is not None and trial.day < day and verdict in EXPERIMENT_RESULTS:
            self.port.save_experiment(replace(trial, result=verdict, result_day=day))
            data["experiment_result"] = verdict
        raw = cast(Mapping[str, Any], given.get("experiment") or {})
        hypothesis, test, prediction = (
            _clean(raw.get(k, ""), 300) for k in ("hypothesis", "test", "prediction")
        )
        if hypothesis:
            self.port.save_experiment(Experiment(day, hypothesis, test, prediction))
            data["experiment"] = {"hypothesis": hypothesis, "test": test, "prediction": prediction}

    def apply_reflection(
        self, request: ModelRequest, response: ModelResponse, clock: Clock, day: int
    ) -> Reflection | None:
        """A resposta da reflexão vira crenças guardadas e eventos; `None` sem a ferramenta."""
        chosen = next((t for t in response.tool_uses() if t.get("name") == REFLECT), None)
        if chosen is None:
            return None
        given = cast(Mapping[str, Any], chosen.get("input") or {})
        if response.stop_reason == "max_tokens" or not str(given.get("summary", "")).strip():
            return None  # cortada no meio: nada se guarda, e a manhã tenta de novo
        revisions: list[BeliefRevision] = []
        for raw in cast(Sequence[Mapping[str, Any]], given.get("beliefs") or ()):
            statement = " ".join(str(raw.get("statement", "")).split())[:500]
            if not statement:
                continue
            status = str(raw.get("status", "confirmed"))
            if status not in ("new", "confirmed", "weakened", "retracted"):
                status = "confirmed"
            evidence = tuple(
                " ".join(str(e).split())[:300]
                for e in cast(Sequence[Any], raw.get("evidence") or ())
                if str(e).strip()
            )[:20]
            belief_id = str(raw.get("id") or "").strip() or None
            reason = " ".join(str(raw.get("reason", "")).split())[:500] or None
            try:
                confidence = min(1.0, max(0.0, float(raw.get("confidence", 0.5))))
            except TypeError, ValueError:
                confidence = 0.5
            revisions.append(
                BeliefRevision(
                    statement,
                    round(confidence, 2),
                    evidence,
                    status,
                    reason,
                    belief_id,
                )
            )
        summary = _clean(given.get("summary", ""), 2000) or "(sem resumo)"
        plan = _clean(given.get("plan", ""), 1000) or None
        reflection = Reflection(
            day, clock.tick, summary, plan, tuple(revisions), request_sha256(request)
        )
        changes = self.port.save_reflection(reflection)
        counts = {"formed": 0, "updated": 0, "retracted": 0}
        for change in changes:
            counts[change.kind] += 1
            self._events.append(
                self._belief_event(change.kind, change.belief, change.previous_confidence)
            )
        data: dict[str, Any] = {
            "avatar_id": self.avatar_id,
            "day": day,
            "summary": summary,
            "beliefs": {**counts, "total": len(self.port.beliefs())},
            "prompt_sha256": reflection.prompt_sha256,
        }
        if plan:
            data["plan"] = plan
        if self.settings.experiments:
            self._experiment(given, day, data)
        self._events.insert(
            len(self._events) - len(changes),
            {"type": "campsverso.memory.reflected.v1", "data": data},
        )
        self.reflect_due = None
        self.fresh = True
        return reflection

    def _belief_event(self, kind: str, belief: Belief, previous: float | None) -> dict[str, Any]:
        data: dict[str, Any] = {
            "avatar_id": self.avatar_id,
            "belief_id": belief.belief_id,
            "statement": belief.statement,
        }
        if kind != "retracted":
            data["evidence"] = list(belief.evidence)
            data["source"] = {
                "kind": belief.source_kind,
                **({"by": belief.source_by} if belief.source_by else {}),
            }
            data["confidence"] = (
                belief.confidence
                if kind == "formed"
                else {
                    "before": previous if previous is not None else belief.confidence,
                    "after": belief.confidence,
                }
            )
        if belief.reason:
            data["reason"] = belief.reason
        return {"type": f"campsverso.memory.belief.{kind}.v1", "data": data}
