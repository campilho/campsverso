"""O que uma mente sabe, como dado: o cartão de identidade (o cenário), as notas do mundo (o
gênero) e o catálogo de ferramentas, uma por ação do cartucho (ADR-0059)."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Literal, cast

import yaml

from campsverso_mind.compare import Columns

type ParamType = Literal["string", "integer"]


@dataclass(frozen=True, slots=True)
class ParamDef:
    name: str
    type: ParamType
    description: str
    enum: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ToolDef:
    """Uma ferramenta oferecida ao modelo. `action` é a ação do kernel que ela propõe; `shape`,
    quando existe, é o molde dos parâmetros da ação, com `$nome` no lugar de cada parâmetro da
    ferramenta (ex.: `{target: {x: $x, y: $y}}`); sem molde, os parâmetros vão como vieram."""

    name: str
    action: str
    description: str
    params: tuple[ParamDef, ...] = ()
    shape: Mapping[str, Any] | None = None
    duration_ticks: int | None = None
    energy: float | None = None
    # Estrita: a API garante o schema por gramática. A gramática de todas as ferramentas estritas
    # juntas tem um teto; um catálogo grande marca as simples como `strict: false` (ADR-0062).
    strict: bool = True


@dataclass(frozen=True, slots=True)
class Mind:
    name: str
    card: str  # o cartão de identidade: quem é o avatar e o que quer
    notes: str  # as notas do mundo: o que um recém-chegado saberia
    tools: tuple[ToolDef, ...]
    # O caderno de campo e o experimento da noite (ADR-0070): a mente de cada cenário diz se os usa.
    field_notebook: bool = False
    experiments: bool = False
    craft: str = ""  # o ofício do gênero, a segunda camada do playbook (ADR-0071)
    columns: Columns | None = None  # o que a ferramenta de comparação mede (ADR-0074)

    def extend(self, *, card: str | None = None, notes: str | None = None) -> Mind:
        """Uma camada por cima (ADR-0031): o cenário troca o cartão, ou as notas, do gênero."""
        return replace(
            self, card=card if card is not None else self.card, notes=notes or self.notes
        )

    def tool(self, name: str) -> ToolDef | None:
        return next((t for t in self.tools if t.name == name), None)


def _param(raw: Mapping[str, Any]) -> ParamDef:
    kind = str(raw.get("type", "string"))
    if kind not in ("string", "integer"):
        raise ValueError(f"parâmetro {raw.get('name')!r}: tipo {kind!r} não suportado")
    return ParamDef(
        name=str(raw["name"]),
        type=kind,
        description=str(raw.get("description", "")),
        enum=tuple(str(v) for v in cast(Sequence[Any], raw.get("enum") or ())),
    )


def tools_from(raw: Sequence[Mapping[str, Any]]) -> tuple[ToolDef, ...]:
    tools: list[ToolDef] = []
    for item in raw:
        tools.append(
            ToolDef(
                name=str(item["name"]),
                action=str(item.get("action", item["name"])),
                description=str(item["description"]).strip(),
                params=tuple(
                    _param(p) for p in cast(Sequence[Mapping[str, Any]], item.get("params") or ())
                ),
                shape=cast(Mapping[str, Any] | None, item.get("shape")),
                duration_ticks=(None if item.get("duration") is None else int(item["duration"])),
                energy=None if item.get("energy") is None else float(item["energy"]),
                strict=bool(item.get("strict", True)),
            )
        )
    names = [t.name for t in tools]
    if len(set(names)) != len(names):
        raise ValueError(f"ferramentas repetidas: {sorted(n for n in names if names.count(n) > 1)}")
    return tuple(tools)


def load_tools(path: Path) -> tuple[ToolDef, ...]:
    """O catálogo de ferramentas de um `tools.yaml` (`tools: [{name, action?, description,
    params?, shape?, duration?, energy?, strict?}]`)."""
    doc = cast(Mapping[str, Any], yaml.safe_load(path.read_text(encoding="utf-8")))
    return tools_from(cast(Sequence[Mapping[str, Any]], doc["tools"]))


def load_columns(path: Path) -> Columns:
    """As colunas da ferramenta de comparação de um `comparar.yaml` (ADR-0074)."""
    return Columns.of(cast(Mapping[str, Any], yaml.safe_load(path.read_text(encoding="utf-8"))))
