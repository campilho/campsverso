"""Núcleo determinístico do kernel: recebe comandos, avança ticks e produz fatos (ADR-0038).

Não lê relógio de parede, não faz IO e não conhece fazendas: só o modelo de mundo (ADR-0025).
"""

import math
from collections import deque
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import datetime
from typing import Any, Literal, cast

from campsverso_cartridge_api import (
    Accepted,
    ActionContext,
    ControllerRef,
    DailyAt,
    OnSessionStart,
    OnThreshold,
    Position,
    Rechecked,
    Rejection,
    SystemContext,
    SystemSpec,
    Validation,
)
from campsverso_kernel.calendar import Calendar, parse_hhmm
from campsverso_kernel.definition import WorldDefinition
from campsverso_kernel.facts import Fact, FactLog
from campsverso_kernel.rng import RngStreams
from campsverso_kernel.rules import RulesEngine
from campsverso_kernel.space import corners, find_path, nearest
from campsverso_kernel.world import (
    Avatar,
    RunningAction,
    Trajectory,
    World,
    controller_data,
    plain,
    position_data,
    to_units,
)
from campsverso_ports import RuleConfig

type ClockMode = Literal["continuous", "max"]

PROPOSE = "campsverso.cmd.action.propose.v1"
# Quando vários motivos se acumulam, o pedido de decisão leva o mais importante.
REASON_PRECEDENCE = (
    "possessed",
    "session_started",
    "woke_up",
    "action_completed",
    "action_rejected",
    "action_interrupted",
    "need_threshold",
    "phase_changed",
)
LOCKSTEP_CONTROLLERS = frozenset({"script", "replay"})  # modo máximo (escopo §5)


@dataclass(frozen=True, slots=True)
class WorldConfig:
    worldid: str
    seed: int
    start: datetime  # data-base do calendário, com fuso (ADR-0038)
    map: str | None = None  # a variante do mapa (ADR-0070); None: o mapa do cartucho


class KernelCore:
    def __init__(
        self,
        definition: WorldDefinition,
        config: WorldConfig,
        rules: Sequence[RuleConfig] = (),
        rules_source: str = "",
    ) -> None:
        self.definition = definition
        self.config = config
        self.calendar = Calendar.create(config.start, definition.clock, definition.year)
        self.log = FactLog()
        self.world = World(
            definition,
            self.calendar,
            RngStreams(config.seed),
            RulesEngine(definition.rule_impls, rules),
            self.log,
        )
        self.rules_source = rules_source
        self.mode: ClockMode = "continuous"
        self.scale = float(definition.clock.default_scale)
        self.paused = False
        self.tiles_per_tick = definition.tiles_per_minute / self.calendar.ticks_per_minute
        self._queue: deque[Mapping[str, Any]] = deque()
        self._scheduled: list[tuple[int, Mapping[str, Any]]] = []  # (at_tick, comando) do replay
        self._initial_controllers: dict[str, ControllerRef] = {}
        self._action_counter = 0
        self._triggered: list[tuple[SystemSpec, OnThreshold, str]] = []
        self._phases = {parse_hhmm(hhmm): name for name, hhmm in definition.clock.phases}
        self._daily = self._index_daily()
        self._handlers: dict[str, Callable[[], None]] = {
            "scheduled": self._stage_scheduled,
            "clock": self._stage_clock,
            "needs": self._stage_needs,
            "wake": self._stage_wake,
            "actions": self._stage_actions,
            "commands": self._stage_commands,
            "decisions": self._stage_decisions,
        }
        self._control: dict[str, Callable[[Mapping[str, Any], Mapping[str, Any]], str | None]] = {
            "campsverso.cmd.clock.set_mode.v1": self._set_mode,
            "campsverso.cmd.clock.set_scale.v1": self._set_scale,
            "campsverso.cmd.clock.pause.v1": self._pause,
            "campsverso.cmd.clock.resume.v1": self._resume,
            "campsverso.cmd.clock.step.v1": self._step_command,
            "campsverso.cmd.avatar.possess.v1": self._possess,
            "campsverso.cmd.avatar.release.v1": self._release,
            "campsverso.cmd.rules.toggle.v1": self._toggle_rule,
        }

    # ------------------------------------------------------------- estado público

    @property
    def tick(self) -> int:
        return self.world.tick

    def drain(self) -> list[Fact]:
        return self.log.drain()

    def _index_daily(self) -> dict[tuple[str, int], list[SystemSpec]]:
        index: dict[tuple[str, int], list[SystemSpec]] = {}
        for system in self.definition.systems.values():
            for trigger in system.triggers:
                if isinstance(trigger, DailyAt):
                    for hhmm in trigger.times:
                        index.setdefault((system.stage, parse_hhmm(hhmm)), []).append(system)
        return {key: sorted(set(v), key=lambda s: (s.priority, s.name)) for key, v in index.items()}

    def describe_order(self, hhmm: str) -> list[str]:
        """Ordem efetiva das etapas e sistemas num horário (ADR-0037), para o teste."""
        minute = parse_hhmm(hhmm)
        lines: list[str] = []
        for stage in self.definition.stages:
            parts = ["kernel"] if stage in self._handlers else []
            parts += [f"{s.name}({s.priority})" for s in self._daily.get((stage, minute), [])]
            if stage == "clock" and minute in self._phases:
                parts.append(f"fase:{self._phases[minute]}")
            lines.append(f"{stage}: {', '.join(parts) or '-'}")
        return lines

    def configure_controllers(self, controllers: Mapping[str, ControllerRef]) -> None:
        """Quem controla cada avatar quando um mundo novo começa (config/worlds/), antes de `start`.

        O controlador padrão continua o do cartucho: é para ele que `release` devolve o avatar.
        """
        unknown = sorted(set(controllers) - set(self.definition.avatars))
        if unknown:
            raise ValueError(f"avatares inexistentes: {unknown}")
        self._initial_controllers = dict(controllers)

    def configure_clock(self, mode: ClockMode, scale: float | None, paused: bool) -> None:
        """Estado inicial do relógio de um mundo novo, antes de `start` (config/worlds/)."""
        initial = {a.entity_id: a.default_controller for a in self.definition.avatars.values()}
        initial |= self._initial_controllers
        if mode == "max" and any(c.type not in LOCKSTEP_CONTROLLERS for c in initial.values()):
            raise ValueError("o modo max só é permitido com controladores script ou replay")
        if scale is not None and scale <= 0:
            raise ValueError("a escala precisa ser positiva")
        self.mode, self.paused = mode, paused
        self.scale = self.scale if scale is None else float(scale)

    # ------------------------------------------------------------- snapshot (M2)

    def export_state(self) -> dict[str, Any]:
        """Tudo o que muda durante a simulação; a definição vem de novo dos cartuchos."""
        return {
            "mode": self.mode,
            "scale": self.scale,
            "paused": self.paused,
            "queue": [plain(command) for command in self._queue],
            "scheduled": [[tick, plain(command)] for tick, command in self._scheduled],
            "action_counter": self._action_counter,
            "triggered": [
                {
                    "system": system.name,
                    "need": trigger.need,
                    "value": trigger.value,
                    "direction": trigger.direction,
                    "avatar_id": avatar_id,
                }
                for system, trigger, avatar_id in self._triggered
            ],
            "next_seq": self.log.next_seq,
            "world": self.world.export_state(),
        }

    def restore_state(self, state: Mapping[str, Any]) -> None:
        self.mode = cast(ClockMode, state["mode"])
        self.scale = float(state["scale"])
        self.paused = bool(state["paused"])
        self._queue = deque(cast(list[Mapping[str, Any]], state["queue"]))
        self._scheduled = [
            (int(tick), cast(Mapping[str, Any], command)) for tick, command in state["scheduled"]
        ]
        self._action_counter = int(state["action_counter"])
        self._triggered = []
        for raw in cast(list[Mapping[str, Any]], state["triggered"]):
            system = self.definition.systems[str(raw["system"])]
            trigger = next(
                t
                for t in system.triggers
                if isinstance(t, OnThreshold)
                and (t.need, t.value, t.direction) == (raw["need"], raw["value"], raw["direction"])
            )
            self._triggered.append((system, trigger, str(raw["avatar_id"])))
        self.log.next_seq = int(state["next_seq"])
        self.world.import_state(cast(Mapping[str, Any], state["world"]))

    # ------------------------------------------------------------- sessão

    def _perception(self) -> dict[str, Any]:
        """A configuração da percepção declarada pelo cartucho (ADR-0056, ADR-0067, ADR-0068)."""
        d = self.definition
        config: dict[str, Any] = {"radius": d.perception_radius}
        if d.perception_landmarks:
            config["landmarks"] = list(d.perception_landmarks)
        if d.perception_by_phase:
            config["by_phase"] = dict(d.perception_by_phase)
        if d.perception_lights:
            config["lights"] = dict(d.perception_lights)
        return config

    def _affordances(self) -> dict[str, Any]:
        """O catálogo de ações do cartucho, para quem joga (ADR-0051); ausente se não houver."""
        catalog: list[dict[str, Any]] = []
        for a in self.definition.affordances:
            entry: dict[str, Any] = {
                "action": a.action,
                "label": a.label,
                "on": list(a.on),
                "target": a.target,
            }
            params: list[dict[str, Any]] = []
            for p in a.params:
                param: dict[str, Any] = {"name": p.name, "label": p.label, "source": p.source}
                if p.choices:
                    param["choices"] = list(p.choices)
                if p.minimum is not None:
                    param["minimum"] = p.minimum
                if p.default is not None:
                    param["default"] = p.default
                if p.entities:
                    param["entities"] = True
                params.append(param)
            if params:
                entry["params"] = params
            catalog.append(entry)
        return {"affordances": catalog} if catalog else {}

    def _metrics(self) -> dict[str, Any]:
        """O catálogo de métricas do dia (ADR-0054); ausente se o cartucho não declarar nenhuma."""
        catalog: list[dict[str, Any]] = []
        for m in self.definition.metrics:
            entry: dict[str, Any] = {"id": m.id, "label": m.label, "kind": m.kind}
            if m.event is not None:
                entry["event"] = m.event
            if m.where:
                entry["where"] = dict(m.where)
            if m.by_field is not None:
                entry["by"] = {"field": m.by_field} | (
                    {"attribute": m.by_attribute} if m.by_attribute else {}
                )
            if m.need is not None:
                entry["need"] = m.need
            if m.item is not None:
                entry["item"] = m.item
            if m.field is not None:
                entry["field"] = m.field
            catalog.append(entry)
        return {"metrics": catalog} if catalog else {}

    def _labels(self) -> dict[str, Any]:
        """Os rótulos da linha do tempo (ADR-0068); ausente se o cartucho não declarar nenhum."""
        catalog = [
            {"event": x.event, "text": x.text} | ({"where": dict(x.where)} if x.where else {})
            for x in self.definition.labels
        ]
        return {"labels": catalog} if catalog else {}

    def start(self) -> None:
        world = self.world
        grid = self.definition.grid
        rows, legend = grid.terrain()  # o terreno inteiro, uma vez (ADR-0056)
        world.emit_fact(
            "campsverso.world.session.started.v1",
            {
                "cartridge_version": self.definition.top.version,
                "seed": self.config.seed,
                "tick_seconds": self.calendar.tick_seconds,
                "mode": self.mode,
                "paused": self.paused,
                "scale": self.scale,
                "resumed": False,
                "map": {
                    "id": grid.map_id,
                    "width": grid.width,
                    "height": grid.height,
                    "rows": rows,
                    "legend": legend,
                },
                "perception": self._perception(),
                **self._affordances(),
                **self._metrics(),
                **self._labels(),
            },
        )
        world.emit_fact(
            "campsverso.rules.loaded.v1",
            {"rules": world.rules.loaded(), "source_ref": self.rules_source or "(nenhum)"},
        )
        world.spawn_all()
        for avatar_id, controller in sorted(self._initial_controllers.items()):
            world.avatar_map[avatar_id].controller = controller
        for avatar in world.avatar_map.values():
            world.emit_fact(
                "campsverso.avatar.possessed.v1",
                {
                    "avatar_id": avatar.avatar_id,
                    "controller": controller_data(avatar.controller),
                    "by": "system/kernel",
                },
            )
            avatar.add_pending("session_started")
        starters = [
            s
            for s in self.definition.systems.values()
            if any(isinstance(t, OnSessionStart) for t in s.triggers)
        ]
        for system in sorted(starters, key=lambda s: (s.priority, s.name)):
            with world.context(cause=system.name):
                system.run(SystemContext(world, OnSessionStart()), world)

    # ------------------------------------------------------------- comandos

    @property
    def has_pending_proposals(self) -> bool:
        """Há proposta esperando a etapa `commands` do próximo tick (ADR-0057)."""
        return bool(self._queue)

    @property
    def lockstep_blocked(self) -> bool:
        """No modo máximo, o relógio espera o controlador que deve uma decisão (escopo §5)."""
        return self.mode == "max" and any(
            a.awaiting and a.controller.type in LOCKSTEP_CONTROLLERS
            for a in self.world.avatar_map.values()
        )

    def submit(self, command: Mapping[str, Any]) -> None:
        """Propostas de ação esperam a etapa `commands`; controle vale já (ADR-0037).

        Uma proposta com `at_tick` no futuro (controlador replay) espera esse tick.
        """
        command_type = str(command.get("type", ""))
        if command_type == PROPOSE:
            data = cast(Mapping[str, Any], command.get("data") or {})
            avatar = self.world.avatar_map.get(str(data.get("avatar_id")))
            if avatar is not None and command.get("controllerid") == avatar.controller.id:
                avatar.awaiting = False
            at_tick = data.get("at_tick")
            if isinstance(at_tick, int) and at_tick > self.tick:
                self._scheduled.append((at_tick, command))
            else:
                self._queue.append(command)
            return
        handler = self._control.get(command_type)
        if handler is None:
            self.reject_command(command, "unknown_command")
            return
        try:
            reason = handler(command, cast(Mapping[str, Any], command.get("data") or {}))
        except (KeyError, TypeError, ValueError) as error:
            reason = f"invalid_command:{error}"
        if reason is not None:
            code, _, detail = reason.partition(":")
            self.reject_command(command, code, detail or None)

    def reject_command(
        self, command: Mapping[str, Any], reason: str, detail: str | None = None
    ) -> None:
        data: dict[str, Any] = {
            "command_id": str(command.get("id", "")),
            "command_type": str(command.get("type", "")),
            "reason": reason,
        }
        if detail:
            data["detail"] = detail
        self.world.emit_fact(
            "campsverso.world.command.rejected.v1", data, caused_by=data["command_id"]
        )

    @staticmethod
    def _by(command: Mapping[str, Any]) -> str:
        return str(command.get("actor") or command.get("controllerid") or "unknown")

    def _set_mode(self, command: Mapping[str, Any], data: Mapping[str, Any]) -> str | None:
        mode = cast(ClockMode, data["mode"])
        if mode == self.mode:
            return "no_change"
        if mode == "max" and any(
            a.controller.type not in LOCKSTEP_CONTROLLERS for a in self.world.avatar_map.values()
        ):
            return "mode_not_allowed:o modo max só é permitido com controladores script ou replay"
        previous, self.mode = self.mode, mode
        self.world.emit_fact(
            "campsverso.world.clock.mode_changed.v1",
            {
                "previous_mode": previous,
                "mode": mode,
                "reason": str(data.get("reason") or "operator"),
                "by": self._by(command),
            },
            caused_by=str(command.get("id")),
        )
        return None

    def _set_scale(self, command: Mapping[str, Any], data: Mapping[str, Any]) -> str | None:
        scale = float(data["scale"])
        if scale <= 0:
            return "invalid_command:a escala precisa ser positiva"
        previous, self.scale = self.scale, scale
        self.world.emit_fact(
            "campsverso.world.clock.scale_changed.v1",
            {
                "previous_scale": previous,
                "scale": scale,
                "reason": data["reason"],
                "by": self._by(command),
            },
            caused_by=str(command.get("id")),
        )
        return None

    def _pause(self, command: Mapping[str, Any], data: Mapping[str, Any]) -> str | None:
        if self.paused:
            return "already_paused"
        self.paused = True
        self.world.emit_fact(
            "campsverso.world.clock.paused.v1",
            {"reason": data["reason"], "by": self._by(command)},
            caused_by=str(command.get("id")),
        )
        return None

    def _resume(self, command: Mapping[str, Any], _: Mapping[str, Any]) -> str | None:
        if not self.paused:
            return "not_paused"
        self.paused = False
        self.world.emit_fact(
            "campsverso.world.clock.resumed.v1",
            {"by": self._by(command)},
            caused_by=str(command.get("id")),
        )
        return None

    def _step_command(self, command: Mapping[str, Any], data: Mapping[str, Any]) -> str | None:
        if not self.paused:
            return "not_paused:o passo a passo só vale com o relógio pausado (ADR-0026)"
        ticks = int(data["ticks"])
        start = self.tick
        for _ in range(ticks):
            self.step()
        self.world.emit_fact(
            "campsverso.world.clock.stepped.v1",
            {"ticks": ticks, "from_tick": start, "to_tick": self.tick},
            caused_by=str(command.get("id")),
        )
        return None

    def _possess(self, command: Mapping[str, Any], data: Mapping[str, Any]) -> str | None:
        avatar = self.world.avatar_map.get(str(data["avatar_id"]))
        if avatar is None:
            return "unknown_avatar"
        raw = cast(Mapping[str, Any], data["controller"])
        controller = ControllerRef(raw["type"], str(raw["id"]))
        if controller == avatar.controller:
            return "no_change"
        if self.mode == "max" and controller.type not in LOCKSTEP_CONTROLLERS:
            return "mode_not_allowed:no modo max só script ou replay assumem o avatar"
        previous, avatar.controller = avatar.controller, controller
        avatar.awaiting = False
        self.world.emit_fact(
            "campsverso.avatar.possessed.v1",
            {
                "avatar_id": avatar.avatar_id,
                "previous_controller": controller_data(previous),
                "controller": controller_data(controller),
                "by": self._by(command),
            },
            caused_by=str(command.get("id")),
        )
        avatar.add_pending("possessed")
        return None

    def _release(self, command: Mapping[str, Any], data: Mapping[str, Any]) -> str | None:
        avatar = self.world.avatar_map.get(str(data["avatar_id"]))
        if avatar is None:
            return "unknown_avatar"
        if avatar.controller == avatar.default_controller:
            return "no_change"
        previous, avatar.controller = avatar.controller, avatar.default_controller
        avatar.awaiting = False
        self.world.emit_fact(
            "campsverso.avatar.released.v1",
            {
                "avatar_id": avatar.avatar_id,
                "previous_controller": controller_data(previous),
                "controller": controller_data(avatar.controller),
                "by": self._by(command),
            },
            caused_by=str(command.get("id")),
        )
        avatar.add_pending("possessed")
        return None

    def _toggle_rule(self, command: Mapping[str, Any], data: Mapping[str, Any]) -> str | None:
        rule = str(data["rule"])
        if not self.world.rules.knows(rule):
            return "unknown_rule"
        params = cast(Mapping[str, Any] | None, data.get("params"))
        version = self.world.rules.toggle(rule, bool(data["enabled"]), params)
        payload: dict[str, Any] = {
            "rule": rule,
            "from_version": version,
            "to_version": version,
            "enabled": bool(data["enabled"]),
            "by": self._by(command),
            "reason": str(data["reason"]),
            "effective_at_tick": self.tick,
        }
        if params is not None:
            payload["params"] = dict(params)
        if data.get("experiment_id"):
            payload["experiment_id"] = str(data["experiment_id"])
        self.world.emit_fact(
            "campsverso.rules.toggled.v1", payload, caused_by=str(command.get("id"))
        )
        return None

    # ------------------------------------------------------------- tick

    def step(self) -> None:
        """Roda as etapas do tick corrente e avança um tick."""
        for stage in self.definition.stages:
            handler = self._handlers.get(stage)
            if handler is not None:
                handler()
            self._collect_crossings()
            self._run_systems(stage)
        self.world.tick += 1

    def advance(self, ticks: int, *, jump: bool = False) -> None:
        """Avança `ticks` ticks. Com `jump`, salta trechos em que nada acontece (tempo §4)."""
        target = self.tick + ticks
        while self.tick < target:
            if jump:
                due = min(self.next_due_tick(), target)
                if due > self.tick:
                    start = self.tick
                    self.world.integrate_needs(due - start)
                    self.world.emit_fact(
                        "campsverso.world.clock.jumped.v1", {"from_tick": start, "to_tick": due}
                    )
                    self.world.tick = due
                    continue
            self.step()

    def _collect_crossings(self) -> None:
        for avatar_id, threshold in self.world.crossings:
            for system in self.definition.systems.values():
                for trigger in system.triggers:
                    if isinstance(trigger, OnThreshold) and (
                        trigger.need,
                        trigger.value,
                        trigger.direction,
                    ) == (threshold.need, threshold.value, threshold.direction):
                        self._triggered.append((system, trigger, avatar_id))
        self.world.crossings.clear()

    def _run_systems(self, stage: str) -> None:
        world = self.world
        if self.calendar.is_minute_start(self.tick):
            minute = self.calendar.minute_of_day(self.tick)
            for system in self._daily.get((stage, minute), []):
                trigger = next(t for t in system.triggers if isinstance(t, DailyAt))
                with world.context(cause=system.name):
                    system.run(SystemContext(world, trigger), world)
        ready = sorted(
            (item for item in self._triggered if item[0].stage == stage),
            key=lambda item: (item[0].priority, item[0].name, item[2]),
        )
        self._triggered = [item for item in self._triggered if item[0].stage != stage]
        for system, trigger, avatar_id in ready:
            with world.context(cause=system.name):
                system.run(SystemContext(world, trigger, avatar_id), world)

    def _stage_scheduled(self) -> None:
        """Antes dos sistemas agendados: na virada do dia, o kernel estraga o que venceu
        (ADR-0062). Nada a fazer sem lotes."""
        if (
            self.world.lots
            and self.calendar.is_minute_start(self.tick)
            and self.calendar.minute_of_day(self.tick) == self.calendar.day_starts_at
        ):
            with self.world.context(cause="spoilage"):
                self.world.spoil()

    def _stage_clock(self) -> None:
        if not self.calendar.is_minute_start(self.tick):
            return
        minute, day = self.calendar.minute_of_day(self.tick), self.world.day
        season = self.calendar.season(day)
        if minute == self.calendar.day_starts_at and day > 1 and season is not None:
            previous = self.calendar.season(day - 1)
            if season != previous:  # a virada do dia que troca a estação (ADR-0067)
                self.world.emit_fact(
                    "campsverso.world.clock.season_changed.v1",
                    {"day": day, "date": self.world.date(day), "season": season}
                    | ({"previous_season": previous} if previous else {}),
                )
        phase = self._phases.get(minute)
        if phase is None:
            return
        data: dict[str, Any] = {"phase": phase, "day": day}
        if season is not None:
            data |= {"date": self.world.date(day), "season": season}
        self.world.emit_fact("campsverso.world.clock.phase_changed.v1", data)
        for avatar in self.world.avatar_map.values():
            if avatar.present:  # quem está fora do mundo não decide nada (ADR-0072)
                avatar.add_pending("phase_changed")

    def _stage_needs(self) -> None:
        self.world.integrate_needs(1)
        if (
            self.calendar.is_minute_start(self.tick)
            and self.calendar.minute_of_day(self.tick) % 60 == 0
        ):
            self.world.report_needs()

    def _stage_wake(self) -> None:
        for avatar_id, avatar in sorted(self.world.avatar_map.items()):
            if avatar.asleep and avatar.wake_tick == self.tick:
                self.world.wake(avatar_id)

    def _stage_actions(self) -> None:
        for _, avatar in sorted(self.world.avatar_map.items()):
            if avatar.action is not None and avatar.action.end_tick == self.tick:
                self._complete(avatar)

    def _stage_commands(self) -> None:
        due = [command for tick, command in self._scheduled if tick == self.tick]
        self._scheduled = [
            (tick, command) for tick, command in self._scheduled if tick != self.tick
        ]
        self._queue.extendleft(reversed(due))
        while self._queue:
            self._propose(self._queue.popleft())

    def _has_scheduled(self, avatar: Avatar) -> bool:
        return any(
            command.get("controllerid") == avatar.controller.id
            and cast(Mapping[str, Any], command.get("data") or {}).get("avatar_id")
            == avatar.avatar_id
            for _, command in self._scheduled
        )

    def _stage_decisions(self) -> None:
        for avatar_id, avatar in sorted(self.world.avatar_map.items()):
            if not avatar.present:  # fora do mundo: nada a decidir até entrar (ADR-0072)
                avatar.pending.clear()
                continue
            if avatar.pending and avatar.idle:
                reason = next(r for r in REASON_PRECEDENCE if r in avatar.pending)
                position = self.world.position_of(avatar_id)
                assert position is not None
                self.world.emit_fact(
                    "campsverso.avatar.decision_requested.v1",
                    {
                        "avatar_id": avatar_id,
                        "reason": reason,
                        "controller": controller_data(avatar.controller),
                        "needs": self.world.needs_points(avatar_id),
                        "position": position_data(position),
                    },
                    caused_by=None,
                    correlation=None,
                    opens_correlation=True,
                )
                # Quem já mandou uma proposta agendada (replay) não deve nada ao relógio.
                avatar.awaiting = not self._has_scheduled(avatar)
            avatar.pending.clear()

    # ------------------------------------------------------------- ações

    def _propose(self, command: Mapping[str, Any]) -> None:
        world = self.world
        command_id = str(command.get("id", ""))
        correlation = cast(str | None, command.get("correlationid"))
        data = cast(Mapping[str, Any], command.get("data") or {})
        avatar = world.avatar_map.get(str(data.get("avatar_id")))
        if avatar is None:
            self.reject_command(command, "unknown_avatar")
            return
        name = str(data.get("action", ""))
        params = dict(cast(Mapping[str, Any], data.get("params") or {}))

        def reject(reason: str, detail: str | None = None) -> None:
            payload: dict[str, Any] = {
                "avatar_id": avatar.avatar_id,
                "action": name,
                "params": params,
                "reason": reason,
            }
            if detail:
                payload["detail"] = detail
            world.emit_fact(
                "campsverso.action.rejected.v1",
                payload,
                caused_by=command_id,
                correlation=correlation,
            )
            avatar.add_pending("action_rejected")

        if command.get("controllerid") != avatar.controller.id:
            return reject("not_in_control")
        if not avatar.present:
            return reject("absent", "o avatar está fora do mundo")  # ADR-0072
        at_tick = data.get("at_tick")
        if at_tick is not None:
            if avatar.controller.type != "replay" or self.mode != "max":
                return reject("unsupported", "at_tick só vale do controlador replay no modo máximo")
            if at_tick != self.tick:  # chegou depois do tick pedido
                return reject("too_late", f"at_tick {at_tick}, tick atual {self.tick}")
        if avatar.asleep:
            return reject("busy", "o avatar está dormindo")
        running = avatar.action
        if running is not None and running.interrupt == "never":  # ADR-0052
            return reject("busy", f"{running.name} termina no tick {running.end_tick}")
        action_id = f"act-{self._action_counter + 1:06d}"
        result, trajectory = self._validate(avatar, name, params, action_id)
        if isinstance(result, Rejection):
            return reject(result.reason, result.detail)

        with world.context(caused_by=command_id, correlation=correlation):
            replaced = world.interrupt_action(avatar.avatar_id, "cancelled")
        if running is not None and running.interrupt == "partial":
            # O trabalho guardado pode mudar a validação: retomar a mesma ação fica mais curto.
            result, trajectory = self._validate(avatar, name, params, action_id)
            if isinstance(result, Rejection):
                return reject(result.reason, result.detail)
        self._action_counter += 1
        action = RunningAction(
            action_id=action_id,
            name=name,
            params=params,
            applied_tick=self.tick,
            end_tick=self.tick + result.duration_ticks,
            command_id=command_id,
            correlation=correlation,
            trajectory=trajectory,
            interrupt=result.interrupt,
        )
        avatar.action = action
        accepted: dict[str, Any] = {
            "action_id": action_id,
            "avatar_id": avatar.avatar_id,
            "action": name,
            "params": params,
            "applied_tick": self.tick,
            "duration_ticks": result.duration_ticks,
            "interrupt": result.interrupt,
        }
        if replaced is not None:
            accepted["replaces"] = replaced
        intent = data.get("intent")
        if intent:  # a intenção declarada vai no fato, para a tela e a linha do tempo (ADR-0059)
            accepted["intent"] = str(intent)[:500]
        world.emit_fact(
            "campsverso.action.accepted.v1", accepted, caused_by=command_id, correlation=correlation
        )
        if trajectory is not None:
            world.emit_fact(
                "campsverso.world.entity.moved.v1",
                {
                    "entity_id": avatar.avatar_id,
                    "action_id": action_id,
                    "origin": position_data(trajectory.origin),
                    "waypoints": [position_data(p) for p in corners(trajectory.path)],
                    "depart_tick": self.tick,
                    "arrival_tick": action.end_tick,
                    "tiles_per_tick": trajectory.tiles_per_tick,
                },
                caused_by=command_id,
                correlation=correlation,
            )

    def _validate(
        self, avatar: Avatar, name: str, params: Mapping[str, Any], action_id: str
    ) -> tuple[Validation, Trajectory | None]:
        if name == "move":
            return self._validate_move(avatar, params)
        if name == "wait":
            ticks = params.get("ticks")
            if not isinstance(ticks, int) or not 1 <= ticks <= 60:
                return Rejection("invalid_params", "wait exige ticks entre 1 e 60"), None
            return Accepted(ticks, "cancel"), None  # andar e esperar se cancelam (ADR-0052)
        spec = self.definition.actions.get(name)
        if spec is None:
            return Rejection("unknown_action"), None
        result = spec.validate(ActionContext(avatar.avatar_id, action_id, params, self.world))
        if isinstance(result, Accepted) and result.duration_ticks < 1:
            raise ValueError(f"a ação {name} declarou duração {result.duration_ticks} (mínimo 1)")
        factor = self.world.traits(avatar.avatar_id).time_factor(name)  # a ficha (ADR-0072)
        if isinstance(result, Accepted) and factor != 1.0:
            ticks = max(1, math.ceil(result.duration_ticks * factor - 1e-9))
            result = replace(result, duration_ticks=ticks)
        return result, None

    def _validate_move(
        self, avatar: Avatar, params: Mapping[str, Any]
    ) -> tuple[Validation, Trajectory | None]:
        """`{target: {x, y}}` ou `{near: entity_id | {x, y}}`: no `near`, o tile livre mais perto ao
        lado da coisa ou do tile (ADR-0047; o tile, ADR-0068)."""
        origin = self.world.position_of(avatar.avatar_id)
        assert origin is not None
        raw, near = params.get("target"), params.get("near")
        if (raw is None) == (near is None):
            return Rejection("invalid_params", "move exige target {x, y} ou near"), None
        if near is not None:
            spot = self._near_spot(near)
            if spot is None:
                return Rejection("invalid_params", f"{near!r} não é uma entidade no mapa"), None
            if origin.chebyshev(spot) <= 1:
                return Rejection("already_there"), None
            around = (
                Position(spot.x + dx, spot.y + dy)
                for dy in (-1, 0, 1)
                for dx in (-1, 0, 1)
                if (dx, dy) != (0, 0)
            )
            target = nearest(origin, around, self.world.walkable)
            if target is None:
                return Rejection("unreachable"), None
        else:
            if not isinstance(raw, Mapping):
                return Rejection("invalid_params", "move exige target {x, y}"), None
            target_raw = cast(Mapping[str, Any], raw)
            x, y = target_raw.get("x"), target_raw.get("y")
            if not isinstance(x, int) or not isinstance(y, int):
                return Rejection("invalid_params", "move exige target {x, y}"), None
            target = Position(x, y)
            if target == origin:
                return Rejection("already_there"), None
            if not self.world.walkable(target):
                return Rejection("not_passable"), None
        path = find_path(origin, target, self.world.walkable)
        if path is None:
            return Rejection("unreachable"), None
        speed = self.tiles_per_tick * self.world.traits(avatar.avatar_id).speed  # ADR-0072
        duration = max(1, math.ceil((len(path) - 1) / speed - 1e-9))
        trajectory = Trajectory(origin, tuple(path), self.tick, speed)
        return Accepted(duration, "cancel"), trajectory

    def _near_spot(self, near: Any) -> Position | None:
        """Onde fica o `near` de um move: a entidade no mapa, ou um tile `{x, y}` dentro dele."""
        if isinstance(near, str):
            entity = self.world.entity_map.get(near)
            return None if entity is None else self.world.position_of(entity.entity_id)
        if not isinstance(near, Mapping):
            return None
        raw = cast(Mapping[str, Any], near)
        x, y = raw.get("x"), raw.get("y")
        if not isinstance(x, int) or not isinstance(y, int):
            return None
        spot = Position(x, y)
        return spot if self.definition.grid.in_bounds(spot) else None

    def _complete(self, avatar: Avatar) -> None:
        world = self.world
        action = avatar.action
        assert action is not None
        avatar.action = None
        with world.context(
            action=action,
            cause=action.name,
            caused_by=action.command_id,
            correlation=action.correlation,
        ):
            if action.trajectory is not None:
                world.entity_map[avatar.avatar_id].position = action.trajectory.path[-1]
                cost = self.definition.movement_cost
                tiles = len(action.trajectory.path) - 1
                if cost is not None and cost[1] and tiles > 0:  # andar gasta (ADR-0062)
                    world.change_need(avatar.avatar_id, cost[0], -(cost[1] * tiles))
            spec = self.definition.actions.get(action.name)
            ctx = ActionContext(avatar.avatar_id, action.action_id, action.params, world)
            if isinstance(spec, Rechecked) and spec.recheck(ctx) is not None:
                # Outro avatar desfez a ação no meio (ADR-0072): ela não conclui.
                world.emit_fact(
                    "campsverso.action.failed.v1",
                    {
                        "action_id": action.action_id,
                        "avatar_id": avatar.avatar_id,
                        "action": action.name,
                        "reason": "precondition_lost",
                        "elapsed_ticks": self.tick - action.applied_tick,
                    },
                )
                avatar.add_pending("action_interrupted")
                return
            if spec is not None:
                spec.complete(ctx, world)
            world.emit_fact(
                "campsverso.action.completed.v1",
                {
                    "action_id": action.action_id,
                    "avatar_id": avatar.avatar_id,
                    "action": action.name,
                    "params": action.params,
                    "duration_ticks": self.tick - action.applied_tick,
                },
            )
        avatar.add_pending("action_completed")

    # ------------------------------------------------------------- salto de tempo

    def next_due_tick(self) -> int:
        """Próximo tick em que algo pode acontecer; os ticks antes dele só integram necessidades."""
        now = self.tick
        world = self.world
        if (
            self._queue
            or self._triggered
            or any(a.pending and a.present for a in world.avatar_map.values())
        ):
            return now
        candidates_scheduled = [tick for tick, _ in self._scheduled if tick >= now]
        minutes = (
            {minute for _, minute in self._daily}
            | set(self._phases)
            | set(range(0, 1440, 60))
            | {self.calendar.day_starts_at}  # a virada do dia pode trocar a estação (ADR-0067)
        )
        if self.calendar.is_minute_start(now) and self.calendar.minute_of_day(now) in minutes:
            return now
        candidates = [now + self.calendar.ticks_until(now, minute) for minute in minutes]
        candidates += candidates_scheduled
        candidates += [tick for tick in world.modifier_expiries() if tick >= now]
        for avatar_id, avatar in world.avatar_map.items():
            if not avatar.present:  # fora do mundo, nada acontece com ele (ADR-0072)
                continue
            if avatar.action is not None:
                candidates.append(avatar.action.end_tick)
            if avatar.wake_tick is not None:
                candidates.append(avatar.wake_tick)
            for threshold in self.definition.thresholds:
                rate = world.rate(avatar_id, threshold.need)
                units = world.needs[avatar_id][threshold.need]
                level = to_units(threshold.value)
                if threshold.direction == "up" and rate > 0 and units < level:
                    candidates.append(now + math.ceil((level - units) / rate) - 1)
                if threshold.direction == "down" and rate < 0 and units > level:
                    candidates.append(now + math.ceil((units - level) / -rate) - 1)
        return max(now, min(candidates))
