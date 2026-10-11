"""Porta de geração de ids de evento (UUIDv7, ADR-009 dos contratos)."""

from typing import Protocol


class IdGenerator(Protocol):
    def new_id(self) -> str: ...
