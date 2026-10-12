"""Fatos: o que o núcleo determinístico produz. O serviço os transforma em envelopes (ADR-0038)."""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from campsverso_contracts import CONTRACT_TYPES
from campsverso_kernel.errors import WorldRuleError


@dataclass(frozen=True, slots=True)
class Fact:
    seq: int
    tick: int
    type: str
    data: Mapping[str, Any]
    caused_by: int | str | None = None  # seq de outro fato do kernel, ou id de um comando
    correlation: str | None = None  # correlationid herdado do comando
    opens_correlation: bool = False  # o serviço cria um correlationid novo (pedido de decisão)


class FactLog:
    """Numera os fatos em ordem (seq monotônica por source, contratos §5)."""

    def __init__(self, next_seq: int = 0) -> None:
        self.next_seq = next_seq
        self._pending: list[Fact] = []

    def emit(
        self,
        tick: int,
        event_type: str,
        data: Mapping[str, Any],
        *,
        caused_by: int | str | None = None,
        correlation: str | None = None,
        opens_correlation: bool = False,
    ) -> Fact:
        if event_type not in CONTRACT_TYPES or CONTRACT_TYPES[event_type].kind != "event":
            raise WorldRuleError(f"tipo de evento não declarado em contracts/: {event_type}")
        fact = Fact(
            self.next_seq, tick, event_type, data, caused_by, correlation, opens_correlation
        )
        self.next_seq += 1
        self._pending.append(fact)
        return fact

    def drain(self) -> list[Fact]:
        facts, self._pending = self._pending, []
        return facts
