"""O núcleo mais os snapshots completos agendados: o que o serviço e a recuperação repetem igual.

O snapshot agendado cai depois do tick que fecha cada bloco de `snapshot_every` ticks. Ele mesmo é
um fato (`world.snapshot.created.v1`, internal), com seq, então faz parte do resultado
determinístico: a mesma execução gera os mesmos snapshots com o mesmo sha256.
"""

import hashlib
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from campsverso_kernel.core import KernelCore
from campsverso_kernel.snapshot import document, encode
from campsverso_kernel.version import RunVersion
from campsverso_ports import EnvelopeValidator

# Só dá para responder com command.rejected a quem tem id e tipo de comando válidos.
_UUID7 = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")
_COMMAND_TYPE = re.compile(r"^campsverso\.cmd\.[a-z0-9_]+(\.[a-z0-9_]+)+\.v[0-9]+$")


@dataclass(frozen=True, slots=True)
class Snapshot:
    snapshot_id: str
    ref: str  # chave no BlobStore
    tick: int
    data: bytes
    sha256: str
    next_seq: int


class Engine:
    def __init__(
        self, core: KernelCore, version: RunVersion, validator: EnvelopeValidator | None = None
    ) -> None:
        if version.snapshot_every < 1:
            raise ValueError("snapshot_every precisa ser pelo menos 1")
        self.core = core
        self.version = version
        self._validator = validator

    def submit(self, command: Mapping[str, Any]) -> None:
        """Comandos vêm de fora: fora do contrato, são recusados sem tocar no mundo (ADR-0046).

        A validação roda aqui, no caminho que a recuperação também reexecuta, para que a mesma
        entrada do diário dê sempre o mesmo resultado.
        """
        problems = [] if self._validator is None else list(self._validator.validate(command))
        command_type = str(command.get("type", ""))
        if not problems and _COMMAND_TYPE.match(command_type):
            self.core.submit(command)
        elif _UUID7.match(str(command.get("id", ""))) and _COMMAND_TYPE.match(command_type):
            self.core.reject_command(command, "invalid_command", str(problems[0])[:500])
        # Sem id ou sem tipo de comando não há a quem responder: o diário guarda e mais nada.

    def step(self) -> Snapshot | None:
        self.core.step()
        if self.core.tick % self.version.snapshot_every == 0:
            return self.snapshot()
        return None

    def snapshot(self) -> Snapshot:
        core = self.core
        seq = core.log.next_seq  # o aviso do snapshot vai ganhar este seq
        data = encode(document(core, self.version.as_dict(), next_seq=seq + 1))
        sha = hashlib.sha256(data).hexdigest()
        snapshot_id = f"t{core.tick:09d}-s{seq:09d}"
        ref = f"{core.config.worldid}/snapshots/{snapshot_id}.json"
        core.world.emit_fact(
            "campsverso.world.snapshot.created.v1",
            {
                "snapshot_id": snapshot_id,
                "ref": ref,
                "last_seq": seq - 1,
                "sha256": sha,
                "size_bytes": len(data),
            },
        )
        return Snapshot(snapshot_id, ref, core.tick, data, sha, seq + 1)
