"""O perfil da memória de um mundo (o plano do M24, §2.2 e §2.3): o tick, as linhas, o ruído e
a revisão de vários dias. O padrão é a fazenda, que `test_memory.py` e as fitas cobrem."""

from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path
from typing import Any

from campsverso_adapters import SqliteMemory
from campsverso_mind import Clock, Memory, MemoryProfile, MemorySettings, load_profile
from campsverso_mind.memory import REFLECT_TOOL
from campsverso_ports import Episode, ModelResponse, ModelUsage

REVIEW_TOOL: dict[str, Any] = {**REFLECT_TOOL, "name": "revisar"}
OFFICE = MemoryProfile(
    tick_seconds=0.25,
    importance_by_type={
        "campsverso.office.ticket.returned.v1": 9,
        "campsverso.avatar.spoke.v1": 5,
        "campsverso.avatar.spoke.v1:self": 3,
    },
    importance_by_action={},
    lines={
        "campsverso.office.ticket.returned.v1": "{when} {by} devolveu o pedido {number}: {comment}",
        "campsverso.office.ticket.taken.v1:self": "{when} peguei o pedido {number}",
        "campsverso.avatar.spoke.v1": "{when} {avatar_id} disse: {text}",
        "campsverso.avatar.spoke.v1:self": "{when} eu disse: {text}",
    },
    quiet_actions=frozenset({"work", "coffee"}),
    skipped=("campsverso.world.entity.state_changed.",),
    places=False,
    reflected_when="na revisão",
    empty="Primeiro dia no escritório.",
    review_instructions="## A revisão da manhã",
    review_tool=REVIEW_TOOL,
    review_closing="Feche a revisão com a ferramenta revisar.",
)
NINE = 9 * 3600 * 4  # o tick das 09:00, num tick de 250 ms


def office(**settings: Any) -> Memory:
    return Memory(SqliteMemory(":memory:"), "camps", MemorySettings(profile=OFFICE, **settings))


def delivery(day: int, tick: int, hhmm: str, *events: Mapping[str, Any]) -> dict[str, Any]:
    clock = {"tick": tick, "day": day, "sim_time": f"2026-11-{12 + day}T{hhmm}:00-03:00"}
    return {
        "avatar_id": "camps",
        "decision": {"reason": "action_completed"},
        "as_of_tick": tick,
        "view": {
            "clock": clock,
            "self": {"entity_id": "camps", "position": {"x": 4, "y": 5}},
            "entities": [{"entity_id": "quadro", "kind": "board", "position": {"x": 9, "y": 1}}],
            "containers": [],
        },
        "events": list(events),
    }


def test_a_hora_de_um_tick_passado_usa_o_tick_do_mundo() -> None:
    now = Clock(NINE + 3600 * 4, 1, "2026-11-16T10:00:00-03:00", tick_seconds=0.25)
    assert now.at(NINE) == "09:00"
    assert now.at(NINE + 30 * 60 * 4) == "09:30"
    farm = Clock(600, 1, "2026-10-10T10:00:00-03:00")  # um minuto por tick, como sempre
    assert farm.at(540) == "09:00"


def test_o_perfil_conta_o_dia_de_trabalho_nas_palavras_do_escritorio() -> None:
    memory = office()
    memory.observe(
        delivery(
            1,
            NINE + 3600 * 4,
            "10:00",
            {
                "type": "campsverso.office.ticket.returned.v1",
                "tick": NINE + 1800 * 4,
                "data": {
                    "ticket_id": "pedido-003",
                    "number": 3,
                    "by": "gerente",
                    "comment": "falta o caso vazio",
                },
            },
            {
                "type": "campsverso.office.ticket.taken.v1",
                "tick": NINE,
                "data": {"by": "camps", "number": 3},
            },
            {
                "type": "campsverso.avatar.spoke.v1",
                "tick": NINE,
                "data": {"avatar_id": "gerente", "text": "Bom dia"},
            },
            {
                "type": "campsverso.avatar.spoke.v1",
                "tick": NINE,
                "data": {"avatar_id": "camps", "text": "Bom dia!"},
            },
            {
                "type": "campsverso.action.completed.v1",
                "tick": NINE,
                "data": {"action": "coffee", "params": {}},
            },
            {
                "type": "campsverso.action.rejected.v1",
                "tick": NINE,
                "data": {"action": "work", "reason": "done"},
            },
            {
                "type": "campsverso.world.entity.state_changed.v1",
                "tick": NINE,
                "data": {"entity_id": "pedido-003"},
            },
            {
                "type": "campsverso.action.completed.v1",
                "tick": NINE,
                "data": {"action": "deliver", "params": {}},
            },
        )
    )
    lines = {(e.text, e.importance) for e in memory.port.episodes(1)}
    assert lines == {
        ("09:30 gerente devolveu o pedido 3: falta o caso vazio", 9),
        ("09:00 peguei o pedido 3", 1),
        ("09:00 gerente disse: Bom dia", 5),
        ("09:00 eu disse: Bom dia!", 3),
        ("09:00 fiz deliver {}", 3),  # fora da rotina: conta, com o peso de sempre
    }
    assert memory.port.places() == []  # a sala não tem raio: nada a lembrar de onde fica


def test_as_acoes_dos_outros_ficam_de_fora_quando_o_perfil_pede() -> None:
    accepted: dict[str, Any] = {
        "type": "campsverso.action.completed.v1",
        "tick": NINE,
        "data": {"avatar_id": "gerente", "action": "accept_ticket", "params": {}},
    }
    mine: dict[str, Any] = {
        "type": "campsverso.action.completed.v1",
        "tick": NINE,
        "data": {"avatar_id": "camps", "action": "accept_ticket", "params": {}},
    }
    quiet = Memory(
        SqliteMemory(":memory:"),
        "camps",
        MemorySettings(profile=replace(OFFICE, others_actions=False)),
    )
    quiet.observe(delivery(1, NINE, "09:00", accepted, mine))
    assert [e.text for e in quiet.port.episodes(1)] == ["09:00 fiz accept_ticket {}"]
    farm = office()  # o padrão conta todas, como a fazenda sempre contou
    farm.observe(delivery(1, NINE, "09:00", accepted))
    assert [e.text for e in farm.port.episodes(1)] == ["09:00 fiz accept_ticket {}"]


def test_a_anotacao_e_o_episodio_que_a_mente_conta() -> None:
    memory = office()
    clock = Clock(NINE + 600 * 4, 1, "2026-11-13T09:10:00-03:00", tick_seconds=0.25)
    assert memory.write_note(clock, "  Os testes do tools/ rodam com\n o pytest. ") == (
        "Os testes do tools/ rodam com o pytest."
    )
    assert memory.write_note(clock, "   ") == ""
    memory.record(
        clock, "trabalhei no pedido 3 na oficina, em 12 passos", 7, "workshop", ("pedido-003",)
    )
    (episode,) = memory.port.episodes(1)
    assert (episode.text, episode.importance, episode.tags) == (
        "09:10 trabalhei no pedido 3 na oficina, em 12 passos",
        7,
        ("pedido-003",),
    )
    (noted,) = memory.drain_events()
    assert noted["type"] == "campsverso.memory.noted.v1"
    block = memory.block(clock)
    assert "Os testes do tools/ rodam com o pytest." in block
    assert "Primeiro dia" not in block
    assert office().block(clock) == "## O que você lembra\nPrimeiro dia no escritório."


def _worked(memory: Memory, *days: int) -> None:
    for day in days:
        memory.port.record(Episode(day * 100, day, f"09:00 trabalhei no dia {day}", 7, "workshop"))


def test_a_revisao_da_manha_olha_ate_o_ultimo_dia_revisto() -> None:
    memory = office()
    _worked(memory, 1, 2)  # quinta e sexta; sábado e domingo sem nada
    monday = Clock(500, 5, "2026-11-16T09:00:00-03:00", tick_seconds=0.25)
    assert memory.pending_days(monday) == [1, 2]
    assert memory.pending_days(Clock(100, 1, "", tick_seconds=0.25)) == []  # o primeiro dia
    many = office()
    _worked(many, 1, 2, 3, 4, 5)
    assert many.pending_days(Clock(700, 6, "", tick_seconds=0.25)) == [3, 4, 5]  # até três
    # Duas tentativas que falham, e a mesma revisão não volta nesta execução.
    many.attempted(5)
    many.attempted(5)
    assert many.pending_days(Clock(700, 6, "", tick_seconds=0.25)) == []


def test_a_revisao_de_varios_dias_e_guardada_no_mais_novo() -> None:
    memory = office()
    _worked(memory, 1, 2)
    memory.write_note(
        Clock(250, 2, "2026-11-14T09:10:00-03:00", tick_seconds=0.25),
        "O gerente quer o caso vazio.",
    )
    monday = Clock(500, 5, "2026-11-16T09:00:00-03:00", tick_seconds=0.25)
    request = memory.review_request("Você é o Camps.", monday, [1, 2], "claude-sonnet-5-5")
    text = request.messages[0]["content"][0]["text"]
    assert text.startswith("Dia 1. O que aconteceu, na ordem:\n- 09:00 trabalhei no dia 1")
    assert "Dia 2. O que aconteceu" in text
    assert "O que você anotou no dia 2:" in text
    assert text.endswith("Feche a revisão com a ferramenta revisar.")
    assert [t["name"] for t in request.tools] == ["revisar"]
    assert request.purpose == "reflection"
    system = request.system
    assert isinstance(system, list)
    assert "## A revisão da manhã" in str(system[0]["text"])
    given = {
        "summary": "Entreguei o pedido 3 e o gerente devolveu; corrigi e ele aceitou.",
        "plan": "Cobrir o caso vazio.",
        "beliefs": [
            {
                "id": "",
                "statement": "O gerente devolve pedido sem o caso vazio.",
                "confidence": 0.7,
                "evidence": ["pedido 3"],
                "status": "new",
                "reason": "",
            }
        ],
    }
    response = ModelResponse(
        content=[{"type": "tool_use", "id": "t1", "name": "revisar", "input": given}],
        stop_reason="tool_use",
        usage=ModelUsage(10, 5),
        model="claude-sonnet-5-5",
        latency_ms=1,
    )
    memory.drain_events()
    reflection = memory.apply_reflection(request, response, monday, 2, [1, 2])
    assert reflection is not None
    assert reflection.day == 2
    reflected = memory.drain_events()[0]
    assert reflected["type"] == "campsverso.memory.reflected.v1"
    assert (reflected["data"]["day"], reflected["data"]["days"]) == (2, [1, 2])
    assert memory.pending_days(monday) == []
    block = memory.block(monday)
    assert "Dia 2, na revisão: Entreguei o pedido 3" in block
    assert "Plano: Cobrir o caso vazio." in block


def test_o_perfil_do_arquivo(tmp_path: Path) -> None:
    path = tmp_path / "memoria.yaml"
    path.write_text(
        "tick_seconds: 0.25\nplaces: false\nquiet_actions: [work]\n"
        "skipped: [campsverso.world.clock.]\n"
        "importance: {events: {a: 2}, actions: {}}\nlines: {a: '{when} a'}\n"
        "review: {days: 2, closing: 'Feche.', instructions: 'Reveja.', tool: {name: revisar}}\n"
        "note_tool: {name: anotar}\n",
        encoding="utf-8",
    )
    profile = load_profile(path)
    assert profile.tick_seconds == 0.25
    assert not profile.places
    assert profile.quiet_actions == {"work"}
    assert profile.skipped == ("campsverso.world.clock.",)
    assert profile.importance_by_type == {"a": 2}
    assert profile.importance_by_action == {}
    assert (profile.review_days, profile.review_closing, profile.review_instructions) == (
        2,
        "Feche.",
        "Reveja.",
    )
    assert profile.note_tool == {"name": "anotar"}
    assert profile.reflected_when == "ao dormir"  # o que o arquivo não diz é o da fazenda
    assert MemoryProfile().importance_by_type is None
