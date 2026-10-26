"""A mente da Fazenda Boa Vista: o catálogo bate com as afordâncias do cenário (gênero mais a
sobreposição), as durações vêm dos dados, e as notas calam as regras ocultas (princípio 5)."""

import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, cast

import yaml

import campsverso_farm_boavista_sim
import campsverso_farm_sim
from campsverso_farm_boavista_mind import NOTES, load, mind
from campsverso_mind import playbook

GENRE = Path(campsverso_farm_sim.__file__).parent / "data" / "farm.yaml"
OVERLAY = Path(campsverso_farm_boavista_sim.__file__).parent / "data" / "boavista.yaml"
# O que o manual não pode dizer: o rio, as regras por cultura, o baú que dobra, o ensopado que
# segura a fome, o tamanho do adubo e o ciclo do quiosque.
FORBIDDEN = (
    "bônus",
    "bonus",
    "multiplicador",
    "regra oculta",
    "r-001",
    "perto do rio",
    "faixa do rio",
    "tiles do rio",
    "dobra",
    "satisfeito",
    "metade",
    "0,5 ponto",
    "meio ponto",
    "ciclo",
    "a cada 5",
    "10%",
    "um dia sem rega",
    "um dia seco",
    "sem rega",
    "não precisa de rega",
    "needs_water",
    "wither_after",
    "guarda bem",  # o baú que conserva é oculto (arena do M14: a dica estava no catálogo)
    "conserva",
    "dura mais",
    "estraga menos",
)


def _yaml(path: Path) -> Mapping[str, Any]:
    return cast(Mapping[str, Any], yaml.safe_load(path.read_text(encoding="utf-8")))


def affordances() -> list[Mapping[str, Any]]:
    """As do gênero, trocadas pelas do cenário onde a ação se repete (contribute_extensions)."""
    genre = cast(Sequence[Mapping[str, Any]], _yaml(GENRE)["affordances"])
    overlay = cast(Sequence[Mapping[str, Any]], _yaml(OVERLAY)["affordances"])
    replaced = {str(a["action"]) for a in overlay}
    return [a for a in genre if str(a["action"]) not in replaced] + list(overlay)


def actions() -> Mapping[str, Mapping[str, Any]]:
    return {**_yaml(GENRE)["actions"], **_yaml(OVERLAY)["actions"]}


def test_toda_afordancia_tem_ferramenta_com_os_mesmos_parametros() -> None:
    tools = list(mind.tools)
    for affordance in affordances():
        action = str(affordance["action"])
        candidates = [t for t in tools if t.action == action]
        assert candidates, f"sem ferramenta para {action}"
        wanted = {
            str(p["name"])
            for p in cast(Sequence[Mapping[str, Any]], affordance.get("params") or ())
        }
        if affordance.get("kinds") == ["grass"]:  # o menu da grama: o tile, em x e y (ADR-0068)
            wanted |= {"x", "y"}
        elif affordance.get("target", True) and affordance.get("kinds") != ["self"]:
            wanted.add("target")
        assert any(wanted <= {p.name for p in t.params} for t in candidates), (
            f"{action}: nenhuma ferramenta com {sorted(wanted)}"
        )


def test_as_ferramentas_novas_estao_no_catalogo() -> None:
    names = {t.name for t in mind.tools}
    assert {"dig", "fertilize", "cook"} <= names
    buy = next(t for t in mind.tools if t.name == "buy")
    for word in ("semente_tomate", "adubo", "watering_can_large", "plow"):
        assert word in buy.description, word  # as opções ficam na descrição: sem enum, a gramática
    # das ferramentas estritas estouraria o teto da API; as simples nem são estritas.
    assert sum(not t.strict for t in mind.tools) == 9
    assert all(t.strict for t in mind.tools if t.name in ("buy", "plant", "cook", "deposit"))


def test_duracao_e_energia_vem_do_cartucho() -> None:
    table = actions()
    for tool in mind.tools:
        spec = table.get(tool.action)
        if spec is None:
            assert tool.action in ("move", "wait")
            continue
        if tool.action == "sleep":
            assert tool.duration_ticks is None
            continue
        assert tool.duration_ticks == int(spec["duration"]), tool.name
        assert tool.energy == int(spec["energy"]), tool.name


def test_o_cartao_e_o_do_camps() -> None:
    assert "Camps" in load().card
    assert mind.name == "camps_boavista"


def test_as_notas_contam_o_visivel_e_calam_o_oculto() -> None:
    notes = NOTES.read_text(encoding="utf-8").lower()
    catalog = (NOTES.parent / "tools.yaml").read_text(encoding="utf-8").lower()
    for phrase in FORBIDDEN:  # as descrições das ferramentas também são lidas pela mente
        if phrase.isalpha():
            assert re.search(rf"\b{phrase}\b", catalog) is None, phrase
        else:
            assert phrase not in catalog, phrase
    method = playbook(mind).lower()  # o playbook também é lido pela mente (ADR-0071)
    for phrase in FORBIDDEN:
        for text in (notes, method):
            if phrase.isalpha():  # palavra inteira: "rio" não é o "rio" de "superior"
                assert re.search(rf"\b{phrase}\b", text) is None, phrase
            else:
                assert phrase not in text, phrase
    for visible in ("too_heavy", "estoque_hoje", "preco_", "expires_in_days", "dig", "adubado"):
        assert visible in notes, visible
