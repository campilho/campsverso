"""Compatibilidade dos schemas dentro da mesma versão maior (contratos §9; princípio 6).

A versão maior está no nome do arquivo (`.v1`), então o mesmo caminho significa a mesma versão
maior. Comparado com a versão em `base` (um commit do git), um schema só pode ganhar campos
opcionais. Remover ou renomear campo, mudar tipo, tornar obrigatório, mudar enum ou apertar
restrição exige um tipo novo (`.v2`).

Acrescentar valor a um enum também conta como incompatível: os modelos gerados usam Literal,
então um consumidor antigo recusaria o valor novo.
"""

import json
import subprocess
from pathlib import Path
from typing import Any

from campsverso_tools.contracts.catalog import SUFFIX, Contracts, JsonObject
from campsverso_tools.contracts.validation import Problem

_TIGHTER_IF_SMALLER = ("maxLength", "maximum", "exclusiveMaximum", "maxItems", "maxProperties")
_TIGHTER_IF_LARGER = ("minLength", "minimum", "exclusiveMinimum", "minItems", "minProperties")


def _as_dict(node: Any) -> JsonObject:
    return node if isinstance(node, dict) else {}  # pyright: ignore[reportUnknownVariableType]


def compare(old: JsonObject, new: JsonObject, where: str) -> list[Problem]:
    problems: list[Problem] = []
    for key in ("type", "$ref", "const", "pattern", "format"):
        if key in old and old.get(key) != new.get(key):
            problems.append(
                Problem(
                    "compat_changed", f"{where}: {key} mudou de {old[key]!r} para {new.get(key)!r}"
                )
            )
    if "enum" in old or "enum" in new:
        before, after = set(old.get("enum", [])), set(new.get("enum", []))
        if before != after:
            problems.append(
                Problem(
                    "compat_enum", f"{where}: enum mudou de {sorted(before)} para {sorted(after)}"
                )
            )
    for key in _TIGHTER_IF_SMALLER:
        if key in new and (key not in old or new[key] < old[key]):
            problems.append(Problem("compat_tightened", f"{where}: {key} ficou mais restrito"))
    for key in _TIGHTER_IF_LARGER:
        if key in new and (key not in old or new[key] > old[key]):
            problems.append(Problem("compat_tightened", f"{where}: {key} ficou mais restrito"))

    old_props, new_props = _as_dict(old.get("properties")), _as_dict(new.get("properties"))
    for name in sorted(old_props.keys() - new_props.keys()):
        problems.append(Problem("compat_removed_field", f"{where}.{name}: campo removido"))
    for name in sorted(set(new.get("required", [])) - set(old.get("required", []))):
        problems.append(
            Problem("compat_new_required", f"{where}.{name}: campo passou a ser obrigatório")
        )
    for name in sorted(old_props.keys() & new_props.keys()):
        problems.extend(
            compare(_as_dict(old_props[name]), _as_dict(new_props[name]), f"{where}.{name}")
        )

    for key in ("items", "additionalProperties"):
        if isinstance(old.get(key), dict) and isinstance(new.get(key), dict):
            problems.extend(compare(_as_dict(old[key]), _as_dict(new[key]), f"{where}[{key}]"))
    old_defs, new_defs = _as_dict(old.get("$defs")), _as_dict(new.get("$defs"))
    for name in sorted(old_defs.keys() - new_defs.keys()):
        problems.append(Problem("compat_removed_field", f"{where}#{name}: definição removida"))
    for name in sorted(old_defs.keys() & new_defs.keys()):
        problems.extend(
            compare(_as_dict(old_defs[name]), _as_dict(new_defs[name]), f"{where}#{name}")
        )
    return problems


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=False)


def check_compat(contracts: Contracts, repo: Path, base: str) -> list[Problem]:
    if _git(repo, "rev-parse", "--verify", "--quiet", f"{base}^{{commit}}").returncode != 0:
        print(f"compatibilidade: base {base!r} não existe; nada a comparar")
        return []
    listed = _git(repo, "ls-tree", "-r", "--name-only", base, "contracts/").stdout.splitlines()
    before = {Path(p).relative_to("contracts") for p in listed if p.endswith(SUFFIX)}
    now = {f.path: f for f in contracts.files}

    problems = [
        Problem(
            "compat_removed_schema", f"{p}: schema removido; publique um tipo novo em vez disso"
        )
        for p in sorted(before - now.keys())
    ]
    for path in sorted(before & now.keys()):
        old: JsonObject = json.loads(
            _git(repo, "show", f"{base}:contracts/{path.as_posix()}").stdout
        )
        problems.extend(compare(old, now[path].content, path.as_posix()))
    print(
        f"compatibilidade com {base}: {len(before & now.keys())} schema(s) comparado(s), "
        f"{len(now.keys() - before)} novo(s)"
    )
    return problems
