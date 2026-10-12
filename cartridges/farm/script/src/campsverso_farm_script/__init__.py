"""Fazendeiro-script do cartucho farm. Depende só dos contratos (ADR-0011)."""

from campsverso_farm_script.farmer import FarmerScript

controller = FarmerScript.load()  # entry point campsverso.controllers: farmer

__all__ = ["FarmerScript", "controller"]
