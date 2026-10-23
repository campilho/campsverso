"""O ciclo de decisão inteiro em memória: kernel, percepção e controladores (plano do M3 §5)."""

import json
from collections.abc import Mapping, Sequence
from typing import Any

import pytest

from campsverso_controller_runner.replay import recorded_proposals
from campsverso_kernel.replay import DayReplay, replay_day
from campsverso_ports import Envelope
from campsverso_testkit.hashing import canonical_hash
from campsverso_testkit.pipeline import DAY, Pipeline

HIDDEN = ("growth_points", "planted_day", "dry_days", "payee")  # atributos ocultos da fazenda
WORLDS = ("farm_camps", "farm_boavista", "farm_morada_do_sol")  # as três fazendas (ADR-0067)


async def test_dois_dias_do_script_pelo_ciclo_completo() -> None:
    pipeline = Pipeline()
    await pipeline.start()
    await pipeline.run_days(2)
    decisions = pipeline.of_type("avatar.decision_requested.v1")
    perceptions = pipeline.of_type("perception.delivered.v1")
    proposals = pipeline.of_type("cmd.action.propose.v1")
    assert len(decisions) == len(perceptions) == len(proposals) > 100
    assert pipeline.of_type("action.rejected.v1") == []
    assert pipeline.of_type("avatar.fainted.v1") == []
    actions = {a["action"] for a in pipeline.of_type("action.completed.v1")}
    assert {"plant", "water", "eat", "sleep", "buy"} <= actions
    views = json.dumps([p["view"] for p in perceptions])
    assert not any(name in views for name in HIDDEN)  # nada oculto chega à foto (princípio 5)


def _hash(envelopes: Sequence[Envelope]) -> str:
    return canonical_hash(sorted(envelopes, key=lambda e: (str(e["source"]), int(e["seq"]))))


@pytest.mark.parametrize("cartridge", WORLDS)
async def test_a4_mesma_seed_mesmo_hash_pelo_ciclo_inteiro(cartridge: str) -> None:
    runs: list[str] = []
    for seed in (20261010, 20261010, 7):
        pipeline = Pipeline(seed, cartridge=cartridge)
        await pipeline.start()
        await pipeline.run_days(3)
        runs.append(_hash(pipeline.envelopes))  # kernel, percepção e comandos do script
    assert runs[0] == runs[1]
    assert runs[0] != runs[2]


# ----------------------------------------------------------------- posse (A9)


def _control(pipeline: Pipeline, command: str, data: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "specversion": "1.0",
        "id": pipeline.ids.new_id(),
        "source": "/operator/teste",
        "type": f"campsverso.cmd.{command}.v1",
        "time": "2026-10-12T01:00:00Z",
        "datacontenttype": "application/json",
        "dataschema": f"contracts://commands/{command.replace('.', '/', 1)}.v1",
        "worldid": "farm-camps-01",
        "cartridge": "farm_camps",
        "seq": 0,
        "actor": "human/operador",
        "provenance": "simulated",
        "visibility": "observer",
        "data": dict(data),
    }


def _propose(pipeline: Pipeline, controller: str, action: str, **params: Any) -> dict[str, Any]:
    envelope = _control(pipeline, "action.propose", {"avatar_id": "camps", "action": action})
    envelope["data"]["params"] = params
    envelope["controller"], envelope["controllerid"] = controller.split("/")[0], controller
    return envelope


async def _send(pipeline: Pipeline, envelope: Mapping[str, Any]) -> None:
    command = str(envelope["type"]).removeprefix("campsverso.cmd.").removesuffix(".v1")
    await pipeline.bus.publish(f"campsverso.farm-camps-01.cmd.{command}.v1", envelope)


async def test_a9_humano_assume_joga_e_devolve() -> None:
    pipeline = Pipeline()
    await pipeline.start()
    await pipeline.run_until(600)
    human = {"type": "human", "id": "human/camps-browser"}
    await _send(
        pipeline, _control(pipeline, "avatar.possess", {"avatar_id": "camps", "controller": human})
    )
    rejected = pipeline.of_type("world.command.rejected.v1")
    assert rejected[-1]["reason"] == "mode_not_allowed"  # no modo máximo, humano não entra
    await _send(pipeline, _control(pipeline, "clock.set_mode", {"mode": "continuous"}))
    await _send(
        pipeline, _control(pipeline, "avatar.possess", {"avatar_id": "camps", "controller": human})
    )
    await pipeline.run_until(pipeline.core.tick + 30)
    answered = len(pipeline.of_type("cmd.action.propose.v1"))
    await _send(pipeline, _propose(pipeline, "script/farmer-v1", "wait", ticks=1))
    await pipeline.run_until(pipeline.core.tick + 1)
    assert pipeline.of_type("action.rejected.v1")[-1]["reason"] == "not_in_control"
    await _send(pipeline, _propose(pipeline, "human/camps-browser", "move", near="well"))
    await pipeline.run_until(pipeline.core.tick + 1)
    assert pipeline.of_type("action.accepted.v1")[-1]["action"] == "move"
    assert len(pipeline.of_type("cmd.action.propose.v1")) == answered + 2  # o script calou
    await _send(pipeline, _control(pipeline, "avatar.release", {"avatar_id": "camps"}))
    await _send(
        pipeline, _control(pipeline, "clock.set_mode", {"mode": "max", "reason": "experiment"})
    )
    await pipeline.run_until(pipeline.core.tick + 120)
    script = [p for p in pipeline.of_type("cmd.action.propose.v1") if p["avatar_id"] == "camps"]
    assert len(script) > answered + 2  # o script voltou a decidir


# ----------------------------------------------------------------- controlador replay


def _world(envelopes: Sequence[Envelope], until: int) -> list[tuple[Any, ...]]:
    """Fatos do kernel que não dependem de quem controla (posse e pedidos dizem o controlador)."""
    skip = {"avatar.possessed.v1", "avatar.decision_requested.v1", "world.snapshot.created.v1"}
    return [
        (e["seq"], e["tick"], e["type"], json.dumps(e["data"], sort_keys=True))
        for e in envelopes
        if str(e["source"]).startswith("/kernel/")
        and str(e["type"]).removeprefix("campsverso.") not in skip
        and int(e["tick"]) < until
    ]


@pytest.mark.parametrize("cartridge", WORLDS)
async def test_replay_reproduz_a_sessao_gravada(cartridge: str) -> None:
    original = Pipeline(cartridge=cartridge)
    await original.start()
    await original.run_days(1)
    recording = recorded_proposals(original.envelopes, "camps")
    assert len(recording) > 50
    replay = Pipeline(controller="replay", recording=recording, cartridge=cartridge)
    await replay.start()
    await replay.run_until(DAY)
    assert _world(replay.envelopes, DAY) == _world(original.envelopes, DAY)
    assert replay.core.world.items("camps") == original.core.world.items("camps")


# ----------------------------------------------------------------- replay de um dia (A5)


@pytest.mark.parametrize("cartridge", WORLDS)
async def test_a5_reexecutar_um_dia_reproduz_o_arquivo(cartridge: str) -> None:
    pipeline = Pipeline(cartridge=cartridge)
    await pipeline.start()
    await pipeline.run_days(3)
    core = pipeline.core

    def replay(day: int, archive: Sequence[Envelope]) -> DayReplay:
        return replay_day(
            core.definition,
            core.config,
            pipeline.version,
            pipeline.store,
            pipeline.blobs,
            archive,
            day,
            pipeline.validator,
        )

    for day in (1, 2, 3):
        result = replay(day, pipeline.envelopes)
        assert result.equal, result.first_difference()
        assert len(result.recorded) > 100
    tampered = [dict(e) for e in pipeline.envelopes]
    harvest = next(e for e in tampered if e["type"] == "campsverso.action.completed.v1")
    harvest["data"] = {**harvest["data"], "duration_ticks": 99}
    assert not replay(1, tampered).equal
