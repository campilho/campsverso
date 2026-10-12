"""Projeção do mundo, montada só com eventos `world` e `agent` publicados (ADR-0028, ADR-0050).

Nada aqui conhece fazendas: o estado é o modelo de mundo do kernel (ADR-0025), e o que é da fazenda
chega como atributo. Também não há nada de desenho: posições são tiles, trajetos são ticks.
Pontos de crescimento e regras ocultas nunca chegam a esta projeção, porque o kernel não os publica
fora de `internal`, e quem a usa (percepção, gateway) não aplica eventos `internal` (princípio 5).
"""

import math
from collections.abc import Mapping
from typing import Any, cast

UNKNOWN_PHASE = "desconhecida"


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
        self.motion: dict[str, dict[str, Any]] = dict(raw.get("motion", {}))
        self.actions: dict[str, dict[str, Any]] = dict(raw.get("actions", {}))
        self.needs: dict[str, dict[str, float]] = {
            k: dict(v) for k, v in raw.get("needs", {}).items()
        }
        self.asleep: dict[str, bool] = dict(raw.get("asleep", {}))
        self.sleep: dict[str, dict[str, int]] = {  # início e fim previsto do sono (ADR-0052)
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
            "motion": self.motion,
            "actions": self.actions,
            "needs": self.needs,
            "asleep": self.asleep,
            "sleep": self.sleep,
            "session": self.session,
            "clock": self.clock,
            "controllers": self.controllers,
            "decisions": self.decisions,
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
        if data.get("display_name") is not None:
            entity["display_name"] = data["display_name"]
        self.entities[str(data["entity_id"])] = entity

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
        action: dict[str, Any] = {
            "action_id": data["action_id"],
            "action": data["action"],
            "params": dict(data.get("params") or {}),
            "applied_tick": int(data["applied_tick"]),
            "end_tick": int(data["applied_tick"]) + int(data["duration_ticks"]),
        }
        if "interrupt" in data:  # ADR-0052; ausente nos arquivos antigos
            action["interrupt"] = data["interrupt"]
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
