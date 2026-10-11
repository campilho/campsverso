import shutil
from pathlib import Path

import pytest

from campsverso_tools.contracts import catalog

REPO_CONTRACTS = catalog.find_contracts_dir(Path(__file__).resolve().parent)


@pytest.fixture(scope="session")
def contracts() -> catalog.Contracts:
    return catalog.load(REPO_CONTRACTS)


@pytest.fixture
def contracts_copy(tmp_path: Path) -> Path:
    """Cópia descartável de contracts/, para testes que alteram arquivos."""
    target = tmp_path / "contracts"
    shutil.copytree(REPO_CONTRACTS, target)
    return target
