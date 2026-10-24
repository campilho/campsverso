"""A diferença entre duas visões da percepção (ADR-0056): o que um delta leva além do próprio
avatar, do relógio e dos eventos. Serve à percepção e às ferramentas que estimam o custo."""

from collections.abc import Callable, Mapping
from typing import Any


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
