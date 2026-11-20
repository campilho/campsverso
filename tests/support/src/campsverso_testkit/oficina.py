"""O repositório de exemplo da fita do escritório (o plano do M24, §8): `tests/fixtures/oficina/`.

A fita guarda, para cada pedido ao modelo, o hash dele; o pedido leva o que as ferramentas da
oficina devolveram. No repositório de verdade, cada commit mudaria essas respostas, e a fita
deixaria de bater. Aqui o repositório é pequeno e fixo, copiado para uma pasta nova com um commit
de nome, e-mail e data fixos: o mesmo hash de commit em toda máquina, a cada gravação e reprodução.
"""

import os
import shutil
import subprocess
from pathlib import Path

from campsverso_testkit.nats_server import REPO

FIXTURE = REPO / "tests" / "fixtures" / "oficina"
WHEN = "2026-11-13T18:00:00-03:00"  # a sexta antes da segunda do mundo de teste


def example_office_repo(root: Path) -> Path:
    """Copia o repositório de exemplo para `root/escritorio` e faz o commit fixo."""
    repo = root / "escritorio"
    shutil.copytree(FIXTURE, repo, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "Exemplo",
        "GIT_AUTHOR_EMAIL": "exemplo@exemplo",
        "GIT_AUTHOR_DATE": WHEN,
        "GIT_COMMITTER_NAME": "Exemplo",
        "GIT_COMMITTER_EMAIL": "exemplo@exemplo",
        "GIT_COMMITTER_DATE": WHEN,
    }
    git = ["git", "-C", str(repo), "-c", "commit.gpgsign=false", "-c", "core.autocrlf=false"]
    subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True, env=env)
    subprocess.run([*git, "add", "-A"], check=True, env=env)
    subprocess.run([*git, "commit", "-q", "-m", "o escritório de exemplo"], check=True, env=env)
    return repo
