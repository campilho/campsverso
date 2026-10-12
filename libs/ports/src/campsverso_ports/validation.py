"""Porta de validação de envelopes contra os contratos (critério A2)."""

from collections.abc import Sequence
from typing import Protocol

from campsverso_ports.bus import Envelope


class EnvelopeValidator(Protocol):
    def validate(
        self, envelope: Envelope, published_subject: str | None = None
    ) -> Sequence[object]:
        """Problemas do envelope diante do contrato, em ordem estável; vazio se está tudo certo."""
        ...
