"""A diferença entre duas visões da percepção (ADR-0056): o que um delta leva além do próprio
avatar, do relógio e dos eventos. Serve à percepção e às ferramentas que estimam o custo."""

from collections.abc import Mapping
from typing import Any


def diff_views(before: Mapping[str, Any], after: Mapping[str, Any]) -> dict[str, Any]:
    """Só o que mudou de `before` para `after`: entidades que apareceram ou mudaram (o registro
    inteiro), as que sumiram, contêineres que mudaram (um que esvaziou vem sem itens) e o clima,
    se mudou. Chaves ausentes significam "nada mudou"."""
    old_entities = {str(e["entity_id"]): e for e in before["entities"]}
    old_containers = {str(c["container_id"]): c for c in before["containers"]}
    new_containers = {str(c["container_id"]): c for c in after["containers"]}
    entities = [e for e in after["entities"] if old_entities.get(str(e["entity_id"])) != e]
    gone = sorted(set(old_entities) - {str(e["entity_id"]) for e in after["entities"]})
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
    return diff
