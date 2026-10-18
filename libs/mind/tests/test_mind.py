"""A mente com uma porta falsa: a janela, as ferramentas, as recusas, as falhas (ADR-0059)."""

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, cast

import pytest

from campsverso_mind import (
    INTENT,
    LlmController,
    Mind,
    ParamDef,
    ToolDef,
    Window,
    load_tools,
    proposal_from,
    reason_text,
    tool_specs,
)
from campsverso_mind.controller import INSTRUCTIONS
from campsverso_ports import (
    ModelCallError,
    ModelCapabilities,
    ModelRequest,
    ModelResponse,
    ModelUsage,
)

TOOLS = (
    ToolDef(
        "plant",
        "plant",
        "Plantar uma semente num canteiro vazio ao seu lado.",
        (
            ParamDef("target", "string", "id do canteiro"),
            ParamDef("crop", "string", "a cultura", ("rabanete", "batata")),
        ),
        duration_ticks=5,
        energy=2,
    ),
    ToolDef(
        "move_near",
        "move",
        "Andar até ficar ao lado de uma coisa.",
        (ParamDef("near", "string", "id"),),
    ),
    ToolDef(
        "move_to",
        "move",
        "Andar até um tile.",
        (ParamDef("x", "integer", "coluna"), ParamDef("y", "integer", "linha")),
        shape={"target": {"x": "$x", "y": "$y"}},
    ),
    ToolDef(
        "wait", "wait", "Esperar.", (ParamDef("ticks", "integer", "minutos"),), duration_ticks=1
    ),
    ToolDef("sleep_here", "sleep", "Dormir onde está."),
)
MIND = Mind("teste", "Você é o Camps.", "O quiosque fecha às 18:00.", TOOLS)


def tool_use(name: str, **given: Any) -> dict[str, Any]:
    return {"type": "tool_use", "id": f"toolu_{name}_{len(given)}", "name": name, "input": given}


def response(*content: Mapping[str, Any], stop: str = "tool_use") -> ModelResponse:
    return ModelResponse(
        content=list(content), stop_reason=stop, usage=ModelUsage(10, 5), model="m", latency_ms=1
    )


THINKING = {"type": "thinking", "thinking": "", "signature": "abc"}


class ScriptedModel:
    """Responde na ordem combinada e guarda cada pedido; pode falhar sob encomenda."""

    provider = "scripted"

    def __init__(self, *responses: ModelResponse | ModelCallError) -> None:
        self.queue = list(responses)
        self.requests: list[ModelRequest] = []

    def capabilities(self) -> ModelCapabilities:
        return ModelCapabilities()

    async def count_tokens(self, request: ModelRequest) -> int:
        return 1

    async def complete(self, request: ModelRequest) -> ModelResponse:
        self.requests.append(request)
        item = self.queue.pop(0)
        if isinstance(item, ModelCallError):
            raise item
        return item


class Notes:
    def __init__(self) -> None:
        self.events: list[tuple[str, str]] = []

    def info(self, event: str, **fields: Any) -> None:
        self.events.append(("info", event))

    def warning(self, event: str, **fields: Any) -> None:
        self.events.append(("warning", event))

    def error(self, event: str, **fields: Any) -> None:
        self.events.append(("error", event))


def snapshot(tick: int = 0, reason: str = "session_started") -> dict[str, Any]:
    return {
        "avatar_id": "camps",
        "kind": "snapshot",
        "as_of_tick": tick,
        "decision": {"reason": reason, "controller": {"type": "llm", "id": "llm/camps"}},
        "view": {
            "clock": {
                "tick": tick,
                "sim_time": "2026-10-10T06:00:00-03:00",
                "day": 1,
                "phase": "manha",
            },
            "weather": {"condition": "sun", "day": 1},
            "self": {"entity_id": "camps", "position": {"x": 1, "y": 1}, "needs": {"fome": 10.0}},
            "containers": [],
            "entities": [{"entity_id": "plot-e-01", "kind": "plot", "attributes": {}}],
        },
    }


def delta(
    since: int,
    tick: int,
    reason: str = "action_completed",
    events: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    return {
        "avatar_id": "camps",
        "since_tick": since,
        "as_of_tick": tick,
        "decision": {"reason": reason, "controller": {"type": "llm", "id": "llm/camps"}},
        "clock": {
            "tick": tick,
            "sim_time": "2026-10-10T06:05:00-03:00",
            "day": 1,
            "phase": "manha",
        },
        "self": {"entity_id": "camps", "position": {"x": 2, "y": 1}, "needs": {"fome": 11.0}},
        "events": list(events),
    }


def controller(model: ScriptedModel, notes: Notes | None = None) -> LlmController:
    return LlmController(
        MIND, model, controller_id="llm/camps", avatar_id="camps", model="m", telemetry=notes
    )


def user_blocks(request: ModelRequest, index: int) -> list[dict[str, Any]]:
    return cast(list[dict[str, Any]], request.messages[index]["content"])


async def decided(mind: LlmController, delivery: dict[str, Any]) -> dict[str, Any]:
    proposal = await mind.decide(delivery)
    assert proposal is not None
    return proposal


# ------------------------------------------------------------- ferramentas


def test_ferramentas_estritas_com_intencao_obrigatoria() -> None:
    specs = {s["name"]: s for s in tool_specs(TOOLS)}
    plant = specs["plant"]
    assert plant["strict"] is True
    schema = plant["input_schema"]
    assert schema["additionalProperties"] is False
    assert schema["required"] == ["target", "crop", INTENT]
    assert schema["properties"]["crop"]["enum"] == ["rabanete", "batata"]
    assert plant["description"].endswith("Dura 5 minutos. Gasta 2 de energia.")
    assert specs["wait"]["description"] == "Esperar. Dura 1 minuto."
    assert specs["sleep_here"]["input_schema"]["required"] == [INTENT]


def test_proposta_pelo_molde_e_sem_molde() -> None:
    moved = proposal_from(TOOLS[2], {"x": 3, "y": 4, INTENT: "ir ao poço"})
    assert moved == {"action": "move", "params": {"target": {"x": 3, "y": 4}}, INTENT: "ir ao poço"}
    planted = proposal_from(
        TOOLS[0], {"target": "plot-e-01", "crop": "rabanete", INTENT: "  plantar\n já "}
    )
    assert planted["params"] == {"target": "plot-e-01", "crop": "rabanete"}
    assert planted[INTENT] == "plantar já"  # espaços e quebras colapsados
    assert proposal_from(TOOLS[4], {})[INTENT] == "sleep_here"  # sem intenção, o nome da ferramenta
    assert len(proposal_from(TOOLS[4], {INTENT: "x" * 900})[INTENT]) == 500


def test_carrega_tools_yaml(tmp_path: Path) -> None:
    path = tmp_path / "tools.yaml"
    path.write_text(
        "tools:\n"
        "  - name: harvest\n    description: Colher.\n    duration: 3\n    energy: 1\n"
        "    params: [{name: target, type: string, description: id do canteiro}]\n"
        "  - name: move_to\n    action: move\n    description: Andar.\n"
        "    params: [{name: x, type: integer, description: coluna}]\n"
        "    shape: {target: {x: $x}}\n",
        encoding="utf-8",
    )
    tools = load_tools(path)
    assert [t.name for t in tools] == ["harvest", "move_to"]
    assert tools[0].action == "harvest"
    assert tools[0].duration_ticks == 3
    assert tools[0].energy == 1
    assert tools[1].action == "move"
    assert tools[1].shape == {"target": {"x": "$x"}}
    path.write_text("tools:\n  - {name: a, description: x}\n  - {name: a, description: y}\n")
    with pytest.raises(ValueError, match="repetidas"):
        load_tools(path)
    path.write_text("tools:\n  - {name: a, description: x, params: [{name: p, type: float}]}\n")
    with pytest.raises(ValueError, match="não suportado"):
        load_tools(path)


def test_a_camada_de_cima_troca_o_cartao() -> None:
    camps = MIND.extend(card="Você é o Camps, da Fazenda do Camps.")
    assert camps.card.startswith("Você é o Camps, da")
    assert camps.notes == MIND.notes
    assert camps.tools == TOOLS
    assert camps.tool("plant") is TOOLS[0]
    assert camps.tool("x") is None


# ------------------------------------------------------------- a janela


async def test_a_foto_abre_a_janela() -> None:
    model = ScriptedModel(
        response(THINKING, tool_use("plant", target="plot-e-01", crop="rabanete", intent="plantar"))
    )
    mind = controller(model)
    proposal = await mind.decide(snapshot())
    assert proposal == {
        "action": "plant",
        "params": {"target": "plot-e-01", "crop": "rabanete"},
        INTENT: "plantar",
    }
    request = model.requests[0]
    assert request.model == "m"
    assert request.effort == "low"
    assert request.purpose == "decision"
    assert request.avatar_id == "camps"
    assert [t["name"] for t in request.tools] == [t.name for t in TOOLS]
    system = cast(Sequence[Mapping[str, Any]], request.system)
    assert system[0]["cache_control"] == {"type": "ephemeral"}
    assert "Você é o Camps." in system[0]["text"]
    assert "O quiosque fecha às 18:00." in system[0]["text"]
    assert INSTRUCTIONS in system[0]["text"]
    assert len(request.messages) == 1
    (block,) = user_blocks(request, 0)
    assert block["type"] == "text"
    assert block["text"].startswith("A sessão começou.\nFoto do mundo no tick 0:\n{")
    assert '"plot-e-01"' in block["text"]
    assert block["cache_control"] == {"type": "ephemeral"}
    assert mind.calls == 1
    assert mind.window.snapshots == 1


async def test_o_delta_e_o_resultado_da_ferramenta_e_o_raciocinio_volta() -> None:
    first = tool_use("plant", target="plot-e-01", crop="rabanete", intent="plantar")
    model = ScriptedModel(
        response(THINKING, first), response(tool_use("wait", ticks=5, intent="esperar"))
    )
    mind = controller(model)
    await mind.decide(snapshot())
    proposal = await mind.decide(delta(0, 5))
    assert proposal == {"action": "wait", "params": {"ticks": 5}, INTENT: "esperar"}
    request = model.requests[1]
    assert [m["role"] for m in request.messages] == ["user", "assistant", "user"]
    assert "cache_control" not in user_blocks(request, 0)[0]  # o marcador andou
    assert request.messages[1]["content"] == [THINKING, first]
    (result,) = user_blocks(request, 2)
    assert result["type"] == "tool_result"
    assert result["tool_use_id"] == first["id"]
    assert "is_error" not in result
    assert result["content"].startswith("Sua ação terminou.\nO que mudou do tick 0 ao 5:\n{")
    assert '"decision"' not in result["content"]
    assert result["cache_control"] == {"type": "ephemeral"}


async def test_a_recusa_vira_erro_com_o_motivo() -> None:
    first = tool_use("plant", target="plot-e-01", crop="rabanete", intent="plantar")
    model = ScriptedModel(
        response(first), response(tool_use("move_near", near="plot-e-01", intent="ir"))
    )
    mind = controller(model)
    await mind.decide(snapshot())
    rejected: dict[str, Any] = {
        "tick": 1,
        "type": "campsverso.action.rejected.v1",
        "data": {
            "avatar_id": "camps",
            "action": "plant",
            "params": {},
            "reason": "not_adjacent",
            "detail": "longe do canteiro",
        },
    }
    proposal = await decided(mind, delta(0, 1, "action_rejected", [rejected]))
    assert proposal["action"] == "move"
    (result,) = user_blocks(model.requests[1], 2)
    assert result["is_error"] is True
    assert result["content"].startswith("Sua ação foi recusada: not_adjacent. longe do canteiro\n")


def test_o_motivo_em_uma_linha() -> None:
    assert reason_text(delta(0, 1, "woke_up")) == "Você acordou."
    assert reason_text(delta(0, 1, "action_rejected")) == "Sua ação foi recusada."
    failed = {"tick": 1, "type": "campsverso.action.failed.v1", "data": {"reason": "fainted"}}
    assert (
        reason_text(delta(0, 1, "action_interrupted", [failed]))
        == "Sua ação foi interrompida: fainted."
    )
    assert reason_text(delta(0, 1, "estranho")) == "Pedido de decisão: estranho."


async def test_a_foto_seguinte_fecha_a_janela() -> None:
    model = ScriptedModel(
        response(tool_use("wait", ticks=1, intent="a")),
        response(tool_use("wait", ticks=1, intent="b")),
        response(tool_use("wait", ticks=1, intent="c")),
    )
    mind = controller(model)
    await mind.decide(snapshot())
    await mind.decide(delta(0, 1))
    await mind.decide(snapshot(20, "possessed"))
    request = model.requests[2]
    assert len(request.messages) == 1
    assert user_blocks(request, 0)[0]["text"].startswith(
        "Você assumiu o corpo.\nFoto do mundo no tick 20:"
    )
    assert mind.window.snapshots == 2
    assert mind.window.deliveries == 3


async def test_resposta_sem_ferramenta_vira_esperar_e_o_turno_seguinte_e_texto() -> None:
    notes = Notes()
    model = ScriptedModel(
        response({"type": "text", "text": "Vou pensar melhor."}, stop="end_turn"),
        response(tool_use("wait", ticks=2, intent="ok")),
    )
    mind = controller(model, notes)
    proposal = await mind.decide(snapshot())
    assert proposal == {"action": "wait", "params": {"ticks": 15}, INTENT: "Vou pensar melhor."}
    assert mind.no_tool == 1
    assert ("info", "mind.no_tool") in notes.events
    await mind.decide(delta(0, 15))
    (block,) = user_blocks(model.requests[1], 2)
    assert block["type"] == "text"  # sem ferramenta aberta, o delta vai como texto
    assert block["text"].startswith("Sua ação terminou.")


async def test_recusa_do_modelo_e_ferramenta_desconhecida() -> None:
    model = ScriptedModel(
        response({"type": "text", "text": ""}, stop="refusal"),
        response(tool_use("voar", intent="x")),
    )
    mind = controller(model)
    assert (await decided(mind, snapshot()))[INTENT] == "sem ação escolhida (refusal)"
    assert (await decided(mind, delta(0, 15)))[INTENT] == "ferramenta desconhecida (voar)"
    assert mind.no_tool == 2


async def test_tres_falhas_seguidas_desistem_e_uma_isolada_nao_perde_a_entrega() -> None:
    notes = Notes()
    timeout = ModelCallError("timeout", "demorou")
    model = ScriptedModel(
        timeout,
        response(tool_use("wait", ticks=1, intent="a")),
        timeout,
        ModelCallError("rate_limit", "429"),
        ModelCallError("auth", "401"),
        response(tool_use("wait", ticks=1, intent="nunca")),
    )
    mind = controller(model, notes)
    proposal = await mind.decide(snapshot())
    assert proposal == {
        "action": "wait",
        "params": {"ticks": 15},
        INTENT: "sem resposta do modelo (timeout)",
    }
    assert mind.failures == 1
    assert not mind.gave_up
    await mind.decide(delta(0, 15))  # a falha não consumiu a foto: ela vai junto com o delta
    (block,) = user_blocks(model.requests[1], 0)
    assert block["text"].startswith("A sessão começou.")
    assert "\n\nSua ação terminou." in block["text"]
    assert mind.failures == 0
    for _ in range(3):
        proposal = await mind.decide(delta(15, 16))
    assert mind.failures == 3
    assert mind.gave_up
    assert proposal is not None
    assert proposal[INTENT] == "sem resposta do modelo (auth)"
    assert ("error", "mind.gave_up") in notes.events
    assert await mind.decide(delta(16, 17)) is None  # desistiu: nem chama o modelo
    assert len(model.requests) == 5


async def test_entregas_superadas_se_acumulam_no_mesmo_turno() -> None:
    first = tool_use("plant", target="plot-e-01", crop="rabanete", intent="plantar")
    model = ScriptedModel(response(first), response(tool_use("wait", ticks=1, intent="x")))
    mind = controller(model)
    await mind.decide(snapshot())
    rejected = {"tick": 1, "type": "campsverso.action.rejected.v1", "data": {"reason": "busy"}}
    mind.observe(delta(0, 1, "action_rejected", [rejected]))  # superada: sem chamada
    await mind.decide(delta(1, 3, "phase_changed"))
    assert len(model.requests) == 2
    (result,) = user_blocks(model.requests[1], 2)
    assert result["tool_use_id"] == first["id"]
    assert result["is_error"] is True  # uma das entregas era uma recusa
    assert "Sua ação foi recusada: busy." in result["content"]
    assert "\n\nA fase do dia mudou.\n" in result["content"]


async def test_ferramentas_extras_sao_ignoradas() -> None:
    first = tool_use("wait", ticks=1, intent="a")
    second = {"type": "tool_use", "id": "toolu_extra", "name": "sleep_here", "input": {INTENT: "b"}}
    model = ScriptedModel(response(first, second), response(tool_use("wait", ticks=1, intent="c")))
    mind = controller(model)
    assert (await decided(mind, snapshot()))["action"] == "wait"
    await mind.decide(delta(0, 1))
    results = user_blocks(model.requests[1], 2)
    assert [r["tool_use_id"] for r in results] == [first["id"], "toolu_extra"]
    assert results[1]["is_error"] is True
    assert results[1]["content"].startswith("Ignorada: uma ação por vez")
    assert results[1]["cache_control"] == {"type": "ephemeral"}


def test_sem_entrega_pendente_nao_ha_pedido() -> None:
    window = Window()
    assert not window.is_open
    with pytest.raises(ValueError, match="nada pendente"):
        window.request_messages()
