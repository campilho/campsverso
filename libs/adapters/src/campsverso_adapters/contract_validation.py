"""Validação de envelopes contra os contratos empacotados em campsverso_contracts (critério A2).

Os códigos de erro são os mesmos do validador de desenvolvimento (tools/contracts).
"""

import json
from dataclasses import dataclass
from importlib.resources import files
from importlib.resources.abc import Traversable
from typing import Any

from jsonschema import Draft202012Validator, ValidationError
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

from campsverso_contracts import CONTRACT_TYPES, subject
from campsverso_ports import Envelope


@dataclass(frozen=True, order=True)
class Problem:
    code: str
    message: str

    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"


def _schema_files(folder: Traversable) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    for entry in sorted(folder.iterdir(), key=lambda e: e.name):
        if entry.is_dir():
            found.extend(_schema_files(entry))
        elif entry.name.endswith(".schema.json"):
            found.append(json.loads(entry.read_text(encoding="utf-8")))
    return found


def _errors(validator: Draft202012Validator, instance: Any) -> list[ValidationError]:
    # O stub do jsonschema declara um overload com tipo desconhecido; o uso aqui é o simples.
    return list(validator.iter_errors(instance))  # pyright: ignore[reportUnknownMemberType]


def _describe(error: ValidationError) -> str:
    location = "/".join(str(part) for part in error.absolute_path) or "(raiz)"
    return f"{location}: {error.message}"


class ContractValidator:
    def __init__(self) -> None:
        schemas = _schema_files(files("campsverso_contracts").joinpath("schemas"))
        resources: list[tuple[str, Resource[Any]]] = [
            (str(s["$id"]), DRAFT202012.create_resource(s)) for s in schemas
        ]
        registry: Registry[Any] = Registry[Any]().with_resources(resources)
        by_id = {str(s["$id"]): s for s in schemas}
        checker = Draft202012Validator.FORMAT_CHECKER
        self._envelope = Draft202012Validator(
            by_id["contracts://envelope/envelope.v1"], registry=registry, format_checker=checker
        )
        self._payloads = {
            name: Draft202012Validator(
                by_id[info.dataschema], registry=registry, format_checker=checker
            )
            for name, info in CONTRACT_TYPES.items()
        }

    def validate(self, envelope: Envelope, published_subject: str | None = None) -> list[Problem]:
        problems = sorted(
            Problem("envelope_schema", _describe(e)) for e in _errors(self._envelope, envelope)
        )
        if problems:
            return problems
        event_type = str(envelope["type"])
        info = CONTRACT_TYPES.get(event_type)
        if info is None:
            return [Problem("unknown_type", f"tipo sem schema em contracts/: {event_type}")]
        if envelope["dataschema"] != info.dataschema:
            problems.append(Problem("dataschema_mismatch", f"esperado {info.dataschema}"))
        if envelope["visibility"] != info.visibility:
            problems.append(
                Problem("visibility_mismatch", f"{event_type} tem visibilidade {info.visibility}")
            )
        problems.extend(
            sorted(
                Problem("payload_schema", _describe(e))
                for e in _errors(self._payloads[event_type], envelope["data"])
            )
        )
        if published_subject is not None and not problems:
            avatar_id = envelope["data"].get("avatar_id")
            expected = subject(event_type, str(envelope["worldid"]), avatar_id)
            if published_subject != expected:
                problems.append(Problem("subject_mismatch", f"assunto esperado: {expected}"))
        return problems
