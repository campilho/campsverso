"""Projeção do mundo, montada só com eventos `world` e `agent` publicados (ADR-0028, ADR-0050).

Nada aqui conhece fazendas: o estado é o modelo de mundo do kernel (ADR-0025), e o que é da fazenda
chega como atributo. Também não há nada de desenho: posições são tiles, trajetos são ticks.
Pontos de crescimento e regras ocultas nunca chegam a esta projeção, porque o kernel não os publica
fora de `internal`, e quem a usa (percepção, gateway) não aplica eventos `internal` (princípio 5).
"""

import math
from collections.abc import Mapping
from typing import Any, cast

NOTES_KEPT = 20  # anotações do caderno que a tela guarda (ADR-0060)
BELIEFS_KEPT = 50
UNKNOWN_PHASE = "desconhecida"
METRIC_DAYS = 8  # hoje e os 7 anteriores (ADR-0054)


def _lookup(data: Mapping[str, Any], path: str) -> Any:
    """Um campo do evento por caminho com ponto (`params.target`); ausente vira None."""
    node: Any = data
    for key in path.split("."):
        if not isinstance(node, Mapping):
            return None
        node = cast(Mapping[str, Any], node).get(key)
    return node


def _position(raw: Any) -> dict[str, int]:
    return {"x": int(raw["x"]), "y": int(raw["y"])}


def path_from(
    origin: Mapping[str, int], waypoints: list[Mapping[str, int]]
) -> list[dict[str, int]]:
    """Refaz o trajeto tile a tile a partir das esquinas (D1): segmentos retos em 4 direções."""
    path = [_position(origin)]
    for corner in waypoints:
        x, y = path[-1]["x"], path[-1]["y"]
        dx = (corner["x"] > x) - (corner["x"] < x)
        dy = (corner["y"] > y) - (corner["y"] < y)
        while (x, y) != (corner["x"], corner["y"]):
            x, y = x + dx, y + dy
            path.append({"x": x, "y": y})
    return path


class Projection:
    """O mundo como se vê de fora, por mundo. Serializável em JSON; chaves desconhecidas ficam de
    fora, para que um serviço guarde as suas junto (a percepção guarda o `seq` das fotos)."""

    def __init__(self, state: Mapping[str, Any] | None = None) -> None:
        raw: Mapping[str, Any] = state or {}
        self.last_seq: dict[str, int] = dict(raw.get("last_seq", {}))  # por stream lido
        self.cartridge: str | None = raw.get("cartridge")
        self.tick: int = int(raw.get("tick", 0))
        self.simtime: str | None = raw.get("simtime")
        self.day: int = int(raw.get("day", 1))
        self.phase: str = str(raw.get("phase", UNKNOWN_PHASE))
        self.weather: dict[str, str] = dict(raw.get("weather", {}))  # dia -> condição
        self.entities: dict[str, dict[str, Any]] = {
            k: dict(v) for k, v in raw.get("entities", {}).items()
        }
        self.containers: dict[str, dict[str, int]] = {
            k: dict(v) for k, v in raw.get("containers", {}).items()
        }
        # Os lotes com validade (ADR-0062): contêiner -> item -> dia em que vence -> qty. Só os
        # eventos de item que trazem `expires_day` entram aqui; a contagem fica em `containers`.
        self.lots: dict[str, dict[str, dict[str, int]]] = {
            c: {item: dict(days) for item, days in by_item.items()}
            for c, by_item in raw.get("lots", {}).items()
        }
        self.motion: dict[str, dict[str, Any]] = dict(raw.get("motion", {}))
        self.actions: dict[str, dict[str, Any]] = dict(raw.get("actions", {}))
        self.needs: dict[str, dict[str, float]] = {
            k: dict(v) for k, v in raw.get("needs", {}).items()
        }
        self.asleep: dict[str, bool] = dict(raw.get("asleep", {}))
        self.sleep: dict[str, dict[str, Any]] = {  # início, fim previsto e cama (ADR-0052)
            k: dict(v) for k, v in raw.get("sleep", {}).items()
        }
        self.session: dict[str, Any] | None = raw.get("session")  # do session.started
        self.clock: dict[str, Any] = dict(raw.get("clock", {}))  # mode, scale, paused
        self.controllers: dict[str, dict[str, str]] = {
            k: dict(v) for k, v in raw.get("controllers", {}).items()
        }
        self.decisions: dict[str, dict[str, Any]] = {  # último pedido de decisão por avatar
            k: dict(v) for k, v in raw.get("decisions", {}).items()
        }
        self.metrics: dict[str, dict[str, Any]] = {  # dia -> id -> valor (ADR-0054)
            k: dict(v) for k, v in raw.get("metrics", {}).items()
        }
        # O pico de cada necessidade por dia, com ou sem catálogo: a fome chega pelo stream
        # agent, que pode passar na frente do session.started (stream world). O máximo não
        # depende da ordem.
        self.peaks: dict[str, dict[str, float]] = {
            k: dict(v) for k, v in raw.get("peaks", {}).items()
        }
        # O caderno de cada avatar (ADR-0060): crenças, anotações e a última reflexão, dos
        # eventos memory.* (observer). Só quem lê o stream observer o preenche (o gateway).
        self.memory: dict[str, dict[str, Any]] = {
            k: dict(v) for k, v in raw.get("memory", {}).items()
        }
        self._event_tick = self.tick  # o tick do evento sendo aplicado

    def export(self) -> dict[str, Any]:
        return {
            "last_seq": self.last_seq,
            "cartridge": self.cartridge,
            "tick": self.tick,
            "simtime": self.simtime,
            "day": self.day,
            "phase": self.phase,
            "weather": self.weather,
            "entities": self.entities,
            "containers": self.containers,
            "lots": self.lots,
            "motion": self.motion,
            "actions": self.actions,
            "needs": self.needs,
            "asleep": self.asleep,
            "sleep": self.sleep,
            "session": self.session,
            "clock": self.clock,
            "memory": self.memory,
            "controllers": self.controllers,
            "decisions": self.decisions,
            "metrics": self.metrics,
            "peaks": self.peaks,
        }

    # ------------------------------------------------------------- eventos

    def seen(self, stream: str, envelope: Mapping[str, Any]) -> bool:
        """Já aplicado? Cada stream chega em ordem de seq; uma reentrega fica para trás."""
        return int(envelope["seq"]) <= self.last_seq.get(stream, -1)

    def apply(self, stream: str, envelope: Mapping[str, Any]) -> None:
        self.last_seq[stream] = int(envelope["seq"])
        self.cartridge = str(envelope.get("cartridge") or self.cartridge)
        tick = envelope.get("tick")
        # O tick do próprio evento: `self.tick` é o maior já visto, e world e agent chegam por
        # streams diferentes, sem ordem garantida entre eles.
        self._event_tick = tick if isinstance(tick, int) else self.tick
        if isinstance(tick, int) and tick >= self.tick:
            self.tick, self.simtime = tick, cast(str | None, envelope.get("simtime"))
        name = str(envelope["type"]).removeprefix("campsverso.").rsplit(".", 1)[0]
        data = cast(Mapping[str, Any], envelope["data"])
        if str(envelope["type"]) == "campsverso.world.session.started.v1":
            self._on_world_session_started(data)  # o catálogo precisa estar lá antes de contar
            for day in list(self.peaks):
                self._show_peaks(day)
        else:
            self._count(str(envelope["type"]), data)  # antes: o grupo é o da entidade agora
            self._peak(str(envelope["type"]), data)
        handler = getattr(self, "_on_" + name.replace(".", "_"), None)
        if handler is not None and name != "world.session.started":
            handler(data)
        if stream == "world":  # itens só mudam por eventos world, que chegam em ordem
            self._sample()

    def _on_world_entity_spawned(self, data: Mapping[str, Any]) -> None:
        entity: dict[str, Any] = {
            "kind": data["kind"],
            "attributes": dict(data.get("attributes") or {}),
        }
        if data.get("position") is not None:
            entity["position"] = _position(data["position"])
        if data.get("container_id") is not None:
            entity["container_id"] = data["container_id"]
        if data.get("display_name") is not None:
            entity["display_name"] = data["display_name"]
        self.entities[str(data["entity_id"])] = entity

    def _on_world_entity_stored(self, data: Mapping[str, Any]) -> None:
        """A entidade foi guardada noutro contêiner (ADR-0062): sai do mapa."""
        entity = self.entities.get(str(data["entity_id"]))
        if entity is None:
            return
        entity["container_id"] = data["to_container"]
        entity.pop("position", None)
        self.motion.pop(str(data["entity_id"]), None)

    def _on_world_entity_state_changed(self, data: Mapping[str, Any]) -> None:
        entity = self.entities.get(str(data["entity_id"]))
        if entity is not None:
            entity["attributes"].update(data["changes"])

    def _on_world_entity_moved(self, data: Mapping[str, Any]) -> None:
        entity_id = str(data["entity_id"])
        path = path_from(data["origin"], list(data["waypoints"]))
        self.motion[entity_id] = {
            "path": path,
            "depart_tick": int(data["depart_tick"]),
            "tiles_per_tick": float(data["tiles_per_tick"]),
        }
        if entity_id in self.entities:
            self.entities[entity_id]["position"] = path[-1]  # onde vai estar ao chegar

    def _on_world_entity_move_interrupted(self, data: Mapping[str, Any]) -> None:
        entity_id = str(data["entity_id"])
        self.motion.pop(entity_id, None)
        if entity_id in self.entities:
            self.entities[entity_id]["position"] = _position(data["position"])

    def _add(self, container: str, item: str, qty: int) -> None:
        stock = self.containers.setdefault(container, {})
        stock[item] = stock.get(item, 0) + qty
        if stock[item] <= 0:
            del stock[item]

    def _add_lot(self, container: str, item: str, data: Mapping[str, Any], qty: int) -> None:
        if "expires_day" not in data:
            return
        day = str(int(data["expires_day"]))
        days = self.lots.setdefault(container, {}).setdefault(item, {})
        days[day] = days.get(day, 0) + qty
        if days[day] <= 0:
            del days[day]
        if not days:
            del self.lots[container][item]
        if not self.lots[container]:
            del self.lots[container]

    def expires_in(self, container: str, item: str) -> int | None:
        """Dias até o lote mais antigo do item vencer, pela validade nominal; None sem lotes."""
        days = self.lots.get(container, {}).get(item)
        if not days:
            return None
        return min(int(day) for day in days) - self.day

    def stack(self, container: str, item: str, qty: int) -> dict[str, Any]:
        """Um `item_stack` do contrato, com a validade quando o item a tem."""
        entry: dict[str, Any] = {"item": item, "qty": qty}
        expires = self.expires_in(container, item)
        if expires is not None:
            entry["expires_in_days"] = expires
        return entry

    def _on_world_item_created(self, data: Mapping[str, Any]) -> None:
        container, item, qty = str(data["container_id"]), str(data["item"]), int(data["qty"])
        self._add(container, item, qty)
        self._add_lot(container, item, data, qty)

    def _on_world_item_transferred(self, data: Mapping[str, Any]) -> None:
        item, qty = str(data["item"]), int(data["qty"])
        source, target = str(data["from_container"]), str(data["to_container"])
        self._add(source, item, -qty)
        self._add(target, item, qty)
        self._add_lot(source, item, data, -qty)
        self._add_lot(target, item, data, qty)

    def _on_world_item_consumed(self, data: Mapping[str, Any]) -> None:
        container, item, qty = str(data["container_id"]), str(data["item"]), int(data["qty"])
        self._add(container, item, -qty)
        self._add_lot(container, item, data, -qty)

    def _on_world_weather_changed(self, data: Mapping[str, Any]) -> None:
        self.weather[str(data["day"])] = str(data["condition"])

    def _on_world_clock_phase_changed(self, data: Mapping[str, Any]) -> None:
        self.phase, self.day = str(data["phase"]), int(data["day"])

    def _on_action_accepted(self, data: Mapping[str, Any]) -> None:
        action: dict[str, Any] = {
            "action_id": data["action_id"],
            "action": data["action"],
            "params": dict(data.get("params") or {}),
            "applied_tick": int(data["applied_tick"]),
            "end_tick": int(data["applied_tick"]) + int(data["duration_ticks"]),
        }
        if "interrupt" in data:  # ADR-0052; ausente nos arquivos antigos
            action["interrupt"] = data["interrupt"]
        if data.get("intent"):  # ADR-0059; o script e o humano nem sempre declaram
            action["intent"] = str(data["intent"])
        self.actions[str(data["avatar_id"])] = action

    def _finish(self, data: Mapping[str, Any]) -> None:
        avatar_id = str(data["avatar_id"])
        current = self.actions.get(avatar_id)
        if current is not None and current["action_id"] == data["action_id"]:
            del self.actions[avatar_id]
            self.motion.pop(avatar_id, None)

    _on_action_completed = _finish
    _on_action_failed = _finish

    def _on_avatar_sleep_started(self, data: Mapping[str, Any]) -> None:
        avatar_id = str(data["avatar_id"])
        self.asleep[avatar_id] = True
        if "wake_at_tick" in data:  # só na v2
            self.sleep[avatar_id] = {
                "since_tick": self._event_tick,
                "wake_at_tick": int(data["wake_at_tick"]),
            }
            if data.get("bed_id") is not None:
                self.sleep[avatar_id]["bed_id"] = str(data["bed_id"])

    def _on_avatar_sleep_ended(self, data: Mapping[str, Any]) -> None:
        avatar_id = str(data["avatar_id"])
        self.asleep[avatar_id] = False
        self.sleep.pop(avatar_id, None)

    def _on_world_need_changed(self, data: Mapping[str, Any]) -> None:
        self.needs.setdefault(str(data["avatar_id"]), {})[str(data["need"])] = float(data["value"])

    def _on_avatar_decision_requested(self, data: Mapping[str, Any]) -> None:
        avatar_id = str(data["avatar_id"])
        self.needs[avatar_id] = {k: float(v) for k, v in data["needs"].items()}
        if avatar_id in self.entities:
            self.entities[avatar_id]["position"] = _position(data["position"])
        self.controllers[avatar_id] = dict(data["controller"])
        self.decisions[avatar_id] = {"reason": data["reason"], "tick": self._event_tick}

    def _on_avatar_possessed(self, data: Mapping[str, Any]) -> None:
        self.controllers[str(data["avatar_id"])] = dict(data["controller"])

    _on_avatar_released = _on_avatar_possessed

    # ------------------------------------------------------------- sessão e relógio

    def _on_world_session_started(self, data: Mapping[str, Any]) -> None:
        self.session = {
            "cartridge_version": data["cartridge_version"],
            "tick_seconds": int(data["tick_seconds"]),
        }
        if data.get("map") is not None:
            self.session["map"] = dict(data["map"])
        if data.get("affordances"):
            self.session["affordances"] = [dict(a) for a in data["affordances"]]  # ADR-0051
        if data.get("metrics"):
            self.session["metrics"] = [dict(m) for m in data["metrics"]]  # ADR-0054
        # ADR-0056. O estado não carrega null: o raio nulo (o mapa inteiro) é ausência.
        perception = cast(Mapping[str, Any], data.get("perception") or {})
        radius = perception.get("radius")
        if radius is not None:
            self.session["perception"] = {"radius": int(radius)}
        self.clock = {
            "mode": data["mode"],
            "scale": float(data["scale"]),
            "paused": bool(data["paused"]),
        }

    def _on_world_clock_paused(self, data: Mapping[str, Any]) -> None:
        self.clock["paused"] = True

    def _on_world_clock_resumed(self, data: Mapping[str, Any]) -> None:
        self.clock["paused"] = False

    def _on_world_clock_mode_changed(self, data: Mapping[str, Any]) -> None:
        self.clock["mode"] = data["mode"]

    def _on_world_clock_scale_changed(self, data: Mapping[str, Any]) -> None:
        self.clock["scale"] = float(data["scale"])

    # ------------------------------------------------------------- consultas

    def position_at(self, entity_id: str, tick: int) -> dict[str, int] | None:
        motion = self.motion.get(entity_id)
        if motion is None:
            return self.entities.get(entity_id, {}).get("position")
        path = cast(list[dict[str, int]], motion["path"])
        steps = math.floor((tick - motion["depart_tick"]) * motion["tiles_per_tick"] + 1e-9)
        return path[max(0, min(len(path) - 1, steps))]

    # ------------------------------------------------------------- métricas do dia (ADR-0054)

    def _catalog(self) -> list[Mapping[str, Any]]:
        return list((self.session or {}).get("metrics", []))

    def _metric_day(self) -> str:
        """O dia simulado do evento: o tick dividido pelos ticks de um dia, a partir do dia 1."""
        tick_seconds = int((self.session or {}).get("tick_seconds", 60))
        return str(self._event_tick // max(1, 86400 // tick_seconds) + 1)

    def _day_values(self, day: str) -> dict[str, Any]:
        values = self.metrics.setdefault(day, {})
        newest = max(int(d) for d in self.metrics)
        for old in [d for d in self.metrics if int(d) <= newest - METRIC_DAYS]:
            del self.metrics[old]
        return values

    def _count(self, kind: str, data: Mapping[str, Any]) -> None:
        for metric in self._catalog():
            if metric["kind"] == "count" and metric.get("event") == kind:
                where = cast(Mapping[str, Any], metric.get("where") or {})
                if all(_lookup(data, path) == value for path, value in where.items()):
                    values = self._day_values(self._metric_day())
                    by = cast(Mapping[str, Any] | None, metric.get("by"))
                    if by is None:
                        values[metric["id"]] = values.get(metric["id"], 0) + 1
                    else:
                        group = self._group(_lookup(data, str(by["field"])), by.get("attribute"))
                        counts = values.setdefault(metric["id"], {})
                        counts[group] = counts.get(group, 0) + 1

    def _peak(self, kind: str, data: Mapping[str, Any]) -> None:
        values: Mapping[str, Any] = {}
        if kind == "campsverso.world.need.changed.v1":
            values = {str(data["need"]): data["value"]}
        elif kind == "campsverso.avatar.decision_requested.v1":
            values = cast(Mapping[str, Any], data.get("needs") or {})
        if not values:
            return
        day = self._metric_day()
        peaks = self.peaks.setdefault(day, {})
        for need, value in values.items():
            peaks[need] = max(peaks.get(need, 0.0), float(value))
        newest = max(int(d) for d in self.peaks)
        for old in [d for d in self.peaks if int(d) <= newest - METRIC_DAYS]:
            del self.peaks[old]
        self._show_peaks(day)

    def _show_peaks(self, day: str) -> None:
        peaks = self.peaks.get(day, {})
        for metric in self._catalog():
            need = str(metric.get("need"))
            if metric["kind"] == "max_need" and need in peaks:
                self._day_values(day)[metric["id"]] = peaks[need]

    def _group(self, value: Any, attribute: Any) -> str:
        if attribute is None:
            return str(value)
        entity = self.entities.get(str(value))
        group = None if entity is None else entity["attributes"].get(str(attribute))
        return "?" if group is None else str(group)

    def _sample(self) -> None:
        """Itens com os avatares: o último valor do dia é o do fim do dia."""
        items = [m for m in self._catalog() if m["kind"] == "item"]
        if not items or self.session is None:
            return
        day = self._metric_day()
        avatars = [i for i, e in self.entities.items() if e["kind"] == "avatar"]
        values = self._day_values(day)
        for metric in items:
            item = str(metric.get("item"))
            values[metric["id"]] = sum(self.containers.get(a, {}).get(item, 0) for a in avatars)

    # ------------------------------------------------------------- o caderno (ADR-0060)

    def _notebook(self, avatar_id: str) -> dict[str, Any]:
        return self.memory.setdefault(avatar_id, {"beliefs": [], "notes": []})

    def _on_memory_noted(self, data: Mapping[str, Any]) -> None:
        notes = cast(list[dict[str, Any]], self._notebook(str(data["avatar_id"]))["notes"])
        notes.append({"tick": self._event_tick, "text": str(data["text"])})
        del notes[:-NOTES_KEPT]

    def _on_memory_reflected(self, data: Mapping[str, Any]) -> None:
        book = self._notebook(str(data["avatar_id"]))
        book["day"] = int(data["day"])
        book["summary"] = str(data["summary"])
        if data.get("plan"):
            book["plan"] = str(data["plan"])
        else:
            book.pop("plan", None)

    def _on_memory_belief_formed(self, data: Mapping[str, Any]) -> None:
        self._belief(data, float(data["confidence"]))

    def _on_memory_belief_updated(self, data: Mapping[str, Any]) -> None:
        after = cast(Mapping[str, Any], data["confidence"])["after"]
        self._belief(data, float(after))

    def _on_memory_belief_retracted(self, data: Mapping[str, Any]) -> None:
        book = self._notebook(str(data["avatar_id"]))
        beliefs = cast(list[dict[str, Any]], book["beliefs"])
        book["beliefs"] = [b for b in beliefs if b["belief_id"] != data["belief_id"]]

    def _belief(self, data: Mapping[str, Any], confidence: float) -> None:
        book = self._notebook(str(data["avatar_id"]))
        beliefs = [
            b
            for b in cast(list[dict[str, Any]], book["beliefs"])
            if b["belief_id"] != data["belief_id"]
        ]
        beliefs.append(
            {
                "belief_id": str(data["belief_id"]),
                "statement": str(data["statement"]),
                "confidence": confidence,
            }
        )
        beliefs.sort(key=lambda b: (-float(b["confidence"]), str(b["belief_id"])))
        book["beliefs"] = beliefs[:BELIEFS_KEPT]
