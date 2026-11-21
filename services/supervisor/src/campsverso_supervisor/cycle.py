"""O ciclo do supervisor do escritório vivo: o auto-update (ADR-0083).

O escritório roda de uma de duas worktrees, `a` e `b`, cada uma presa num commit. A cada volta:

1. **Olhar:** busca o `origin/main`. O mesmo commit que roda, ou um que já falhou, não muda nada.
2. **Preparar, ao lado:** põe o commit novo na outra worktree e prepara as dependências e a tela.
   O escritório segue rodando.
3. **A fumaça, numa cópia:** a versão nova sobe sobre uma cópia dos dados, com o NATS próprio, e
   anda um tempo simulado. Se falha, o commit é recusado, e nada muda.
4. **Esperar a hora:** com o dev numa sessão na oficina, espera ela acabar, até 30 minutos.
5. **Guardar a volta:** para o escritório com elegância (o kernel grava o snapshot) e copia os dados
   e o NATS. Ficam as três últimas cópias.
6. **A troca:** sobe a outra worktree sobre os mesmos dados, sem o arquivador.
7. **A saúde:** por 2 minutos, nenhum processo cai, o gateway responde e o pulso do kernel anda.
8. **Deu certo:** liga o arquivador, e a worktree nova passa a ser a viva. O kernel já publicou a
   troca (`world.version.changed`), pelo commit que o supervisor lhe disse.
9. **Deu errado:** para a versão nova, devolve os dados e o NATS guardados e sobe de novo a
   worktree de antes, que ficou intacta. O commit fica recusado até chegar outro.

O arquivador só liga depois da saúde: o arquivo é o registro histórico e nunca se reescreve, então
o que a versão nova publicou numa troca que voltou fica fora dele.

Trocar de papel entre duas worktrees, em vez de mudar a viva de commit, deixa a troca e a volta
rápidas: a worktree nova já tem as dependências e a tela prontas, e a de antes fica como estava.
"""

import asyncio
import contextlib
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from campsverso_supervisor.state import Journal, State, Swap


@dataclass(frozen=True)
class Build:
    """A versão que uma pilha roda, como o kernel e a placa a recebem."""

    commit: str
    date: str
    pull_requests: tuple[int, ...] = ()


@dataclass(frozen=True)
class Health:
    """O que o `/health` do gateway diz."""

    tick: int
    alive: bool  # o pulso do kernel chega
    busy: bool  # um dev numa sessão na oficina


class Releases(Protocol):
    async def fetch(self) -> str:
        """O commit do `origin/main` agora."""
        ...

    async def build(self, commit: str, since: str | None) -> Build:
        """A data do commit e os PRs mesclados desde `since`."""
        ...

    async def place(self, slot: Path, commit: str) -> None:
        """A worktree `slot` presa em `commit`, criada se preciso."""
        ...

    async def prepare(self, slot: Path) -> None:
        """As dependências e a tela da worktree, prontas para subir."""
        ...

    def prepared(self, slot: Path) -> bool:
        """A worktree já tem as dependências (o `.venv`)."""
        ...


class Running(Protocol):
    def dead(self) -> list[str]: ...

    async def health(self) -> Health | None: ...

    async def start_archiver(self) -> None: ...

    async def stop(self) -> None: ...


class Stacks(Protocol):
    async def start(self, slot: Path, build: Build, *, archiver: bool) -> Running: ...

    async def smoke(self, live: Path, candidate: Path, build: Build) -> str | None:
        """A versão nova numa cópia dos dados: None se passou, ou o motivo."""
        ...


class Vault(Protocol):
    def backup(self, label: str) -> Path: ...

    def restore(self, backup: Path) -> None: ...

    def prune(self, keep: int) -> None: ...


@dataclass(frozen=True)
class Settings:
    poll_seconds: float = 60.0
    health_seconds: float = 120.0
    health_every: float = 5.0
    busy_wait_seconds: float = 1800.0
    busy_every: float = 15.0
    keep_backups: int = 3
    # Um laço de quedas: depois de tantos reinícios na janela, o supervisor espera a janela passar
    # (ou um commit novo, que pode trazer o conserto) em vez de reiniciar de novo.
    restarts: int = 3
    restart_window: float = 600.0


class Supervisor:
    def __init__(
        self,
        home: Path,
        releases: Releases,
        stacks: Stacks,
        vault: Vault,
        journal: Journal,
        settings: Settings | None = None,
        *,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self.home = home
        self._releases = releases
        self._stacks = stacks
        self._vault = vault
        self.journal = journal
        self._settings = settings or Settings()
        self._sleep = sleep
        self._monotonic = monotonic
        self._state_path = home / "estado.json"
        self.state = State.load(self._state_path)
        self.running: Running | None = None
        self.build: Build | None = None
        self._first_healthy: float | None = None  # quando a versão nova respondeu bem
        self._restarted: list[float] = []  # os reinícios recentes, para o laço de quedas

    def slot(self, name: str) -> Path:
        return self.home / name

    def _save(self) -> None:
        self.state.save(self._state_path)

    # ------------------------------------------------------------------ subir

    async def boot(self) -> None:
        """Sobe o escritório: termina a volta de uma troca interrompida, instala a primeira versão
        se não há nenhuma e sobe a viva."""
        if self.state.swap is not None:
            self._finish_interrupted(self.state.swap)
        if self.state.commit is None:
            commit = await self._releases.fetch()
            await self._releases.place(self.slot(self.state.live), commit)
            await self._releases.prepare(self.slot(self.state.live))
            self.state.commit = commit
            self._save()
            self.journal.write("instalou", commit=commit, slot=self.state.live)
        assert self.state.commit is not None
        live = self.slot(self.state.live)
        if not self._releases.prepared(live):  # a worktree sumiu, ou perdeu o .venv
            await self._releases.place(live, self.state.commit)
            await self._releases.prepare(live)
            self.journal.write("preparou", commit=self.state.commit, slot=self.state.live)
        self.build = await self._releases.build(self.state.commit, None)
        self.running = await self._stacks.start(
            self.slot(self.state.live), self.build, archiver=True
        )
        self.journal.write("subiu", commit=self.state.commit, slot=self.state.live)

    def _finish_interrupted(self, swap: Swap) -> None:
        """O supervisor caiu no meio de uma troca: a volta, com os dados de antes dela."""
        self._vault.restore(Path(swap.backup))
        self.state.live, self.state.commit = swap.from_slot, swap.from_commit
        if swap.to_commit not in self.state.rejected:
            self.state.rejected.append(swap.to_commit)
        self.state.swap = None
        self._save()
        self.journal.write(
            "voltou", commit=swap.to_commit, to=swap.from_commit, reason="troca interrompida"
        )

    async def stop(self) -> None:
        if self.running is not None:
            await self.running.stop()
            self.running = None
            self.journal.write("parou", commit=self.state.commit)

    async def run(self, stop: asyncio.Event) -> None:
        await self.boot()
        try:
            while not stop.is_set():
                await self.turn()
                with contextlib.suppress(TimeoutError):
                    await asyncio.wait_for(stop.wait(), self._settings.poll_seconds)
        finally:
            await self.stop()

    # ------------------------------------------------------------------ uma volta

    async def turn(self) -> str:
        """Uma volta do ciclo; devolve o que aconteceu, para os testes e o diário."""
        assert self.running is not None
        waiting = False
        if dead := self.running.dead():
            if self._may_restart():
                return await self._restart(dead)
            waiting = True
        try:
            head = await self._releases.fetch()
        except Exception as error:  # sem rede: a próxima volta tenta de novo
            self.journal.write("sem_origem", error=str(error)[:300])
            return "sem_origem"
        if head == self.state.commit or head in self.state.rejected:
            return "em_espera" if waiting else "em_dia"
        return await self._update(head)

    def _may_restart(self) -> bool:
        now = self._monotonic()
        window = self._settings.restart_window
        self._restarted = [t for t in self._restarted if now - t < window]
        if len(self._restarted) < self._settings.restarts:
            return True
        if len(self._restarted) == self._settings.restarts:  # avisa uma vez por laço
            self._restarted.append(now)
            self.journal.write("laco_de_quedas", commit=self.state.commit, window=window)
        return False

    async def _restart(self, dead: list[str]) -> str:
        """Um processo caiu sem troca nenhuma: o escritório sobe de novo, na mesma versão."""
        assert self.running is not None
        assert self.build is not None
        self._restarted.append(self._monotonic())
        self.journal.write("caiu", commit=self.state.commit, processes=dead)
        await self.running.stop()
        self.running = await self._stacks.start(
            self.slot(self.state.live), self.build, archiver=True
        )
        return "reiniciou"

    async def _update(self, head: str) -> str:
        old, live, other = self.state.commit, self.state.live, self.state.other
        assert old is not None
        started = self._monotonic()
        self.journal.write("candidata", commit=head, slot=other)
        try:
            await self._releases.place(self.slot(other), head)
            await self._releases.prepare(self.slot(other))
            build = await self._releases.build(head, old)
        except Exception as error:
            return self._reject(head, "preparar", str(error))
        reason = await self._stacks.smoke(self.slot(live), self.slot(other), build)
        if reason is not None:
            return self._reject(head, "fumaca", reason)
        self.journal.write("fumaca_ok", commit=head, seconds=self._since(started))
        await self._wait_quiet(head)
        return await self._swap(head, build, old, live, other)

    def _reject(self, commit: str, step: str, reason: str) -> str:
        self.state.rejected.append(commit)
        self._save()
        self.journal.write("recusou", commit=commit, at_step=step, reason=reason[:500])
        return f"recusou:{step}"

    async def _wait_quiet(self, head: str) -> None:
        """Espera o dev sair de uma sessão na oficina, até o limite; passou dele, troca assim
        mesmo, e a sessão volta no próximo bloco de trabalho."""
        assert self.running is not None
        start = self._monotonic()
        while True:
            health = await self.running.health()
            if health is None or not health.busy:
                return
            waited = self._monotonic() - start
            if waited >= self._settings.busy_wait_seconds:
                self.journal.write("espera_estourou", commit=head, seconds=round(waited))
                return
            await self._sleep(self._settings.busy_every)

    async def _swap(self, head: str, build: Build, old: str, live: str, other: str) -> str:
        assert self.running is not None
        assert self.build is not None
        down = self._monotonic()
        await self.running.stop()
        self.running = None
        backup = self._vault.backup(old)
        self.state.swap = Swap(live, old, other, head, str(backup))
        self._save()
        self.journal.write("troca", commit=head, previous=old, backup=str(backup))
        new: Running | None = None
        try:
            new = await self._stacks.start(self.slot(other), build, archiver=False)
            reason = await self._healthy(new)
        except Exception as error:
            reason = f"não subiu: {error}"
        if reason is None:
            assert new is not None
            await new.start_archiver()
            self.running, self.build = new, build
            self.state.live, self.state.commit, self.state.swap = other, head, None
            self._save()
            self._vault.prune(self._settings.keep_backups)
            self.journal.write(
                "trocou",
                commit=head,
                previous=old,
                pull_requests=list(build.pull_requests),
                down_seconds=self._since(down, self._first_healthy),
            )
            return "trocou"
        if new is not None:
            await new.stop()
        self._vault.restore(backup)
        self.state.rejected.append(head)
        self.state.swap = None
        self._save()
        self.running = await self._stacks.start(self.slot(live), self.build, archiver=True)
        self.journal.write(
            "voltou", commit=head, to=old, reason=reason[:500], down_seconds=self._since(down)
        )
        return "voltou"

    async def _healthy(self, running: Running) -> str | None:
        """A saúde da versão nova: até o fim do prazo, nenhum processo cai; no fim, o gateway
        respondeu, o pulso do kernel chega e o tick andou. None se está bem, ou o motivo."""
        start = self._monotonic()
        self._first_healthy = None
        first_tick: int | None = None
        last: Health | None = None
        while self._monotonic() - start < self._settings.health_seconds:
            if dead := running.dead():
                return f"caiu: {', '.join(dead)}"
            last = await running.health()
            if last is not None and last.alive:
                self._first_healthy = self._first_healthy or self._monotonic()
                first_tick = last.tick if first_tick is None else first_tick
            await self._sleep(self._settings.health_every)
        if dead := running.dead():
            return f"caiu: {', '.join(dead)}"
        if last is None:
            return "o gateway não respondeu"
        if not last.alive:
            return "o pulso do kernel não chega"
        if first_tick is None or last.tick <= first_tick:
            return "o tick não andou"
        return None

    def _since(self, start: float, end: float | None = None) -> float:
        return round((end if end is not None else self._monotonic()) - start, 1)
