"""Os scripts do escritório (ADR-0078). Dependem só dos contratos (ADR-0011)."""

from campsverso_office_script.scripts import DevScript, GuardScript, ManagerScript, staff

dev = DevScript.load()  # entry point campsverso.controllers: dev
# entry point campsverso.controllers: escritorio, a fábrica `staff(avatar_id)` (o vigia e o gerente)

__all__ = ["DevScript", "GuardScript", "ManagerScript", "dev", "staff"]
