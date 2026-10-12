"""Validação de um evento ou comando completo (envelope + payload), com códigos de erro estáveis.

Os mesmos códigos existem no validador TypeScript (tools/contracts-ts), para que os dois
validadores concordem sobre cada exemplo (contratos §10).
"""

from dataclasses import dataclass
from typing import Any

from jsonschema import Draft202012Validator, ValidationError
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

from campsverso_tools.contracts.catalog import Contracts, JsonObject


@dataclass(frozen=True, order=True)
class Problem:
    code: str
    message: str

    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"


def _errors(validator: Draft202012Validator, instance: Any) -> list[ValidationError]:
    # O stub do jsonschema declara um overload com tipo desconhecido; o uso aqui é o simples.
    return list(validator.iter_errors(instance))  # pyright: ignore[reportUnknownMemberType]


def _describe(error: ValidationError) -> str:
    location = "/".join(str(part) for part in error.absolute_path) or "(raiz)"
    return f"{location}: {error.message}"


def _registry(contracts: Contracts) -> Registry[Any]:
    resources: list[tuple[str, Resource[Any]]] = [
        (f.schema_id, DRAFT202012.create_resource(f.content)) for f in contracts.files
    ]
    return Registry[Any]().with_resources(resources)


class MessageValidator:
    """Mensagens do WebSocket entre gateway e UI (contracts/realtime, ADR-0050)."""

    def __init__(self, contracts: Contracts) -> None:
        registry = _registry(contracts)
        checker = Draft202012Validator.FORMAT_CHECKER
        self._messages = {
            name: Draft202012Validator(f.content, registry=registry, format_checker=checker)
            for name, f in contracts.by_message.items()
        }

    def validate(self, message: JsonObject) -> list[Problem]:
        name = str(message.get("type", ""))
        validator = self._messages.get(name)
        if validator is None:
            return [Problem("unknown_message", f"mensagem sem schema em contracts/: {name}")]
        return sorted(Problem("message_schema", _describe(e)) for e in _errors(validator, message))


class EventValidator:
    def __init__(self, contracts: Contracts) -> None:
        registry = _registry(contracts)
        checker = Draft202012Validator.FORMAT_CHECKER
        self._types = contracts.by_type
        self._envelope = Draft202012Validator(
            contracts.envelope.content, registry=registry, format_checker=checker
        )
        self._payloads = {
            name: Draft202012Validator(f.content, registry=registry, format_checker=checker)
            for name, f in self._types.items()
        }

    def validate(self, event: JsonObject) -> list[Problem]:
        problems = sorted(
            Problem("envelope_schema", _describe(e)) for e in _errors(self._envelope, event)
        )
        if problems:
            return problems
        event_type = str(event["type"])
        schema = self._types.get(event_type)
        if schema is None:
            return [Problem("unknown_type", f"tipo sem schema em contracts/: {event_type}")]
        if event["dataschema"] != schema.schema_id:
            problems.append(
                Problem(
                    "dataschema_mismatch",
                    f"dataschema {event['dataschema']!r}, esperado {schema.schema_id!r}",
                )
            )
        if event["visibility"] != schema.visibility:
            problems.append(
                Problem(
                    "visibility_mismatch",
                    f"{event_type} tem visibilidade {schema.visibility!r}, "
                    f"mas o envelope diz {event['visibility']!r}",
                )
            )
        problems.extend(
            sorted(
                Problem("payload_schema", _describe(e))
                for e in _errors(self._payloads[event_type], event["data"])
            )
        )
        return problems
