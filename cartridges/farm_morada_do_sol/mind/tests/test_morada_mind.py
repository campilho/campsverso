"""A mente da Fazenda Morada do Sol (ADR-0067): o catálogo bate com as afordâncias das três
camadas (gênero, Boa Vista e Morada do Sol), as durações vêm dos dados, e o manual conta o visível
(o ano, o calendário, o raio, os canteiros que voltam a ser grama) e cala as regras ocultas."""

import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, cast

import yaml

import campsverso_farm_boavista_sim
import campsverso_farm_morada_do_sol_sim
import campsverso_farm_sim
from campsverso_farm_morada_do_sol_mind import NOTES, SEASONS, load, mind
from campsverso_mind import COMPARE_INSTRUCTIONS, COMPARE_TOOL, playbook
from campsverso_mind.memory import (
    ADVISOR_INSTRUCTIONS,
    ADVISOR_NOTE,
    NOTEBOOK_INSTRUCTIONS,
    OPEN_EXPERIMENT_INSTRUCTIONS,
    reflect_tool,
)
from campsverso_mind.notebook import TABLE_HEADER

GENRE = Path(campsverso_farm_sim.__file__).parent / "data" / "farm.yaml"
BOAVISTA = Path(campsverso_farm_boavista_sim.__file__).parent / "data" / "boavista.yaml"
MORADA = Path(campsverso_farm_morada_do_sol_sim.__file__).parent / "data" / "morada.yaml"
# O que o manual não pode dizer: as regras da Boa Vista (o baú que conserva, o ensopado, o adubo,
# o tomate e o alho, o ciclo do quiosque) e as da Morada do Sol (a várzea, os corvos e a distância
# deles, o raio do espantalho, a fadiga do solo e a rotação).
FORBIDDEN = (
    "bônus",
    "bonus",
    "multiplicador",
    "regra oculta",
    "r-001",
    "r-002",
    "r-003",
    "perto do rio",
    "faixa do rio",
    "margem do rio",
    "várzea",
    "fértil",
    "água perto",
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
    "guarda bem",
    "conserva",
    "dura mais",
    "estraga menos",
    "corvo",
    "corvos",
    "pássaro",
    "pássaros",
    "ave",
    "aves",
    "bicho",
    "longe da casa",
    "distância",
    "raio do espantalho",
    "em volta do espantalho",
    "fadiga",
    "cansa o solo",
    "solo cansado",
    "rotação",
    "revezar",
    "mesma cultura",
    "repetir",
    # R-004 (ADR-0069): o manual só diz que os clientes lembram de quem cumpre o prazo.
    "r-004",
    "reputação",
    "mais pedidos",
    "menos pedidos",
    "prêmio maior",
    "prêmios maiores",
    "um terço",
)


def _yaml(path: Path) -> Mapping[str, Any]:
    return cast(Mapping[str, Any], yaml.safe_load(path.read_text(encoding="utf-8")))


def affordances() -> list[Mapping[str, Any]]:
    """As do gênero, trocadas pelas da Boa Vista e pelas da Morada do Sol onde a ação se repete."""
    layers = [
        cast(Sequence[Mapping[str, Any]], _yaml(p)["affordances"])
        for p in (GENRE, BOAVISTA, MORADA)
    ]
    result: list[Mapping[str, Any]] = []
    for layer in layers:
        replaced = {str(a["action"]) for a in layer}
        result = [a for a in result if str(a["action"]) not in replaced] + list(layer)
    return result


def actions() -> Mapping[str, Mapping[str, Any]]:
    return {**_yaml(GENRE)["actions"], **_yaml(BOAVISTA)["actions"], **_yaml(MORADA)["actions"]}


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
        # O que o molde da ferramenta fixa também conta (a composteira só faz adubo).
        assert any(wanted <= {p.name for p in t.params} | set(t.shape or {}) for t in candidates), (
            f"{action}: nenhuma ferramenta com {sorted(wanted)}"
        )


def test_o_catalogo_tem_o_espantalho_e_as_culturas_novas() -> None:
    names = {t.name for t in mind.tools}
    assert {"dig", "fertilize", "cook", "place"} <= names
    buy = next(t for t in mind.tools if t.name == "buy")
    for word in ("semente_milho", "semente_couve", "espantalho", "plow"):
        assert word in buy.description, word
    plant = next(t for t in mind.tools if t.name == "plant")
    for crop in ("milho", "melancia", "mandioca", "couve"):
        assert crop in plant.description, crop
    assert sum(not t.strict for t in mind.tools) == 20  # as simples, para caber na gramática


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
        assert tool.energy == float(spec["energy"]), tool.name


def test_o_cartao_e_o_do_camps() -> None:
    assert "Camps" in load().card
    assert mind.name == "camps_morada"


def test_o_manual_conta_o_visivel_e_cala_o_oculto() -> None:
    notes = NOTES.read_text(encoding="utf-8").lower()
    catalog = (NOTES.parent / "tools.yaml").read_text(encoding="utf-8").lower()
    # As descrições das ferramentas, o playbook (ADR-0071) e a ferramenta de comparação, com as
    # colunas (ADR-0074), também são lidos pela mente.
    assert mind.columns is not None
    # E o conselheiro (ADR-0074): as instruções e o pedido de brevidade. E o caderno completo
    # (decisão 35): as instruções, a tabela, os títulos das seções da noite e a ferramenta.
    comparison = " ".join(
        [
            str(COMPARE_TOOL),
            COMPARE_INSTRUCTIONS,
            *mind.columns.names,
            ADVISOR_INSTRUCTIONS,
            ADVISOR_NOTE,
            NOTEBOOK_INSTRUCTIONS,
            OPEN_EXPERIMENT_INSTRUCTIONS,
            TABLE_HEADER,
            "Onde ficam as coisas que você conhece",
            "O mapa que você já viu",
            "Os seus experimentos",
            "Por semente e estação",
            str(reflect_tool(True, open_ended=True)),
        ]
    ).lower()
    for text in (notes, catalog, playbook(mind).lower(), comparison):
        for phrase in FORBIDDEN:
            if phrase.replace(" ", "").isalpha():  # palavra inteira: "ave" não é o de "chave"
                assert re.search(rf"\b{phrase}\b", text) is None, phrase
            else:
                assert phrase not in text, phrase
    for visible in ("season", "primavera", "inverno", "12 tiles", "três manhãs", "plot-001"):
        assert visible in notes, visible
    for crop in ("milho", "melancia", "mandioca", "couve"):
        assert notes.count(crop) >= 2, crop  # na tabela e no calendário


def _table(heading: str) -> list[list[str]]:
    """As linhas de uma tabela do manual, a que vem depois do parágrafo que começa com `heading`."""
    text = NOTES.read_text(encoding="utf-8")
    after = text[text.index(heading) :]
    rows = [line for line in after.splitlines() if line.startswith("|")]
    block: list[list[str]] = []
    for line in after.splitlines()[after.splitlines().index(rows[0]) :]:
        if not line.startswith("|"):
            break
        block.append([cell.strip() for cell in line.strip("|").split("|")])
    return block[2:]  # sem o cabeçalho e a régua


def test_as_estacoes_da_mente_sao_as_do_manual() -> None:
    """ADR-0074, decisão 35: os dias esperados da tabela do caderno saem dos números do manual que
    o modelo lê, e não dos do mundo."""
    seasons = mind.seasons
    assert seasons is not None
    assert SEASONS.exists()
    crops = {row[0]: int(row[2]) for row in _table("**As plantas.**")}
    assert dict(seasons.days) == crops
    calendar = {row[0]: row[1:5] for row in _table("**O calendário de plantio.**")}
    order = ("primavera", "verao", "outono", "inverno")
    assert {c: [seasons.calendar[c][s] for s in order] for c in calendar} == calendar
    assert seasons.expected("batata", "primavera") == "10"  # fraca: duas vezes
    assert seasons.expected("alho", "verao") == "parada"
    assert seasons.name("verao") == "verão"


def test_o_procedimento_e_o_playbook_da_morada() -> None:
    """ADR-0074, decisão 35: o procedimento operacional, no lugar do método e do ofício. Diz onde
    cada coisa está, as etapas, os formatos e o nunca e o sempre."""
    text = playbook(mind)
    assert text.startswith("## O procedimento")
    for part in (
        "A Fazenda Morada do Sol, para quem acabou de chegar",
        "### Etapa 1. Ao acordar",
        "### Etapa 3. À noite, na reflexão, nesta ordem",
        "Cada suspeita tem duas tentativas",
        "### Os formatos",
        "**A escada de confiança.**",
        "### Nunca",
        "### Sempre",
    ):
        assert part in text, part
    assert "A Fazenda Morada do Sol, para quem acabou de chegar" in mind.notes  # o nome existe
    for column in TABLE_HEADER.strip("| ").split(" | "):
        assert f"`{column}`" in text, column  # cada coluna da tabela está explicada
