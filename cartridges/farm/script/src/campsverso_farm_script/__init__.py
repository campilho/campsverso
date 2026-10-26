"""Fazendeiros-script do cartucho farm. Dependem só dos contratos (ADR-0011)."""

from campsverso_farm_script.farmer import FarmerScript
from campsverso_farm_script.farmer2 import Farmer2Script
from campsverso_farm_script.farmer3 import Farmer3Script
from campsverso_farm_script.helper import HelperScript, helper

controller = FarmerScript.load()  # entry point campsverso.controllers: farmer
controller2 = Farmer2Script.load()  # entry point campsverso.controllers: farmer2 (bíblia 2, §11)
controller3 = Farmer3Script.load()  # entry point campsverso.controllers: farmer3 (ADR-0070)
oracle = Farmer3Script.oracle()  # entry point campsverso.controllers: oracle (ADR-0070)
# entry point campsverso.controllers: ajudante, a fábrica `helper(avatar_id)` (ADR-0072)

__all__ = [
    "Farmer2Script",
    "Farmer3Script",
    "FarmerScript",
    "HelperScript",
    "controller",
    "controller2",
    "controller3",
    "helper",
    "oracle",
]
