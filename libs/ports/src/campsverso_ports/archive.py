"""Porta do arquivo histórico de eventos: JSONL hoje, S3 + Athena na fase AWS (contratos §12)."""

from collections.abc import Sequence
from typing import Protocol

from campsverso_ports.bus import Envelope


class EventArchive(Protocol):
    def append(self, envelope: Envelope) -> bool:
        """Acrescenta ao fim. Devolve False se o `id` já estava no arquivo (entrega repetida)."""
        ...

    def flush(self) -> None:
        """Garante no disco tudo o que foi acrescentado."""
        ...

    def compress_old(self) -> Sequence[str]:
        """Comprime os dias antigos; devolve o que foi comprimido. Nunca apaga conteúdo."""
        ...

    def close(self) -> None: ...
