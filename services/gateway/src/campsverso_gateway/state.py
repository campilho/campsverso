"""O estado que a UI recebe (`ObserverState`, contracts/realtime) e o merge patch entre dois
estados (RFC 7386; ADR-0050).

O estado não carrega null: no merge patch, null apaga a chave. Atributo nulo é atributo ausente.
"""

from collections.abc import Mapping
from typing import Any, cast

from campsverso_world_view import Projection


def without_nulls(value: Any) -> Any:
    """Cópia profunda sem as chaves de valor None (listas ficam como estão, copiadas)."""
    if isinstance(value, Mapping):
        items = cast(Mapping[str, Any], value).items()
        return {k: without_nulls(v) for k, v in items if v is not None}
    if isinstance(value, list):
        return [without_nulls(v) for v in cast(list[Any], value)]
    return value


def observer_state(
    projection: Projection, pulse: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    """O estado da UI; `pulse` é o último pulso do kernel, já com `alive` (ADR-0051)."""
    p = projection
    return without_nulls(
        {
            "cartridge": p.cartridge,
            "tick": p.tick,
            "sim_time": p.simtime,
            "day": p.day,
            "phase": p.phase,
            "date": p.date,
            "season": p.season,
            "session": p.session,
            "clock": p.clock,
            "pulse": pulse,
            "weather": p.weather,
            "entities": p.entities,
            "containers": {k: v for k, v in p.containers.items() if v},
            "motion": p.motion,
            "actions": p.actions,
            "needs": p.needs,
            "asleep": p.asleep,
            "sleep": p.sleep,
            "controllers": p.controllers,
            "decisions": p.decisions,
            "metrics": p.metrics,
            "memory": p.memory,
        }
    )


def merge_diff(old: Mapping[str, Any], new: Mapping[str, Any]) -> dict[str, Any]:
    """O merge patch que leva `old` a `new`. Vazio quando não mudou nada."""
    patch: dict[str, Any] = {key: None for key in old if key not in new}
    for key, value in new.items():
        before = old.get(key)
        if key in old and before == value:
            continue
        if isinstance(before, Mapping) and isinstance(value, Mapping):
            patch[key] = merge_diff(cast(Mapping[str, Any], before), cast(Mapping[str, Any], value))
        else:
            patch[key] = value
    return patch


def apply_merge_patch(target: Any, patch: Any) -> Any:
    """RFC 7386, como a UI aplica (usado nos testes para conferir o vai e volta)."""
    if not isinstance(patch, Mapping):
        return patch
    result: dict[str, Any] = (
        dict(cast(Mapping[str, Any], target)) if isinstance(target, Mapping) else {}
    )
    for key, value in cast(Mapping[str, Any], patch).items():
        if value is None:
            result.pop(key, None)
        else:
            result[key] = apply_merge_patch(result.get(key), value)
    return result
