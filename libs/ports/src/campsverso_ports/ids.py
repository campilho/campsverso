"""Porta de geração de ids de evento (UUIDv7, ADR-009 dos contratos)."""

from typing import Protocol


class IdGenerator(Protocol):
    def new_id(self) -> str: ...

    def derive(self, source_id: str, salt: str) -> str:
        """UUIDv7 determinístico a partir de outro id: o mesmo par dá sempre o mesmo resultado.

        Quem reage a um evento e pode reenviar a reação depois de uma queda (percepção,
        controladores) usa o id derivado; a reação repetida é deduplicada pelo id.
        """
        ...
