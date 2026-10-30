"""O catálogo da mente bate com o cartucho (as afordâncias e as ações do farm.yaml), e as notas
não contam a regra oculta (princípio 5)."""

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, cast

import yaml

import campsverso_farm_sim
from campsverso_farm_mind import NOTES, mind

FARM = Path(campsverso_farm_sim.__file__).parent / "data" / "farm.yaml"
FORBIDDEN = ("bônus", "bonus", "multiplicador", "regra oculta", "r-001", "perto do rio")


def farm() -> Mapping[str, Any]:
    return cast(Mapping[str, Any], yaml.safe_load(FARM.read_text(encoding="utf-8")))


def test_toda_afordancia_tem_ferramenta_com_os_mesmos_parametros() -> None:
    doc = farm()
    tools = {t.name: t for t in mind().tools}
    by_action = {t.action: t for t in tools.values()}
    for affordance in cast(Sequence[Mapping[str, Any]], doc["affordances"]):
        action = str(affordance["action"])
        assert action in by_action, f"sem ferramenta para {action}"
        candidates = [t for t in tools.values() if t.action == action]
        wanted = {
            str(p["name"])
            for p in cast(Sequence[Mapping[str, Any]], affordance.get("params") or ())
        }
        if affordance.get("target", True) and affordance.get("kinds") != ["self"]:
            wanted.add("target")
        assert any(wanted <= {p.name for p in t.params} for t in candidates), (
            f"{action}: nenhuma ferramenta com {sorted(wanted)}"
        )


def test_duracao_e_energia_vem_do_cartucho() -> None:
    actions = cast(Mapping[str, Mapping[str, Any]], farm()["actions"])
    for tool in mind().tools:
        spec = actions.get(tool.action)
        if spec is None:  # move e wait são do kernel
            assert tool.action in ("move", "wait")
            continue
        if tool.action == "sleep":  # a duração do sono é até de manhã, não a do farm.yaml
            assert tool.duration_ticks is None
            continue
        assert tool.duration_ticks == int(spec["duration"]), tool.name
        assert tool.energy == float(spec["energy"]), tool.name


def test_mover_e_esperar_sao_do_kernel() -> None:
    tools = {t.name: t for t in mind().tools}
    assert tools["move_near"].action == "move"
    assert tools["move_to"].action == "move"
    assert tools["move_to"].shape == {"target": {"x": "$x", "y": "$y"}}
    assert tools["sleep_here"].action == "sleep"
    assert tools["sleep_here"].shape == {}
    assert tools["wait"].action == "wait"


def test_as_notas_nao_contam_a_regra_oculta() -> None:
    notes = NOTES.read_text(encoding="utf-8").lower()
    for word in FORBIDDEN:
        assert word not in notes, word
    assert "not_adjacent" in notes  # o glossário das recusas está lá
