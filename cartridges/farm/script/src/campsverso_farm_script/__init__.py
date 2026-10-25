"""Fazendeiros-script do cartucho farm. Dependem só dos contratos (ADR-0011)."""

from campsverso_farm_script.farmer import FarmerScript
from campsverso_farm_script.farmer2 import Farmer2Script
from campsverso_farm_script.farmer3 import Farmer3Script

controller = FarmerScript.load()  # entry point campsverso.controllers: farmer
controller2 = Farmer2Script.load()  # entry point campsverso.controllers: farmer2 (bíblia 2, §11)
controller3 = Farmer3Script.load()  # entry point campsverso.controllers: farmer3 (ADR-0070)
oracle = Farmer3Script.oracle()  # entry point campsverso.controllers: oracle (ADR-0070)

__all__ = [
    "Farmer2Script",
    "Farmer3Script",
    "FarmerScript",
    "controller",
    "controller2",
    "controller3",
    "oracle",
]
