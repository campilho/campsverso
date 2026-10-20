"""Fazendeiros-script do cartucho farm. Dependem só dos contratos (ADR-0011)."""

from campsverso_farm_script.farmer import FarmerScript
from campsverso_farm_script.farmer2 import Farmer2Script

controller = FarmerScript.load()  # entry point campsverso.controllers: farmer
controller2 = Farmer2Script.load()  # entry point campsverso.controllers: farmer2 (bíblia 2, §11)

__all__ = ["Farmer2Script", "FarmerScript", "controller", "controller2"]
