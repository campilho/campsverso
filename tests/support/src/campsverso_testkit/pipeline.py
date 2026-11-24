"""O ciclo de decisão inteiro num processo só: kernel, percepção e controlador (escopo §5).

Tudo passa pelo barramento em memória com validação de contrato, como passaria pelo NATS: os
serviços não se conhecem, só trocam envelopes. Serve aos testes rápidos do M3; os processos de
verdade ficam para os testes com NATS e para o `make soak`.

Os ajudantes do mundo (ADR-0072) entram como o processo `helpers`: um runner por avatar, com o
script de cada um, pela lista do arquivo do mundo.

Com `controller="llm"` entra a mente (ADR-0059) sobre uma porta de modelo dada pelo teste (uma
porta falsa, ou a fita em `replay`), medida pelo `MeteredModel`, e opcionalmente a guarda de
orçamento. No escritório, a mente com rotina (ADR-0080), com a oficina num repositório dado pelo
teste (`workshop_repo`, o de exemplo da fita), e o mundo espera a sessão e a revisão da manhã.
Com o dev-script, `workshop_repo` também liga a oficina, como o processo `controller` do sandbox; e
`codehost=True` põe o publicador e o vigia sobre o GitHub falso (ADR-0083): a entrega vira um PR.
O relógio fica no modo contínuo, porque o máximo é só de script e replay (princípio 7);
em memória não faz diferença: o barramento entrega e espera a resposta antes do próximo tick.
"""

import dataclasses
import functools
import sys
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any, Literal, cast

from campsverso_adapters import (
    ContractValidator,
    FakeWallClock,
    InMemoryBus,
    MemoryBlobStore,
    MemoryCodeHost,
    MemoryTelemetry,
    MeteredModel,
    SequentialUuid7Ids,
    SqliteMemory,
    SqliteWorldStore,
    ValidatingBus,
    files_after_patch,
    load_env,
    load_world,
)
from campsverso_adapters.workshop_local import LocalWorkshop
from campsverso_adapters.workshop_review import review
from campsverso_budget.ledger import BudgetLimits
from campsverso_budget.service import BudgetService
from campsverso_cartridge_api import ControllerRef
from campsverso_codehost.service import CodeHostService
from campsverso_controller_runner.office_mind import OfficeMind
from campsverso_controller_runner.replay import Recorded, ReplayRunner
from campsverso_controller_runner.runner import (
    Controller,
    ControllerRunner,
    SimTime,
    load_controller,
    load_mind,
)
from campsverso_controller_runner.workshop import WorkshopSession
from campsverso_kernel.engine import Engine
from campsverso_kernel.service import KernelService
from campsverso_kernel.version import run_version
from campsverso_mind import LlmController, Memory, MemoryProfile, MemorySettings
from campsverso_perception.service import PerceptionService
from campsverso_ports import CallMeter, Effort, Envelope, Hands, MemoryPort, ModelPort
from campsverso_testkit.farm import WORLD, make_core
from campsverso_testkit.nats_server import REPO

DAY = 1440
REPLAY_ID = "replay/teste"
LLM_ID = "llm/camps"
MODEL = "claude-haiku-5-5"
ENV = REPO / "config" / "env" / "local.yaml"
# Os mundos de teste por cartucho (ADR-0062): o id do mundo, o fazendeiro-script, a mente e o avatar
# que o script ou a mente conduz.
WORLDS: dict[str, tuple[str, str, str, str]] = {
    "farm_camps": (WORLD, "farmer", "camps", "camps"),
    "farm_boavista": ("farm-boavista-01", "farmer2", "camps_boavista", "camps"),
    "farm_morada_do_sol": ("farm-morada-do-sol-01", "farmer2", "camps_morada", "camps"),
    # O escritório de teste (ADR-0078): o dev-script, o vigia e o gerente-script; com o modelo, a
    # mente com rotina do M24 (ADR-0080). O dev é o Tiago desde 22/nov (ADR-0092).
    "office_campsverso": ("office-campsverso-teste", "dev", "tiago_escritorio", "tiago"),
}

type ControllerKind = Literal["script", "replay", "none", "llm"]


def _helper(script: str, avatar: str, extra: Mapping[str, Any] | None) -> Controller:
    """O script de um ajudante, com as chaves de `extra` por cima da configuração dele."""
    controller = load_controller(script, avatar)
    if not extra:
        return controller
    found = cast(Any, controller)  # um script com `config` (o gerente-script)
    return cast(Controller, dataclasses.replace(found, config={**found.config, **extra}))


class DeadlockError(Exception):
    """O lockstep esperou um controlador que não respondeu."""


class Pipeline:
    def __init__(
        self,
        seed: int = 20261010,
        *,
        controller: ControllerKind = "script",
        recording: Sequence[Recorded] = (),
        river_bonus: bool = True,
        port: ModelPort | None = None,
        mind: str | None = None,
        budget: BudgetLimits | None = None,
        memory: MemoryPort | bool = True,
        cartridge: str = "farm_camps",
        model: str = MODEL,
        map_variant: str | None = None,
        script: str | None = None,
        playbook: bool = False,
        script_config: Mapping[str, Any] | None = None,
        compare: bool = False,
        advisor: str | None = None,
        full_notebook: bool = False,
        workshop_repo: Path | None = None,
        effort: Effort | None = "medium",
        codehost: bool = False,
        hands: Callable[[CallMeter], Mapping[str, Hands]] | None = None,
        helper_config: Mapping[str, Mapping[str, Any]] | None = None,
        workshop_root: Path | None = None,
        python_env: bool = False,
    ) -> None:
        """`memory=True` dá à mente um caderno SQLite em memória (ADR-0060); `False` é o M10;
        uma porta pronta (um arquivo) serve ao teste de reinício. `cartridge` escolhe o mundo
        (a Fazenda do Camps ou a Boa Vista), com o script e a mente de cada um (ADR-0062);
        `map_variant` escolhe a variante do mapa, e `script` troca o fazendeiro-script
        (ADR-0070); `playbook` dá à mente o método e o ofício (ADR-0071); `script_config` troca
        chaves do arquivo do script 3 (a contratação forçada; ADR-0073); `compare` dá à
        reflexão a ferramenta de comparação, e `advisor`, o conselheiro (ADR-0074); `full_notebook`
        dá à memória o caderno completo (ADR-0074, decisão 35). No escritório, `workshop_repo` é o
        repositório da oficina do dev, e `effort` o esforço da sessão (o dos mundos do
        escritório); `hands` recebe o medidor da mente e devolve as mãos de fora (ADR-0089), e
        `helper_config` troca chaves da configuração do script de um ajudante (o roteiro do
        gerente-script). A oficina fica ao lado do repositório, ou em `workshop_root`; com
        `python_env`, cada espaço ganha o ambiente Python dele (`uv sync`, sem rede), como no
        escritório vivo (a comparação das mãos)."""
        worldid, default_script, default_mind, avatar = WORLDS[cartridge]
        script = script or default_script
        self.worldid, self.cartridge = worldid, cartridge
        self.avatar, self.llm_id = avatar, f"llm/{avatar}"
        mind = mind or default_mind
        self.inner = InMemoryBus()
        self.bus = ValidatingBus(self.inner)
        self.ids = SequentialUuid7Ids()
        self.clock = FakeWallClock()
        self.telemetry = MemoryTelemetry()
        validator = ContractValidator()
        world_file = load_world(REPO / "config" / "worlds" / f"{worldid}.yaml", REPO)
        office = cartridge.startswith("office")
        self._workshop_root = workshop_root
        self._python_env = python_env
        core = make_core(
            seed,
            river_bonus=river_bonus,
            cartridge=cartridge,
            map_variant=map_variant,
            worldid=worldid if office else None,
            start=world_file.start if office else None,
        )
        # Um dia em ticks pelo relógio do cartucho: 1.440 na fazenda, 43.200 no escritório.
        self.day = core.calendar.ticks_per_minute * DAY
        if controller == "replay":
            core.configure_controllers({self.avatar: ControllerRef("replay", REPLAY_ID)})
        if controller == "llm":
            core.configure_controllers({self.avatar: ControllerRef("llm", self.llm_id)})
            core.configure_clock("continuous", None, False)
        else:
            core.configure_clock("max", None, False)
        self.validator = validator
        self.version = run_version(cartridge, core.calendar.ticks_per_minute * 60)
        self.store, self.blobs = SqliteWorldStore(":memory:"), MemoryBlobStore()
        engine = Engine(core, self.version, validator)
        self.kernel = KernelService(
            engine, self.bus, self.clock, self.ids, self.store, self.blobs, self.telemetry
        )
        self.core = core
        self.perception = PerceptionService(
            worldid, self.bus, MemoryBlobStore(), self.clock, self.ids, self.telemetry
        )
        self.runner: ControllerRunner | ReplayRunner | None = None
        self.mind: LlmController | None = None
        self.office_mind: OfficeMind | None = None
        self.deliveries = MemoryBlobStore()  # os patches da oficina do escritório
        self.script: Controller | None = None  # o fazendeiro-script (a prova lê o modelo dele)
        self.guard: BudgetService | None = None
        if controller == "script":
            farmer = load_controller(script)
            if script_config:
                configured = getattr(farmer, "configured", None)
                if configured is None:
                    raise ValueError(f"o script {script!r} não aceita configuração")
                farmer = cast(Controller, configured(script_config))
            self.script = farmer
            # O avatar nasce com o script do cartucho; outro script (o 3, o oráculo) pede a posse.
            core.configure_controllers({self.avatar: ControllerRef("script", farmer.controller_id)})
            self.runner = ControllerRunner(
                worldid,
                self.avatar,
                farmer,
                self.bus,
                self.ids,
                self.clock,
                self.telemetry,
                workshop=None
                if workshop_repo is None
                else self._workshop(worldid, workshop_repo, self.avatar),
            )
        elif controller == "replay":
            self.runner = ReplayRunner(
                worldid,
                self.avatar,
                REPLAY_ID,
                recording,
                self.bus,
                self.ids,
                self.clock,
                self.telemetry,
            )
        elif controller == "llm":
            if port is None:
                raise ValueError("o controlador llm precisa de uma porta de modelo (port=...)")
            sim_time = SimTime()
            metered = MeteredModel(
                port,
                bus=self.bus,
                worldid=worldid,
                cartridge=cartridge,
                controller={"type": "llm", "id": self.llm_id},
                prices=load_env(ENV).models,
                clock=self.clock,
                ids=self.ids,
                sim_clock=sim_time,
            )
            notebook: Memory | None = None
            store: MemoryPort | None
            if isinstance(memory, bool):
                store = SqliteMemory(":memory:") if memory else None
            else:
                store = memory
            package = load_mind(mind)
            if store is not None:
                settings = MemorySettings(
                    compare=compare,
                    advisor=advisor,
                    full_notebook=full_notebook,
                    profile=package.memory or MemoryProfile(),  # o do escritório, ou o da fazenda
                )
                notebook = Memory(store, self.avatar, settings)
            elif compare or advisor or full_notebook:
                raise ValueError(
                    "a comparação, o conselheiro e o caderno completo são da reflexão: precisam "
                    "de memória"
                )
            if advisor is not None:
                metered.assert_priced(advisor)
            brain: LlmController | OfficeMind
            workshop: WorkshopSession | None = None
            if office:
                if workshop_repo is None:
                    raise ValueError("o escritório precisa de um repositório: workshop_repo")
                workshop = self._workshop(worldid, workshop_repo, self.avatar)
                brain = self.office_mind = OfficeMind(
                    load_controller(script, self.avatar),
                    package,
                    metered,
                    workshop,
                    controller_id=self.llm_id,
                    avatar_id=self.avatar,
                    model=model,
                    session_tools=package.workshop,
                    session_instructions=package.session,
                    chat_instructions=package.conversation,
                    effort=effort,
                    telemetry=self.telemetry,
                    memory=notebook,
                    background=False,  # o mundo espera a sessão: a fita reproduz o dia
                    hands=None if hands is None else hands(metered),
                    hands_instructions=package.hands_session,
                    spent=metered.ticket_cost,
                )
            else:
                brain = self.mind = LlmController(
                    package,
                    metered,
                    controller_id=self.llm_id,
                    avatar_id=self.avatar,
                    model=model,
                    telemetry=self.telemetry,
                    memory=notebook,
                    with_playbook=playbook,
                )
            runner = ControllerRunner(
                worldid,
                self.avatar,
                brain,
                self.bus,
                self.ids,
                self.clock,
                self.telemetry,
                cartridge=cartridge,
                sim_time=sim_time,
            )
            if self.office_mind is not None and workshop is not None:
                self.office_mind.propose = runner.propose_now
                workshop.publish = runner.publish_observed
            self.runner = runner
        # Os controladores do arquivo do mundo (o gerente-script do escritório de teste).
        core.configure_controllers(
            {
                avatar: ControllerRef(cast(Any, kind), cid)
                for avatar, (kind, cid) in world_file.controllers.items()
            }
        )
        # Os outros devs do mundo (ADR-0093), como o processo `controller`: o dev-script de cada um,
        # com a oficina dele. O avatar principal fica com o controlador escolhido acima.
        self.devs = [
            ControllerRunner(
                worldid,
                dev,
                load_controller(world_file.script, dev),
                self.bus,
                self.ids,
                self.clock,
                self.telemetry,
                workshop=None
                if workshop_repo is None
                else self._workshop(worldid, workshop_repo, dev),
            )
            for dev in world_file.devs
            if dev != self.avatar
        ]
        # Os ajudantes (ADR-0072), como o processo `helpers`: um runner e um script por avatar.
        self.helpers = [
            ControllerRunner(
                worldid,
                avatar,
                _helper(world_file.helper_script, avatar, (helper_config or {}).get(avatar)),
                self.bus,
                self.ids,
                self.clock,
                self.telemetry,
            )
            for avatar in world_file.helpers
        ]
        if budget is not None:
            self.guard = BudgetService(
                worldid, budget, self.bus, MemoryBlobStore(), self.clock, self.ids, self.telemetry
            )
        self.host: MemoryCodeHost | None = None
        self.codehost: CodeHostService | None = None
        if codehost:
            if workshop_repo is None:
                raise ValueError("o publicador precisa do repositório da oficina: workshop_repo")
            self.host = MemoryCodeHost()
            self.codehost = CodeHostService(
                worldid,
                self.bus,
                self.host,
                self.deliveries,
                MemoryBlobStore(),
                functools.partial(files_after_patch, workshop_repo),
                lambda diff: review(diff, []),
                [],
                self.clock,
                self.ids,
                self.telemetry,
            )

    def _workshop(self, worldid: str, repo: Path, avatar: str) -> WorkshopSession:
        """A oficina de um dev num clone do repositório dado, com as entregas em `deliveries`."""
        shop = LocalWorkshop(
            repo,
            self._workshop_root or repo.parent / "oficina",
            python_env=self._python_env,
            python=None if self._python_env else Path(sys.executable),
        )
        return WorkshopSession(
            worldid, avatar, shop, self.deliveries, lambda diff: review(diff, [])
        )

    async def start(self) -> None:
        if self.guard is not None:
            await self.guard.start()
        if self.codehost is not None:
            await self.codehost.start()
        await self.perception.start()
        if self.runner is not None:
            await self.runner.start()
        for dev in self.devs:
            await dev.start()
        for helper in self.helpers:
            await helper.start()
        await self.kernel.start()

    async def run_until(self, tick: int) -> None:
        while self.core.tick < tick:
            if await self.kernel.run_ticks(min(60, tick - self.core.tick)) == 0:
                raise DeadlockError(f"o lockstep parou no tick {self.core.tick}")

    async def run_days(self, days: int) -> None:
        await self.run_until(self.core.tick + days * self.day)

    @property
    def envelopes(self) -> list[Envelope]:
        return [envelope for _, envelope in self.inner.published]

    def kernel_events(self) -> list[Envelope]:
        return [e for e in self.envelopes if str(e["source"]).startswith("/kernel/")]

    def of_type(self, event: str) -> list[dict[str, Any]]:
        return [dict(e["data"]) for e in self.envelopes if e["type"] == f"campsverso.{event}"]
