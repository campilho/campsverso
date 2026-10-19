"""A memória da mente (ADR-0060): episódios sem chamada ao modelo, o caderno, o bloco que abre
cada janela e a reflexão de fim de dia.

Tudo o que a mente escreve na memória vem das entregas da percepção e das próprias propostas; o
que ela devolve ao modelo é texto montado só com isso, determinístico, para a fita reproduzir.
"""

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, cast

from campsverso_ports import (
    Belief,
    BeliefRevision,
    Effort,
    Episode,
    MemoryPort,
    ModelRequest,
    ModelResponse,
    Note,
    Reflection,
    request_sha256,
)

NOTE = "note"
NOTE_DESCRIPTION = (
    'Algo que vale lembrar amanhã (uma observação, um número, uma dúvida), ou "" se nada.'
)
NOTE_MAX = 500
REFLECT = "reflect"

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
    reflection_model: str | None = None  # None: o modelo das decisões
    reflection_effort: Effort | None = "medium"
    reflection_max_tokens: int = 2048
    reflection_episodes: int = 200  # linhas do dia que a reflexão lê, as mais recentes


@dataclass(frozen=True, slots=True)
class Clock:
    tick: int
    day: int
    sim_time: str

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
    return Clock(
        int(raw.get("tick", delivery.get("as_of_tick", 0))),
        int(raw.get("day", 1)),
        str(raw.get("sim_time", "")),
    )


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

REFLECTION_INSTRUCTIONS = """\
## A reflexão da noite

O dia acabou. Você recebe o que aconteceu hoje (uma linha por acontecimento, na ordem), o que \
você mesmo anotou e as crenças que já tinha. Responda com a ferramenta `reflect`, e só com ela: \
o resumo do dia, o plano para amanhã e a lista inteira de crenças revisada. Uma crença é uma \
regra que você acha que vale nesta fazenda, tirada do que viu, com a confiança que a evidência \
sustenta: confirme o que se repetiu, enfraqueça o que não se repetiu, abandone o que o dia \
desmentiu, e forme crenças novas só com evidência. Cite as horas e os fatos."""


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

    # ------------------------------------------------------------- registrar

    def observe(self, delivery: Mapping[str, Any]) -> Clock:
        """O que aconteceu desde a última entrega vira episódios; a foto não (é estado)."""
        clock = clock_of(delivery)
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
        if self.last_proposal:
            lines.append(f"Última ação: {self.last_proposal}")
        if len(lines) == 1:
            lines.append("O caderno ainda está vazio: é o seu primeiro dia.")
        return "\n".join(lines)

    # ------------------------------------------------------------- refletir

    def pending_day(self, clock: Clock) -> int | None:
        """Um dia anterior com episódios e sem reflexão: a noite passou sem dormir (desmaio)."""
        previous = clock.day - 1
        if (
            previous < 1
            or self.port.has_reflection(previous)
            or not self.port.episodes(previous, limit=1)
        ):
            return None
        return previous

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
        parts.append("Feche o dia com a ferramenta reflect.")
        return ModelRequest(
            model=s.reflection_model or model,
            messages=[{"role": "user", "content": [{"type": "text", "text": "\n".join(parts)}]}],
            system=[
                {
                    "type": "text",
                    "text": f"{system}\n\n{REFLECTION_INSTRUCTIONS}",
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            tools=[REFLECT_TOOL],
            max_tokens=s.reflection_max_tokens,
            effort=s.reflection_effort,
            purpose="reflection",
            avatar_id=self.avatar_id,
        )

    def apply_reflection(
        self, request: ModelRequest, response: ModelResponse, clock: Clock, day: int
    ) -> Reflection | None:
        """A resposta da reflexão vira crenças guardadas e eventos; `None` sem a ferramenta."""
        chosen = next((t for t in response.tool_uses() if t.get("name") == REFLECT), None)
        if chosen is None:
            return None
        given = cast(Mapping[str, Any], chosen.get("input") or {})
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
        summary = " ".join(str(given.get("summary", "")).split())[:2000] or "(sem resumo)"
        plan = " ".join(str(given.get("plan", "")).split())[:1000] or None
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
        self._events.insert(
            len(self._events) - len(changes),
            {"type": "campsverso.memory.reflected.v1", "data": data},
        )
        self.reflect_due = None
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
