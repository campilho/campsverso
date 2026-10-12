"""Versão do que roda a simulação: kernel, cartridge-api, contratos e a cadeia de cartuchos.

Os incrementais (diário de entradas) só se reexecutam com a mesma versão que os gravou: o mesmo
estado e os mesmos comandos só dão os mesmos fatos se o código for o mesmo (plano do M2 §1).
A versão de um pacote em desenvolvimento quase nunca muda, então ela é o sha256 dos arquivos.
"""

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass
from importlib.util import find_spec
from pathlib import Path
from typing import Any

from campsverso_cartridge_api import Cartridge
from campsverso_kernel.loader import discover, resolve_chain

# Os contratos entram porque o kernel recusa comandos fora deles (Engine.submit).
_CORE_PACKAGES = ("campsverso_kernel", "campsverso_cartridge_api", "campsverso_contracts")


@dataclass(frozen=True, slots=True)
class RunVersion:
    code: str  # sha256 dos arquivos dos pacotes que simulam
    cartridges: tuple[tuple[str, str], ...]  # (id, versão) da base para o topo
    snapshot_every: int  # mudar a cadência muda onde os snapshots caem, logo os fatos

    @property
    def key(self) -> str:
        return f"{self.code}/snapshot_every={self.snapshot_every}"

    def as_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "cartridges": {cid: version for cid, version in self.cartridges},
            "snapshot_every": self.snapshot_every,
        }


def _package_files(package: str) -> list[tuple[str, Path]]:
    spec = find_spec(package)
    if spec is None or not spec.submodule_search_locations:
        raise ValueError(f"pacote sem diretório: {package}")
    files: list[tuple[str, Path]] = []
    for location in spec.submodule_search_locations:
        root = Path(location)
        for path in root.rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
                files.append((f"{package}/{path.relative_to(root).as_posix()}", path))
    return files


def run_version(
    top: str, snapshot_every: int, cartridges: Mapping[str, Cartridge] | None = None
) -> RunVersion:
    chain = resolve_chain(top, cartridges if cartridges is not None else discover())
    packages = set(_CORE_PACKAGES) | {type(c).__module__.split(".")[0] for c in chain}
    digest = hashlib.sha256()
    for name, path in sorted(f for package in sorted(packages) for f in _package_files(package)):
        digest.update(name.encode())
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return RunVersion(
        code=digest.hexdigest(),
        cartridges=tuple((c.manifest.id, c.manifest.version) for c in chain),
        snapshot_every=snapshot_every,
    )
