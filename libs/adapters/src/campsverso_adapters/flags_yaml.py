"""Adaptador da porta FlagPort: regras em YAML versionado (ADR-0015)."""

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, cast

import yaml

from campsverso_ports import RuleConfig


class YamlFlags:
    """Lê um arquivo no formato `rules: {<regra>: {impl, version, hidden, enabled, params}}`."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def rules(self) -> Sequence[RuleConfig]:
        document = cast(Mapping[str, Any], yaml.safe_load(self._path.read_text(encoding="utf-8")))
        rules = cast(Mapping[str, Mapping[str, Any]], document.get("rules") or {})
        return tuple(
            RuleConfig(
                rule=name,
                impl=str(spec["impl"]),
                version=str(spec["version"]),
                hidden=bool(spec["hidden"]),
                enabled=bool(spec["enabled"]),
                params=dict(spec.get("params") or {}),
            )
            for name, spec in sorted(rules.items())
        )
