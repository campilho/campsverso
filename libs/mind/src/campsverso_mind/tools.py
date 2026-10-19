"""As ferramentas no formato da Messages API, uma por ação do catálogo, estritas e com a intenção
obrigatória; e o caminho de volta, da ferramenta escolhida à proposta de ação (ADR-0059)."""

from collections.abc import Mapping, Sequence
from typing import Any, cast

from campsverso_mind.mind import ParamDef, ToolDef

INTENT = "intent"
INTENT_MAX = 500  # o contrato de cmd.action.propose limita o intent a 500 caracteres
INTENT_DESCRIPTION = "O que você pretende com esta ação, em uma frase, em português."
NOTE = "note"  # o caderno (ADR-0060): entra em toda ferramenta quando há memória
NOTE_DESCRIPTION = (
    "Para o caderno: só o que a próxima foto não vai mostrar (uma conclusão, uma dúvida, um "
    "plano, um número que você quer comparar depois). Fome, energia, moedas, cargas e o que "
    'está em cada canteiro já estão na foto: não anote. Na maioria das decisões, "".'
)


def describe(tool: ToolDef) -> str:
    """A descrição com a duração e a energia, quando o cartucho as declara."""
    extra: list[str] = []
    if tool.duration_ticks is not None:
        minutes = "minuto" if tool.duration_ticks == 1 else "minutos"
        extra.append(f"Dura {tool.duration_ticks} {minutes}.")
    if tool.energy:
        extra.append(f"Gasta {tool.energy} de energia.")
    return " ".join([tool.description, *extra])


def _schema(param: ParamDef) -> dict[str, Any]:
    schema: dict[str, Any] = {"type": param.type, "description": param.description}
    if param.enum:
        schema["enum"] = list(param.enum)
    return schema


def tool_spec(tool: ToolDef, *, with_note: bool = False) -> dict[str, Any]:
    properties = {p.name: _schema(p) for p in tool.params}
    properties[INTENT] = {"type": "string", "description": INTENT_DESCRIPTION}
    required = [*(p.name for p in tool.params), INTENT]
    if with_note:
        properties[NOTE] = {"type": "string", "description": NOTE_DESCRIPTION}
        required.append(NOTE)
    return {
        "name": tool.name,
        "description": describe(tool),
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": properties,
            "required": required,
            "additionalProperties": False,
        },
    }


def tool_specs(tools: Sequence[ToolDef], *, with_note: bool = False) -> list[dict[str, Any]]:
    return [tool_spec(t, with_note=with_note) for t in tools]


def _fill(shape: Any, values: Mapping[str, Any]) -> Any:
    if isinstance(shape, str) and shape.startswith("$"):
        return values[shape[1:]]
    if isinstance(shape, Mapping):
        return {str(k): _fill(v, values) for k, v in cast(Mapping[str, Any], shape).items()}
    if isinstance(shape, list):
        return [_fill(v, values) for v in cast(Sequence[Any], shape)]
    return shape


def intent_text(raw: Any, fallback: str) -> str:
    text = " ".join(str(raw).split()) if raw is not None else ""
    return (text or fallback)[:INTENT_MAX]


def proposal_from(tool: ToolDef, given: Mapping[str, Any]) -> dict[str, Any]:
    """A proposta de `cmd.action.propose` a partir do que o modelo pôs na ferramenta."""
    values = {p.name: given.get(p.name) for p in tool.params}
    params = _fill(tool.shape, values) if tool.shape is not None else dict(values)
    return {
        "action": tool.action,
        "params": cast(dict[str, Any], params),
        INTENT: intent_text(given.get(INTENT), tool.name),
    }
