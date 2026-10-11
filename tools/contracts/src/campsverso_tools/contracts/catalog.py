"""Leitura dos schemas em contracts/ e a correspondência tipo, arquivo e $id (catálogo §1.1)."""

import json
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Any, Literal

type JsonObject = dict[str, Any]
type Kind = Literal["common", "envelope", "event", "command"]

VISIBILITIES = ("world", "agent", "observer", "internal")
ID_PREFIX = "contracts://"
SUFFIX = ".schema.json"
_KIND_BY_DIR: dict[str, Kind] = {
    "common": "common",
    "envelope": "envelope",
    "events": "event",
    "commands": "command",
}


@dataclass(frozen=True)
class SchemaFile:
    path: Path  # relativo à pasta contracts/
    kind: Kind
    content: JsonObject

    @property
    def schema_id(self) -> str:
        return str(self.content.get("$id", ""))

    @property
    def expected_id(self) -> str:
        return ID_PREFIX + self.path.as_posix().removesuffix(SUFFIX)

    @property
    def title(self) -> str:
        return str(self.content.get("title", ""))

    @property
    def event_type(self) -> str | None:
        value = self.content.get("x-type")
        return str(value) if value is not None else None

    @property
    def expected_type(self) -> str | None:
        """events/<domínio>/<nome>.vN vira campsverso.<domínio>.<nome>.vN.

        commands/<domínio>/<verbo>.vN vira campsverso.cmd.<domínio>.<verbo>.vN.
        """
        if self.kind not in ("event", "command"):
            return None
        parts = self.path.as_posix().removesuffix(SUFFIX).split("/")
        if len(parts) != 3:
            return None
        _, domain, name = parts
        prefix = "campsverso.cmd." if self.kind == "command" else "campsverso."
        return f"{prefix}{domain}.{name}"

    @property
    def visibility(self) -> str | None:
        value = self.content.get("x-visibility")
        return str(value) if value is not None else None


@dataclass(frozen=True)
class Contracts:
    root: Path  # a pasta contracts/
    files: tuple[SchemaFile, ...]
    kernel_domains: frozenset[str]
    cartridge_domains: frozenset[str]

    @cached_property
    def by_type(self) -> dict[str, SchemaFile]:
        return {f.event_type: f for f in self.files if f.event_type is not None}

    @cached_property
    def envelope(self) -> SchemaFile:
        return next(f for f in self.files if f.kind == "envelope")

    @property
    def examples_dir(self) -> Path:
        return self.root / "examples"


def find_contracts_dir(start: Path) -> Path:
    """Sobe a partir de `start` até achar a raiz do repositório (contracts/ e pyproject.toml)."""
    for candidate in (start, *start.parents):
        if (candidate / "contracts").is_dir() and (candidate / "pyproject.toml").is_file():
            return candidate / "contracts"
    raise FileNotFoundError(f"pasta contracts/ não encontrada a partir de {start}")


def load(contracts_dir: Path) -> Contracts:
    files: list[SchemaFile] = []
    for path in sorted(contracts_dir.rglob(f"*{SUFFIX}")):
        relative = path.relative_to(contracts_dir)
        kind = _KIND_BY_DIR.get(relative.parts[0])
        if kind is None:
            continue
        content: JsonObject = json.loads(path.read_text(encoding="utf-8"))
        files.append(SchemaFile(path=relative, kind=kind, content=content))
    domains: JsonObject = json.loads((contracts_dir / "domains.json").read_text(encoding="utf-8"))
    return Contracts(
        root=contracts_dir,
        files=tuple(files),
        kernel_domains=frozenset(domains["kernel"]),
        cartridge_domains=frozenset(domains["cartridges"]),
    )
