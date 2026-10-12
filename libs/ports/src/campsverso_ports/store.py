"""Porta do estado durável do kernel: outbox, diário de entradas e snapshots (plano do M2 §1)."""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal, Protocol

from campsverso_ports.bus import Envelope

type InputKind = Literal["command", "snapshot"]


@dataclass(frozen=True, slots=True)
class OutboxRow:
    """Um fato já envelopado, na ordem de `seq`, esperando (ou não) a publicação."""

    seq: int
    subject: str
    envelope: Envelope


@dataclass(frozen=True, slots=True)
class InputRow:
    """Uma entrada do diário: o que entrou no núcleo e em que fronteira de tick.

    `tick` é a fronteira: a entrada valeu antes de rodar esse tick. `snapshot` marca um snapshot
    pedido fora do horário (parada elegante), para que reexecutar o diário o reproduza.
    """

    position: int
    tick: int
    kind: InputKind
    command_id: str | None = None
    envelope: Envelope | None = None


@dataclass(frozen=True, slots=True)
class SnapshotRef:
    """Onde está um snapshot completo e o que ele cobre."""

    ref: str  # chave no BlobStore
    tick: int
    sha256: str
    next_seq: int  # primeiro seq que o snapshot ainda não contém
    next_input: int  # primeira posição do diário que o snapshot ainda não contém
    version: str


@dataclass(frozen=True, slots=True)
class StoreState:
    tick: int  # fronteira da última gravação
    version: str  # versão do código que fez a última gravação
    next_seq: int
    next_input: int


@dataclass(frozen=True, slots=True)
class Commit:
    """Tudo o que uma operação do núcleo produziu, gravado numa transação só."""

    tick: int
    version: str
    inputs: Sequence[InputRow] = ()
    outbox: Sequence[OutboxRow] = ()
    snapshot: SnapshotRef | None = None


class WorldStore(Protocol):
    def commit(self, commit: Commit) -> None: ...

    def state(self) -> StoreState | None:
        """None num mundo novo, que ainda não gravou nada."""
        ...

    def snapshots(self) -> Sequence[SnapshotRef]:
        """Do mais antigo para o mais recente."""
        ...

    def forget_snapshot(self, ref: str) -> None: ...

    def prune_outbox(self, before_seq: int) -> None:
        """Apaga do outbox os fatos já publicados com seq menor (o arquivo JSONL os guarda)."""
        ...

    def inputs_from(self, position: int) -> Sequence[InputRow]: ...

    def has_command(self, command_id: str) -> bool: ...

    def outbox_from(self, seq: int) -> Sequence[OutboxRow]: ...

    def unpublished(self, limit: int) -> Sequence[OutboxRow]: ...

    def mark_published(self, up_to_seq: int) -> None: ...

    def recent_ids(self, limit: int) -> Sequence[tuple[int, str]]:
        """(seq, id) dos últimos fatos, para resolver `causationid` depois de um reinício."""
        ...

    def close(self) -> None: ...
