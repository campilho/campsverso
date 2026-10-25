"""A prova do mundo (ADR-0070, decisão 12): perguntas fechadas, a ferramenta estrita, a nota."""

from pathlib import Path
from typing import Any, cast

import pytest

from campsverso_mind import Exam, exam_request, grade, load_exam, read_answers
from campsverso_mind.exam import ANSWER, INSTRUCTIONS, exam_tool
from campsverso_ports import ModelResponse, ModelUsage

PROVA = """\
unknown: nao_sei
questions:
  - id: agua
    text: >-
      Dois canteiros, um perto da água
      e o outro longe. Qual amadurece antes?
    options: {perto: o perto, longe: o longe, nao_sei: não sei}
    answer: perto
    script: {effect: [agua<=2], above: perto, below: longe}
  - id: bau
    text: Quais estragam primeiro?
    options: {inventario: os do inventário, bau: os do baú, nao_sei: não sei}
    answer: inventario
"""


def _exam(tmp_path: Path, text: str = PROVA) -> Exam:
    path = tmp_path / "prova.yaml"
    path.write_text(text, encoding="utf-8")
    return load_exam(path)


def _response(given: dict[str, Any] | None) -> ModelResponse:
    content = [] if given is None else [{"type": "tool_use", "name": ANSWER, "input": given}]
    return ModelResponse(content, "tool_use", ModelUsage(10, 5, 0, 0), "claude-haiku-5-5", 1)


def test_a_prova_carrega_as_perguntas_com_o_gabarito_e_a_leitura_do_script(
    tmp_path: Path,
) -> None:
    exam = _exam(tmp_path)
    assert exam.unknown == "nao_sei"
    assert [q.id for q in exam.questions] == ["agua", "bau"]
    agua = exam.questions[0]
    assert agua.text == "Dois canteiros, um perto da água e o outro longe. Qual amadurece antes?"
    assert (agua.answer, agua.script["above"]) == ("perto", "perto")
    assert exam.questions[1].script == {}


def test_um_gabarito_fora_das_opcoes_e_erro(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="pergunta bau"):
        _exam(tmp_path, PROVA.replace("answer: inventario", "answer: geladeira"))


def test_a_ferramenta_e_estrita_com_uma_opcao_por_pergunta(tmp_path: Path) -> None:
    tool = exam_tool(_exam(tmp_path))
    schema = cast(dict[str, Any], tool["input_schema"])
    assert (tool["name"], tool["strict"]) == ("answer", True)
    assert schema["required"] == ["agua", "bau"]
    assert schema["additionalProperties"] is False
    assert schema["properties"]["agua"]["enum"] == ["perto", "longe", "nao_sei"]


def test_o_pedido_leva_a_identidade_a_memoria_e_as_perguntas(tmp_path: Path) -> None:
    exam = _exam(tmp_path)
    request = exam_request(
        exam,
        system="Você é o Camps.",
        memory="## O que você lembra\nO caderno ainda está vazio.",
        model="claude-haiku-5-5",
        avatar_id="camps",
    )
    assert (request.purpose, request.effort, request.avatar_id) == ("exam", "low", "camps")
    system = cast(list[dict[str, Any]], request.system)
    assert system[0]["text"] == f"Você é o Camps.\n\n{INSTRUCTIONS}"
    text = request.messages[0]["content"][0]["text"]
    assert text.startswith("## O que você lembra\nO caderno ainda está vazio.")
    assert "- `bau`: Quais estragam primeiro?\n  - `inventario`: os do inventário" in text
    assert [t["name"] for t in request.tools] == ["answer"]


def test_o_que_falta_ou_nao_e_opcao_vira_nao_sei_e_a_nota_conta(tmp_path: Path) -> None:
    exam = _exam(tmp_path)
    answers = read_answers(exam, _response({"agua": "longe", "bau": "geladeira"}))
    assert answers == {"agua": "longe", "bau": "nao_sei"}
    assert read_answers(exam, _response(None)) == {"agua": "nao_sei", "bau": "nao_sei"}
    graded = grade(exam, {"agua": "perto", "bau": "nao_sei"})
    assert (graded.right, graded.wrong, graded.unknown) == (1, 0, 1)
    assert grade(exam, answers).as_dict() == {
        "right": 0,
        "wrong": 1,
        "unknown": 1,
        "answers": {"agua": "longe", "bau": "nao_sei"},
    }
