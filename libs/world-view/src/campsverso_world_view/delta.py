"""A diferença entre duas visões da percepção (ADR-0056): o que um delta leva além do próprio
avatar, do relógio e dos eventos. Serve à percepção e às ferramentas que estimam o custo."""

from collections.abc import Callable, Mapping, Sequence
from typing import Any, cast


def diff_views(
    before: Mapping[str, Any],
    after: Mapping[str, Any],
    exists: Callable[[str], bool] | None = None,
) -> dict[str, Any]:
    """Só o que mudou de `before` para `after`: entidades que apareceram ou mudaram (o registro
    inteiro), as que sumiram, contêineres que mudaram (um que esvaziou vem sem itens) e o clima,
    se mudou. Chaves ausentes significam "nada mudou". Com `exists` (o mundo ainda tem a
    entidade?), quem sumiu da visão mas continua no mundo vai para `out_of_view`, e `gone` fica
    só com o que deixou de existir (ADR-0067)."""
    old_entities = {str(e["entity_id"]): e for e in before["entities"]}
    old_containers = {str(c["container_id"]): c for c in before["containers"]}
    new_containers = {str(c["container_id"]): c for c in after["containers"]}
    entities = [e for e in after["entities"] if old_entities.get(str(e["entity_id"])) != e]
    vanished = sorted(set(old_entities) - {str(e["entity_id"]) for e in after["entities"]})
    away = [e for e in vanished if exists is not None and exists(e)]
    gone = [e for e in vanished if e not in away]
    containers = [c for cid, c in new_containers.items() if old_containers.get(cid) != c]
    containers += [
        {"container_id": cid, "items": []} for cid in old_containers if cid not in new_containers
    ]
    diff: dict[str, Any] = {}
    if after["weather"] != before["weather"]:
        diff["weather"] = after["weather"]
    if containers:
        diff["containers"] = sorted(containers, key=lambda c: str(c["container_id"]))
    if entities:
        diff["entities"] = entities
    if gone:
        diff["gone"] = gone
    if away:
        diff["out_of_view"] = away
    return diff


SPOKE = "campsverso.avatar.spoke.v1"


def apply_delta(view: Mapping[str, Any], delta: Mapping[str, Any]) -> dict[str, Any]:
    """A foto depois de um delta da percepção (o inverso de `diff_views`): para quem precisa da foto
    inteira e recebe deltas, como a rotina do dev quando a mente o conduz (ADR-0080). As entidades e
    os contêineres que mudaram trocam de registro, na ordem da foto; os que sumiram saem; o relógio,
    o próprio corpo e o clima vêm do delta. O `heard` passa a ser as falas do delta, como a foto
    traria desde a última entrega (ADR-0078)."""
    me = str(cast(Mapping[str, Any], delta["self"])["entity_id"])
    out: dict[str, Any] = {**view, "clock": delta["clock"], "self": delta["self"]}
    if "weather" in delta:
        out["weather"] = delta["weather"]
    removed = {str(e) for e in [*delta.get("gone", ()), *delta.get("out_of_view", ())]}
    changed = {str(e["entity_id"]): e for e in delta.get("entities", ())}
    entities = [
        changed.pop(str(e["entity_id"]), e)
        for e in view.get("entities", ())
        if str(e["entity_id"]) not in removed
    ]
    out["entities"] = entities + list(changed.values())
    boxes = {str(c["container_id"]): c for c in delta.get("containers", ())}
    containers = [boxes.pop(str(c["container_id"]), c) for c in view.get("containers", ())]
    out["containers"] = [c for c in containers + list(boxes.values()) if c.get("items")]
    heard: list[dict[str, Any]] = []
    for event in cast(Sequence[Mapping[str, Any]], delta.get("events") or ()):
        if event.get("type") != SPOKE:
            continue
        data = cast(Mapping[str, Any], event.get("data") or {})
        if str(data.get("avatar_id")) == me:
            continue
        item: dict[str, Any] = {
            "tick": event.get("tick"),
            "avatar_id": str(data["avatar_id"]),
            "text": data["text"],
        }
        if data.get("listener_id") is not None:
            item["listener_id"] = str(data["listener_id"])
        heard.append(item)
    if heard:
        out["heard"] = heard
    else:
        out.pop("heard", None)
    return out
