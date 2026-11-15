"""A guarda no pipeline em memória (ADR-0058): chamadas cobradas estouram o teto e o kernel para."""

from typing import Any

from campsverso_adapters import MemoryBlobStore
from campsverso_budget.ledger import BudgetLimits
from campsverso_budget.service import (
    COMPLETED,
    EXCEEDED,
    LIMITS_CHANGED,
    PAUSE,
    PULSE,
    SET,
    THRESHOLD,
    BudgetService,
)
from campsverso_contracts import subject
from campsverso_testkit.farm import WORLD
from campsverso_testkit.pipeline import Pipeline

RESUME = "campsverso.cmd.clock.resume.v1"
LIMITS = BudgetLimits(usd_per_sim_day=0.6, usd_total=10.0)


def _call(
    pipeline: Pipeline,
    seq: int,
    tick: int,
    cost: float,
    *,
    charged: bool = True,
    ticket_id: str | None = None,
) -> dict[str, Any]:
    envelope: dict[str, Any] = {
        "specversion": "1.0",
        "id": pipeline.ids.new_id(),
        "source": "/controller-runner/llm/haiku",
        "type": COMPLETED,
        "time": "2026-10-18T03:00:00Z",
        "datacontenttype": "application/json",
        "dataschema": "contracts://events/llm/call.completed.v1",
        "worldid": WORLD,
        "cartridge": "farm_camps",
        "tick": tick,
        "simtime": "2026-10-10T06:10:00-03:00",
        "seq": seq,
        "provenance": "simulated",
        "visibility": "observer",
        "actor": "system/controller-runner",
        "data": {
            "controller": {"type": "llm", "id": "llm/haiku"},
            "purpose": "decision",
            "provider": "anthropic",
            "model": "claude-haiku-5-5",
            "prompt_sha256": "ab" * 32,
            "latency_ms": 900,
            "usage": {"input_tokens": 10, "output_tokens": 5},
            "cost_usd": cost,
            "charged": charged,
            "stop_reason": "tool_use",
        },
    }
    if ticket_id is not None:
        envelope["data"]["ticket_id"] = ticket_id
    return envelope


async def test_estourar_o_teto_do_dia_pausa_o_mundo_e_o_gasto_sobrevive_a_uma_queda() -> None:
    pipeline = Pipeline(controller="none")
    blobs = MemoryBlobStore()
    guard = BudgetService(
        WORLD, LIMITS, pipeline.bus, blobs, pipeline.clock, pipeline.ids, pipeline.telemetry
    )
    await guard.start()
    await pipeline.start()
    assert pipeline.core.paused is False

    async def call(seq: int, tick: int, cost: float, **kw: Any) -> None:
        await pipeline.bus.publish(
            subject(COMPLETED, WORLD), _call(pipeline, seq, tick, cost, **kw)
        )

    await call(0, 10, 0.25)
    await call(1, 20, 0.40, charged=False)  # reproduzida da fita: não conta
    await call(2, 30, 0.25)
    assert pipeline.core.paused is False
    assert [n["threshold_pct"] for n in pipeline.of_type("ops.budget.threshold_reached.v2")] == [
        50,
        80,
    ]
    await call(3, 40, 0.25)
    assert pipeline.core.paused is True  # o kernel recebeu cmd.clock.pause pelo barramento
    pauses = pipeline.of_type("cmd.clock.pause.v1")
    assert pauses == [{"reason": "budget"}]
    (exceeded,) = pipeline.of_type("ops.budget.exceeded.v2")
    assert exceeded == {
        "scope": "day",
        "day": 1,
        "spent_usd": 0.75,
        "limit_usd": 0.6,
        "paused": True,
    }
    assert guard.paused_times == 1
    assert [
        e["type"] for _, e in pipeline.inner.published if e["type"] in (THRESHOLD, PAUSE, EXCEEDED)
    ] == [THRESHOLD, THRESHOLD, THRESHOLD, PAUSE, EXCEEDED]

    # A guarda caiu e voltou: o livro-caixa veio do arquivo, e uma chamada repetida não conta.
    again = BudgetService(
        WORLD, LIMITS, pipeline.bus, blobs, pipeline.clock, pipeline.ids, pipeline.telemetry
    )
    assert again.ledger.total == 0.75
    assert again.ledger.record(pipeline.inner.published[-5][1]["id"], 1, 0.25) == []
    await guard.stop()


async def test_retomado_com_o_teto_estourado_a_proxima_chamada_pausa_de_novo() -> None:
    """Só o operador retoma o mundo. Se ele retomar sem subir o teto, a guarda não deixa o gasto
    seguir: a chamada cobrada seguinte pausa de novo, sem repetir os avisos de limiar."""
    pipeline = Pipeline(controller="none")
    guard = BudgetService(
        WORLD,
        BudgetLimits(usd_per_sim_day=0.6, usd_total=1.0),
        pipeline.bus,
        MemoryBlobStore(),
        pipeline.clock,
        pipeline.ids,
        pipeline.telemetry,
    )
    await guard.start()
    await pipeline.start()

    async def call(seq: int, tick: int, cost: float) -> None:
        await pipeline.bus.publish(subject(COMPLETED, WORLD), _call(pipeline, seq, tick, cost))

    async def resume() -> None:
        envelope = _call(pipeline, 0, 0, 0.0)
        del envelope["tick"], envelope["simtime"]
        envelope["source"], envelope["actor"] = "/operator/teste", "human/operator"
        envelope["type"], envelope["data"] = RESUME, {}
        envelope["dataschema"] = "contracts://commands/clock/resume.v1"
        await pipeline.bus.publish(subject(RESUME, WORLD), envelope)
        assert pipeline.core.paused is False

    def published() -> list[str]:
        kinds = (THRESHOLD, PAUSE, EXCEEDED)
        return [e["type"] for _, e in pipeline.inner.published if e["type"] in kinds]

    await call(0, 10, 0.70)  # o dia estoura de uma vez: 50, 80 e 100% do dia, e 50% do mundo
    assert pipeline.core.paused is True
    assert published() == [THRESHOLD, THRESHOLD, THRESHOLD, PAUSE, EXCEEDED, THRESHOLD]

    await resume()
    await call(1, 20, 0.05)  # o teto do dia continua estourado: pausa de novo, sem limiar novo
    assert pipeline.core.paused is True
    assert published()[6:] == [PAUSE, EXCEEDED]
    assert guard.paused_times == 2

    await resume()
    await call(2, 30, 0.40)  # o dia de novo, e o mundo passa de 80% e do teto dele
    assert pipeline.core.paused is True
    assert published()[8:] == [PAUSE, EXCEEDED, THRESHOLD, THRESHOLD, EXCEEDED]
    assert guard.paused_times == 3  # uma pausa por chamada, mesmo com os dois tetos
    assert [e["scope"] for e in pipeline.of_type("ops.budget.exceeded.v2")] == [
        "day",
        "day",
        "day",
        "total",
    ]
    await guard.stop()


def _guard(pipeline: Pipeline, limits: BudgetLimits, **kw: Any) -> BudgetService:
    return BudgetService(
        WORLD,
        limits,
        pipeline.bus,
        MemoryBlobStore(),
        pipeline.clock,
        pipeline.ids,
        pipeline.telemetry,
        **kw,
    )


async def test_no_escritorio_o_teto_desliga_a_mente_e_o_mundo_segue() -> None:
    """`on_exceeded: mind_off` (ADR-0080): no teto do dia, a guarda avisa sem pedir a pausa; quem
    reage é a mente, que desliga e deixa a rotina conduzir o dev."""
    pipeline = Pipeline(controller="none")
    guard = _guard(
        pipeline, BudgetLimits(usd_per_sim_day=0.6, usd_total=10.0), on_exceeded="mind_off"
    )
    await guard.start()
    await pipeline.start()
    await pipeline.bus.publish(subject(COMPLETED, WORLD), _call(pipeline, 0, 10, 0.7))
    assert pipeline.core.paused is False
    assert [e["type"] for _, e in pipeline.inner.published if e["type"] == PAUSE] == []
    (exceeded,) = pipeline.of_type("ops.budget.exceeded.v2")
    assert (exceeded["scope"], exceeded["paused"]) == ("day", False)
    assert guard.paused_times == 0
    await guard.stop()


async def test_o_teto_do_pedido_nunca_pausa_o_mundo() -> None:
    """O pedido estourado é da mente, que larga o pedido (ADR-0080): mesmo no mundo que pausa, a
    guarda só avisa, com o id do pedido."""
    pipeline = Pipeline(controller="none")
    limits = BudgetLimits(usd_per_sim_day=10.0, usd_total=100.0, usd_per_ticket=1.0)
    guard = _guard(pipeline, limits)
    await guard.start()
    await pipeline.start()
    await pipeline.bus.publish(
        subject(COMPLETED, WORLD), _call(pipeline, 0, 10, 1.2, ticket_id="pedido-1")
    )
    assert pipeline.core.paused is False
    (exceeded,) = pipeline.of_type("ops.budget.exceeded.v2")
    assert exceeded == {
        "scope": "ticket",
        "ticket_id": "pedido-1",
        "spent_usd": 1.2,
        "limit_usd": 1.0,
        "paused": False,
    }
    assert guard.ledger.exceeded_now() == ["pedido-1"]
    await guard.stop()


async def test_o_operador_sobe_o_teto_com_o_mundo_vivo_e_a_guarda_da_sinal_de_vida() -> None:
    """`cmd.ops.budget.set` (ADR-0080): a guarda troca os tetos, publica o fato e um sinal de vida
    logo atrás; o kernel deixa o comando de lado, sem recusa e sem diário. O sinal sai em
    `live.budget`, sem envelope (o exemplo do contrato confere o formato)."""
    pipeline = Pipeline(controller="none")
    guard = _guard(
        pipeline, BudgetLimits(usd_per_sim_day=0.6, usd_total=10.0), on_exceeded="mind_off"
    )
    pulses: list[dict[str, Any]] = []

    async def heard(_: str, message: Any) -> None:
        pulses.append(dict(message))

    await pipeline.inner.subscribe(f"campsverso.{WORLD}.live.budget", heard)
    await guard.start()
    await pipeline.start()
    await guard.announce_pulse(5.0)
    assert pulses[-1]["exceeded"] == []
    assert pulses[-1]["limits"] == {
        "usd_per_sim_day": 0.6,
        "usd_total": 10.0,
    }
    await pipeline.bus.publish(subject(COMPLETED, WORLD), _call(pipeline, 0, 10, 0.7))
    await guard.announce_pulse(5.0)
    assert pulses[-1]["exceeded"] == ["day"]
    assert (pulses[-1]["day"], pulses[-1]["spent_day_usd"]) == (1, 0.7)

    command = _call(pipeline, 0, 10, 0.0)
    command["source"], command["actor"] = "/gateway/teste", "human/operador"
    command["type"], command["dataschema"] = SET, "contracts://commands/ops/budget.set.v1"
    command["data"] = {"usd_per_sim_day": 2.0, "usd_per_ticket": 1.0, "reason": "o testador"}
    await pipeline.bus.publish(subject(SET, WORLD), command)
    (changed,) = pipeline.of_type("ops.budget.limits_changed.v1")
    assert changed == {
        "usd_per_sim_day": 2.0,
        "usd_per_ticket": 1.0,
        "usd_total": 10.0,
        "reason": "o testador",
    }
    assert [
        e["causationid"] for _, e in pipeline.inner.published if e["type"] == LIMITS_CHANGED
    ] == [command["id"]]
    assert pulses[-1]["type"] == PULSE
    assert pulses[-1]["exceeded"] == []
    assert pulses[-1]["limits"]["usd_per_ticket"] == 1.0
    assert pipeline.of_type("world.command.rejected.v1") == []
    assert set(pulses[-1]) == {
        "type",
        "worldid",
        "limits",
        "spent_total_usd",
        "spent_day_usd",
        "day",
        "exceeded",
        "pulse_seconds",
        "sent_at",
    }
    await guard.stop()
