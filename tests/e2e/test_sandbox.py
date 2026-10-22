"""O arquivo do mundo do sandbox; o começo parado é da rodada do humano (ADR-0066)."""

from pathlib import Path

import yaml

from campsverso_testkit import sandbox

BOAVISTA = Path(__file__).parents[2] / "config" / "worlds" / "farm-boavista-01.yaml"


def test_o_sandbox_pausado_comeca_com_o_relogio_parado(tmp_path: Path) -> None:
    write = sandbox._world_file  # pyright: ignore[reportPrivateUsage]
    parado = yaml.safe_load(write(tmp_path, source=BOAVISTA, paused=True).read_text("utf-8"))
    assert parado["clock"] == {"mode": "continuous", "scale": 72, "paused": True}
    assert not parado.get("minds")  # sem mente, nenhuma mente sobe
    andando = yaml.safe_load(write(tmp_path, source=BOAVISTA).read_text("utf-8"))
    assert andando["clock"]["paused"] is False
