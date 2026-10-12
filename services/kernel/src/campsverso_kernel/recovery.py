"""Abrir um mundo: novo, ou retomado do último snapshot mais os incrementais (ADR-0044).

A recuperação é a de um banco de dados: carrega o último snapshot completo e reexecuta o diário de
entradas até a última fronteira gravada. Como o núcleo é determinístico, os fatos regenerados têm de
ser idênticos aos que já estão no outbox; qualquer diferença denuncia quebra de determinismo e é
erro fatal. Para quem consome os eventos, a queda é só uma pausa: nada é publicado de novo além do
que ainda não tinha saído.
"""

import hashlib
from collections.abc import Sequence
from dataclasses import dataclass

from campsverso_kernel.core import KernelCore, WorldConfig
from campsverso_kernel.definition import WorldDefinition
from campsverso_kernel.engine import Engine
from campsverso_kernel.facts import Fact
from campsverso_kernel.snapshot import decode, restore
from campsverso_kernel.version import RunVersion
from campsverso_kernel.world import plain
from campsverso_ports import (
    BlobStore,
    EnvelopeValidator,
    InputRow,
    OutboxRow,
    RuleConfig,
    WorldStore,
)


class RecoveryError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class Recovery:
    snapshot_ref: str
    snapshot_tick: int
    tick: int
    inputs: int
    facts: int


def open_world(
    definition: WorldDefinition,
    config: WorldConfig,
    rules: Sequence[RuleConfig],
    version: RunVersion,
    store: WorldStore,
    blobs: BlobStore,
    *,
    rules_source: str = "",
    validator: EnvelopeValidator | None = None,
) -> tuple[Engine, Recovery | None]:
    """Um mundo novo ainda não começou: o serviço chama `start`. Um mundo gravado volta pronto."""
    state = store.state()
    if state is None:
        core = KernelCore(definition, config, rules, rules_source)
        return Engine(core, version, validator), None
    snapshots = store.snapshots()
    if not snapshots:
        raise RecoveryError("há estado gravado, mas nenhum snapshot para começar")
    latest = snapshots[-1]
    data = blobs.get(latest.ref)
    if hashlib.sha256(data).hexdigest() != latest.sha256:
        raise RecoveryError(f"o snapshot {latest.ref} não confere com o sha256 gravado")
    engine = Engine(restore(definition, config, decode(data)), version, validator)

    inputs = store.inputs_from(latest.next_input)
    expected = store.outbox_from(latest.next_seq)
    if (inputs or expected or state.tick > latest.tick) and state.version != version.key:
        raise RecoveryError(
            "os incrementais depois do último snapshot foram gravados por outra versão do código "
            f"({state.version}); a atual é {version.key}. Volte à versão que gravou para "
            "recuperar: ela termina o trabalho e grava um snapshot ao parar com elegância."
        )
    produced = _replay(engine, inputs, state.tick)
    _verify(produced, expected)
    return engine, Recovery(latest.ref, latest.tick, state.tick, len(inputs), len(produced))


def _replay(engine: Engine, inputs: Sequence[InputRow], until_tick: int) -> list[Fact]:
    core = engine.core
    produced: list[Fact] = []
    index = 0
    while True:
        while index < len(inputs) and inputs[index].tick == core.tick:
            entry = inputs[index]
            if entry.kind == "snapshot":
                engine.snapshot()
            elif entry.envelope is not None:
                engine.submit(entry.envelope)
            index += 1
        produced += core.drain()
        if core.tick >= until_tick:
            break
        engine.step()
    if index != len(inputs):
        entry = inputs[index]
        raise RecoveryError(
            f"a entrada {entry.position} do diário vale no tick {entry.tick}, "
            f"mas a reexecução parou no tick {core.tick}"
        )
    return produced


def _verify(produced: Sequence[Fact], expected: Sequence[OutboxRow]) -> None:
    for fact, row in zip(produced, expected, strict=False):
        envelope = row.envelope
        regenerated = (fact.seq, fact.tick, fact.type, plain(fact.data))
        recorded = (envelope["seq"], envelope["tick"], envelope["type"], envelope["data"])
        if regenerated != recorded:
            raise RecoveryError(
                f"determinismo quebrado no seq {fact.seq}: a reexecução gerou {regenerated}, "
                f"o outbox tem {recorded}"
            )
    if len(produced) != len(expected):
        raise RecoveryError(
            f"a reexecução gerou {len(produced)} fatos, mas o outbox tem {len(expected)} "
            "depois do snapshot"
        )
