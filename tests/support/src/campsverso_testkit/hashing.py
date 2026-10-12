"""Hash canônico de eventos (ADR-0021): prova que duas execuções produziram os mesmos fatos."""

import hashlib
import json
from collections.abc import Iterable, Mapping
from typing import Any

# Campos de relógio de parede ou aleatórios por natureza; o resto precisa ser idêntico.
IGNORED = frozenset({"id", "time", "causationid", "correlationid", "traceparent"})


def canonical_hash(envelopes: Iterable[Mapping[str, Any]]) -> str:
    digest = hashlib.sha256()
    for envelope in envelopes:
        kept = {k: v for k, v in envelope.items() if k not in IGNORED}
        digest.update(
            json.dumps(kept, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
        )
        digest.update(b"\n")
    return digest.hexdigest()
