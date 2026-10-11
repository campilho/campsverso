"""Adaptadores da porta IdGenerator."""

import uuid


class Uuid7Ids:
    def new_id(self) -> str:
        return str(uuid.uuid7())


class SequentialUuid7Ids:
    """Ids UUIDv7 válidos e previsíveis, para testes: o contador ocupa o campo de tempo."""

    def __init__(self) -> None:
        self._counter = 0

    def new_id(self) -> str:
        self._counter += 1
        value = (self._counter << 80) | (0x7 << 76) | (0x2 << 62)
        return str(uuid.UUID(int=value))
