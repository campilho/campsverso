"""Projeção do mundo visível, montada só com eventos `world` e `agent` (ADR-0028; bíblia §12).

Nada aqui conhece fazendas: a visão é genérica; o que é da fazenda chega como atributo.
Pontos de crescimento e regras ocultas nunca chegam a esta projeção, porque o kernel não os publica
fora de `internal`, que a percepção não tem permissão de ler (princípio 5).
"""

import math
from collections.abc import Mapping
from typing import Any, cast

UNKNOWN_PHASE = "desconhecida"


def _position(raw: Any) -> dict[str, int]:
    return {"x": int(raw["x"]), "y": int(raw["y"])}


def _path(origin: Mapping[str, int], waypoints: list[Mapping[str, int]]) -> list[dict[str, int]]:
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
    """O mundo como os avatares podem percebê-lo, por mundo. Serializável em JSON."""

    def __init__(self, state: Mapping[str, Any] | None = None) -> None:
        raw: Mapping[str, Any] = state or {}
        self.last_seq: dict[str, int] = dict(raw.get("last_seq", {}))  # por stream lido
        self.out_seq: int = int(raw.get("out_seq", 0))  # seq das fotos publicadas
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
        self.motion: dict[str, dict[str, Any]] = dict(raw.get("motion", {}))
        self.actions: dict[str, dict[str, Any]] = dict(raw.get("actions", {}))
        self.needs: dict[str, dict[str, float]] = {
            k: dict(v) for k, v in raw.get("needs", {}).items()
        }
        self.asleep: dict[str, bool] = dict(raw.get("asleep", {}))

    def export(self) -> dict[str, Any]:
        return {
            "last_seq": self.last_seq,
            "out_seq": self.out_seq,
            "cartridge": self.cartridge,
            "tick": self.tick,
            "simtime": self.simtime,
            "day": self.day,
            "phase": self.phase,
            "weather": self.weather,
            "entities": self.entities,
            "containers": self.containers,
            "motion": self.motion,
            "actions": self.actions,
            "needs": self.needs,
            "asleep": self.asleep,
        }

    # ------------------------------------------------------------- eventos

    def seen(self, stream: str, envelope: Mapping[str, Any]) -> bool:
        """Já aplicado? Cada stream chega em ordem de seq; uma reentrega fica para trás."""
        return int(envelope["seq"]) <= self.last_seq.get(stream, -1)

    def apply(self, stream: str, envelope: Mapping[str, Any]) -> None:
        self.last_seq[stream] = int(envelope["seq"])
        self.cartridge = str(envelope.get("cartridge") or self.cartridge)
        tick = envelope.get("tick")
        if isinstance(tick, int) and tick >= self.tick:
            self.tick, self.simtime = tick, cast(str | None, envelope.get("simtime"))
        name = str(envelope["type"]).removeprefix("campsverso.").rsplit(".", 1)[0]
        handler = getattr(self, "_on_" + name.replace(".", "_"), None)
        if handler is not None:
            handler(cast(Mapping[str, Any], envelope["data"]))

    def _on_world_entity_spawned(self, data: Mapping[str, Any]) -> None:
        entity: dict[str, Any] = {
            "kind": data["kind"],
            "attributes": dict(data.get("attributes") or {}),
        }
        if data.get("position") is not None:
            entity["position"] = _position(data["position"])
        if data.get("container_id") is not None:
            entity["container_id"] = data["container_id"]
        self.entities[str(data["entity_id"])] = entity

    def _on_world_entity_state_changed(self, data: Mapping[str, Any]) -> None:
        entity = self.entities.get(str(data["entity_id"]))
        if entity is not None:
            entity["attributes"].update(data["changes"])

    def _on_world_entity_moved(self, data: Mapping[str, Any]) -> None:
        entity_id = str(data["entity_id"])
        path = _path(data["origin"], list(data["waypoints"]))
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

    def _on_world_item_created(self, data: Mapping[str, Any]) -> None:
        self._add(str(data["container_id"]), str(data["item"]), int(data["qty"]))

    def _on_world_item_transferred(self, data: Mapping[str, Any]) -> None:
        self._add(str(data["from_container"]), str(data["item"]), -int(data["qty"]))
        self._add(str(data["to_container"]), str(data["item"]), int(data["qty"]))

    def _on_world_item_consumed(self, data: Mapping[str, Any]) -> None:
        self._add(str(data["container_id"]), str(data["item"]), -int(data["qty"]))

    def _on_world_weather_changed(self, data: Mapping[str, Any]) -> None:
        self.weather[str(data["day"])] = str(data["condition"])

    def _on_world_clock_phase_changed(self, data: Mapping[str, Any]) -> None:
        self.phase, self.day = str(data["phase"]), int(data["day"])

    def _on_action_accepted(self, data: Mapping[str, Any]) -> None:
        self.actions[str(data["avatar_id"])] = {
            "action_id": data["action_id"],
            "action": data["action"],
            "params": dict(data.get("params") or {}),
            "end_tick": int(data["applied_tick"]) + int(data["duration_ticks"]),
        }

    def _finish(self, data: Mapping[str, Any]) -> None:
        avatar_id = str(data["avatar_id"])
        current = self.actions.get(avatar_id)
        if current is not None and current["action_id"] == data["action_id"]:
            del self.actions[avatar_id]
            self.motion.pop(avatar_id, None)

    _on_action_completed = _finish
    _on_action_failed = _finish

    def _on_avatar_sleep_started(self, data: Mapping[str, Any]) -> None:
        self.asleep[str(data["avatar_id"])] = True

    def _on_avatar_sleep_ended(self, data: Mapping[str, Any]) -> None:
        self.asleep[str(data["avatar_id"])] = False

    def _on_world_need_changed(self, data: Mapping[str, Any]) -> None:
        self.needs.setdefault(str(data["avatar_id"]), {})[str(data["need"])] = float(data["value"])

    def _on_avatar_decision_requested(self, data: Mapping[str, Any]) -> None:
        avatar_id = str(data["avatar_id"])
        self.needs[avatar_id] = {k: float(v) for k, v in data["needs"].items()}
        if avatar_id in self.entities:
            self.entities[avatar_id]["position"] = _position(data["position"])

    # ------------------------------------------------------------- visão

    def position_at(self, entity_id: str, tick: int) -> dict[str, int] | None:
        motion = self.motion.get(entity_id)
        if motion is None:
            return self.entities.get(entity_id, {}).get("position")
        path = cast(list[dict[str, int]], motion["path"])
        steps = math.floor((tick - motion["depart_tick"]) * motion["tiles_per_tick"] + 1e-9)
        return path[max(0, min(len(path) - 1, steps))]

    def view(self, avatar_id: str) -> dict[str, Any]:
        """O instantâneo de `perception.delivered.v1` (catálogo §3.7), no tick mais recente."""
        tick = self.tick
        me: dict[str, Any] = {
            "entity_id": avatar_id,
            "position": self.position_at(avatar_id, tick),
            "needs": dict(sorted(self.needs.get(avatar_id, {}).items())),
            "asleep": self.asleep.get(avatar_id, False),
        }
        if avatar_id in self.actions:
            me["action"] = dict(self.actions[avatar_id])
        today = str(self.day)
        weather_day = today if today in self.weather else max(self.weather, key=int, default=today)
        entities: list[dict[str, Any]] = []
        for entity_id, entity in sorted(self.entities.items()):
            item: dict[str, Any] = {"entity_id": entity_id, "kind": entity["kind"]}
            position = self.position_at(entity_id, tick)
            if position is not None:
                item["position"] = position
            if "container_id" in entity:
                item["container_id"] = entity["container_id"]
            item["attributes"] = dict(sorted(entity["attributes"].items()))
            entities.append(item)
        return {
            "clock": {"tick": tick, "sim_time": self.simtime, "day": self.day, "phase": self.phase},
            "weather": {
                "condition": self.weather.get(weather_day, "desconhecido"),
                "day": int(weather_day),
            },
            "self": me,
            "containers": [
                {
                    "container_id": container,
                    "items": [{"item": i, "qty": q} for i, q in sorted(stock.items())],
                }
                for container, stock in sorted(self.containers.items())
                if stock
            ],
            "entities": entities,
        }
