"""O ciclo do supervisor com peças falsas (ADR-0083): o git, a pilha e os dados de mentira, e o
estado e o diário de verdade, numa pasta temporária. O relógio só anda quando o ciclo espera."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import pytest

from campsverso_supervisor.cycle import Build, Health, Settings, Supervisor
from campsverso_supervisor.state import Journal, State, Swap

OLD, NEW, NEWER = "1" * 40, "2" * 40, "3" * 40


class Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def monotonic(self) -> float:
        return self.now

    async def sleep(self, seconds: float) -> None:
        self.now += seconds


@dataclass
class Releases:
    head: str = OLD
    placed: list[tuple[str, str]] = field(default_factory=list[tuple[str, str]])
    broken: set[str] = field(default_factory=set[str])  # commits que não preparam
    offline: bool = False

    async def fetch(self) -> str:
        if self.offline:
            raise OSError("sem rede")
        return self.head

    async def build(self, commit: str, since: str | None) -> Build:
        return Build(commit, "2026-11-21T09:00:00-03:00", (7,) if since else ())

    async def place(self, slot: Path, commit: str) -> None:
        self.placed.append((slot.name, commit))

    async def prepare(self, slot: Path) -> None:
        if self.placed[-1][1] in self.broken:
            raise RuntimeError("uv sync falhou")


@dataclass
class Running:
    slot: str
    build: Build
    archiver: bool
    clock: Clock
    behavior: str = "ok"  # ok, dies, silent, busy:<segundos>
    stopped: bool = False

    def dead(self) -> list[str]:
        return ["kernel"] if self.behavior == "dies" and self.clock.now > 0 else []

    async def health(self) -> Health | None:
        busy = self.behavior.startswith("busy:") and self.clock.now < float(self.behavior[5:])
        return Health(int(self.clock.now * 10), self.behavior != "silent", busy)

    async def start_archiver(self) -> None:
        self.archiver = True

    async def stop(self) -> None:
        self.stopped = True


@dataclass
class Stacks:
    clock: Clock
    behavior: dict[str, str] = field(default_factory=dict[str, str])  # commit -> comportamento
    smoke_fails: dict[str, str] = field(default_factory=dict[str, str])
    started: list[Running] = field(default_factory=list[Running])

    async def start(self, slot: Path, build: Build, *, archiver: bool) -> Running:
        running = Running(
            slot.name, build, archiver, self.clock, self.behavior.get(build.commit, "ok")
        )
        self.started.append(running)
        return running

    async def smoke(self, live: Path, candidate: Path, build: Build) -> str | None:
        return self.smoke_fails.get(build.commit)


@dataclass
class Vault:
    backups: list[str] = field(default_factory=list[str])
    restored: list[str] = field(default_factory=list[str])
    pruned: list[int] = field(default_factory=list[int])

    def backup(self, label: str) -> Path:
        self.backups.append(label)
        return Path(f"/versoes/{label[:7]}")

    def restore(self, backup: Path) -> None:
        self.restored.append(backup.name)

    def prune(self, keep: int) -> None:
        self.pruned.append(keep)


class Rig:
    def __init__(self, home: Path) -> None:
        self.home = home
        self.clock = Clock()
        self.releases = Releases()
        self.stacks = Stacks(self.clock)
        self.vault = Vault()

    def supervisor(self) -> Supervisor:
        journal = Journal(self.home / "versoes" / "supervisor.jsonl", lambda: datetime.now(UTC))
        return Supervisor(
            self.home,
            self.releases,
            self.stacks,
            self.vault,
            journal,
            Settings(busy_wait_seconds=600),
            sleep=self.clock.sleep,
            monotonic=self.clock.monotonic,
        )

    def steps(self) -> list[str]:
        path = self.home / "versoes" / "supervisor.jsonl"
        return [str(e["step"]) for e in Journal(path, lambda: datetime.now(UTC)).entries()]


@pytest.fixture
def rig(tmp_path: Path) -> Rig:
    return Rig(tmp_path)


async def test_a_primeira_subida_instala_o_main_na_worktree_a(rig: Rig) -> None:
    supervisor = rig.supervisor()
    await supervisor.boot()
    assert rig.releases.placed == [("a", OLD)]
    (running,) = rig.stacks.started
    assert (running.slot, running.build.commit, running.archiver) == ("a", OLD, True)
    assert State.load(rig.home / "estado.json").commit == OLD
    assert await supervisor.turn() == "em_dia"
    assert rig.steps() == ["instalou", "subiu"]


async def test_um_commit_bom_troca_de_worktree_e_liga_o_arquivador_so_depois(rig: Rig) -> None:
    supervisor = rig.supervisor()
    await supervisor.boot()
    old = rig.stacks.started[0]
    rig.releases.head = NEW
    assert await supervisor.turn() == "trocou"
    new = rig.stacks.started[-1]
    assert old.stopped
    assert (new.slot, new.build, new.archiver) == ("b", Build(NEW, new.build.date, (7,)), True)
    assert rig.vault.backups == [OLD]  # os dados de antes, guardados antes de subir a nova
    assert rig.vault.pruned == [3]
    state = State.load(rig.home / "estado.json")
    assert (state.live, state.commit, state.swap) == ("b", NEW, None)
    assert rig.steps()[-4:] == ["candidata", "fumaca_ok", "troca", "trocou"]
    assert await supervisor.turn() == "em_dia"
    # A próxima volta usa a worktree a de novo: as duas trocam de papel.
    rig.releases.head = NEWER
    assert await supervisor.turn() == "trocou"
    assert rig.stacks.started[-1].slot == "a"


async def test_a_fumaca_que_falha_recusa_o_commit_e_nao_toca_no_escritorio(rig: Rig) -> None:
    supervisor = rig.supervisor()
    await supervisor.boot()
    rig.releases.head = NEW
    rig.stacks.smoke_fails[NEW] = "o kernel não leu o snapshot"
    assert await supervisor.turn() == "recusou:fumaca"
    assert not rig.stacks.started[0].stopped
    assert len(rig.stacks.started) == 1
    assert rig.vault.backups == []
    assert await supervisor.turn() == "em_dia"  # não tenta de novo o mesmo commit
    rig.releases.head = NEWER  # até chegar outro
    assert await supervisor.turn() == "trocou"


async def test_a_versao_que_cai_depois_de_subir_volta_com_os_dados_de_antes(rig: Rig) -> None:
    supervisor = rig.supervisor()
    await supervisor.boot()
    rig.releases.head = NEW
    rig.stacks.behavior[NEW] = "dies"
    assert await supervisor.turn() == "voltou"
    new, back = rig.stacks.started[-2], rig.stacks.started[-1]
    assert new.stopped
    assert not new.archiver  # o arquivo nunca viu a versão que voltou
    assert (back.slot, back.build.commit, back.archiver) == ("a", OLD, True)
    assert rig.vault.restored == [OLD[:7]]
    state = State.load(rig.home / "estado.json")
    assert (state.live, state.commit, state.rejected, state.swap) == ("a", OLD, [NEW], None)
    assert rig.steps()[-1] == "voltou"


async def test_a_versao_sem_pulso_tambem_volta(rig: Rig) -> None:
    supervisor = rig.supervisor()
    await supervisor.boot()
    rig.releases.head = NEW
    rig.stacks.behavior[NEW] = "silent"
    assert await supervisor.turn() == "voltou"
    entry = [e for e in Journal(rig.home / "versoes" / "supervisor.jsonl", datetime.now).entries()]
    assert entry[-1]["reason"] == "o pulso do kernel não chega"


async def test_a_troca_espera_o_dev_sair_da_oficina(rig: Rig) -> None:
    rig.stacks.behavior[OLD] = "busy:90"
    supervisor = rig.supervisor()
    await supervisor.boot()
    rig.releases.head = NEW
    assert await supervisor.turn() == "trocou"
    assert 90 <= rig.clock.now < 300  # esperou a sessão, e depois a saúde
    assert "espera_estourou" not in rig.steps()


async def test_a_espera_tem_limite(rig: Rig) -> None:
    rig.stacks.behavior[OLD] = "busy:99999"
    supervisor = rig.supervisor()
    await supervisor.boot()
    rig.releases.head = NEW
    assert await supervisor.turn() == "trocou"
    assert "espera_estourou" in rig.steps()


async def test_o_supervisor_que_cai_no_meio_da_troca_volta_ao_subir(rig: Rig) -> None:
    state = State(live="a", commit=OLD, swap=Swap("a", OLD, "b", NEW, "/versoes/1111111"))
    state.save(rig.home / "estado.json")
    supervisor = rig.supervisor()
    await supervisor.boot()
    assert rig.vault.restored == ["1111111"]
    (running,) = rig.stacks.started
    assert (running.slot, running.build.commit) == ("a", OLD)
    rig.releases.head = NEW
    assert await supervisor.turn() == "em_dia"  # o commit da troca interrompida ficou recusado
    assert rig.steps()[:2] == ["voltou", "subiu"]


async def test_um_processo_que_cai_sem_troca_sobe_de_novo_na_mesma_versao(rig: Rig) -> None:
    rig.stacks.behavior[OLD] = "dies"
    supervisor = rig.supervisor()
    await supervisor.boot()
    rig.clock.now = 1
    assert await supervisor.turn() == "reiniciou"
    assert rig.stacks.started[0].stopped
    assert rig.stacks.started[-1].build.commit == OLD


async def test_o_laco_de_quedas_espera_mas_aceita_o_conserto(rig: Rig) -> None:
    rig.stacks.behavior[OLD] = "dies"
    supervisor = rig.supervisor()
    await supervisor.boot()
    rig.clock.now = 1
    assert [await supervisor.turn() for _ in range(5)] == [
        "reiniciou",
        "reiniciou",
        "reiniciou",
        "em_espera",
        "em_espera",
    ]
    assert rig.steps().count("laco_de_quedas") == 1
    rig.releases.head = NEW  # o conserto chega: a troca segue, mesmo com o escritório caído
    assert await supervisor.turn() == "trocou"
    rig.clock.now += 601  # e, passada a janela, reiniciar volta a valer
    rig.stacks.started[-1].behavior = "dies"
    assert await supervisor.turn() == "reiniciou"


async def test_sem_rede_nada_muda(rig: Rig) -> None:
    supervisor = rig.supervisor()
    await supervisor.boot()
    rig.releases.offline = True
    assert await supervisor.turn() == "sem_origem"
    assert len(rig.stacks.started) == 1


async def test_um_commit_que_nao_prepara_e_recusado(rig: Rig) -> None:
    supervisor = rig.supervisor()
    await supervisor.boot()
    rig.releases.head = NEW
    rig.releases.broken.add(NEW)
    assert await supervisor.turn() == "recusou:preparar"
    assert len(rig.stacks.started) == 1
