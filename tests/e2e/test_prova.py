"""A prova do mundo na arena (ADR-0070, decisão 12): a mente antes e depois, o script no modelo.

O oráculo, lido pela mesma regra que o script 3 com a verdade no lugar da crença, tem de tirar o
gabarito em todas as perguntas que o modelo cobre: é o que confere o gabarito contra as regras do
cartucho. As corridas são curtas e sem API (uma porta falsa responde a prova).
"""

import json
import math
from pathlib import Path

from campsverso_farm_script import Farmer3Script
from campsverso_farm_script.knowledge import Spot
from campsverso_mind import Exam
from campsverso_ports import ModelCapabilities, ModelRequest, ModelResponse, ModelUsage
from campsverso_testkit.arena import Spec, run_spec
from campsverso_testkit.prova import exam_of, knowledge_of, script_answers

MORADA = "farm_morada_do_sol"
SEED = 20261022  # a do mundo farm-morada-do-sol-01


def _exam() -> Exam:
    exam = exam_of(MORADA)
    assert exam is not None
    return exam


def _answers(script: Farmer3Script) -> dict[str, str]:
    known = knowledge_of(script)
    assert known is not None
    return script_answers(_exam(), *known)


def test_o_oraculo_tira_o_gabarito_em_tudo_o_que_o_modelo_cobre() -> None:
    exam = _exam()
    answers = _answers(Farmer3Script.oracle())
    covered = [q for q in exam.questions if q.script]
    assert len(covered) == 6
    assert {q.id: answers[q.id] for q in covered} == {q.id: q.answer for q in covered}
    assert all(answers[q.id] == "nao_sei" for q in exam.questions if not q.script)


def test_o_script_3_sem_caderno_nao_sabe_nada() -> None:
    assert set(_answers(Farmer3Script.load()).values()) == {"nao_sei"}


def test_o_script_3_responde_o_que_a_crenca_sustenta() -> None:
    script = Farmer3Script.load()
    beliefs = script.book.beliefs
    far = (30, 30, 30, 30)  # água, mata, caminho e porta longe: a base do modelo
    near_water = (1, 30, 30, 30)
    for _ in range(6):
        beliefs.learn_growth(Spot(far), 0.0)
        beliefs.learn_growth(Spot(near_water), math.log(1.5))
        beliefs.learn_growth(Spot(far, repeat=True), math.log(0.6))
    for lost in (True, True, False, True, True):
        beliefs.learn_loss(30, None, lost)
    for _ in range(4):
        beliefs.learn_loss(5, None, False)
        beliefs.learn_loss(30, 1, False)  # ao lado do espantalho
    answers = _answers(script)
    assert answers["agua"] == "perto"
    assert answers["agua_alcance"] == "um"  # só mediu colado na água: não sabe que vai até 4
    assert answers["fadiga"] == "devagar"
    assert (answers["corvos_longe"], answers["corvos_perto"]) == ("comida", "sem_risco")
    assert answers["espantalho"] == "lado"  # protegeu ao lado; a 6 tiles, nunca mediu


async def test_a_corrida_do_script_3_grava_a_prova_do_fim(tmp_path: Path) -> None:
    spec = Spec("script3", "script", seed=SEED, cartridge=MORADA, script="farmer3")
    result = await run_spec(spec, 1, tmp_path / "script3")
    prova = json.loads((tmp_path / "script3" / "prova.json").read_text(encoding="utf-8"))
    assert set(prova) == {"key", "after"}  # o script não faz a prova antes: não supõe nada
    assert prova["key"]["agua"] == "perto"
    assert set(result["prova"]) == {"after"}
    assert "answers" not in result["prova"]["after"]  # as respostas ficam só no prova.json
    model = json.loads((tmp_path / "script3" / "modelo.json").read_text(encoding="utf-8"))
    names = [e["name"] for e in model["effects"]]
    assert names[0] == "base"
    assert {"agua<=2", "repetida", "adubada"} <= set(names)


class ExamPort:
    """Espera sempre; na prova, "não sei" com a memória vazia e o gabarito com o caderno."""

    provider = "fake"

    def __init__(self, key: dict[str, str]) -> None:
        self.key = key
        self.exams: list[str] = []

    def capabilities(self) -> ModelCapabilities:
        return ModelCapabilities()

    async def count_tokens(self, request: ModelRequest) -> int:
        return 1

    async def complete(self, request: ModelRequest) -> ModelResponse:
        if request.purpose == "exam":
            text = str(request.messages[0]["content"][0]["text"])
            self.exams.append(text)
            empty = "O caderno ainda está vazio" in text
            given = {q: ("nao_sei" if empty else a) for q, a in self.key.items()}
            block = {"type": "tool_use", "id": "toolu_p", "name": "answer", "input": given}
        else:
            given = {"ticks": 60, "intent": "esperar"}
            block = {"type": "tool_use", "id": "toolu_1", "name": "wait", "input": given}
        return ModelResponse(
            [block], "tool_use", ModelUsage(1000, 100, 0, 0), request.model, latency_ms=1
        )


async def test_a_mente_faz_a_prova_antes_e_depois_fora_do_medidor(tmp_path: Path) -> None:
    exam = _exam()
    port = ExamPort({q.id: q.answer for q in exam.questions})
    spec = Spec("haiku-memoria", "llm", memory=True, seed=SEED, cartridge=MORADA, days=1)
    result = await run_spec(spec, 1, tmp_path / "haiku", port=port)
    assert len(port.exams) == 2
    assert "O caderno ainda está vazio" in port.exams[0]
    assert "Momentos de hoje" in port.exams[1]  # o fim leva o que ela lembra
    prova = json.loads((tmp_path / "haiku" / "prova.json").read_text(encoding="utf-8"))
    total = len(exam.questions)
    assert (prova["before"]["right"], prova["before"]["unknown"]) == (0, total)
    assert (prova["after"]["right"], prova["after"]["wrong"]) == (total, 0)
    assert prova["after"]["cost_usd"] > 0  # o preço do Haiku na configuração
    assert set(result["prova"]) == {"before", "after"}
    # A prova vai pela fita da corrida, mas não pelo medidor: não conta nas chamadas do mundo.
    tape = (tmp_path / "haiku" / "llm.jsonl").read_text(encoding="utf-8").splitlines()
    assert result["calls"] == len(tape) - 2
