import re
from pathlib import Path

from campsverso_adapters import FakeWallClock, SequentialUuid7Ids, Uuid7Ids, YamlFlags

UUID7 = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")


def test_ids_sao_uuid7_validos_e_os_sequenciais_sao_ordenados() -> None:
    sequential = SequentialUuid7Ids()
    ids = [sequential.new_id() for _ in range(3)]
    assert all(UUID7.match(i) for i in [*ids, Uuid7Ids().new_id()])
    assert ids == sorted(ids)
    assert len(set(ids)) == 3


def test_relogio_falso_so_anda_quando_mandado() -> None:
    clock = FakeWallClock()
    before = clock.now()
    clock.advance(1.5)
    assert (clock.now() - before).total_seconds() == 1.5
    assert clock.monotonic() == 1.5


def test_flags_em_yaml(tmp_path: Path) -> None:
    path = tmp_path / "rules.yaml"
    path.write_text(
        "rules:\n"
        "  river_proximity_bonus:\n"
        "    impl: water_proximity_bonus\n"
        "    version: 1.0.0\n"
        "    hidden: true\n"
        "    enabled: true\n"
        "    params: {radius: 4, multiplier: 1.5}\n",
        encoding="utf-8",
    )
    (rule,) = YamlFlags(path).rules()
    assert rule.rule == "river_proximity_bonus"
    assert rule.impl == "water_proximity_bonus"
    assert rule.hidden
    assert rule.enabled
    assert rule.params == {"radius": 4, "multiplier": 1.5}
