"""O estado da percepção: a projeção comum (ADR-0050) mais o `seq` das fotos publicadas, e a foto
de `perception.delivered.v1` (catálogo §3.7) que a percepção monta para cada avatar."""

from collections.abc import Mapping
from typing import Any

from campsverso_world_view import Projection


class PerceptionState(Projection):
    def __init__(self, state: Mapping[str, Any] | None = None) -> None:
        super().__init__(state)
        self.out_seq: int = int((state or {}).get("out_seq", 0))  # seq das fotos publicadas

    def export(self) -> dict[str, Any]:
        return {**super().export(), "out_seq": self.out_seq}

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
