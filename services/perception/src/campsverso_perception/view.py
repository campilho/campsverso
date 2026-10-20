"""O estado da percepção: a projeção comum (ADR-0050), o `seq` das entregas publicadas, o que foi
entregue a cada avatar (para o delta, ADR-0056) e a foto de `perception.delivered.v1` (catálogo
§3.7) que a percepção monta para cada avatar."""

from collections.abc import Mapping
from typing import Any, cast

from campsverso_world_view import Projection, diff_views

MAX_PENDING = 1000  # eventos guardados por avatar entre uma entrega e outra (o contrato limita)
# O que não entra em "o que aconteceu": as próprias entregas e o pedido que elas respondem.
_NOT_PERCEIVED = ("campsverso.perception.", "campsverso.avatar.decision_requested.")
_SNAPSHOT_REASONS = frozenset({"session_started", "possessed"})


def _chebyshev(a: Mapping[str, int], b: Mapping[str, int]) -> int:
    return max(abs(int(a["x"]) - int(b["x"])), abs(int(a["y"]) - int(b["y"])))


class PerceptionState(Projection):
    def __init__(self, state: Mapping[str, Any] | None = None) -> None:
        super().__init__(state)
        raw: Mapping[str, Any] = state or {}
        self.out_seq: int = int(raw.get("out_seq", 0))  # seq das entregas publicadas
        # Por avatar: a última visão entregue, com o tick, o controlador e quantos deltas saíram
        # desde a última foto.
        self.delivered: dict[str, dict[str, Any]] = {
            k: dict(v) for k, v in raw.get("delivered", {}).items()
        }
        # Por avatar: os eventos aplicados desde a última entrega, que o delta leva.
        self.pending: dict[str, list[dict[str, Any]]] = {
            k: list(v) for k, v in raw.get("pending", {}).items()
        }

    def export(self) -> dict[str, Any]:
        return {
            **super().export(),
            "out_seq": self.out_seq,
            "delivered": self.delivered,
            "pending": self.pending,
        }

    # ------------------------------------------------------------- eventos

    def apply(self, stream: str, envelope: Mapping[str, Any]) -> None:
        super().apply(stream, envelope)
        event_type = str(envelope["type"])
        if event_type.startswith(_NOT_PERCEIVED):
            return
        data = cast(Mapping[str, Any], envelope.get("data") or {})
        seen = {"tick": self._event_tick, "type": event_type, "data": dict(data)}
        # Um evento `agent` é de um avatar; um `world`, de todos. Antes da primeira entrega não há
        # com o que comparar, então só quem já recebeu uma foto acumula o que aconteceu.
        if stream == "agent" and "avatar_id" in data:
            targets = [str(data["avatar_id"])]
        else:
            targets = list(self.delivered)
        for avatar_id in targets:
            if avatar_id in self.delivered:
                queue = self.pending.setdefault(avatar_id, [])
                queue.append(seen)
                del queue[:-MAX_PENDING]

    # ------------------------------------------------------------- entregas

    def wants_snapshot(self, avatar_id: str, controller_id: str, reason: str, every: int) -> bool:
        """Foto na primeira entrega, ao começar a sessão ou assumir a posse, quando o controlador
        mudou e a cada `every` deltas (ADR-0056); delta no resto."""
        last = self.delivered.get(avatar_id)
        return (
            last is None
            or reason in _SNAPSHOT_REASONS
            or str(last["controller"]) != controller_id
            or int(last["deltas"]) >= every
        )

    def deliver(self, avatar_id: str, controller_id: str, *, snapshot: bool) -> None:
        """Registra uma entrega: a foto zera os deltas, o delta os incrementa; a fila zera."""
        previous = self.delivered.get(avatar_id)
        deltas = 0 if snapshot or previous is None else int(previous["deltas"]) + 1
        self.delivered[avatar_id] = {
            "tick": self.tick,
            "controller": controller_id,
            "deltas": deltas,
            "view": self.view(avatar_id),
        }
        self.pending[avatar_id] = []

    # ------------------------------------------------------------- a foto

    def radius(self) -> int | None:
        """O raio declarado pelo cartucho (session.started); None é o mapa inteiro."""
        perception = cast(Mapping[str, Any], (self.session or {}).get("perception") or {})
        value = perception.get("radius")
        return int(value) if isinstance(value, int) else None

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
        radius = self.radius()
        center = cast(Mapping[str, int] | None, me["position"])

        def near(entity_id: str) -> bool:
            """Dentro do raio: pela posição, ou pela do contêiner que a guarda; o próprio avatar
            e o que não tem lugar conhecido entram sempre."""
            if radius is None or center is None or entity_id == avatar_id:
                return True
            where = self.position_at(entity_id, tick)
            if where is None:
                holder = self.entities.get(entity_id, {}).get("container_id")
                where = self.position_at(str(holder), tick) if holder else None
            return where is None or _chebyshev(center, where) <= radius

        today = str(self.day)
        weather_day = today if today in self.weather else max(self.weather, key=int, default=today)
        entities: list[dict[str, Any]] = []
        for entity_id, entity in sorted(self.entities.items()):
            if not near(entity_id):
                continue
            item: dict[str, Any] = {"entity_id": entity_id, "kind": entity["kind"]}
            position = self.position_at(entity_id, tick)
            if position is not None:
                item["position"] = position
            if "container_id" in entity:
                item["container_id"] = entity["container_id"]
            item["attributes"] = dict(sorted(entity["attributes"].items()))
            entities.append(item)
        view: dict[str, Any] = {
            "clock": {"tick": tick, "sim_time": self.simtime, "day": self.day, "phase": self.phase},
            "weather": {
                "condition": self.weather.get(weather_day, "desconhecido"),
                "day": int(weather_day),
            },
            "self": me,
            "containers": [
                {
                    "container_id": container,
                    "items": [self.stack(container, i, q) for i, q in sorted(stock.items())],
                }
                for container, stock in sorted(self.containers.items())
                if stock and near(container)
            ],
            "entities": entities,
        }
        window = self.window(center, radius)
        if window is not None:
            view["map"] = window
        return view

    def window(self, center: Mapping[str, int] | None, radius: int | None) -> dict[str, Any] | None:
        """O terreno ao alcance (ADR-0056): as linhas recortadas ao raio e a legenda do que
        aparece nelas. Sem terreno na sessão (kernel antigo), nada."""
        session_map = cast(Mapping[str, Any], (self.session or {}).get("map") or {})
        rows = cast(list[str], session_map.get("rows") or [])
        legend = cast(Mapping[str, Any], session_map.get("legend") or {})
        if not rows or not legend:
            return None
        if radius is None or center is None:
            x0, y0, cut = 0, 0, list(rows)
        else:
            x0, y0 = max(0, int(center["x"]) - radius), max(0, int(center["y"]) - radius)
            x1, y1 = int(center["x"]) + radius + 1, int(center["y"]) + radius + 1
            cut = [row[x0:x1] for row in rows[y0:y1]]
        used = set("".join(cut))
        return {
            "origin": {"x": x0, "y": y0},
            "rows": cut,
            "legend": {code: dict(legend[code]) for code in sorted(legend) if code in used},
        }

    # ------------------------------------------------------------- o delta

    def delta(self, avatar_id: str) -> dict[str, Any]:
        """O que mudou desde a última entrega (ADR-0056): a visão de agora contra a entregue,
        registro inteiro de quem mudou, quem sumiu e o que aconteceu no meio-tempo."""
        last = self.delivered[avatar_id]
        now = self.view(avatar_id)
        return {
            "avatar_id": avatar_id,
            "since_tick": int(last["tick"]),
            "as_of_tick": self.tick,
            "clock": now["clock"],
            "self": now["self"],
            "events": list(self.pending.get(avatar_id, [])),
            **diff_views(cast(Mapping[str, Any], last["view"]), now),
        }
