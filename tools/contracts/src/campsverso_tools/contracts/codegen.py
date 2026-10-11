"""Codegen dos contratos (lado Python).

Gera, a partir de contracts/:
- packages/contracts-py: modelos Pydantic, registro de tipos e cópia dos schemas;
- packages/contracts-ts/schemas: cópia dos schemas e o pacote único (bundle.json) usado pelo
  codegen TypeScript (tools/contracts-ts);
- contracts/asyncapi.yaml: canais NATS e mensagens (contratos §6, §10).

Com `check=True`, nada é escrito: a saída é comparada com o que está no repositório.
"""

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml

from campsverso_tools.contracts.catalog import Contracts, JsonObject, SchemaFile
from campsverso_tools.contracts.validation import Problem

HEADER = "GERADO por tools/contracts a partir de contracts/: não editar à mão."
PY_PACKAGE = Path("packages/contracts-py/src/campsverso_contracts")
TS_SCHEMAS = Path("packages/contracts-ts/schemas")
ASYNCAPI = Path("contracts/asyncapi.yaml")
# O datamodel-code-generator 0.83 ainda não roda sob o Python 3.15 (ADR-0023): roda isolado no
# 3.14, com versão fixa, e gera código compatível com o 3.15.
GENERATOR = (
    "uvx", "--quiet", "--python", "3.14", "--from", "datamodel-code-generator==0.83.0",
    "--with", "ruff==0.17.0", "datamodel-codegen",
)  # fmt: skip
GENERATOR_OPTIONS = (
    "--input-file-type", "jsonschema",
    "--output-model-type", "pydantic_v2.BaseModel",
    "--target-python-version", "3.14",
    "--use-title-as-name",
    "--use-annotated",
    "--collapse-root-models",
    "--use-standard-collections",
    "--use-union-operator",
    "--enum-field-as-literal", "all",
    "--extra-fields", "ignore",  # leitor tolerante (ADR-0016)
    "--field-constraints",
    "--use-schema-description",
    "--use-field-description",
    "--disable-timestamp",
    "--use-double-quotes",
    "--formatters", "ruff-format",
    "--custom-file-header", f"# {HEADER}",
)  # fmt: skip
# Palavras que só servem à validação e atrapalham a geração de tipos. A validação de verdade
# usa os schemas completos (jsonschema e ajv); os modelos gerados são leitores tolerantes.
VALIDATION_ONLY = frozenset({"propertyNames"})


# ---------------------------------------------------------------- pacote único (bundle)


def _defs_titles(contracts: Contracts) -> dict[str, str]:
    common = next(f for f in contracts.files if f.kind == "common")
    defs: JsonObject = common.content["$defs"]
    return {key: str(value["title"]) for key, value in defs.items()}


def _rewrite(node: Any, titles: dict[str, str], prefix: str) -> Any:
    """Troca refs para `<prefix><Title>` e remove metadados que os geradores não entendem."""
    if isinstance(node, list):
        return [_rewrite(item, titles, prefix) for item in node]  # pyright: ignore[reportUnknownVariableType]
    if not isinstance(node, dict):
        return node
    schema: JsonObject = node  # pyright: ignore[reportUnknownVariableType]
    if "$ref" in schema:
        target = titles[str(schema["$ref"]).rsplit("/", 1)[1]]
        rewritten: JsonObject = {"$ref": f"{prefix}{target}"}
        if "description" in schema:
            rewritten["description"] = schema["description"]
        return rewritten
    return {
        key: _rewrite(value, titles, prefix)
        for key, value in schema.items()
        if not key.startswith("x-")
        and key not in ("$schema", "$id", "$comment")
        and key not in VALIDATION_ONLY
    }


def _bundle_defs(contracts: Contracts, prefix: str) -> JsonObject:
    titles = _defs_titles(contracts)
    common = next(f for f in contracts.files if f.kind == "common")
    defs: JsonObject = {}
    for value in common.content["$defs"].values():
        defs[str(value["title"])] = _rewrite(value, titles, prefix)
    for f in contracts.files:
        if f.kind in ("envelope", "event", "command"):
            defs[f.title] = _rewrite(f.content, titles, prefix)
    return defs


def build_bundle(contracts: Contracts) -> JsonObject:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$comment": HEADER,
        "title": "ContractsBundle",
        "type": "object",
        "$defs": _bundle_defs(contracts, "#/$defs/"),
    }


# ---------------------------------------------------------------- Python


def _models(bundle: JsonObject, repo: Path) -> str:
    with tempfile.TemporaryDirectory() as tmp:
        source = Path(tmp) / "bundle.json"
        target = Path(tmp) / "models.py"
        source.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
        subprocess.run(
            [*GENERATOR, "--input", str(source), "--output", str(target), *GENERATOR_OPTIONS],
            check=True,
            capture_output=True,
            text=True,
        )
        # A formatação final segue a configuração do repositório (line-length etc.).
        subprocess.run(
            [sys.executable, "-m", "ruff", "format", "--quiet", str(target)],
            check=True,
            cwd=repo,
        )
        return target.read_text(encoding="utf-8")


def _type_files(contracts: Contracts) -> list[SchemaFile]:
    return sorted(contracts.by_type.values(), key=lambda f: str(f.event_type))


def _registry(contracts: Contracts) -> str:
    entries = "\n".join(
        f"        ContractType({f.event_type!r}, {f.kind!r}, {f.visibility!r}, "
        f"{f.content['x-producer']!r}, {f.schema_id!r}, models.{f.title}),"
        for f in _type_files(contracts)
    )
    return f'''"""{HEADER}

Registro dos tipos de evento e comando: visibilidade, produtor, schema e modelo do payload.
"""

from dataclasses import dataclass
from typing import Final, Literal

from pydantic import BaseModel

from campsverso_contracts import models

type Visibility = Literal["world", "agent", "observer", "internal"]
type Kind = Literal["event", "command"]


@dataclass(frozen=True, slots=True)
class ContractType:
    name: str
    kind: Kind
    visibility: Visibility
    producer: str
    dataschema: str
    payload: type[BaseModel]


CONTRACT_TYPES: Final[dict[str, ContractType]] = {{
    item.name: item
    for item in (
{entries}
    )
}}
'''


INIT = f'''"""Contratos do Campsverso. {HEADER}"""

from campsverso_contracts.models import EnvelopeV1
from campsverso_contracts.registry import CONTRACT_TYPES, ContractType, Kind, Visibility

__all__ = ["CONTRACT_TYPES", "ContractType", "EnvelopeV1", "Kind", "Visibility"]
'''


def _format_python(source: str, repo: Path) -> str:
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "format", "--quiet", "--stdin-filename", "gerado.py", "-"],
        input=source,
        check=True,
        capture_output=True,
        text=True,
        cwd=repo,
    )
    return result.stdout


# ---------------------------------------------------------------- AsyncAPI


def subject_of(f: SchemaFile) -> str:
    """Assunto NATS de um tipo (catálogo §1.1)."""
    name = str(f.event_type).removeprefix("campsverso.")
    if f.kind == "command":
        return f"campsverso.{{worldid}}.{name}"
    if f.visibility == "agent":
        return f"campsverso.{{worldid}}.agent.{{avatar_id}}.{name}"
    return f"campsverso.{{worldid}}.{f.visibility}.{name}"


def _asyncapi(contracts: Contracts) -> str:
    channels: JsonObject = {}
    operations: JsonObject = {}
    messages: JsonObject = {}
    for f in _type_files(contracts):
        title = f.title
        address = subject_of(f)
        parameters: JsonObject = {"worldid": {"$ref": "#/components/parameters/worldid"}}
        if "{avatar_id}" in address:
            parameters["avatar_id"] = {"$ref": "#/components/parameters/avatar_id"}
        channels[title] = {
            "address": address,
            "title": f.event_type,
            "parameters": parameters,
            "messages": {title: {"$ref": f"#/components/messages/{title}"}},
        }
        messages[title] = {
            "name": f.event_type,
            "title": title,
            "summary": f.content.get("description", ""),
            "contentType": "application/json",
            "payload": {"$ref": f"#/components/schemas/{title}"},
            "x-visibility": f.visibility,
            "x-producer": f.content["x-producer"],
        }
        operations[f"send{title}"] = {
            "action": "send",
            "channel": {"$ref": f"#/channels/{title}"},
            "messages": [{"$ref": f"#/channels/{title}/messages/{title}"}],
            "x-producer": f.content["x-producer"],
        }
    document: JsonObject = {
        "asyncapi": "3.1.0",
        "info": {
            "title": "Campsverso",
            "version": "0.1.0",
            "description": (
                f"{HEADER}\n\nCada mensagem viaja dentro do envelope CloudEvents 1.0 "
                "(EnvelopeV1, modo estruturado); o payload descrito aqui é o campo `data`."
            ),
            "license": {"name": "MIT"},
        },
        "defaultContentType": "application/json",
        "servers": {
            "local": {
                "host": "localhost:4222",
                "protocol": "nats",
                "description": "NATS JetStream local (ADR-0024).",
            }
        },
        "channels": channels,
        "operations": operations,
        "components": {
            "schemas": _bundle_defs(contracts, "#/components/schemas/"),
            "messages": messages,
            "parameters": {
                "worldid": {"description": "Instância do mundo, ex.: farm-camps-01."},
                "avatar_id": {"description": "Avatar destinatário (visibilidade agent)."},
            },
        },
    }
    body = yaml.safe_dump(document, allow_unicode=True, sort_keys=False, width=100)
    return f"# {HEADER}\n{body}"


# ---------------------------------------------------------------- saída


def _schema_copies(contracts: Contracts, target: Path) -> dict[Path, str]:
    return {
        target / f.path: (contracts.root / f.path).read_text(encoding="utf-8")
        for f in contracts.files
    }


def render(contracts: Contracts, repo: Path) -> dict[Path, str]:
    """Todos os arquivos gerados pelo lado Python, com caminho relativo à raiz do repositório."""
    bundle = build_bundle(contracts)
    outputs: dict[Path, str] = {
        PY_PACKAGE / "models.py": _models(bundle, repo),
        PY_PACKAGE / "registry.py": _format_python(_registry(contracts), repo),
        PY_PACKAGE / "__init__.py": _format_python(INIT, repo),
        TS_SCHEMAS / "bundle.json": json.dumps(bundle, ensure_ascii=False, indent=2) + "\n",
        ASYNCAPI: _asyncapi(contracts),
    }
    outputs.update(_schema_copies(contracts, PY_PACKAGE / "schemas"))
    outputs.update(_schema_copies(contracts, TS_SCHEMAS))
    return outputs


OWNED_DIRS = (PY_PACKAGE / "schemas", TS_SCHEMAS)


def _existing(repo: Path, outputs: dict[Path, str]) -> set[Path]:
    found = {path for path in outputs if (repo / path).exists()}
    for directory in OWNED_DIRS:
        if (repo / directory).is_dir():
            found |= {p.relative_to(repo) for p in (repo / directory).rglob("*") if p.is_file()}
    return found


def run(contracts: Contracts, repo: Path, *, check: bool) -> list[Problem]:
    outputs = render(contracts, repo)
    existing = _existing(repo, outputs)
    stale = sorted(existing - set(outputs))
    changed = sorted(
        path
        for path, content in outputs.items()
        if not (repo / path).exists() or (repo / path).read_text(encoding="utf-8") != content
    )
    if check:
        return [
            *(Problem("codegen_stale", f"{p}: arquivo gerado sobrando") for p in stale),
            *(
                Problem("codegen_drift", f"{p}: difere do codegen; rode make contracts")
                for p in changed
            ),
        ]
    for path in stale:
        (repo / path).unlink()
    for path in changed:
        (repo / path).parent.mkdir(parents=True, exist_ok=True)
        (repo / path).write_text(outputs[path], encoding="utf-8")
    for directory in OWNED_DIRS:  # remove pastas que ficaram vazias
        for folder in sorted((repo / directory).rglob("*"), reverse=True):
            if folder.is_dir() and not any(folder.iterdir()):
                shutil.rmtree(folder)
    print(f"codegen: {len(changed)} arquivo(s) atualizado(s), {len(stale)} removido(s)")
    return []
