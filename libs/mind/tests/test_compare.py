"""A ferramenta de comparação (ADR-0074): a conta num caderno feito à mão, o terreno visto, o
pedido da reflexão com a ferramenta e o laço da noite; desligada, nada muda."""

from collections.abc import Mapping, Sequence
from typing import Any, cast

import pytest

from campsverso_adapters import SqliteMemory
from campsverso_mind import (
    COMPARE,
    COMPARE_INSTRUCTIONS,
    Clock,
    Columns,
    Comparison,
    LlmController,
    Memory,
    MemorySettings,
    Mind,
    ToolDef,
)
from campsverso_mind.memory import ADVISOR_INSTRUCTIONS, ADVISOR_NOTE, REFLECT
from campsverso_ports import (
    ModelCapabilities,
    ModelRequest,
    ModelResponse,
    ModelUsage,
    Place,
    Planting,
    Tile,
)

COLUMNS = Columns(
    terrain={
        "água": frozenset({"river"}),
        "mata": frozenset({"tree"}),
        "caminho": frozenset({"path"}),
        "porta": frozenset({"door"}),
    },
    things={"espantalho": frozenset({"scarecrow"})},
)
# O rio na coluna 0, uma árvore em (10,10) e a porta em (11,11): os canteiros de (20,20) ficam
# longe do rio e na mesma faixa da árvore e da porta que o canteiro de (1,2).
TERRAIN = [
    *(Tile(0, y, "river") for y in range(31)),
    Tile(10, 10, "tree"),
    Tile(11, 11, "door"),
]
SPRING = "primavera"


def planting(
    plot: str,
    x: int,
    y: int,
    crop: str,
    day: int,
    took: int | None,
    *,
    outcome: str | None = "colhida",
    previous: str | None = None,
    dry: int = 0,
) -> Planting:
    matured = None if took is None else day + took
    watered = tuple(range(day + dry, matured or day + 1))
    return Planting(
        plot,
        day * 1440 + 600,
        day,
        crop,
        x,
        y,
        previous=previous,
        watered_days=watered,
        matured_day=matured,
        outcome=outcome,
        outcome_day=None if matured is None else matured + 1,
        season=SPRING,
        matured_season=None if matured is None else SPRING,
    )


def notebook() -> list[Planting]:
    """Cinco rabanetes (um perto do rio, que levou 2 dias em vez de 3), quatro milhos (um que
    levou 8 dias em vez de 5, no canteiro que já tinha milho) e um milho maduro que se perdeu."""
    return [
        planting("plot-a", 1, 2, "rabanete", 1, 2),
        *(planting(f"plot-r{i}", 20 + i, 20, "rabanete", 1 + i, 3) for i in range(4)),
        *(planting(f"plot-m{i}", 20, 21 + i, "milho", 2 + i, 5) for i in range(3)),
        planting("plot-m0", 20, 21, "milho", 9, 8, previous="milho"),
        planting("plot-z", 30, 30, "milho", 3, 5, outcome="comida"),
    ]


def test_a_conta_acha_o_que_fugiu_e_as_colunas_em_que_difere() -> None:
    text = Comparison(COLUMNS, notebook(), TERRAIN, []).text("", 18)
    lines = text.splitlines()
    assert lines[0] == "Comparação do caderno de campo, até o dia 18."
    assert lines[1] == "O ritmo: 2 de 10 plantios maduros fugiram do normal:"
    # O milho de 8 dias foge mais (60%) que o rabanete de 2 (33%): vem primeiro.
    assert lines[2] == (
        "- plot-m0 (20,21) milho, plantado no dia 9: 8 dias; o normal desta cultura e estação é "
        "5 dias"
    )
    assert lines[3] == (
        "  este: água 20 tiles, mata 11 tiles, caminho não visto, porta 10 tiles, espantalho não "
        "visto, antes milho, adubo não, rega todos os dias, estação primavera"
    )
    assert "  diferem em: antes" in lines
    rabanete = lines.index(
        "- plot-a (1,2) rabanete, plantado no dia 1: 2 dias; o normal desta cultura e estação é "
        "3 dias"
    )
    peers = lines[rabanete + 2 : rabanete + 5]
    assert [p.split(" (")[0].strip() for p in peers] == [
        "plot-r3, plantado no dia 4",
        "plot-r2, plantado no dia 3",
        "plot-r1, plantado no dia 2",
    ]
    assert lines[rabanete + 5] == "  diferem em: água"  # a mata e a porta, na mesma faixa
    # A perda, ao lado das colhidas mais parecidas.
    assert "As perdas: 1 planta se perdeu antes da colheita, e 9 foram colhidas:" in lines
    lost = lines.index("- plot-z (30,30) milho, comida no dia 9")
    assert lines[lost + 5].startswith("  diferem em: ")
    assert "porta" in lines[lost + 5]


def test_a_conta_filtra_a_cultura_e_diz_quando_nao_ha_o_que_comparar() -> None:
    milho = Comparison(COLUMNS, notebook(), TERRAIN, []).text("milho", 18)
    assert "Comparação do caderno de campo de milho, até o dia 18." in milho
    assert "rabanete" not in milho.split("As perdas")[0]
    empty = Comparison(COLUMNS, notebook()[:2], TERRAIN, []).text("", 3)
    assert empty.startswith("Comparação do caderno de campo, até o dia 3. Ainda não há o que")


def test_a_rega_que_faltou_o_espantalho_e_a_estacao_que_virou_entram_nas_colunas() -> None:
    scarecrow = Place("espantalho-1", "scarecrow", 3, 2, (), 100, 1)
    row, _ = Comparison(COLUMNS, [], TERRAIN, [scarecrow]).row(
        Planting(
            "plot-s",
            9240,
            6,
            "rabanete",
            1,
            2,
            watered_days=(7, 8, 9),
            matured_day=10,
            season=SPRING,
            matured_season="verão",
        )
    )
    assert row["espantalho"] == "2 tiles"
    assert row["rega"] == "faltou em 1 de 4 dias"
    assert row["estação"] == "primavera até verão"


# ------------------------------------------------------------- a mente


TOOLS = (ToolDef("sleep_here", "sleep", "Dormir aqui.", shape={}),)
MIND = Mind("teste", "Você é o Camps.", "Notas.", TOOLS, field_notebook=True, columns=COLUMNS)


def response(*content: Mapping[str, Any]) -> ModelResponse:
    return ModelResponse(
        content=list(content),
        stop_reason="tool_use",
        usage=ModelUsage(10, 5),
        model="m",
        latency_ms=1,
    )


def compare_use(crop: str = "") -> dict[str, Any]:
    return {"type": "tool_use", "id": "toolu_cmp", "name": COMPARE, "input": {"crop": crop}}


def reflect_use() -> dict[str, Any]:
    given: dict[str, Any] = {"summary": "Dormi.", "plan": "", "beliefs": []}
    return {"type": "tool_use", "id": "toolu_reflect", "name": REFLECT, "input": given}


class ScriptedModel:
    provider = "scripted"

    def __init__(self, *responses: ModelResponse) -> None:
        self.queue = list(responses)
        self.requests: list[ModelRequest] = []

    def capabilities(self) -> ModelCapabilities:
        return ModelCapabilities()

    async def count_tokens(self, request: ModelRequest) -> int:
        return 1

    async def complete(self, request: ModelRequest) -> ModelResponse:
        self.requests.append(request)
        return self.queue.pop(0)


def memory(*, compare: bool = True) -> Memory:
    mem = Memory(SqliteMemory(":memory:"), "camps", MemorySettings(compare=compare))
    mem.adopt(MIND)
    return mem


def snapshot(day: int = 1) -> dict[str, Any]:
    tick = (day - 1) * 1440 + 900
    clock = {"tick": tick, "sim_time": "2026-10-10T21:00:00-03:00", "day": day, "season": SPRING}
    return {
        "avatar_id": "camps",
        "as_of_tick": tick,
        "decision": {"reason": "action_completed", "controller": {"type": "llm", "id": "llm"}},
        "view": {
            "clock": clock,
            "weather": {"condition": "sun", "day": day},
            "self": {"entity_id": "camps", "position": {"x": 1, "y": 1}, "needs": {}},
            "containers": [],
            "entities": [],
            "map": {
                "origin": {"x": 0, "y": 0},
                "rows": ["~.T", "~.."],
                "legend": {
                    "~": {"kind": "river", "properties": {}},
                    ".": {"kind": "grass", "properties": {}},
                    "T": {"kind": "tree", "properties": {}},
                },
            },
        },
    }


def test_a_foto_guarda_so_o_terreno_que_a_comparacao_mede() -> None:
    mem = memory()
    mem.observe(snapshot())
    assert mem.port.terrain() == [Tile(0, 0, "river"), Tile(2, 0, "tree"), Tile(0, 1, "river")]
    assert mem.clock is not None
    assert mem.clock.season == SPRING
    off = memory(compare=False)
    off.observe(snapshot())
    assert off.port.terrain() == []


def test_a_reflexao_ganha_a_ferramenta_so_quando_ligada() -> None:
    night = Clock(900, 1, "2026-10-10T21:00:00-03:00")
    on = memory().reflect_request("x", night, 1, "m")
    assert [t["name"] for t in on.tools] == [COMPARE, REFLECT]
    assert COMPARE_INSTRUCTIONS in str(on.system)
    off = memory(compare=False).reflect_request("x", night, 1, "m")
    assert [t["name"] for t in off.tools] == [REFLECT]
    assert COMPARE_INSTRUCTIONS not in str(off.system)


def test_sem_colunas_a_comparacao_nao_liga() -> None:
    mem = Memory(SqliteMemory(":memory:"), "camps", MemorySettings(compare=True))
    with pytest.raises(ValueError, match="colunas"):
        mem.adopt(Mind("m", "c", "n", (), field_notebook=True))


def controller(model: ScriptedModel, mem: Memory) -> LlmController:
    return LlmController(MIND, model, controller_id="llm", avatar_id="camps", model="m", memory=mem)


async def test_a_noite_compara_e_depois_fecha_o_dia() -> None:
    mem = memory()
    for p in notebook():
        mem.port.save_planting(p)
    mem.port.see(TERRAIN)
    model = ScriptedModel(
        response({"type": "tool_use", "id": "toolu_s", "name": "sleep_here", "input": {}}),
        response(compare_use("rabanete")),
        response(reflect_use()),
    )
    mind = controller(model, mem)
    await mind.decide(snapshot(day=18))
    await mind.after_proposal()
    assert (mind.reflections, mem.comparisons) == (1, 1)
    first, second = model.requests[1:]
    assert second.messages[: len(first.messages)] == first.messages
    assert second.messages[-2]["content"] == [compare_use("rabanete")]
    (result,) = cast(Sequence[Mapping[str, Any]], second.messages[-1]["content"])
    assert result["tool_use_id"] == "toolu_cmp"
    assert result["content"].startswith("Comparação do caderno de campo de rabanete, até o dia 18.")
    assert "plot-a (1,2) rabanete" in result["content"]


async def test_a_noite_compara_no_maximo_duas_vezes() -> None:
    mem = memory()
    model = ScriptedModel(
        response({"type": "tool_use", "id": "toolu_s", "name": "sleep_here", "input": {}}),
        response(compare_use()),
        response(compare_use()),
        response(compare_use()),
    )
    mind = controller(model, mem)
    await mind.decide(snapshot())
    await mind.after_proposal()
    assert (len(model.requests), mem.comparisons, mind.reflections) == (4, 2, 0)


# ------------------------------------------------------------- o conselheiro (ADR-0074)

OPUS48 = "claude-opus-4-8"


def advised_memory(advisor: str | None = OPUS48) -> Memory:
    mem = Memory(SqliteMemory(":memory:"), "camps", MemorySettings(advisor=advisor))
    mem.adopt(MIND)
    return mem


def test_a_reflexao_ganha_o_conselheiro_so_quando_ligado() -> None:
    night = Clock(900, 1, "2026-10-10T21:00:00-03:00")
    on = advised_memory().reflect_request("x", night, 1, "m")
    advisor = on.tools[0]
    assert advisor == {
        "type": "advisor_20260301",
        "name": "advisor",
        "model": OPUS48,
        "max_uses": 1,
        "max_tokens": 4096,
    }
    assert on.tools[-1]["name"] == REFLECT
    assert ADVISOR_INSTRUCTIONS in str(on.system)
    assert ADVISOR_NOTE in on.messages[0]["content"][0]["text"]
    off = advised_memory(None).reflect_request("x", night, 1, "m")
    assert [t.get("name") for t in off.tools] == [REFLECT]
    assert ADVISOR_INSTRUCTIONS not in str(off.system)
    assert ADVISOR_NOTE not in off.messages[0]["content"][0]["text"]


async def test_a_noite_ouve_o_conselheiro_e_fecha_o_dia() -> None:
    mem = advised_memory()
    asked: dict[str, Any] = {
        "type": "server_tool_use",
        "id": "srvtoolu_1",
        "name": "advisor",
        "input": {},
    }
    advice = {
        "type": "advisor_tool_result",
        "tool_use_id": "srvtoolu_1",
        "content": {"type": "advisor_result", "text": "Compare dois canteiros."},
    }
    model = ScriptedModel(
        response({"type": "tool_use", "id": "toolu_s", "name": "sleep_here", "input": {}}),
        response(asked, advice, reflect_use()),
    )
    mind = controller(model, mem)
    await mind.decide(snapshot())
    await mind.after_proposal()
    assert (mind.reflections, mem.advised, len(model.requests)) == (1, 1, 2)
