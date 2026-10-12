"""Critérios do M3 com processos e NATS de verdade: A3 (curto), A4 e A5 (plano do M3 §5).

O soak inteiro de 30 dias roda à mão (`make soak DAYS=30`); aqui roda uma versão de 3 dias,
o bastante para a primeira colheita.
"""

import subprocess
import sys
from pathlib import Path

import pytest

from campsverso_adapters import read_world_archive
from campsverso_testkit.hashing import canonical_hash
from campsverso_testkit.nats_server import REPO, available
from campsverso_testkit.soak import ENV, run

pytestmark = pytest.mark.skipif(not available(), reason="sem nats-server: rode `make tools`")
DAY = 1440


async def test_a3_tres_dias_sem_intervencao_e_a5_replay_pelo_kernel(tmp_path: Path) -> None:
    result = await run(3, tmp_path, quiet=True)
    assert result.ok, result.reason
    assert result.metrics["faints"] == 0
    assert result.metrics["rejections"] == {}
    assert result.metrics["days"] == 3
    assert result.metrics["harvests"]  # já colheu
    replay = subprocess.run(
        [
            sys.executable,
            "-m",
            "campsverso_kernel.main",
            "--env",
            str(ENV),
            "--world",
            str(tmp_path / "world.yaml"),
            "--data-dir",
            str(tmp_path / "data"),
            "--archive-dir",
            str(tmp_path / "archive"),
            "--replay-day",
            "1",
        ],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
    )
    assert replay.returncode == 0, replay.stdout + replay.stderr
    assert "iguais" in replay.stdout


def _first_day(folder: Path) -> str:
    envelopes = [
        e
        for e in read_world_archive(folder / "archive" / "farm-camps-01")
        if isinstance(e.get("tick"), int) and e["tick"] < DAY
    ]
    return canonical_hash(sorted(envelopes, key=lambda e: (str(e["source"]), int(e["seq"]))))


async def test_a4_duas_execucoes_com_processos_dao_o_mesmo_hash(tmp_path: Path) -> None:
    for name in ("a", "b"):
        result = await run(1, tmp_path / name, quiet=True)
        assert result.ok, result.reason
    assert _first_day(tmp_path / "a") == _first_day(tmp_path / "b")
