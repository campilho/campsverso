"""O clima sozinho (ADR-0069): as chances por estação, e o sorteio de sempre quando só há chuva."""

from campsverso_climate import ClimateRules, draw


class Fixed:
    def __init__(self, *values: float) -> None:
        self.values = list(values)

    def random(self) -> float:
        return self.values.pop(0)


def test_so_com_chuva_e_o_sorteio_de_sempre() -> None:
    rules = ClimateRules(default={"rain": 0.2})
    assert draw(Fixed(0.19), rules) == "rain"
    assert draw(Fixed(0.2), rules) == "sun"


def test_cada_estacao_tem_as_suas_chances_e_o_resto_e_sol() -> None:
    rules = ClimateRules(
        default={"rain": 0.2, "storm": 0.04, "drought": 0.03},
        by_season={
            "verao": {"rain": 0.3, "storm": 0.08},
            "inverno": {"rain": 0.05, "drought": 0.1},
        },
    )
    # Em ordem alfabética: drought, rain, storm; o que sobra é sol.
    assert draw(Fixed(0.02), rules, "primavera") == "drought"
    assert draw(Fixed(0.10), rules, "primavera") == "rain"
    assert draw(Fixed(0.25), rules, "primavera") == "storm"
    assert draw(Fixed(0.28), rules, "primavera") == "sun"
    assert draw(Fixed(0.35), rules, "verao") == "storm"
    assert draw(Fixed(0.09), rules, "inverno") == "drought"
    assert draw(Fixed(0.14), rules, "inverno") == "rain"
    assert draw(Fixed(0.16), rules, "inverno") == "sun"
    assert draw(Fixed(0.10), rules, None) == "rain"
