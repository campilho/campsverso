"""Gateway sobre o ciclo inteiro em memória: welcome, updates, visões e comandos (ADR-0050)."""

import asyncio
from collections.abc import AsyncIterator, Mapping
from pathlib import Path
from typing import Any

import pytest

from campsverso_adapters import (
    InMemoryBus,
    MemoryBlobStore,
    MemoryClient,
    MemoryRealtime,
    MemoryTelemetry,
    ValidatingBus,
)
from campsverso_gateway.service import (
    BUDGET_SET,
    COMMAND,
    HUMAN_ID,
    PLAY_COMMANDS,
    POSSESS,
    PROPOSE,
    RELEASE,
    GatewayService,
)
from campsverso_gateway.state import apply_merge_patch, observer_state
from campsverso_ports import Envelope, EventBus
from campsverso_testkit.farm import WORLD
from campsverso_testkit.pipeline import DAY, Pipeline
from campsverso_tools.contracts import catalog
from campsverso_tools.contracts.validation import MessageValidator

CONTRACTS = catalog.find_contracts_dir(Path(__file__).resolve().parent)
MESSAGES = MessageValidator(catalog.load(CONTRACTS))


class Rig:
    def __init__(
        self,
        pipeline: Pipeline,
        blobs: MemoryBlobStore | None = None,
        *,
        player_clock: bool = False,
        build: Mapping[str, str] | None = None,
    ) -> None:
        self.pipeline = pipeline
        self.blobs = blobs or MemoryBlobStore()
        self.player_clock = player_clock
        self.build = build
        self.gateway = self.new_gateway()
        self.realtime = MemoryRealtime()

    def new_gateway(self, bus: EventBus | None = None) -> GatewayService:
        p = self.pipeline
        return GatewayService(
            WORLD,
            "camps",
            "farm_camps",
            bus or p.bus,
            self.blobs,
            p.clock,
            p.ids,
            MemoryTelemetry(),
            p.validator,
            flush_seconds=3600,  # os testes chamam flush() na hora certa
            player_clock=self.player_clock,
            build=self.build,
        )

    async def connect(self, view: str) -> tuple[MemoryClient, dict[str, Any]]:
        client = await self.realtime.connect(view)  # pyright: ignore[reportArgumentType]
        welcome = dict(await client.receive())
        assert MESSAGES.validate(welcome) == []
        return client, welcome


class Killed(BaseException):
    """O `kill -9`: nada mais roda no processo."""


class DyingBus(ValidatingBus):
    """O barramento de um gateway que morre logo depois de o servidor guardar um comando."""

    def __init__(self, server: InMemoryBus) -> None:
        super().__init__(server)
        self.server = server

    async def publish(self, subject: str, envelope: Envelope) -> None:
        if str(envelope["source"]).startswith("/gateway/"):
            self.server.published.append((subject, envelope))
            raise Killed
        await super().publish(subject, envelope)


class YieldingBus(ValidatingBus):
    """Um publish que espera a resposta do servidor, como o do NATS: outro comando passa."""

    async def publish(self, subject: str, envelope: Envelope) -> None:
        await asyncio.sleep(0)
        await super().publish(subject, envelope)


PAUSE = {"type": COMMAND, "command": "campsverso.cmd.clock.pause.v1", "data": {"reason": "debug"}}


@pytest.fixture
async def rig() -> AsyncIterator[Rig]:
    pipeline = Pipeline()
    rig = Rig(pipeline)
    await rig.gateway.start()
    serving = asyncio.create_task(rig.realtime.serve(rig.gateway.handle))
    await pipeline.start()
    yield rig
    await rig.realtime.stop()
    await rig.gateway.stop()
    serving.cancel()


async def _drain(client: MemoryClient) -> list[Mapping[str, Any]]:
    """Tudo o que já chegou ou chega logo: o gateway escreve por uma tarefa à parte."""
    received: list[Mapping[str, Any]] = []
    while True:
        try:
            received.append(await client.receive(timeout=0.2))
        except TimeoutError:
            return received


def _types(message: Mapping[str, Any]) -> set[str]:
    return {str(e["type"]).removeprefix("campsverso.") for e in message["events"]}


async def test_a_placa_vem_na_sessao_so_quando_o_supervisor_diz_a_versao(rig: Rig) -> None:
    """ADR-0083: o commit e a data que o gateway roda, para a placa; sem supervisor, nada."""
    await rig.pipeline.run_until(30)
    rig.gateway.flush()
    _, welcome = await rig.connect("player")
    assert "build" not in welcome
    build = {"commit": "a" * 40, "date": "2026-11-20T23:30:00-03:00"}
    other = Rig(rig.pipeline, build=build)
    await other.gateway.start()
    serving = asyncio.create_task(other.realtime.serve(other.gateway.handle))
    try:
        await rig.pipeline.run_until(60)
        other.gateway.flush()
        _, welcome = await other.connect("operator")
        assert welcome["build"] == build
    finally:
        await other.realtime.stop()
        await other.gateway.stop()
        serving.cancel()


async def test_a_saude_diz_o_tick_o_pulso_e_a_sessao_na_oficina(rig: Rig) -> None:
    """ADR-0083: o /health do supervisor. Um passo na oficina que não foi a entrega, há pouco,
    é uma sessão em andamento; a entrega, ou um passo antigo, não."""
    await rig.pipeline.run_until(30)
    rig.gateway.flush()
    health = rig.gateway.health()
    assert health["tick"] > 0
    assert health["busy"] is False
    assert "build" not in health
    tick = rig.gateway.projection.tick
    steps = rig.gateway.projection.workshop.setdefault("steps", {})
    steps["camps"] = {"ticket_id": "pedido-001", "tool": "escrever", "ok": True, "tick": tick}
    assert rig.gateway.health()["busy"] is True
    steps["camps"] = {"ticket_id": "pedido-001", "tool": "pronto", "ok": True, "tick": tick}
    assert rig.gateway.health()["busy"] is False
    steps["camps"] = {"ticket_id": "pedido-001", "tool": "escrever", "ok": True, "tick": tick - 6}
    assert rig.gateway.health()["busy"] is False  # 6 minutos de fazenda: a sessão acabou
    rig.gateway.projection.workshop["robots"] = {"testador": {"state": "working", "tick": tick}}
    assert rig.gateway.health()["busy"] is True


async def test_o_aviso_do_supervisor_vai_a_todas_as_telas(rig: Rig) -> None:
    """A parte 5 do M25: antes de trocar de versão, o supervisor avisa as telas pelo gateway."""
    await rig.pipeline.run_until(30)
    rig.gateway.flush()
    player, _ = await rig.connect("player")
    operator, _ = await rig.connect("operator")
    commit = "8" * 40
    given = {"kind": "troca", "text": "O escritório vai trocar de versão.", "commit": commit}
    assert rig.gateway.notice({**given, "pull_requests": [2]}) is None
    for client in (player, operator):
        message = dict(await client.receive())
        assert MESSAGES.validate(message) == []
        assert (message["kind"], message["commit"], message["pull_requests"]) == (
            "troca",
            commit,
            [2],
        )
    # A tela que reconecta no meio da troca recebe o aviso no welcome, por dois minutos.
    _, welcome = await rig.connect("player")
    assert welcome["notice"]["kind"] == "troca"
    rig.pipeline.clock.advance(121)
    _, later = await rig.connect("player")
    assert "notice" not in later
    assert rig.gateway.notice({"kind": "festa", "text": "oi"}) == (
        "kind é um de ['troca', 'espera', 'volta']"
    )
    assert rig.gateway.notice({"kind": "volta", "text": ""}) is not None


async def test_welcome_traz_o_estado_e_o_mapa(rig: Rig) -> None:
    await rig.pipeline.run_until(30)
    rig.gateway.flush()
    _, welcome = await rig.connect("player")
    state = welcome["state"]
    session_map = state["session"]["map"]
    assert (session_map["id"], session_map["width"], session_map["height"]) == (
        "farm_camps",
        32,
        18,
    )
    assert len(session_map["rows"]) == 18  # o terreno vem no session.started (ADR-0056)
    assert session_map["legend"]["G"]["kind"] == "grass"
    assert state["clock"] == {"mode": "max", "scale": 72.0, "paused": False}
    assert state["entities"]["bed"]["kind"] == "bed"
    assert state["controllers"]["camps"] == {"type": "script", "id": "script/farmer-v1"}
    assert welcome["commands"] == list(PLAY_COMMANDS)  # joga, mas não mexe no relógio
    assert "world.session.started.v1" in _types(welcome)
    assert "perception.delivered.v1" not in _types(welcome)  # as fotos ficam com os controladores


async def test_updates_levam_ao_mesmo_estado_da_projecao(rig: Rig) -> None:
    client, welcome = await rig.connect("operator")
    state = welcome["state"]
    for _ in range(12):
        await rig.pipeline.run_until(rig.pipeline.core.tick + 10)
        rig.gateway.flush()
    updates = await _drain(client)
    assert len(updates) == 12
    for update in updates:
        assert MESSAGES.validate(dict(update)) == []
        state = apply_merge_patch(state, update["patch"])
    assert state == observer_state(rig.gateway.projection)
    # O tick é o do último evento: tick quieto não gera evento, e a UI estima o relógio entre eles.
    assert 100 < state["tick"] <= rig.pipeline.core.tick


async def test_jogador_nunca_recebe_internal_nem_observer(rig: Rig) -> None:
    player, _ = await rig.connect("player")
    operator, _ = await rig.connect("operator")
    await rig.pipeline.run_until(DAY + 60)  # a virada do dia aplica a regra oculta (internal)
    rig.gateway.flush()
    seen_by_player = {e["visibility"] for e in (await player.receive())["events"]}
    seen_by_operator = {e["visibility"] for e in (await operator.receive())["events"]}
    assert seen_by_player <= {"world", "agent"}  # numa fazenda, nem a oficina
    assert "internal" in seen_by_operator


async def test_o_jogador_acompanha_a_oficina_do_dev(rig: Rig) -> None:
    """ADR-0089: o computador do dev fica na sala; o gerente recebe os fatos da oficina, para a
    tela acompanhar a sessão. O resto do observer (o custo, o caderno) continua só do operador."""
    player, _ = await rig.connect("player")
    who = {"avatar_id": "camps", "ticket_id": "pedido-002"}
    step = {"harness": "claude_code", "tool": "Edit", "summary": "Edit: a.py", "ok": True}
    batch = [
        ("x", _observer("id-w1", 1, "workshop.step.v2", duration_ms=5, **step, **who)),
        ("x", _call("id-w2", 2)),
    ]
    await rig.gateway._on_batch("observer", batch)  # pyright: ignore[reportPrivateUsage]
    rig.gateway.flush()
    update = await player.receive_until("update")
    assert "workshop.step.v2" in _types(update)
    assert "llm.call.completed.v1" not in _types(update)
    session = update["patch"]["workshop"]["sessions"]["camps"]
    assert (session["ticket_id"], session["harness"], session["count"]) == (
        "pedido-002",
        "claude_code",
        1,
    )


async def test_operador_pausa_e_o_kernel_responde(rig: Rig) -> None:
    rig.gateway.flush()  # o welcome já sai com a sessão; o update traz só a pausa
    operator, welcome = await rig.connect("operator")
    assert "campsverso.cmd.clock.pause.v1" in welcome["commands"]
    await operator.send(
        {
            "type": "campsverso.realtime.command.v1",
            "request_id": "ui-1",
            "command": "campsverso.cmd.clock.pause.v1",
            "data": {"reason": "debug"},
        }
    )
    reply = await operator.receive_until("reply")
    assert MESSAGES.validate(dict(reply)) == []
    assert (reply["request_id"], reply["ok"]) == ("ui-1", True)
    await rig.pipeline.kernel.run_ticks(1)
    rig.gateway.flush()
    update = await operator.receive_until("update")
    assert update["patch"]["clock"] == {"paused": True}
    assert "world.clock.paused.v1" in _types(update)


async def test_no_sandbox_o_jogador_pausa_e_muda_a_velocidade() -> None:
    """ADR-0074, decisão 16: quem joga o sandbox também opera o relógio, menos o passo a passo."""
    pipeline = Pipeline()
    rig = Rig(pipeline, player_clock=True)
    await rig.gateway.start()
    serving = asyncio.create_task(rig.realtime.serve(rig.gateway.handle))
    await pipeline.start()
    try:
        player, welcome = await rig.connect("player")
        clock = {c for c in welcome["commands"] if ".clock." in c}
        assert clock == {
            "campsverso.cmd.clock.pause.v1",
            "campsverso.cmd.clock.resume.v1",
            "campsverso.cmd.clock.set_scale.v1",
        }
        base = {"type": "campsverso.realtime.command.v1", "request_id": "ui-1"}
        pause = {"command": "campsverso.cmd.clock.pause.v1", "data": {"reason": "debug"}}
        await player.send({**base, **pause})
        assert (await player.receive_until("reply"))["ok"] is True
        step = {"command": "campsverso.cmd.clock.step.v1", "data": {"ticks": 1}}
        await player.send({**base, "request_id": "ui-2", **step})
        assert (await player.receive_until("reply"))["error"]["code"] == "not_allowed"
    finally:
        await rig.realtime.stop()
        await rig.gateway.stop()
        serving.cancel()


async def test_comandos_recusados_pelo_gateway(rig: Rig) -> None:
    player, _ = await rig.connect("player")
    operator, _ = await rig.connect("operator")
    step = {"type": "campsverso.realtime.command.v1", "request_id": "ui-2"}
    await player.send(
        {**step, "command": "campsverso.cmd.clock.pause.v1", "data": {"reason": "debug"}}
    )
    assert (await player.receive_until("reply"))["error"]["code"] == "not_allowed"
    await operator.send({**step, "command": "campsverso.cmd.clock.step.v1", "data": {"ticks": 0}})
    assert (await operator.receive_until("reply"))["error"]["code"] == "invalid_command"
    await operator.send({"type": "campsverso.realtime.hello.v1"})
    reply = await operator.receive_until("reply")
    assert (reply["request_id"], reply["error"]["code"]) == ("desconhecido", "invalid_message")
    published = [e for e in rig.pipeline.envelopes if str(e["source"]).startswith("/gateway/")]
    assert published == []


async def test_gateway_volta_do_arquivo_sem_repetir_eventos(rig: Rig) -> None:
    await rig.pipeline.run_until(120)
    rig.gateway.flush()
    before = observer_state(rig.gateway.projection)
    again = Rig(rig.pipeline, rig.blobs).new_gateway()
    assert observer_state(again.projection) == before
    replayed = [e for _, e in rig.pipeline.inner.published if e["visibility"] == "world"]
    await again._on_batch("world", [("x", e) for e in replayed])  # pyright: ignore[reportPrivateUsage]
    assert observer_state(again.projection) == before  # reentrega não muda nada


async def test_comando_nunca_repete_o_seq(rig: Rig) -> None:
    """O seq de um comando é gasto e gravado antes de ele sair: nem a volta de uma queda depois
    do publish nem dois comandos ao mesmo tempo, de conexões diferentes, o repetem."""
    dying = rig.new_gateway(DyingBus(rig.pipeline.inner))
    with pytest.raises(Killed):
        await dying._command("operator", {**PAUSE, "request_id": "ui-1"})  # pyright: ignore[reportPrivateUsage]
    again = rig.new_gateway(YieldingBus(rig.pipeline.inner))
    replies = await asyncio.gather(
        *(again._command("operator", {**PAUSE, "request_id": f"ui-{n}"}) for n in (2, 3))  # pyright: ignore[reportPrivateUsage]
    )
    assert all(reply["ok"] for reply in replies)
    sent = [e for e in rig.pipeline.envelopes if str(e["source"]).startswith("/gateway/")]
    assert len({e["id"] for e in sent}) == 3
    assert sorted(int(e["seq"]) for e in sent) == [0, 1, 2]


async def test_pulso_do_kernel_e_sem_sinal(rig: Rig) -> None:
    """O pulso entra no estado; sem pulso por 3 intervalos, o kernel fica sem sinal (ADR-0051)."""
    rig.gateway.flush()
    operator, _ = await rig.connect("operator")
    pulse = {
        "type": "campsverso.live.kernel.v1",
        "worldid": WORLD,
        "tick": 42,
        "sim_time": "2026-10-10T06:42:00-03:00",
        "mode": "continuous",
        "scale": 72,
        "paused": False,
        "pulse_seconds": 1,
        "sent_at": "2026-10-12T15:00:00.000Z",
    }
    await rig.pipeline.inner.announce(f"campsverso.{WORLD}.live.kernel", pulse)
    rig.gateway.flush()
    update = await operator.receive_until("update")
    assert MESSAGES.validate(dict(update)) == []
    assert update["patch"]["pulse"] == {
        "tick": 42,
        "sim_time": "2026-10-10T06:42:00-03:00",
        "alive": True,
    }
    rig.pipeline.clock.advance(3.5)
    rig.gateway.flush()
    assert (await operator.receive_until("update"))["patch"] == {"pulse": {"alive": False}}
    assert rig.pipeline.inner.announced[-1][1] is pulse  # nada do pulso em `published`


async def test_sinal_da_guarda_e_os_tetos_pela_tela_do_operador(rig: Rig) -> None:
    """O sinal de vida da guarda entra em `costs.guard`, só na visão do operador, e fica sem sinal
    depois de 3 intervalos; só o operador manda os tetos novos (ADR-0080)."""
    rig.gateway.flush()
    operator, _ = await rig.connect("operator")
    player, _ = await rig.connect("player")
    signal = {
        "type": "campsverso.live.budget.v1",
        "worldid": WORLD,
        "limits": {"usd_per_sim_day": 3.0, "usd_per_ticket": 1.0, "usd_total": 30.0},
        "spent_total_usd": 4.37,
        "spent_day_usd": 1.12,
        "day": 8,
        "exceeded": ["pedido-3"],
        "pulse_seconds": 5,
        "sent_at": "2026-11-16T12:01:05.120Z",
    }
    await rig.pipeline.inner.announce(f"campsverso.{WORLD}.live.budget", signal)
    rig.gateway.flush()
    update = await operator.receive_until("update")
    assert MESSAGES.validate(dict(update)) == []
    assert update["patch"]["costs"]["guard"] == {
        "alive": True,
        "limits": {"usd_per_sim_day": 3.0, "usd_per_ticket": 1.0, "usd_total": 30.0},
        "spent_total_usd": 4.37,
        "spent_day_usd": 1.12,
        "day": 8,
        "exceeded": ["pedido-3"],
    }
    rig.pipeline.clock.advance(15.5)
    rig.gateway.flush()
    assert (await operator.receive_until("update"))["patch"] == {
        "costs": {"guard": {"alive": False}}
    }

    limits = {"usd_per_sim_day": 5.0, "reason": "o testador"}
    assert (await _ask(player, BUDGET_SET, limits))["error"]["code"] == "not_allowed"
    reply = await _ask(operator, BUDGET_SET, limits)
    assert reply["ok"] is True
    (sent,) = [e for e in rig.pipeline.envelopes if e["type"] == BUDGET_SET]
    assert (sent["actor"], sent["data"]) == ("human/operador", limits)
    nothing = await _ask(operator, BUDGET_SET, {"reason": "sem teto"})
    assert nothing["error"]["code"] == "invalid_command"


async def _ask(client: MemoryClient, command: str, data: Mapping[str, Any]) -> Mapping[str, Any]:
    await client.send(
        {
            "type": "campsverso.realtime.command.v1",
            "request_id": command[-24:],
            "command": command,
            "data": dict(data),
        }
    )
    return await client.receive_until("reply")


async def test_jogador_assume_joga_e_devolve(rig: Rig) -> None:
    """A9 pelo gateway (ADR-0051): o humano é sempre o mesmo, e quem diz isso é o gateway."""
    pipeline = rig.pipeline
    rig.gateway.flush()
    player, _ = await rig.connect("player")
    operator, _ = await rig.connect("operator")
    mode = {"mode": "continuous", "reason": "jogar"}
    assert (await _ask(operator, "campsverso.cmd.clock.set_mode.v1", mode))["ok"]
    await pipeline.kernel.run_ticks(1)
    fake = {"avatar_id": "camps", "controller": {"type": "script", "id": "script/farmer-v1"}}
    assert (await _ask(player, POSSESS, fake))["ok"]  # a UI não escolhe quem é
    await pipeline.kernel.run_ticks(1)
    possessed = pipeline.of_type("avatar.possessed.v1")[-1]
    assert possessed["controller"] == {"type": "human", "id": HUMAN_ID}
    move = {"avatar_id": "camps", "action": "move", "params": {"near": "well"}}
    assert (await _ask(player, PROPOSE, move))["ok"]
    await pipeline.kernel.run_ticks(1)
    assert pipeline.of_type("action.accepted.v1")[-1]["action"] == "move"
    sent = [
        e for e in pipeline.envelopes if e["type"] == PROPOSE and e["source"] == f"/gateway/{WORLD}"
    ]
    assert (sent[-1]["controllerid"], sent[-1]["actor"]) == (HUMAN_ID, "human/jogador")
    assert (await _ask(player, RELEASE, {"avatar_id": "camps"}))["ok"]
    await pipeline.kernel.run_ticks(1)
    released = pipeline.of_type("avatar.released.v1")[-1]
    assert released["controller"] == {"type": "script", "id": "script/farmer-v1"}


async def test_a_tela_so_assume_a_cadeira_do_jogador(rig: Rig) -> None:
    """ADR-0078: a cadeira do jogador é uma só (no escritório, o gerente, e nunca o dev). Pedir
    outro avatar é recusado pelo gateway, sem chegar ao kernel."""
    rig.gateway.flush()
    player, _ = await rig.connect("player")
    other = {"avatar_id": "dita", "controller": {"type": "human", "id": "x"}}
    reply = await _ask(player, POSSESS, other)
    assert not reply["ok"]
    assert reply["error"]["code"] == "not_allowed"
    assert (await _ask(player, RELEASE, {"avatar_id": "dita"}))["error"]["code"] == "not_allowed"


async def test_jogador_ve_a_recusa_do_proprio_comando(rig: Rig) -> None:
    """Com o mundo no modo máximo, o kernel recusa o humano; o jogador vê o motivo (ADR-0051)."""
    rig.gateway.flush()
    player, _ = await rig.connect("player")
    other, _ = await rig.connect("player")
    fake = {"avatar_id": "camps", "controller": {"type": "human", "id": "x"}}
    reply = await _ask(player, POSSESS, fake)
    await rig.pipeline.kernel.run_ticks(1)
    rig.gateway.flush()
    update = await player.receive_until("update")
    (rejected,) = [
        e for e in update["events"] if e["type"] == "campsverso.world.command.rejected.v1"
    ]
    assert rejected["data"]["command_id"] == reply["command_id"]
    assert rejected["data"]["reason"] == "mode_not_allowed"
    seen_by_other = await other.receive_until("update")
    assert all(e["visibility"] in {"world", "agent"} for e in seen_by_other["events"])


def _observer(event_id: str, seq: int, kind: str, **data: Any) -> Envelope:
    return {
        "id": event_id,
        "source": "/controller-runner/llm/camps",  # o runner e o medidor: o mesmo source
        "type": f"campsverso.{kind}",
        "seq": seq,
        "tick": 600,
        "visibility": "observer",
        "data": data,
    }


def _call(event_id: str, seq: int) -> Envelope:
    controller = {"type": "llm", "id": "llm/camps"}
    return _observer(
        event_id,
        seq,
        "llm.call.completed.v1",
        controller=controller,
        model="m",
        cost_usd=0.01,
        charged=True,
    )


async def test_o_observer_se_deduplica_pelo_id(rig: Rig) -> None:
    """ADR-0074: no observer, o runner (o caderno) e o medidor (o custo) do mesmo controlador têm
    o mesmo source e contadores próprios, e o seq volta a zero quando o controlador reinicia. Pelo
    seq, o gateway jogava fora o evento do contador que estivesse atrás; pelo id, só a reentrega."""
    batch = [
        ("x", _call("id-1", 5)),
        ("x", _observer("id-2", 0, "memory.noted.v1", avatar_id="camps", day=1, text="oi")),
        ("x", _call("id-3", 6)),
    ]
    await rig.gateway._on_batch("observer", batch)  # pyright: ignore[reportPrivateUsage]
    await rig.gateway._on_batch("observer", batch[:1])  # pyright: ignore[reportPrivateUsage]
    costs = rig.gateway.projection.costs["minds"]["llm/camps"]
    assert costs["calls"] == 2  # a reentrega do id-1 não contou de novo
    assert [n["text"] for n in rig.gateway.projection.memory["camps"]["notes"]] == ["oi"]
    again = Rig(rig.pipeline, rig.blobs).new_gateway()  # o gateway volta do arquivo
    restarted = [
        ("x", _call("id-4", 0)),
        ("x", _call("id-3", 6)),
    ]  # o seq recomeçou; e uma reentrega
    await again._on_batch("observer", restarted)  # pyright: ignore[reportPrivateUsage]
    assert again.projection.costs["minds"]["llm/camps"]["calls"] == 3
