"""A mente genérica do controlador LLM (ADR-0059).

Recebe as entregas da percepção, conversa com o modelo pela `ModelPort` e devolve propostas de
ação. O que a mente sabe do mundo (o cartão de identidade, as notas e o catálogo de ferramentas)
é dado do cartucho; aqui fica só o mecanismo.
"""

from campsverso_mind.controller import LlmController
from campsverso_mind.exam import Exam, Grade, Question, exam_request, grade, load_exam, read_answers
from campsverso_mind.memory import REFLECT_TOOL, Clock, Memory, MemorySettings, clock_of
from campsverso_mind.mind import Mind, ParamDef, ToolDef, load_tools
from campsverso_mind.tools import INTENT, NOTE, proposal_from, tool_specs
from campsverso_mind.window import Window, reason_text

__all__ = [
    "INTENT",
    "NOTE",
    "REFLECT_TOOL",
    "Clock",
    "Exam",
    "Grade",
    "LlmController",
    "Memory",
    "MemorySettings",
    "Mind",
    "ParamDef",
    "Question",
    "ToolDef",
    "Window",
    "clock_of",
    "exam_request",
    "grade",
    "load_exam",
    "load_tools",
    "proposal_from",
    "read_answers",
    "reason_text",
    "tool_specs",
]
