"""Cartucho office, o gênero do escritório (ADR-0077, ADR-0078)."""

from campsverso_office_sim.cartridge import OfficeCartridge

cartridge = OfficeCartridge()  # entry point campsverso.cartridges: office

__all__ = ["OfficeCartridge", "cartridge"]
