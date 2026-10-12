"""Erros do kernel."""


class DefinitionError(Exception):
    """Cadeia de cartuchos inválida: falha na carga, antes de o mundo começar (ADR-0036)."""


class WorldRuleError(Exception):
    """Um cartucho pediu algo impossível ao mundo (ex.: consumir item que não existe)."""
