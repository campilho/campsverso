import shutil
from pathlib import Path

import pytest
from hypothesis import settings

from campsverso_tools.contracts import catalog

REPO_CONTRACTS = catalog.find_contracts_dir(Path(__file__).resolve().parent)

# Sem prazo por exemplo: máquinas de CI variam de velocidade, e o prazo não testa nada nosso.
settings.register_profile("campsverso", deadline=None)
settings.load_profile("campsverso")


@pytest.fixture(scope="session")
def contracts() -> catalog.Contracts:
    return catalog.load(REPO_CONTRACTS)


@pytest.fixture
def contracts_copy(tmp_path: Path) -> Path:
    """Cópia descartável de contracts/, para testes que alteram arquivos."""
    target = tmp_path / "contracts"
    shutil.copytree(REPO_CONTRACTS, target)
    return target
