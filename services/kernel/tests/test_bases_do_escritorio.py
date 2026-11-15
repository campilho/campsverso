"""As bases do escritório no kernel (M23, ADR-0078): quem pode assumir cada avatar, o gerente que
entra pela porta ao ser assumido, as durações em segundos e a fala."""

import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from campsverso_cartridge_api import (
    Accepted,
    ActionContext,
    AvatarDef,
    CartridgeManifest,
    ClockDef,
    ControllerRef,
    NeedDef,
    Position,
    SpawnDef,
    Validation,
    WorldBuilder,
    WorldOps,
)
from campsverso_kernel.core import KernelCore, WorldConfig
from campsverso_kernel.errors import DefinitionError
from campsverso_kernel.facts import Fact
from campsverso_kernel.loader import build_world
from campsverso_kernel.testing import RULES, START, LabCartridge, command, control

DEV_SCRIPT = ControllerRef("script", "script/dev")
AWAY = ControllerRef("script", "script/gerente-fora")
HUMAN = {"type": "human", "id": "human/camps-browser"}
DOOR = Position(1, 1)


@dataclass(frozen=True)
class Think:
    """Uma ação de laboratório declarada em segundos, como as do escritório."""

    name: str = "think"

    def validate(self, ctx: ActionContext) -> Validation:
        return Accepted(0, "partial", seconds=float(ctx.params.get("seconds", 90)))

    def complete(self, ctx: ActionContext, ops: WorldOps) -> None:
        pass

    def interrupted(self, ctx: ActionContext, ops: WorldOps, elapsed_ticks: int) -> None:
        pass


@dataclass(frozen=True)
class OfficeLab:
    """O laboratório com o dev, que não aceita humano, e o gerente, que vem de fora."""

    tick_seconds: int = 60
    speech_interrupts: bool = True
    manifest: CartridgeManifest = field(
        default_factory=lambda: CartridgeManifest("lab_office", "0.1.0", ("lab",))
    )

    def contribute(self, world: WorldBuilder) -> None:
        if self.tick_seconds != 60:
            # Um tick curto pede taxas que rendem um número inteiro por tick: múltiplos de 15 por
            # hora num tick de 2 s (o que o levantamento do M23 achou).
            world.configure_clock(
                ClockDef(self.tick_seconds, "06:00", (("manha", "06:00"),), default_scale=1)
            )
            world.define_need(NeedDef("energia", 25, {"asleep": 15}, role="energy"), override=True)
            world.define_need(NeedDef("fome", 79, {"awake": 15, "asleep": 15}), override=True)
        world.spawn(SpawnDef("dev", "avatar", position=Position(4, 1)))
        world.spawn(SpawnDef("gerente", "avatar"))
        agents = frozenset({"llm", "script", "replay"})
        world.add_avatar(AvatarDef("dev", DEV_SCRIPT, controllers=agents))
        world.add_avatar(
            AvatarDef(
                "gerente",
                AWAY,
                present=False,
                controllers=frozenset({"human", "script", "replay"}),
                enters_at=DOOR,
            )
        )
        world.add_action(Think())
        world.set_interrupt_on_speech(self.speech_interrupts)

    def rules_file(self) -> Path | None:
        return None


def _core(
    tick_seconds: int = 60,
    controllers: dict[str, ControllerRef] | None = None,
    speech_interrupts: bool = True,
) -> KernelCore:
    definition = build_world(
        "lab_office",
        {"lab": LabCartridge(), "lab_office": OfficeLab(tick_seconds, speech_interrupts)},
    )
    core = KernelCore(definition, WorldConfig("lab-02", 7, START), RULES, rules_source="test")
    if controllers:
        core.configure_controllers(controllers)
    core.start()
    return core


def _only(facts: Sequence[Fact], event: str) -> list[dict[str, Any]]:
    wanted = f"campsverso.{event}" if re.search(r"\.v\d+$", event) else f"campsverso.{event}.v1"
    return [dict(f.data) for f in facts if f.type == wanted]


def _run(core: KernelCore, ticks: int = 1) -> list[Fact]:
    facts = core.drain()
    for _ in range(ticks):
        core.step()
        facts += core.drain()
    return facts


def _as(avatar: str, action: str, params: dict[str, Any], controller: str) -> dict[str, Any]:
    cmd = command(action, params, controller=controller)
    cmd["id"] = f"cmd-{avatar}-{action}"
    cmd["data"]["avatar_id"] = avatar
    return cmd


# ------------------------------------------------------------------ quem pode assumir


def test_nenhum_humano_assume_o_dev() -> None:
    core = _core()
    core.submit(control("avatar.possess", {"avatar_id": "dev", "controller": HUMAN}))
    (rejected,) = _only(core.drain(), "world.command.rejected")
    assert rejected["reason"] == "controller_not_allowed"
    assert core.world.avatar_map["dev"].controller == DEV_SCRIPT
    llm = {"type": "llm", "id": "llm/dev"}
    core.submit(control("avatar.possess", {"avatar_id": "dev", "controller": llm}))
    assert _only(core.drain(), "avatar.possessed")[0]["controller"] == llm


def test_o_arquivo_do_mundo_tambem_nao_poe_um_humano_no_dev() -> None:
    definition = build_world("lab_office", {"lab": LabCartridge(), "lab_office": OfficeLab()})
    core = KernelCore(definition, WorldConfig("lab-02", 7, START), RULES, rules_source="test")
    with pytest.raises(ValueError, match="dev não aceita um controlador human"):
        core.configure_controllers({"dev": ControllerRef("human", "human/alguem")})


def test_o_controlador_padrao_precisa_estar_entre_os_aceitos() -> None:
    @dataclass(frozen=True)
    class Wrong:
        manifest: CartridgeManifest = field(
            default_factory=lambda: CartridgeManifest("lab_wrong", "0.1.0", ("lab",))
        )

        def contribute(self, world: WorldBuilder) -> None:
            world.spawn(SpawnDef("dev", "avatar", position=Position(4, 1)))
            world.add_avatar(AvatarDef("dev", DEV_SCRIPT, controllers=frozenset({"llm"})))

        def rules_file(self) -> Path | None:
            return None

    with pytest.raises(DefinitionError, match="não está entre os aceitos"):
        build_world("lab_wrong", {"lab": LabCartridge(), "lab_wrong": Wrong()})


# ------------------------------------------------------------------ o gerente pela porta


def test_o_gerente_entra_pela_porta_ao_ser_assumido_e_sai_ao_ser_devolvido() -> None:
    core = _core()
    assert not core.world.avatar_map["gerente"].present
    core.submit(control("avatar.possess", {"avatar_id": "gerente", "controller": HUMAN}))
    facts = core.drain()
    (entered,) = _only(facts, "avatar.entered")
    assert entered == {"avatar_id": "gerente", "position": {"x": 1, "y": 1}, "reason": "possessed"}
    assert core.world.avatar_map["gerente"].present
    core.submit(control("avatar.release", {"avatar_id": "gerente"}))
    (left,) = _only(core.drain(), "avatar.left")
    assert left["reason"] == "released"
    assert not core.world.avatar_map["gerente"].present


def test_o_gerente_script_dos_testes_comeca_la_dentro() -> None:
    core = _core(controllers={"gerente": ControllerRef("script", "script/gerente")})
    assert core.world.avatar_map["gerente"].present
    assert core.world.position_of("gerente") == DOOR


def test_a_porta_pede_um_avatar_que_comeca_fora() -> None:
    @dataclass(frozen=True)
    class Inside:
        manifest: CartridgeManifest = field(
            default_factory=lambda: CartridgeManifest("lab_inside", "0.1.0", ("lab",))
        )

        def contribute(self, world: WorldBuilder) -> None:
            world.spawn(SpawnDef("gerente", "avatar", position=DOOR))
            world.add_avatar(AvatarDef("gerente", AWAY, enters_at=DOOR))

        def rules_file(self) -> Path | None:
            return None

    with pytest.raises(DefinitionError, match="present=False"):
        build_world("lab_inside", {"lab": LabCartridge(), "lab_inside": Inside()})


# ------------------------------------------------------------------ o tempo em segundos


def test_a_duracao_em_segundos_vira_ticks_pelo_relogio_do_cartucho() -> None:
    core = _core(tick_seconds=2)
    core.submit(_as("dev", "think", {"seconds": 90}, DEV_SCRIPT.id))
    (accepted,) = _only(_run(core), "action.accepted")
    assert accepted["duration_ticks"] == 45  # 90 s num tick de 2 s
    core.submit(_as("dev", "think", {"seconds": 3}, DEV_SCRIPT.id))
    accepted = _only(_run(core), "action.accepted")[-1]
    assert accepted["duration_ticks"] == 2  # arredonda para cima


def test_esperar_em_segundos_num_mundo_de_tick_curto() -> None:
    core = _core(tick_seconds=2)
    core.submit(_as("dev", "wait", {"seconds": 600}, DEV_SCRIPT.id))
    assert _only(_run(core), "action.accepted")[-1]["duration_ticks"] == 300
    for params in ({"seconds": 0}, {"seconds": 3601}, {"ticks": 5, "seconds": 10}, {}):
        core.submit(_as("dev", "wait", dict(params), DEV_SCRIPT.id))
        assert _only(_run(core), "action.rejected")[-1]["reason"] == "invalid_params"


# ------------------------------------------------------------------ a fala


def test_o_gerente_fala_com_o_dev_e_o_kernel_publica_a_fala_inteira() -> None:
    core = _core(tick_seconds=2)
    core.submit(control("avatar.possess", {"avatar_id": "gerente", "controller": HUMAN}))
    core.drain()
    text = "Bom dia! Deixei um pedido novo no quadro: a busca por nome."
    core.submit(_as("gerente", "say", {"text": text, "to": "dev"}, HUMAN["id"]))
    facts = _run(core)
    (spoke,) = _only(facts, "avatar.spoke")
    assert spoke["avatar_id"] == "gerente"
    assert spoke["text"] == text
    assert spoke["listener_id"] == "dev"
    assert spoke["position"] == {"x": 1, "y": 1}
    (accepted,) = _only(facts, "action.accepted")
    assert accepted["duration_ticks"] == 3  # uns 5 s de fala, num tick de 2 s


def test_a_fala_recusa_o_texto_vazio_longo_e_quem_nao_esta() -> None:
    core = _core()
    for params, reason in (
        ({"text": "   "}, "invalid_params"),
        ({"text": "x" * 281}, "invalid_params"),
        ({"text": "oi", "to": "gerente"}, "not_present"),
        ({"text": "oi", "to": "dev"}, "invalid_params"),
    ):
        core.submit(_as("dev", "say", params, DEV_SCRIPT.id))
        assert _only(_run(core), "action.rejected")[-1]["reason"] == reason


def _dev_thinking_when_spoken_to(speech_interrupts: bool) -> list[Fact]:
    core = _core(tick_seconds=2, speech_interrupts=speech_interrupts)
    core.submit(control("avatar.possess", {"avatar_id": "gerente", "controller": HUMAN}))
    core.submit(_as("dev", "think", {"seconds": 600}, DEV_SCRIPT.id))
    _run(core, 3)
    core.submit(_as("gerente", "say", {"text": "Camps, um minuto?", "to": "dev"}, HUMAN["id"]))
    return _run(core, 2)


def test_falar_com_o_dev_interrompe_o_que_ele_faz_e_ele_decide_de_novo() -> None:
    """ADR-0080: o trabalho é parcial, então o progresso fica, e o dev responde."""
    facts = _dev_thinking_when_spoken_to(speech_interrupts=True)
    (failed,) = _only(facts, "action.failed")
    who = (failed["avatar_id"], failed["action"], failed["reason"])
    assert who == ("dev", "think", "cancelled")
    asked = [d for d in _only(facts, "avatar.decision_requested") if d["avatar_id"] == "dev"]
    assert [d["reason"] for d in asked] == ["action_interrupted"]


def test_sem_a_opcao_do_cartucho_a_fala_nao_interrompe() -> None:
    facts = _dev_thinking_when_spoken_to(speech_interrupts=False)
    assert not _only(facts, "action.failed")
    assert not [d for d in _only(facts, "avatar.decision_requested") if d["avatar_id"] == "dev"]


# ------------------------------------------------------------------ o relógio ancorado


def test_o_relogio_ancorado_salta_ate_agora_e_roda_o_que_vence_no_caminho() -> None:
    from datetime import timedelta

    from campsverso_adapters import ContractValidator
    from campsverso_kernel.main import catch_up_command, tick_of

    core = _core()
    core.drain()
    now = START + timedelta(hours=26, seconds=59)
    to_tick = tick_of(START, now, 60_000)
    assert to_tick == 26 * 60  # os segundos que sobram não fazem um tick
    command_id = "01a12d2b-6c36-7a10-9c4e-3f1d2a7b8c90"
    jump = catch_up_command("lab-02", "lab_office", core.tick, to_tick, now, command_id)
    assert jump is not None
    assert list(ContractValidator().validate(jump)) == []
    core.submit(jump)
    facts = core.drain()
    (caught,) = _only(facts, "world.clock.caught_up")
    assert caught == {"from_tick": 0, "to_tick": 26 * 60, "reason": "wall_clock"}
    assert core.tick == 26 * 60
    assert _only(facts, "world.clock.jumped")  # pulou o que não acontecia
    phases = [p["phase"] for p in _only(facts, "world.clock.phase_changed")]
    assert "noite" in phases  # e a noite das 20:00, que venceu no caminho, chegou
    # Em dia, não salta de novo.
    assert catch_up_command("lab-02", "lab_office", core.tick, to_tick, now, "x") is None
