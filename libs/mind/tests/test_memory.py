"""A memória da mente (ADR-0060): episódios, anotações, o bloco de abertura, a reflexão."""

from collections.abc import Mapping, Sequence
from typing import Any, cast

from campsverso_adapters import SqliteMemory
from campsverso_mind import (
    NOTE,
    Clock,
    LlmController,
    Memory,
    MemorySettings,
    Mind,
    ParamDef,
    ToolDef,
    clock_of,
)
from campsverso_mind.memory import REFLECT
from campsverso_mind.memory import clock_of as _clock_of
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
        "Plantar.",
        (ParamDef("target", "string", "canteiro"), ParamDef("crop", "string", "cultura")),
    ),
    ToolDef("move_near", "move", "Andar.", (ParamDef("near", "string", "id"),)),
    ToolDef("wait", "wait", "Esperar.", (ParamDef("ticks", "integer", "minutos"),)),
    ToolDef("sleep_here", "sleep", "Dormir aqui.", shape={}),
)
MIND = Mind("teste", "Você é o Camps.", "Notas.", TOOLS)


def tool_use(name: str, **given: Any) -> dict[str, Any]:
    return {"type": "tool_use", "id": f"toolu_{name}_{len(given)}", "name": name, "input": given}


def response(*content: Mapping[str, Any], stop: str = "tool_use") -> ModelResponse:
    return ModelResponse(
        content=list(content), stop_reason=stop, usage=ModelUsage(10, 5), model="m", latency_ms=1
    )


class ScriptedModel:
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


def snapshot(reason: str = "session_started") -> dict[str, Any]:
    return {
        "avatar_id": "camps",
        "kind": "snapshot",
        "as_of_tick": 0,
        "decision": {"reason": reason, "controller": {"type": "llm", "id": "llm/camps"}},
        "view": {
            "clock": {"tick": 0, "sim_time": "2026-10-10T06:00:00-03:00", "day": 1, "phase": "m"},
            "weather": {"condition": "sun", "day": 1},
            "self": {"entity_id": "camps", "position": {"x": 1, "y": 1}, "needs": {}},
            "containers": [],
            "entities": [],
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
        "clock": {"tick": tick, "sim_time": "2026-10-10T06:05:00-03:00", "day": 1, "phase": "m"},
        "self": {"entity_id": "camps", "position": {"x": 2, "y": 1}, "needs": {}},
        "events": list(events),
    }


SIM = "2026-10-10T08:00:00-03:00"  # tick 120 do dia 1


def memory(**settings: Any) -> Memory:
    return Memory(SqliteMemory(":memory:"), "camps", MemorySettings(**settings))


def with_clock(
    delivery: dict[str, Any], tick: int, day: int = 1, sim_time: str = SIM
) -> dict[str, Any]:
    clock = {"tick": tick, "sim_time": sim_time, "day": day, "phase": "manha"}
    if "view" in delivery:
        delivery["view"]["clock"] = clock
        delivery["as_of_tick"] = tick
    else:
        delivery["clock"] = clock
        delivery["as_of_tick"] = tick
    return delivery


def event(tick: int, kind: str, **data: Any) -> dict[str, Any]:
    return {"tick": tick, "type": f"campsverso.{kind}", "data": data}


def reflect_use(summary: str, plan: str, *beliefs: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "tool_use",
        "id": "toolu_reflect",
        "name": REFLECT,
        "input": {"summary": summary, "plan": plan, "beliefs": list(beliefs)},
    }


def controller(
    model: ScriptedModel, mem: Memory | None, notes: Notes | None = None
) -> LlmController:
    return LlmController(
        MIND,
        model,
        controller_id="llm/camps",
        avatar_id="camps",
        model="m",
        telemetry=notes,
        memory=mem,
    )


# ------------------------------------------------------------- registrar


def test_o_relogio_de_uma_entrega_e_a_hora_de_um_tick() -> None:
    clock = clock_of(with_clock(delta(100, 120), 120))
    assert clock == Clock(120, 1, SIM)
    assert clock.at(120) == "08:00"
    assert clock.at(65) == "07:05"
    assert Clock(5, 1, "").at(3) == "t3"
    assert _clock_of(with_clock(snapshot(), 7)).tick == 7


def test_o_delta_vira_episodios_com_importancia_por_tabela() -> None:
    mem = memory()
    events = [
        event(100, "action.accepted.v1", action="plant", params={}),  # repete a proposta: fora
        event(101, "world.entity.moved.v1", entity_id="camps"),  # ruído: fora
        event(
            105,
            "action.completed.v1",
            action="harvest",
            params={"target": "plot-e-01"},
            duration_ticks=3,
        ),
        event(
            110,
            "action.rejected.v1",
            action="buy",
            params={"item": "semente_batata"},
            reason="closed",
            detail="fecha às 18:00",
        ),
        event(115, "avatar.fainted.v1", reason="late_night"),
        event(118, "farm.crop.matured.v1", plot_id="plot-e-02", days=2),
        event(119, "world.clock.phase_changed.v1", phase="meio_dia", day=1),
        event(
            120,
            "world.item.transferred.v1",
            item="moeda",
            qty=25,
            from_container="buyer",
            to_container="camps",
        ),
    ]
    mem.observe(with_clock(delta(100, 120, events=events), 120))
    episodes = mem.port.episodes(1)
    assert [(e.text, e.importance, e.kind) for e in episodes] == [
        ('07:45 fiz harvest {"target":"plot-e-01"}', 7, "action.completed"),
        (
            '07:50 recusado buy {"item":"semente_batata"}: closed (fecha às 18:00)',
            6,
            "action.rejected",
        ),
        ("07:55 desmaiei (late_night)", 10, "avatar.fainted"),
        ("07:58 plot-e-02 amadureceu em 2 dias", 7, "farm.crop.matured"),
        ("07:59 fase do dia: meio_dia", 2, "world.clock.phase_changed"),
        (
            "08:00 world.item.transferred "
            '{"from_container":"buyer","item":"moeda","qty":25,"to_container":"camps"}',
            1,
            "world.item.transferred",
        ),
    ]
    assert episodes[0].tags == ("plot-e-01",)
    assert episodes[3].tags == ("plot-e-02",)


def test_a_foto_registra_o_inicio_e_a_proposta_registra_a_anotacao() -> None:
    mem = memory()
    clock = mem.observe(with_clock(snapshot(reason="possessed"), 120))
    assert [e.text for e in mem.port.episodes(1)] == ["08:00 assumi o corpo"]
    mem.proposed(
        clock,
        {
            "action": "plant",
            "params": {"target": "plot-w-01", "crop": "rabanete"},
            "intent": "plantar",
        },
        "  o poço\nfica longe ",
    )
    mem.proposed(clock, {"action": "sleep", "params": {"target": "bed"}, "intent": "dormir"}, "")
    assert [e.text for e in mem.port.episodes(1)][1:] == [
        '08:00 propus plant {"crop":"rabanete","target":"plot-w-01"}: plantar',
        '08:00 propus sleep {"target":"bed"}: dormir',
    ]
    assert mem.port.episodes(1)[1].importance == 3
    assert [n.text for n in mem.port.notes(1)] == ["o poço fica longe"]
    assert mem.drain_events() == [
        {
            "type": "campsverso.memory.noted.v1",
            "data": {"avatar_id": "camps", "day": 1, "text": "o poço fica longe"},
        }
    ]
    assert mem.drain_events() == []
    assert mem.last_proposal == 'sleep {"target":"bed"}: dormir'
    assert mem.reflect_due == clock  # propor dormir marca a reflexão


# ------------------------------------------------------------- lembrar


def test_o_bloco_vazio_e_o_bloco_cheio() -> None:
    mem = memory(block_salient=2)
    clock = Clock(120, 1, SIM)
    assert (
        mem.block(clock)
        == "## O que você lembra\nO caderno ainda está vazio: é o seu primeiro dia."
    )
    mem.observe(
        with_clock(
            delta(
                0,
                120,
                events=[
                    event(10, "action.completed.v1", action="water", params={}),
                    event(100, "avatar.fainted.v1", reason="exhausted"),
                    event(119, "action.completed.v1", action="move", params={}),
                ],
            ),
            120,
        )
    )
    mem.proposed(
        clock,
        {"action": "eat", "params": {"item": "rabanete"}, "intent": "comer"},
        "estou com fome cedo",
    )
    request = mem.reflect_request("Você é o Camps.", clock, 1, "m")
    mem.apply_reflection(
        request,
        response(
            reflect_use(
                "Dia duro.",
                "Dormir cedo.",
                {
                    "id": "",
                    "statement": "Desmaio quando a energia zera.",
                    "confidence": 0.8,
                    "evidence": ["07:40 desmaiei"],
                    "status": "new",
                    "reason": "vi",
                },
            )
        ),
        clock,
        1,
    )
    block = mem.block(Clock(130, 1, "2026-10-10T08:10:00-03:00"))
    assert block.splitlines() == [
        "## O que você lembra",
        "Dia 1, ao dormir: Dia duro.",
        "Plano: Dormir cedo.",
        "Crenças (confiança de 0 a 1):",
        "- bel-0001 (0.80): Desmaio quando a energia zera.",
        "Anotações de hoje (dia 1):",
        "- 08:00 estou com fome cedo",
        "Momentos de hoje:",
        "- 07:40 desmaiei (exhausted)",
        '- 08:00 propus eat {"item":"rabanete"}: comer',
        'Última ação: eat {"item":"rabanete"}: comer',
    ]


# ------------------------------------------------------------- refletir


def test_o_pedido_da_reflexao_leva_o_dia_as_anotacoes_e_as_crencas() -> None:
    mem = memory(reflection_effort="high", reflection_max_tokens=99, reflection_model="r")
    clock = Clock(900, 1, "2026-10-10T21:00:00-03:00")
    mem.observe(
        with_clock(
            delta(
                0,
                900,
                events=[
                    event(
                        300,
                        "action.completed.v1",
                        action="plant",
                        params={"target": "plot-w-01", "crop": "rabanete"},
                    )
                ],
            ),
            900,
            sim_time="2026-10-10T21:00:00-03:00",
        )
    )
    mem.proposed(clock, {"action": "sleep", "params": {}, "intent": "dormir"}, "amanhã regar")
    request = mem.reflect_request("CARTÃO", clock, 1, "m")
    assert (
        request.model,
        request.effort,
        request.max_tokens,
        request.purpose,
        request.avatar_id,
    ) == ("r", "high", 99, "reflection", "camps")
    system = cast(Sequence[Mapping[str, Any]], request.system)
    assert system[0]["text"].startswith("CARTÃO\n\n## A reflexão da noite")
    assert system[0]["cache_control"] == {"type": "ephemeral"}
    assert [t["name"] for t in request.tools] == [REFLECT]
    text = cast(Sequence[Mapping[str, Any]], request.messages[0]["content"])[0]["text"]
    assert text.splitlines() == [
        "Dia 1. O que aconteceu, na ordem:",
        '- 11:00 fiz plant {"crop":"rabanete","target":"plot-w-01"}',
        "- 21:00 propus sleep {}: dormir",
        "O que você anotou:",
        "- 21:00 amanhã regar",
        "As crenças que você já tinha:",
        "- (nenhuma)",
        "Feche o dia com a ferramenta reflect.",
    ]


def test_a_reflexao_vira_crencas_e_eventos_na_ordem() -> None:
    mem = memory()
    clock = Clock(900, 1, "2026-10-10T21:00:00-03:00")
    first = mem.reflect_request("x", clock, 1, "m")
    assert (
        mem.apply_reflection(
            first, response({"type": "text", "text": "sem ferramenta"}, stop="end_turn"), clock, 1
        )
        is None
    )
    reflection = mem.apply_reflection(
        first,
        response(
            reflect_use(
                "Plantei.",
                "",
                {
                    "id": "",
                    "statement": " Rega  diária ",
                    "confidence": 1.7,
                    "evidence": ["09:00 reguei", ""],
                    "status": "estranho",
                    "reason": "",
                },
                {
                    "id": "",
                    "statement": "",
                    "confidence": 0.5,
                    "evidence": [],
                    "status": "new",
                    "reason": "",
                },
            )
        ),
        clock,
        1,
    )
    assert reflection is not None
    assert (reflection.summary, reflection.plan) == ("Plantei.", None)
    assert [(b.statement, b.confidence, b.evidence, b.status) for b in reflection.beliefs] == [
        ("Rega diária", 1.0, ("09:00 reguei",), "confirmed")
    ]
    events = mem.drain_events()
    assert [e["type"] for e in events] == [
        "campsverso.memory.reflected.v1",
        "campsverso.memory.belief.formed.v1",
    ]
    assert events[0]["data"] == {
        "avatar_id": "camps",
        "day": 1,
        "summary": "Plantei.",
        "beliefs": {"formed": 1, "updated": 0, "retracted": 0, "total": 1},
        "prompt_sha256": reflection.prompt_sha256,
    }
    assert events[1]["data"] == {
        "avatar_id": "camps",
        "belief_id": "bel-0001",
        "statement": "Rega diária",
        "evidence": ["09:00 reguei"],
        "source": {"kind": "observation"},
        "confidence": 1.0,
    }
    assert mem.port.has_reflection(1)
    assert mem.reflect_due is None
    later = Clock(2340, 2, "2026-10-11T21:00:00-03:00")
    second = mem.reflect_request("x", later, 2, "m")
    mem.apply_reflection(
        second,
        response(
            reflect_use(
                "Reguei.",
                "Vender.",
                {
                    "id": "bel-0001",
                    "statement": "Rega diária",
                    "confidence": 0.6,
                    "evidence": ["choveu"],
                    "status": "weakened",
                    "reason": "a chuva regou",
                },
                {
                    "id": "",
                    "statement": "O leste amadurece antes.",
                    "confidence": 0.5,
                    "evidence": ["plot-e-01 em 2 dias"],
                    "status": "new",
                    "reason": "",
                },
            )
        ),
        later,
        2,
    )
    events = mem.drain_events()
    assert [e["type"] for e in events] == [
        "campsverso.memory.reflected.v1",
        "campsverso.memory.belief.updated.v1",
        "campsverso.memory.belief.formed.v1",
    ]
    assert events[1]["data"]["confidence"] == {"before": 1.0, "after": 0.6}
    assert events[1]["data"]["reason"] == "a chuva regou"
    assert events[0]["data"]["plan"] == "Vender."
    assert events[0]["data"]["beliefs"] == {"formed": 1, "updated": 1, "retracted": 0, "total": 2}


def test_um_dia_sem_reflexao_fica_pendente_para_a_manha() -> None:
    mem = memory()
    assert (
        mem.pending_day(Clock(1500, 2, "2026-10-11T07:00:00-03:00")) is None
    )  # dia 1 sem episódios
    mem.observe(
        with_clock(
            delta(0, 100, events=[event(50, "action.completed.v1", action="wait", params={})]), 100
        )
    )
    assert mem.pending_day(Clock(100, 1, SIM)) is None  # ainda é o dia 1
    assert mem.pending_day(Clock(1500, 2, "2026-10-11T07:00:00-03:00")) == 1
    clock = Clock(1500, 2, "2026-10-11T07:00:00-03:00")
    mem.apply_reflection(
        mem.reflect_request("x", clock, 1, "m"), response(reflect_use("ok", "")), clock, 1
    )
    assert mem.pending_day(clock) is None


# ------------------------------------------------------------- a mente com memória


async def test_a_mente_abre_a_janela_com_o_bloco_e_reflete_depois_de_dormir() -> None:
    notes = Notes()
    model = ScriptedModel(
        response(
            tool_use(
                "plant",
                target="plot-w-01",
                crop="rabanete",
                intent="plantar",
                note="o w-01 é perto da casa",
            )
        ),
        response(tool_use("sleep_here", intent="dormir", note="")),
        response(
            reflect_use(
                "Plantei um canteiro.",
                "Regar.",
                {
                    "id": "",
                    "statement": "Plantar perto da casa poupa tempo.",
                    "confidence": 0.6,
                    "evidence": ["08:00 plantei o w-01"],
                    "status": "new",
                    "reason": "",
                },
            )
        ),
        response(tool_use("wait", ticks=5, intent="esperar", note="")),
    )
    mind = controller(model, memory(), notes)
    proposal = await mind.decide(with_clock(snapshot(), 120))
    assert all(NOTE in t["input_schema"]["required"] for t in model.requests[0].tools)
    assert proposal == {
        "action": "plant",
        "params": {"target": "plot-w-01", "crop": "rabanete"},
        "intent": "plantar",
    }
    opening = cast(Sequence[Mapping[str, Any]], model.requests[0].messages[0]["content"])[0]["text"]
    first = "## O que você lembra\nMomentos de hoje:\n- 08:00 a sessão começou\n\nA sessão começou."
    assert opening.startswith(first)  # o bloco abre a janela, e o começo já é um momento
    assert mind.drain_events() == [
        {
            "type": "campsverso.memory.noted.v1",
            "data": {"avatar_id": "camps", "day": 1, "text": "o w-01 é perto da casa"},
        }
    ]
    await mind.after_proposal()  # sem sono proposto: nada
    assert mind.reflections == 0
    await mind.decide(with_clock(delta(120, 125), 125))  # propõe dormir
    assert len(model.requests) == 2
    await mind.after_proposal()  # a reflexão da noite
    assert mind.reflections == 1
    assert len(model.requests) == 3
    assert model.requests[2].purpose == "reflection"
    events = mind.drain_events()
    assert [e["type"] for e in events] == [
        "campsverso.memory.reflected.v1",
        "campsverso.memory.belief.formed.v1",
    ]
    assert "mind.reflected" in [e for _, e in notes.events]
    await mind.after_proposal()  # já refletiu hoje: nada
    assert len(model.requests) == 3
    # A manhã seguinte abre com o resumo, o plano e a crença.
    await mind.decide(
        with_clock(snapshot(reason="woke_up"), 1500, day=2, sim_time="2026-10-11T07:00:00-03:00")
    )
    opening = cast(Sequence[Mapping[str, Any]], model.requests[3].messages[0]["content"])[0]["text"]
    assert "Dia 1, ao dormir: Plantei um canteiro." in opening
    assert "Plano: Regar." in opening
    assert "- bel-0001 (0.60): Plantar perto da casa poupa tempo." in opening


async def test_a_noite_sem_sono_reflete_de_manha_e_a_falha_da_reflexao_nao_derruba() -> None:
    model = ScriptedModel(
        response(tool_use("wait", ticks=60, intent="esperar", note="")),
        ModelCallError("timeout", "demorou"),  # a reflexão da manhã falha
        response(tool_use("wait", ticks=5, intent="esperar", note="")),
    )
    mind = controller(model, memory())
    await mind.decide(with_clock(snapshot(), 120))
    await mind.decide(
        with_clock(
            delta(120, 1500, reason="woke_up"), 1500, day=2, sim_time="2026-10-11T07:00:00-03:00"
        )
    )
    assert [r.purpose for r in model.requests] == ["decision", "reflection", "decision"]
    assert mind.reflections == 0
    assert mind.failures == 0  # a reflexão não conta como falha da decisão
    assert not mind.memory.port.has_reflection(1)  # type: ignore[union-attr]


async def test_sem_memoria_nada_muda() -> None:
    model = ScriptedModel(response(tool_use("wait", ticks=5, intent="esperar")))
    mind = controller(model, None)
    await mind.decide(with_clock(snapshot(), 120))
    assert NOTE not in model.requests[0].tools[0]["input_schema"]["properties"]
    assert cast(Sequence[Mapping[str, Any]], model.requests[0].messages[0]["content"])[0][
        "text"
    ].startswith("A sessão começou.")
    await mind.after_proposal()
    assert mind.drain_events() == []
