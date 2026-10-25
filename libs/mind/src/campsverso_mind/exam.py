"""A prova do mundo (ADR-0070, decisão 12): perguntas fechadas sobre como o mundo funciona,
respondidas pela mente com uma ferramenta estrita, uma opção por pergunta, e corrigidas pelo
gabarito. A prova é aplicada fora da corrida: antes (a mente com a memória vazia, o que o modelo
supõe) e depois (com o bloco de abertura e o caderno). As perguntas vêm de um arquivo do
cartucho, fora do pacote da mente: a mente nunca as vê enquanto joga.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

import yaml

from campsverso_ports import Effort, ModelRequest, ModelResponse

ANSWER = "answer"
INSTRUCTIONS = """\
## A prova

Esta não é uma jogada: é uma prova sobre como esta fazenda funciona. Responda cada pergunta com \
o que você sabe pelo que viveu e anotou; quando não souber, escolha "não sei", que não conta \
contra você. Responda com a ferramenta `answer`, e só com ela."""


@dataclass(frozen=True, slots=True)
class Question:
    id: str
    text: str
    options: Mapping[str, str]  # a chave de cada opção e o texto dela
    answer: str  # o gabarito
    script: Mapping[str, Any] = field(default_factory=dict[str, Any])  # como ler um script


@dataclass(frozen=True, slots=True)
class Exam:
    questions: tuple[Question, ...]
    unknown: str  # a opção "não sei"


@dataclass(frozen=True, slots=True)
class Grade:
    """A nota: os acertos, os erros e os "não sei", e a resposta de cada pergunta."""

    right: int
    wrong: int
    unknown: int
    answers: Mapping[str, str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "right": self.right,
            "wrong": self.wrong,
            "unknown": self.unknown,
            "answers": dict(self.answers),
        }


def load_exam(path: Path) -> Exam:
    doc = cast(Mapping[str, Any], yaml.safe_load(path.read_text(encoding="utf-8")))
    questions = tuple(
        Question(
            str(q["id"]),
            " ".join(str(q["text"]).split()),
            {str(k): str(v) for k, v in cast(Mapping[str, Any], q["options"]).items()},
            str(q["answer"]),
            cast(Mapping[str, Any], q.get("script") or {}),
        )
        for q in cast(Sequence[Mapping[str, Any]], doc["questions"])
    )
    unknown = str(doc["unknown"])
    for q in questions:
        if q.answer not in q.options or unknown not in q.options:
            raise ValueError(f"pergunta {q.id}: gabarito ou 'não sei' fora das opções")
    return Exam(questions, unknown)


def exam_tool(exam: Exam) -> dict[str, Any]:
    """A ferramenta `answer`: uma propriedade por pergunta, com as chaves das opções."""
    return {
        "name": ANSWER,
        "description": "Entregue a prova: a opção escolhida em cada pergunta.",
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {
                q.id: {"type": "string", "enum": list(q.options), "description": q.text}
                for q in exam.questions
            },
            "required": [q.id for q in exam.questions],
            "additionalProperties": False,
        },
    }


def exam_request(
    exam: Exam,
    *,
    system: str,
    memory: str,
    model: str,
    avatar_id: str,
    effort: Effort | None = "low",
    max_tokens: int = 4096,
) -> ModelRequest:
    """O pedido da prova: o prompt de sistema da mente, o que ela lembra e as perguntas."""
    lines = [memory, "", "## As perguntas"]
    for q in exam.questions:
        lines.append(f"- `{q.id}`: {q.text}")
        lines.extend(f"  - `{key}`: {text}" for key, text in q.options.items())
    return ModelRequest(
        model=model,
        messages=[{"role": "user", "content": [{"type": "text", "text": "\n".join(lines)}]}],
        system=[{"type": "text", "text": f"{system}\n\n{INSTRUCTIONS}"}],
        tools=[exam_tool(exam)],
        max_tokens=max_tokens,
        effort=effort,
        purpose="exam",
        avatar_id=avatar_id,
    )


def read_answers(exam: Exam, response: ModelResponse) -> dict[str, str]:
    """As respostas da ferramenta; o que falta ou não é opção vira "não sei"."""
    chosen = next((t for t in response.tool_uses() if t.get("name") == ANSWER), None)
    given = cast(Mapping[str, Any], (chosen or {}).get("input") or {})
    answers: dict[str, str] = {}
    for q in exam.questions:
        value = str(given.get(q.id, exam.unknown))
        answers[q.id] = value if value in q.options else exam.unknown
    return answers


def grade(exam: Exam, answers: Mapping[str, str]) -> Grade:
    right = sum(1 for q in exam.questions if answers.get(q.id) == q.answer)
    unknown = sum(1 for q in exam.questions if answers.get(q.id, exam.unknown) == exam.unknown)
    return Grade(right, len(exam.questions) - right - unknown, unknown, dict(answers))
