"""Porta de objetos binários: snapshots no disco hoje, S3 na fase AWS (contratos §12)."""

from typing import Protocol


class BlobStore(Protocol):
    def put(self, key: str, data: bytes) -> None:
        """Grava por inteiro ou não grava: nunca deixa um objeto pela metade."""
        ...

    def get(self, key: str) -> bytes: ...

    def delete(self, key: str) -> None: ...
