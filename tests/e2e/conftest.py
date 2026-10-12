import os
from collections.abc import Iterator
from pathlib import Path

import pytest

from campsverso_testkit.nats_server import NatsServer, available, nats_server


@pytest.fixture
def nats(tmp_path: Path) -> Iterator[NatsServer]:
    """Um NATS de verdade, só deste teste. Sem o binário: pula na máquina local, falha no CI."""
    if not available():
        if os.environ.get("CI"):
            pytest.fail("sem nats-server no CI: o make setup deveria ter rodado o make tools")
        pytest.skip("sem nats-server: rode `make tools`")
    with nats_server(tmp_path) as server:
        yield server
