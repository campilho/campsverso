"""Snapshot completo: o estado do mundo num documento JSON canônico, com sha256 (plano do M2 §1).

O documento guarda também a versão do código e dos cartuchos e os dados do mundo (id, seed, data-
base). A ordem das chaves é a dos dicionários do estado: assim o mundo restaurado itera igual.
"""

import json
from collections.abc import Mapping, Sequence
from typing import Any, cast

from campsverso_kernel.core import KernelCore, WorldConfig
from campsverso_kernel.definition import WorldDefinition
from campsverso_ports import RuleConfig

FORMAT = 1


class SnapshotError(Exception):
    pass


def document(core: KernelCore, version: Mapping[str, Any], next_seq: int) -> dict[str, Any]:
    """`next_seq` é o primeiro seq depois do snapshot (o próprio aviso de snapshot já conta)."""
    state = core.export_state()
    state["next_seq"] = next_seq
    doc: dict[str, Any] = {
        "format": FORMAT,
        "worldid": core.config.worldid,
        "seed": core.config.seed,
        "start": core.config.start.isoformat(),
        "version": dict(version),
        "state": state,
    }
    if core.config.map is not None:  # só quem tem variante: os snapshots de antes não mudam
        doc["map"] = core.config.map
    return doc


def encode(doc: Mapping[str, Any]) -> bytes:
    return json.dumps(doc, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()


def decode(data: bytes) -> dict[str, Any]:
    doc = cast(dict[str, Any], json.loads(data))
    if doc.get("format") != FORMAT:
        raise SnapshotError(f"formato de snapshot desconhecido: {doc.get('format')!r}")
    return doc


def restore(definition: WorldDefinition, config: WorldConfig, doc: Mapping[str, Any]) -> KernelCore:
    """Núcleo montado a partir dos cartuchos, com o estado do snapshot por cima."""
    expected = (config.worldid, config.seed, config.start.isoformat(), config.map)
    found = (doc["worldid"], doc["seed"], doc["start"], doc.get("map"))
    if found != expected:
        raise SnapshotError(
            f"o snapshot é do mundo {found}, mas a configuração diz {expected}; "
            "um mundo existente não muda de id, seed, data-base nem mapa"
        )
    rules: Sequence[RuleConfig] = ()
    core = KernelCore(definition, config, rules, rules_source="snapshot")
    core.restore_state(cast(Mapping[str, Any], doc["state"]))
    return core
