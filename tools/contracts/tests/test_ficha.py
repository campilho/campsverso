"""A ficha de cada corrida e de cada juiz (ADR-0074, decisão 12): lida do que a corrida gravou."""

import json
from pathlib import Path
from typing import Any

from campsverso_tools.ficha import answered_models, calls_of, judge_card, run_card, sha256_of

REPO = Path(__file__).resolve().parents[3]


def _call(purpose: str, effort: str | None, provider: str = "anthropic") -> dict[str, Any]:
    data: dict[str, Any] = {"purpose": purpose, "provider": provider}
    if effort is not None:
        data["effort"] = effort
    return {"type": "campsverso.llm.call.completed.v1", "data": data}


def _tape(path: Path, *responses: dict[str, Any]) -> Path:
    path.write_text("".join(json.dumps({"response": r}) + "\n" for r in responses), "utf-8")
    return path


def test_o_modelo_que_respondeu_vem_da_fita_com_o_conselheiro(tmp_path: Path) -> None:
    tape = _tape(
        tmp_path / "llm.jsonl",
        {"model": "claude-haiku-5-5"},
        {"model": "claude-haiku-5-5", "advisor": {"model": "claude-opus-4-8"}},
    )
    assert answered_models(tape) == ["claude-haiku-5-5", "claude-opus-4-8"]
    assert answered_models(tmp_path / "nenhuma.jsonl") == []


def test_a_rota_e_o_esforco_vem_dos_eventos() -> None:
    events = [_call("decision", "low"), _call("reflection", "medium"), _call("decision", "low")]
    assert calls_of(events) == {
        "route": ["anthropic"],
        "effort": {"decision": ["low"], "reflection": ["medium"]},
    }
    # Pela OpenRouter, a rota diz quem atendeu (ADR-0074).
    routed = _call("decision", "low", "openrouter")
    routed["data"]["served_by"] = "OpenAI"
    assert calls_of([routed])["route"] == ["openrouter: OpenAI"]


def test_a_ficha_de_uma_corrida_pela_openrouter(tmp_path: Path) -> None:
    routed = _call("decision", "low", "openrouter")
    routed["data"]["served_by"] = "OpenAI"
    card = run_card(
        started="2026-10-29T01:00:00+00:00",
        spec={"controller": "llm", "model": "openai/gpt-6-astra", "memory": True},
        envelopes=[routed],
        tape=_tape(tmp_path / "llm.jsonl", {"model": "openai/gpt-6-astra"}),
        root=REPO,
    )
    assert (card["route"], card["answered"]) == (["openrouter: OpenAI"], ["openai/gpt-6-astra"])
    assert card["harness"]["sdk"].startswith("httpx2 ")


def test_a_ficha_da_mente_e_a_do_script(tmp_path: Path) -> None:
    tape = _tape(tmp_path / "llm.jsonl", {"model": "claude-haiku-5-5"})
    spec = {
        "controller": "llm",
        "model": "claude-haiku-5-5",
        "memory": True,
        "playbook": 0,
        "compare": True,
        "advisor": None,
    }
    tools = [{"name": "plant"}, {"name": "wait"}]
    card = run_card(
        started="2026-10-29T01:00:00+00:00",
        spec=spec,
        envelopes=[_call("decision", "low")],
        tape=tape,
        root=REPO,
        mind={
            "name": "camps_morada",
            "system": [{"type": "text", "text": "Você é o Camps."}],
            "tools": tools,
        },
    )
    assert (card["date"], card["model"], card["answered"]) == (
        "2026-10-29",
        "claude-haiku-5-5",
        ["claude-haiku-5-5"],
    )
    assert card["route"] == ["anthropic"]
    harness = card["harness"]
    assert len(harness["commit"]) == 40
    assert harness["sdk"].startswith("anthropic ")
    assert (harness["mind"], harness["tools"], harness["compare"]) == ("camps_morada", 2, True)
    assert harness["tools_sha256"] == sha256_of(tools)
    assert "advisor" not in card
    script = run_card(
        started="2026-10-29T01:00:00+00:00",
        spec={"controller": "script", "script": "farmer3-fixo"},
        envelopes=[],
        tape=tmp_path / "nenhuma.jsonl",
        root=REPO,
    )
    assert script["harness"]["script"] == "farmer3-fixo"
    assert "model" not in script


def test_a_ficha_do_juiz_tem_a_rubrica(tmp_path: Path) -> None:
    rubric = tmp_path / "juiz.yaml"
    rubric.write_text("world: x\n", encoding="utf-8")
    card = judge_card(date="2026-10-29T01:00:00+00:00", rubric=rubric, root=REPO)
    assert card["date"] == "2026-10-29"
    assert card["rubric_sha256"] == sha256_of("world: x\n")
