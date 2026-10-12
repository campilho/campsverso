"""Motor de regras: instâncias vindas das flags, implementações vindas dos cartuchos (ADR-0015)."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from campsverso_cartridge_api import EntityView, RuleImpl, Scalar, WorldView
from campsverso_kernel.errors import DefinitionError
from campsverso_ports import RuleConfig


@dataclass(frozen=True, slots=True)
class Contribution:
    rule: str
    version: str
    hidden: bool
    base: float
    applied: float


@dataclass
class _Instance:
    config: RuleConfig
    impl: RuleImpl
    enabled: bool
    params: dict[str, Scalar]


class RulesEngine:
    def __init__(self, impls: Mapping[str, RuleImpl], configs: Sequence[RuleConfig]) -> None:
        self._rules: dict[str, _Instance] = {}
        for config in sorted(configs, key=lambda c: c.rule):
            impl = impls.get(config.impl)
            if impl is None:
                raise DefinitionError(
                    f"regra {config.rule}: implementação {config.impl!r} inexistente"
                )
            self._rules[config.rule] = _Instance(config, impl, config.enabled, dict(config.params))

    def loaded(self) -> list[dict[str, Any]]:
        return [
            {
                "rule": name,
                "version": r.config.version,
                "hidden": r.config.hidden,
                "enabled": r.enabled,
                "params": dict(r.params),
            }
            for name, r in self._rules.items()
        ]

    def apply(
        self, view: WorldView, target: str, entity: EntityView, base: float
    ) -> tuple[float, list[Contribution]]:
        """Encadeia as regras ligadas que modificam `target`, em ordem de nome."""
        value = base
        contributions: list[Contribution] = []
        for name, rule in self._rules.items():
            if not rule.enabled or rule.impl.target != target:
                continue
            new_value = rule.impl.apply(view, entity, value, rule.params)
            if new_value != value:
                contributions.append(
                    Contribution(name, rule.config.version, rule.config.hidden, value, new_value)
                )
                value = new_value
        return value, contributions

    def knows(self, rule: str) -> bool:
        return rule in self._rules

    def toggle(self, rule: str, enabled: bool, params: Mapping[str, Scalar] | None) -> str:
        """Liga, desliga ou reparametriza; devolve a versão da regra."""
        instance = self._rules[rule]
        instance.enabled = enabled
        if params is not None:
            instance.params = {**instance.params, **params}
        return instance.config.version
