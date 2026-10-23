"""Regras genéricas do gênero. Desligadas por padrão: o cenário declara as instâncias (ADR-0039)."""

from collections.abc import Mapping
from dataclasses import dataclass

from campsverso_cartridge_api import EntityView, Scalar, WorldView


@dataclass(frozen=True)
class WaterProximityBonus:
    """Multiplica o crescimento de quem está perto de água.

    O gênero não sabe onde há água: mede a distância (Chebyshev, como a vizinhança de 8) até o tile
    mais próximo marcado com `water` no mapa do cenário.
    """

    name: str = "water_proximity_bonus"
    target: str = "growth_points"

    def apply(
        self, view: WorldView, entity: EntityView, value: float, params: Mapping[str, Scalar]
    ) -> float:
        if entity.position is None:
            return value
        radius = int(params.get("radius") or 0)
        near = any(entity.position.chebyshev(tile) <= radius for tile in view.tiles_with("water"))
        return value * float(params.get("multiplier") or 1.0) if near else value


@dataclass(frozen=True)
class SoilFatigue:
    """Repetir a cultura no mesmo canteiro cansa o solo: ela cresce mais devagar (ADR-0067).

    O canteiro lembra a cultura que saiu por último (`last_crop`, oculto); trocar de cultura
    recupera o solo. O gênero não sabe o quanto: o multiplicador é parâmetro da instância.
    """

    name: str = "soil_fatigue"
    target: str = "growth_points"

    def apply(
        self, view: WorldView, entity: EntityView, value: float, params: Mapping[str, Scalar]
    ) -> float:
        crop = entity.attributes.get("crop")
        if crop is None or entity.hidden.get("last_crop") != crop:
            return value
        return value * float(params.get("multiplier") or 1.0)
