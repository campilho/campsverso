"""Hash canônico de eventos (ADR-0021): prova que duas execuções produziram os mesmos fatos."""

import hashlib
import json
from collections.abc import Iterable, Mapping
from typing import Any

# Campos de relógio de parede ou aleatórios por natureza; o resto precisa ser idêntico.
IGNORED = frozenset({"id", "time", "causationid", "correlationid", "traceparent"})
# O estado do snapshot guarda os ids dos comandos das ações em curso (UUIDv7, com relógio e
# acaso), então o sha256 muda entre execuções com controlador. Recuperação e replay conferem o
# sha256 exato, porque reexecutam com os mesmos ids do diário (ADR-0048).
IGNORED_DATA = {"campsverso.world.snapshot.created.v1": frozenset({"sha256"})}


def canonical(envelope: Mapping[str, Any]) -> dict[str, Any]:
    kept = {k: v for k, v in envelope.items() if k not in IGNORED}
    skip = IGNORED_DATA.get(str(envelope.get("type")))
    if skip and isinstance(kept.get("data"), Mapping):
        data: Mapping[str, Any] = kept["data"]
        kept["data"] = {k: v for k, v in data.items() if k not in skip}
    return kept


def canonical_hash(envelopes: Iterable[Mapping[str, Any]]) -> str:
    digest = hashlib.sha256()
    for envelope in envelopes:
        digest.update(
            json.dumps(
                canonical(envelope), sort_keys=True, separators=(",", ":"), ensure_ascii=False
            ).encode()
        )
        digest.update(b"\n")
    return digest.hexdigest()
