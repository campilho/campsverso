"""Adaptadores da porta IdGenerator."""

import hashlib
import uuid


def derive_uuid7(source_id: str, salt: str) -> str:
    """Mantém os 48 bits de tempo do original e troca o resto por um hash de (id, sal)."""
    original = uuid.UUID(source_id).int
    digest = int.from_bytes(hashlib.sha256(f"{source_id}:{salt}".encode()).digest()[:10], "big")
    value = (original >> 80) << 80 | 0x7 << 76 | ((digest >> 62) & 0xFFF) << 64
    value |= 0x2 << 62 | (digest & ((1 << 62) - 1))
    return str(uuid.UUID(int=value))


class Uuid7Ids:
    def new_id(self) -> str:
        return str(uuid.uuid7())

    def derive(self, source_id: str, salt: str) -> str:
        return derive_uuid7(source_id, salt)


class SequentialUuid7Ids:
    """Ids UUIDv7 válidos e previsíveis, para testes: o contador ocupa o campo de tempo."""

    def __init__(self) -> None:
        self._counter = 0

    def new_id(self) -> str:
        self._counter += 1
        value = (self._counter << 80) | (0x7 << 76) | (0x2 << 62)
        return str(uuid.UUID(int=value))

    def derive(self, source_id: str, salt: str) -> str:
        return derive_uuid7(source_id, salt)
