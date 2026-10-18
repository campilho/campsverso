"""A mente genérica do controlador LLM (ADR-0059).

Recebe as entregas da percepção, conversa com o modelo pela `ModelPort` e devolve propostas de
ação. O que a mente sabe do mundo (o cartão de identidade, as notas e o catálogo de ferramentas)
é dado do cartucho; aqui fica só o mecanismo.
"""

from campsverso_mind.controller import LlmController
from campsverso_mind.mind import Mind, ParamDef, ToolDef, load_tools
from campsverso_mind.tools import INTENT, proposal_from, tool_specs
from campsverso_mind.window import Window, reason_text

__all__ = [
    "INTENT",
    "LlmController",
    "Mind",
    "ParamDef",
    "ToolDef",
    "Window",
    "load_tools",
    "proposal_from",
    "reason_text",
    "tool_specs",
]
