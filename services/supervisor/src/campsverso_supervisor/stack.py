"""A pilha do escritório vivo em processos (ADR-0083): o NATS e os serviços de uma worktree.

Cada pilha sobe da sua worktree, com o Python dela (`.venv`) e a configuração dela, sobre a pasta
de dados que o supervisor diz. O NATS é próprio, com as senhas geradas a cada subida, para os
usuários que o `nats.conf` daquela versão declara. A parada é elegante: o kernel primeiro, que
grava o snapshot ao parar, depois os outros, e o NATS por último.

**A fumaça,** numa cópia dos dados, com o NATS e o gateway em portas livres:
1. a versão de antes sobe só o kernel na cópia e para com elegância. O kernel só retoma um mundo
   com entradas depois do snapshot na mesma versão do código; parado assim, o snapshot fecha a
   cópia, e a versão nova a lê sem entradas pendentes;
2. a versão nova sobe inteira na cópia, sem o publicador (nada vai ao GitHub) e sem a mente
   (nenhuma chamada paga), com a escala 72, e anda um tempo;
3. passa se nenhum processo caiu, o gateway respondeu, o pulso do kernel chega e o tick andou.

**A cópia para a volta:** os dados e o NATS, parados, numa pasta por troca, sem a oficina (os
clones de trabalho do dev) e sem o arquivo, que nunca se reescreve.
"""

import asyncio
import contextlib
import json
import os
import re
import secrets
import shutil
import signal
import socket
import subprocess
import time
import urllib.request
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, cast

from campsverso_supervisor.cycle import Build, Health

_ROLE = re.compile(r"\$NATS_([A-Z]+)_PASSWORD")
WORKSHOP = "oficina"  # os clones de trabalho do dev: grandes, e refeitos a cada pedido


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@dataclass(frozen=True)
class StackConfig:
    world: str  # o arquivo do mundo, relativo à worktree
    data: Path
    archive: Path
    nats_store: Path
    logs: Path
    nats_bin: Path
    nats_port: int
    gateway_port: int
    environ: Mapping[str, str]
    pids: Path  # os processos de pé, para quem subir depois de uma queda do supervisor
    key: Path | None = None  # a chave do App, para o publicador
    script: str = "dev"
    budget: bool = True
    codehost: bool = True
    mind: str | None = None
    smoke_seconds: float = 50.0
    smoke_scale: float = 72.0
    ready_seconds: float = 120.0


class ProcessStack:
    """Uma pilha de pé: implementa o `Running` do ciclo."""

    def __init__(
        self,
        slot: Path,
        config: StackConfig,
        build: Build | None,
        *,
        data: Path,
        archive: Path,
        nats_store: Path,
        nats_port: int,
        gateway_port: int,
        label: str,
        scale: float | None = None,
        codehost: bool = True,
        mind: str | None = None,
    ) -> None:
        self.slot = slot.resolve()
        self._config = config
        self._build = build
        self._data, self._archive, self._store = data, archive, nats_store
        self._nats_port, self.gateway_port = nats_port, gateway_port
        self._label = label
        self._scale = scale
        self._codehost = codehost and config.codehost
        self._mind = mind
        self.processes: dict[str, subprocess.Popen[bytes]] = {}
        self._env: dict[str, str] = {}

    # ------------------------------------------------------------------ subir

    def _log(self, name: str) -> Path:
        self._config.logs.mkdir(parents=True, exist_ok=True)
        return self._config.logs / f"{self._label}-{name}.log"

    def _spawn(self, name: str, args: Sequence[str]) -> None:
        with self._log(name).open("ab") as log:
            self.processes[name] = subprocess.Popen(
                list(args),
                cwd=self.slot,
                env=self._env,
                stdout=log,
                stderr=subprocess.STDOUT,
                start_new_session=True,  # um Ctrl+C no terminal não derruba a pilha sem ordem
            )
        self._remember()

    def _remember(self) -> None:
        pids = _read_pids(self._config.pids)
        pids[self._label] = {name: p.pid for name, p in self.processes.items()}
        _write_pids(self._config.pids, pids)

    def _service(self, name: str, module: str, *args: str, world: bool = True) -> None:
        python = self.slot / ".venv" / "bin" / "python"
        base = [str(python), "-m", module, "--env", "config/env/local.yaml"]
        base += ["--nats-url", f"nats://127.0.0.1:{self._nats_port}"]
        if world:
            base += ["--world", self._config.world, "--data-dir", str(self._data)]
        self._spawn(name, [*base, *args])

    async def start_nats(self) -> None:
        conf = self.slot / "config" / "nats" / "nats.conf"
        roles = sorted({m.lower() for m in _ROLE.findall(conf.read_text(encoding="utf-8"))})
        self.passwords = {role: secrets.token_hex(16) for role in roles}
        env = {**self._config.environ}
        env |= {f"NATS_{role.upper()}_PASSWORD": pw for role, pw in self.passwords.items()}
        if self._build is not None:
            env |= {
                "CAMPSVERSO_COMMIT": self._build.commit,
                "CAMPSVERSO_COMMIT_DATE": self._build.date,
                "CAMPSVERSO_PRS": ",".join(str(n) for n in self._build.pull_requests),
            }
        self._env = env
        self._store.mkdir(parents=True, exist_ok=True)
        self._spawn(
            "nats",
            [
                str(self._config.nats_bin),
                "-c",
                str(conf),
                "-p",
                str(self._nats_port),
                "-sd",
                str(self._store),
            ],
        )
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            with socket.socket() as sock:
                if sock.connect_ex(("127.0.0.1", self._nats_port)) == 0:
                    return
            if self.processes["nats"].poll() is not None:
                break
            await asyncio.sleep(0.05)
        raise RuntimeError(f"o NATS não subiu (veja {self._log('nats')})")

    async def start_kernel(self) -> None:
        scale = () if self._scale is None else ("--scale", str(self._scale))
        self._service("kernel", "campsverso_kernel.main", *scale)

    async def start(self, *, archiver: bool) -> None:
        await self.start_nats()
        await self.start_kernel()
        self._service("perception", "campsverso_perception.main")
        self._service(
            "controller", "campsverso_controller_runner.main", "--controller", self._config.script
        )
        self._service("helpers", "campsverso_controller_runner.main", "--helpers")
        self._service("gateway", "campsverso_gateway.main", "--port", str(self.gateway_port))
        if self._config.budget:
            self._service("budget", "campsverso_budget.main")
        if self._codehost:
            key = () if self._config.key is None else ("--key", str(self._config.key))
            self._service("codehost", "campsverso_codehost.main", *key)
        if self._mind is not None:
            self._service("mind", "campsverso_controller_runner.main", "--mind", self._mind)
        if archiver:
            await self.start_archiver()

    async def start_archiver(self) -> None:
        self._service(
            "archiver",
            "campsverso_archiver.main",
            "--archive-dir",
            str(self._archive),
            world=False,
        )

    # ------------------------------------------------------------------ olhar

    def dead(self) -> list[str]:
        return sorted(name for name, p in self.processes.items() if p.poll() is not None)

    async def health(self) -> Health | None:
        url = f"http://127.0.0.1:{self.gateway_port}/health"

        def get() -> dict[str, Any] | None:
            try:
                with urllib.request.urlopen(url, timeout=3) as response:
                    return cast(dict[str, Any], json.loads(response.read()))
            except OSError, ValueError:
                return None

        body = await asyncio.to_thread(get)
        if body is None or "tick" not in body:
            return None
        pulse = cast(Mapping[str, Any] | None, body.get("pulse"))
        alive = bool(pulse.get("alive")) if pulse is not None else False
        return Health(int(body["tick"]), alive, bool(body.get("busy")))

    def logged(self, name: str, event: str) -> bool:
        path = self._log(name)
        return path.is_file() and f'"event": "{event}"' in path.read_text(errors="replace")

    # ------------------------------------------------------------------ parar

    async def _terminate(self, names: Sequence[str], timeout: float) -> None:
        for name in names:
            process = self.processes.get(name)
            if process is not None and process.poll() is None:
                process.send_signal(signal.SIGTERM)
        deadline = time.monotonic() + timeout
        for name in names:
            process = self.processes.get(name)
            if process is None:
                continue
            while process.poll() is None and time.monotonic() < deadline:
                await asyncio.sleep(0.1)
            if process.poll() is None:
                process.kill()
                process.wait()

    async def stop(self) -> None:
        """O kernel primeiro, que grava o snapshot ao parar; os outros; o NATS por último."""
        await self._terminate(["kernel"], 60)
        others = [n for n in self.processes if n not in ("kernel", "nats")]
        await self._terminate(others, 30)
        await self._terminate(["nats"], 15)
        pids = _read_pids(self._config.pids)
        pids.pop(self._label, None)
        _write_pids(self._config.pids, pids)


def _read_pids(path: Path) -> dict[str, dict[str, int]]:
    if not path.is_file():
        return {}
    with contextlib.suppress(ValueError):
        return cast(dict[str, dict[str, int]], json.loads(path.read_text(encoding="utf-8")))
    return {}


def _write_pids(path: Path, pids: Mapping[str, Mapping[str, int]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(pids, indent=2) + "\n", encoding="utf-8")


def reap(path: Path, marker: str) -> list[int]:
    """Os processos de uma pilha que ficaram de pé depois de uma queda do supervisor: só os que
    ainda rodam com a pasta do escritório vivo na linha de comando, para não matar um processo
    alheio que herdou o número."""
    killed: list[int] = []
    for group in _read_pids(path).values():
        for pid in group.values():
            probe = subprocess.run(
                ["ps", "-o", "command=", "-p", str(pid)], capture_output=True, text=True
            )
            if marker in probe.stdout:
                with contextlib.suppress(ProcessLookupError):
                    os.kill(pid, signal.SIGKILL)
                killed.append(pid)
    _write_pids(path, {})
    return killed


class ProcessStacks:
    """As pilhas do escritório vivo: implementa o `Stacks` do ciclo."""

    def __init__(self, home: Path, config: StackConfig) -> None:
        self._home = home
        self._config = config

    async def start(self, slot: Path, build: Build, *, archiver: bool) -> ProcessStack:
        c = self._config
        stack = ProcessStack(
            slot,
            c,
            build,
            data=c.data,
            archive=c.archive,
            nats_store=c.nats_store,
            nats_port=c.nats_port,
            gateway_port=c.gateway_port,
            label=f"vivo-{slot.name}",
            mind=c.mind,
        )
        try:
            await stack.start(archiver=archiver)
        except Exception:
            await stack.stop()
            raise
        return stack

    async def smoke(self, live: Path, candidate: Path, build: Build) -> str | None:
        root = self._home / "fumaca"
        shutil.rmtree(root, ignore_errors=True)
        data = root / "dados"
        if self._config.data.is_dir():
            shutil.copytree(
                self._config.data, data, ignore=shutil.ignore_patterns(WORKSHOP), symlinks=True
            )
        data.mkdir(parents=True, exist_ok=True)
        try:
            closed = await self._close_copy(live, data, root, build)
            if closed is not None:
                return closed
            return await self._run_candidate(candidate, data, root, build)
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def _stack(self, slot: Path, build: Build | None, data: Path, root: Path, label: str,
               scale: float | None = None) -> ProcessStack:  # fmt: skip
        return ProcessStack(
            slot,
            self._config,
            build,
            data=data,
            archive=root / "arquivo",
            nats_store=root / "nats",
            nats_port=free_port(),
            gateway_port=free_port(),
            label=label,
            scale=scale,
            codehost=False,  # a fumaça não fala com o GitHub
            mind=None,  # nem chama o modelo
        )

    async def _close_copy(self, live: Path, data: Path, root: Path, build: Build) -> str | None:
        """A versão de antes retoma a cópia e para com elegância: o snapshot a fecha."""
        before = self._stack(live, None, data, root, f"fumaca-{build.commit[:7]}-antes")
        try:
            await before.start_nats()
            await before.start_kernel()
            deadline = time.monotonic() + self._config.ready_seconds
            while not before.logged("kernel", "kernel.running"):
                if before.dead() or time.monotonic() > deadline:
                    return "a versão de antes não retomou a cópia dos dados"
                await asyncio.sleep(0.5)
        finally:
            await before.stop()
        return None

    async def _run_candidate(self, slot: Path, data: Path, root: Path, build: Build) -> str | None:
        label = f"fumaca-{build.commit[:7]}"
        stack = self._stack(slot, build, data, root, label, scale=self._config.smoke_scale)
        try:
            try:
                await stack.start(archiver=True)
            except Exception as error:
                return f"não subiu: {error}"
            first: Health | None = None
            deadline = time.monotonic() + self._config.ready_seconds
            while first is None or not first.alive:
                if dead := stack.dead():
                    return f"caiu ao subir: {', '.join(dead)} (veja {label}-*.log)"
                if time.monotonic() > deadline:
                    return "o gateway ou o pulso do kernel não chegaram"
                await asyncio.sleep(1)
                first = await stack.health()
            end = time.monotonic() + self._config.smoke_seconds
            while time.monotonic() < end:
                if dead := stack.dead():
                    return f"caiu: {', '.join(dead)} (veja {label}-*.log)"
                await asyncio.sleep(1)
            last = await stack.health()
            if last is None or not last.alive:
                return "o gateway ou o pulso do kernel sumiram"
            if last.tick <= first.tick:
                return "o tick não andou"
            return None
        finally:
            await stack.stop()


class DirVault:
    """As cópias dos dados para a volta: implementa o `Vault` do ciclo."""

    def __init__(
        self, data: Path, nats_store: Path, root: Path, now: Callable[[], datetime]
    ) -> None:
        self._data, self._store, self._root, self._now = data, nats_store, root, now

    def backup(self, label: str) -> Path:
        target = self._root / f"{self._now().strftime('%Y%m%d-%H%M%S')}-{label[:7]}"
        target.mkdir(parents=True, exist_ok=False)
        if self._data.is_dir():
            shutil.copytree(
                self._data,
                target / "dados",
                ignore=shutil.ignore_patterns(WORKSHOP),
                symlinks=True,
            )
        if self._store.is_dir():
            shutil.copytree(self._store, target / "nats", symlinks=True)
        return target

    def restore(self, backup: Path) -> None:
        """Os dados e o NATS de volta ao que eram, menos a oficina, que segue a de agora."""
        if self._data.is_dir():
            for entry in self._data.iterdir():
                if entry.name == WORKSHOP:
                    continue
                if entry.is_dir() and not entry.is_symlink():
                    shutil.rmtree(entry)
                else:
                    entry.unlink()
        if (backup / "dados").is_dir():
            shutil.copytree(backup / "dados", self._data, symlinks=True, dirs_exist_ok=True)
        shutil.rmtree(self._store, ignore_errors=True)
        if (backup / "nats").is_dir():
            shutil.copytree(backup / "nats", self._store, symlinks=True)

    def prune(self, keep: int) -> None:
        if not self._root.is_dir():
            return
        copies = sorted(p for p in self._root.iterdir() if p.is_dir())
        for old in copies[: max(0, len(copies) - keep)]:
            shutil.rmtree(old)
