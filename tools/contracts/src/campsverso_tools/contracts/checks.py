"""Verificações dos contratos: meta-schema, convenções (catálogo §1) e exemplos (catálogo §5)."""

import json
import keyword
import re
from collections import Counter
from collections.abc import Iterator
from typing import Any

from jsonschema import Draft202012Validator, SchemaError

from campsverso_tools.contracts.catalog import VISIBILITIES, Contracts, JsonObject, SchemaFile
from campsverso_tools.contracts.validation import EventValidator, Problem

SNAKE_CASE = re.compile(r"^[a-z][a-z0-9]*(_[a-z0-9]+)*$")
PASCAL_CASE = re.compile(r"^[A-Z][A-Za-z0-9]*$")
TYPE_NAME = re.compile(r"^campsverso\.(cmd\.)?([a-z0-9_]+)\.[a-z0-9_]+(\.[a-z0-9_]+)*\.v[0-9]+$")
# Palavras reservadas do Python não viram nome de campo, nem o par `to` (ADR-0030):
# os modelos Pydantic gerados precisariam de apelidos.
RESERVED = frozenset(keyword.kwlist) | {"to"}
PRODUCERS = frozenset({"kernel", "perception", "controller", "operator"})


def _nodes(node: Any, path: str) -> Iterator[tuple[str, JsonObject]]:
    """Percorre os sub-schemas de um schema, com o caminho de cada um."""
    if not isinstance(node, dict):
        return
    schema: JsonObject = node  # pyright: ignore[reportUnknownVariableType]
    yield path, schema
    properties: JsonObject = schema.get("properties", {})
    for name, child in properties.items():
        yield from _nodes(child, f"{path}.{name}")
    defs: JsonObject = schema.get("$defs", {})
    for name, child in defs.items():
        yield from _nodes(child, f"{path}#{name}")
    for key in ("items", "additionalProperties"):
        yield from _nodes(schema.get(key), f"{path}[{key}]")
    for key in ("anyOf", "oneOf", "allOf"):
        for index, child in enumerate(schema.get(key, [])):
            yield from _nodes(child, f"{path}[{key}{index}]")


def _check_file(f: SchemaFile, contracts: Contracts) -> list[Problem]:
    where = f.path.as_posix()
    problems: list[Problem] = []
    if f.schema_id != f.expected_id:
        problems.append(
            Problem("schema_id", f"{where}: $id {f.schema_id!r}, esperado {f.expected_id!r}")
        )
    if not PASCAL_CASE.match(f.title):
        problems.append(Problem("title", f"{where}: title {f.title!r} precisa ser PascalCase"))

    if f.kind in ("event", "command"):
        problems.extend(_check_type(f, contracts))

    for node_path, node in _nodes(f.content, f.title):
        properties: JsonObject = node.get("properties", {})
        if properties and node.get("additionalProperties") is not False:
            problems.append(
                Problem(
                    "not_strict", f"{where}: {node_path} precisa de additionalProperties: false"
                )
            )
        if f.kind == "envelope":
            continue  # atributos do envelope seguem o CloudEvents (ADR-0030)
        for name in properties:
            if not SNAKE_CASE.match(name) or name in RESERVED:
                problems.append(
                    Problem(
                        "field_name",
                        f"{where}: campo {node_path}.{name} fora de snake_case ou reservado",
                    )
                )
    return problems


def _check_type(f: SchemaFile, contracts: Contracts) -> list[Problem]:
    where = f.path.as_posix()
    problems: list[Problem] = []
    if f.event_type != f.expected_type:
        problems.append(
            Problem("type_name", f"{where}: x-type {f.event_type!r}, esperado {f.expected_type!r}")
        )
    match = TYPE_NAME.match(f.event_type or "")
    if match is None:
        problems.append(
            Problem("type_name", f"{where}: x-type fora do padrão campsverso.<domínio>.<nome>.vN")
        )
    else:
        domain = match.group(2)
        if domain not in contracts.kernel_domains | contracts.cartridge_domains:
            problems.append(
                Problem("domain", f"{where}: domínio {domain!r} não está em contracts/domains.json")
            )
    if f.visibility not in VISIBILITIES:
        problems.append(Problem("visibility", f"{where}: x-visibility {f.visibility!r} inválida"))
    if f.kind == "command" and f.visibility != "observer":
        problems.append(
            Problem("visibility", f"{where}: comandos têm visibilidade observer (ADR-0013)")
        )
    if f.content.get("x-producer") not in PRODUCERS:
        problems.append(
            Problem("producer", f"{where}: x-producer precisa ser um de {sorted(PRODUCERS)}")
        )
    required: list[str] = f.content.get("required", [])
    if f.visibility == "agent" and "avatar_id" not in required:
        problems.append(
            Problem("agent_subject", f"{where}: eventos agent exigem avatar_id (catálogo §1.1)")
        )
    return problems


def check_conventions(contracts: Contracts) -> list[Problem]:
    problems: list[Problem] = []
    for f in contracts.files:
        try:
            Draft202012Validator.check_schema(f.content)
        except SchemaError as error:
            problems.append(Problem("meta_schema", f"{f.path.as_posix()}: {error.message}"))
            continue
        problems.extend(_check_file(f, contracts))

    titles = Counter(
        str(node["title"])
        for f in contracts.files
        for _, node in _nodes(f.content, f.title)
        if "title" in node
    )
    problems.extend(
        Problem("duplicate_title", f"title {title!r} aparece {count} vezes; precisa ser único")
        for title, count in sorted(titles.items())
        if count > 1
    )
    if sum(1 for f in contracts.files if f.kind == "envelope") != 1:
        problems.append(Problem("envelope", "precisa existir exatamente um schema de envelope"))
    return problems


def check_examples(contracts: Contracts) -> list[Problem]:
    """Válidos passam e cobrem todos os tipos; cada inválido falha com o código esperado."""
    validator = EventValidator(contracts)
    problems: list[Problem] = []
    covered: set[str] = set()

    for path in sorted((contracts.examples_dir / "valid").glob("*.json")):
        event: JsonObject = json.loads(path.read_text(encoding="utf-8"))
        event_type = str(event.get("type", ""))
        if not (path.stem == event_type or path.stem.startswith(f"{event_type}--")):
            problems.append(
                Problem(
                    "example_name",
                    f"valid/{path.name}: o nome precisa ser <tipo>.json ou <tipo>--<variação>.json",
                )
            )
        found = validator.validate(event)
        problems.extend(Problem("valid_example_fails", f"valid/{path.name}: {p}") for p in found)
        if not found:
            covered.add(event_type)

    problems.extend(
        Problem("missing_example", f"{name} não tem exemplo em examples/valid/")
        for name in sorted(contracts.by_type)
        if name not in covered
    )

    for path in sorted((contracts.examples_dir / "invalid").glob("*.json")):
        document: JsonObject = json.loads(path.read_text(encoding="utf-8"))
        expected = str(document["expect_error"])
        codes = {p.code for p in validator.validate(document["event"])}
        if not codes:
            problems.append(
                Problem(
                    "invalid_example_passes", f"invalid/{path.name}: deveria falhar ({expected})"
                )
            )
        elif expected not in codes:
            problems.append(
                Problem(
                    "invalid_example_wrong_error",
                    f"invalid/{path.name}: esperado {expected}, obtido {sorted(codes)}",
                )
            )
    return problems
