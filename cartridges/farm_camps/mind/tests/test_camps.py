"""A mente do Camps: o cartão do cenário por cima do gênero, registrada como entry point."""

import re
from importlib.metadata import entry_points

import campsverso_farm_mind
from campsverso_farm_camps_mind import CARD, mind
from campsverso_mind import Mind, playbook

FORBIDDEN = ("bônus", "bonus", "multiplicador", "regra oculta", "r-001", r"\brio\b")


def test_o_cartao_vai_por_cima_do_genero() -> None:
    assert mind.name == "farm"
    assert mind.card.startswith("# Camps")
    assert "Fazenda do Camps" in mind.card
    assert mind.notes == campsverso_farm_mind.mind().notes
    assert mind.tools == campsverso_farm_mind.mind().tools


def test_registrada_como_mente_camps() -> None:
    found = {ep.name: ep for ep in entry_points(group="campsverso.minds")}
    assert "camps" in found
    loaded = found["camps"].load()
    assert isinstance(loaded, Mind)
    assert loaded.card == mind.card


def test_o_cartao_nao_conta_a_regra_oculta() -> None:
    card = CARD.read_text(encoding="utf-8").lower()
    method = playbook(mind).lower()  # o playbook também é lido pela mente (ADR-0071)
    for word in FORBIDDEN:
        assert re.search(word, card) is None, word
        assert re.search(word, method) is None, word
