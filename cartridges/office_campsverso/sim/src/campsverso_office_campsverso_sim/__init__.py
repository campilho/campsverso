"""Cartucho office_campsverso, o escritório do Campsverso (ADR-0078)."""

from campsverso_office_campsverso_sim.cartridge import OfficeCampsversoCartridge

cartridge = OfficeCampsversoCartridge()  # entry point campsverso.cartridges: office_campsverso

__all__ = ["OfficeCampsversoCartridge", "cartridge"]
