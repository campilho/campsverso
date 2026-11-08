"""As estações de um mundo com ano, como o manual as conta (ADR-0074, decisão 35): os dias de cada
cultura na estação boa e o calendário de plantio. A tabela do caderno completo calcula com isto os
dias esperados de cada plantio. São os números do manual, que o modelo já lê, e não os do mundo:
o teste da mente de cada cenário confere que os dois dizem o mesmo.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, cast

# Quantas vezes mais a planta leva em cada qualidade de estação; a parada não cresce.
FACTOR: Mapping[str, int] = {"boa": 1, "fraca": 2}
STOPPED = "parada"


@dataclass(frozen=True, slots=True)
class Seasons:
    """`days`: os dias de cada cultura na estação boa; `calendar`: a qualidade (boa, fraca,
    parada) de cada cultura em cada estação, pelo id da estação no relógio; `names`: como cada
    estação se escreve na tela."""

    days: Mapping[str, int]
    calendar: Mapping[str, Mapping[str, str]]
    names: Mapping[str, str]

    @classmethod
    def of(cls, raw: Mapping[str, Any]) -> Seasons:
        """De um `estacoes.yaml`: `names: {id: nome}` e
        `crops: {cultura: {dias, id: qualidade}}`."""
        names = {str(k): str(v) for k, v in cast(Mapping[str, Any], raw["names"]).items()}
        crops = cast(Mapping[str, Mapping[str, Any]], raw["crops"])
        days = {str(c): int(v["dias"]) for c, v in crops.items()}
        calendar = {str(c): {s: str(v[s]) for s in names} for c, v in crops.items()}
        for crop, by_season in calendar.items():
            wrong = {q for q in by_season.values() if q not in (*FACTOR, STOPPED)}
            if wrong:
                raise ValueError(f"{crop}: qualidade de estação desconhecida {sorted(wrong)}")
        return cls(days, calendar, names)

    def name(self, season: str | None) -> str:
        return "-" if season is None else self.names.get(season, season)

    def quality(self, crop: str, season: str | None) -> str | None:
        """Boa, fraca ou parada; `None` se a cultura ou a estação não estão no manual."""
        if season is None:
            return None
        return self.calendar.get(crop, {}).get(season)

    def expected(self, crop: str, season: str | None) -> str:
        """Os dias que o manual dá para a cultura na estação, em texto: `3`, `10` ou `parada`; `-`
        quando o manual não diz."""
        quality = self.quality(crop, season)
        if quality is None or crop not in self.days:
            return "-"
        if quality == STOPPED:
            return STOPPED
        return str(self.days[crop] * FACTOR[quality])
