"""O juiz das crenças (ADR-0070, decisão 13): o dossiê, a rubrica, o pedido e a conferência."""

import json
from pathlib import Path
from typing import Any, cast

from campsverso_ports import ModelCapabilities, ModelRequest, ModelResponse, ModelUsage
from campsverso_tools.judge import (
    INSTRUCTIONS,
    MODEL,
    agreement,
    dossier,
    judge_request,
    judge_run,
    judged_runs,
    load_rubric,
    main,
    read_verdicts,
    verdict_tool,
)


def ev(day: int, kind: str, /, **data: Any) -> dict[str, Any]:
    return {
        "type": f"campsverso.memory.belief.{kind}.v1",
        "tick": (day - 1) * 1440 + 600,
        "data": {"avatar_id": "camps", **data},
    }


ENVELOPES = [
    ev(1, "formed", belief_id="bel-0001", statement="O leste é bom.", confidence=0.6,
       evidence=["e-01 maduro em 2 dias"], source={"kind": "observation"}),
    ev(2, "updated", belief_id="bel-0001", statement="O leste amadurece um dia antes.",
       confidence={"before": 0.6, "after": 0.9}, evidence=["e-01 e e-02 em 2 dias"],
       source={"kind": "observation"}, reason="duas colheitas"),
    ev(2, "formed", belief_id="bel-0002", statement="O baú estraga tudo.", confidence=0.5,
       evidence=[], source={"kind": "observation"}),
    ev(3, "retracted", belief_id="bel-0002", statement="O baú estraga tudo.",
       reason="não se sustentou"),
]  # fmt: skip


def test_o_dossie_tem_as_ativas_com_a_trajetoria_e_as_retiradas() -> None:
    text = dossier(ENVELOPES)
    assert "## As crenças ativas no fim (1)" in text
    assert "### bel-0001 (confiança 0,90)" in text
    assert "Enunciado: O leste amadurece um dia antes." in text
    assert "Como foi formada: O leste é bom." in text
    assert "- evidência: e-01 e e-02 em 2 dias" in text
    assert "Trajetória: dia 1 formada 0,60; dia 2 revisada 0,90" in text
    assert "- bel-0002, retirada no dia 3: O baú estraga tudo. Por quê: não se sustentou" in text
    assert "camps" not in text  # nem o avatar: o juiz não sabe de quem são


def test_o_dossie_cortado_num_dia_mostra_as_crencas_daquele_dia() -> None:
    text = dossier(ENVELOPES, until_day=2)
    assert "## As crenças ativas no fim (2)" in text
    assert "### bel-0002 (confiança 0,50)" in text
    assert "## As crenças retiradas (0)" in text


def test_as_rubricas_dos_tres_mundos() -> None:
    camps, boavista, morada = (
        load_rubric(c) for c in ("farm_camps", "farm_boavista", "farm_morada_do_sol")
    )
    assert camps is not None
    assert boavista is not None
    assert morada is not None
    assert [r.id for r in camps.rules] == ["agua"]
    assert [r.id for r in boavista.rules] == ["agua", "tomate", "alho", "bau", "ensopado", "adubo"]
    assert [r.id for r in morada.rules][:4] == ["agua", "corvos", "fadiga", "reputacao"]
    assert len(morada.rules) == 9
    places = {r.id for r in morada.rules if r.place}
    assert places == {"agua", "corvos", "fadiga"}  # só o lugar é das regras de lugar
    assert load_rubric("farm") is None


def test_a_ferramenta_e_o_pedido() -> None:
    rubric = load_rubric("farm_boavista")
    assert rubric is not None
    tool = verdict_tool(rubric)
    schema = cast(dict[str, Any], tool["input_schema"])
    assert (tool["name"], tool["strict"]) == ("verdicts", True)
    assert schema["properties"]["agua"]["properties"]["verdict"]["enum"] == [
        "causa",
        "lugar",
        "nao",
    ]
    assert schema["properties"]["tomate"]["properties"]["verdict"]["enum"] == ["causa", "nao"]
    request = judge_request(rubric, "## As crenças ativas no fim (0)\n")
    assert (request.model, request.purpose, request.effort) == (MODEL, "judge", "high")
    assert request.system == INSTRUCTIONS
    text = request.messages[0]["content"][0]["text"]
    assert text.startswith("# O mundo\n\nUma fazenda sem canteiros no começo")
    assert "## `tomate`\nA verdade: O tomate murcha" in text
    assert text.endswith("# As crenças do agente\n\n## As crenças ativas no fim (0)\n")


def _response(given: dict[str, Any]) -> ModelResponse:
    block = {"type": "tool_use", "id": "toolu_j", "name": "verdicts", "input": given}
    return ModelResponse([block], "tool_use", ModelUsage(5000, 2000, 0, 0), MODEL, 1)


def test_o_que_falta_ou_nao_e_opcao_vira_nao() -> None:
    rubric = load_rubric("farm_boavista")
    assert rubric is not None
    found = read_verdicts(
        rubric,
        _response(
            {
                "agua": {"verdict": "lugar", "belief_id": "bel-0001", "why": "o leste"},
                "tomate": {"verdict": "lugar", "belief_id": "bel-0002", "why": "?"},
                "alho": {"verdict": "nao", "belief_id": "bel-0003", "why": "nada"},
            }
        ),
    )
    assert found["agua"] == {"verdict": "lugar", "belief_id": "bel-0001", "why": "o leste"}
    assert found["tomate"]["verdict"] == "nao"  # o tomate não tem "só o lugar"
    assert found["alho"] == {"verdict": "nao", "belief_id": "", "why": "nada"}
    assert found["bau"] == {"verdict": "nao", "belief_id": "", "why": ""}


class JudgePort:
    """Dá `lugar` à água pela primeira crença ativa, e conta as chamadas."""

    provider = "fake"

    def __init__(self) -> None:
        self.calls = 0

    def capabilities(self) -> ModelCapabilities:
        return ModelCapabilities()

    async def count_tokens(self, request: ModelRequest) -> int:
        return 1

    async def complete(self, request: ModelRequest) -> ModelResponse:
        self.calls += 1
        assert "bel-0001" in str(request.messages[0]["content"][0]["text"])
        return _response({"agua": {"verdict": "lugar", "belief_id": "bel-0001", "why": "leste"}})


def _arena(tmp_path: Path) -> Path:
    arena = tmp_path / "arena"
    for name, memory in (("haiku-memoria", True), ("script", False)):
        folder = arena / name
        folder.mkdir(parents=True)
        spec = {"name": name, "memory": memory, "cartridge": "farm_camps"}
        (folder / "summary.json").write_text(json.dumps({"spec": spec}), encoding="utf-8")
        (folder / "archive.jsonl").write_text(
            "".join(json.dumps(e) + "\n" for e in ENVELOPES), encoding="utf-8"
        )
    return arena


async def test_o_juiz_grava_a_fita_e_o_veredito_e_repete_de_graca(tmp_path: Path) -> None:
    arena = _arena(tmp_path)
    assert [f.name for f in judged_runs(arena)] == ["haiku-memoria"]  # o script não tem crenças
    port = JudgePort()
    folder = arena / "haiku-memoria"
    first = await judge_run(folder, port)
    assert first is not None
    assert first["rules"]["agua"]["verdict"] == "lugar"
    assert first["cost_usd"] == 0.06  # 5 mil de entrada e 2 mil de saída no preço do Opus
    assert json.loads((folder / "juiz.json").read_text(encoding="utf-8")) == first
    again = await judge_run(folder, port)
    assert again is not None
    assert again["replayed"] is True
    assert port.calls == 1  # a fita respondeu


def test_a_conferencia_conta_as_concordancias(tmp_path: Path, capsys: Any) -> None:
    arena = _arena(tmp_path)
    given = {"rules": {"agua": {"verdict": "lugar", "belief_id": "bel-0001", "why": "o leste"}}}
    (arena / "haiku-memoria" / "juiz.json").write_text(json.dumps(given), encoding="utf-8")
    key = tmp_path / "gabarito.yaml"
    key.write_text(
        "runs:\n  haiku-memoria: {agua: nao}\n  outra: {agua: {verdict: nao, belief: ''}}\n",
        encoding="utf-8",
    )
    agreed, total, differ = agreement(key, arena)
    assert (agreed, total) == (0, 2)
    assert differ == [
        "haiku-memoria agua: à mão nao, o juiz lugar. o leste",
        "outra agua: à mão nao, o juiz sem veredito.",
    ]
    assert main([str(arena), "--conferir", str(key)]) == 0
    assert "concordância: 0 de 2 (0%)" in capsys.readouterr().out
