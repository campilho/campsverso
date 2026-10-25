"""Carrega a cadeia de cartuchos pelo nome, sem importá-los (princípio 8; ADR-0011, ADR-0031)."""

from collections.abc import Mapping
from importlib.metadata import entry_points
from typing import cast

from campsverso_cartridge_api import Cartridge
from campsverso_kernel.definition import DefinitionBuilder, WorldDefinition
from campsverso_kernel.errors import DefinitionError
from campsverso_kernel.pipeline import DEFAULT_STAGES

ENTRY_POINT_GROUP = "campsverso.cartridges"


def discover() -> dict[str, Cartridge]:
    """Cartuchos instalados, registrados no grupo de entry points `campsverso.cartridges`."""
    return {
        ep.name: cast(Cartridge, ep.load())
        for ep in sorted(entry_points(group=ENTRY_POINT_GROUP), key=lambda e: e.name)
    }


def resolve_chain(top: str, available: Mapping[str, Cartridge]) -> list[Cartridge]:
    """Ordem de montagem: cada cartucho depois de tudo o que ele estende."""
    ordered: list[Cartridge] = []
    visiting: set[str] = set()
    done: set[str] = set()

    def visit(name: str, path: tuple[str, ...]) -> None:
        if name in done:
            return
        if name in visiting:
            raise DefinitionError(f"ciclo na cadeia de cartuchos: {' -> '.join((*path, name))}")
        cartridge = available.get(name)
        if cartridge is None:
            raise DefinitionError(
                f"cartucho {name!r} não encontrado (entry point {ENTRY_POINT_GROUP})"
            )
        if cartridge.manifest.id != name:
            raise DefinitionError(
                f"o entry point {name!r} aponta para o cartucho {cartridge.manifest.id!r}"
            )
        visiting.add(name)
        for base in cartridge.manifest.extends:
            visit(base, (*path, name))
        visiting.discard(name)
        done.add(name)
        ordered.append(cartridge)

    visit(top, ())
    return ordered


def build_world(
    top: str,
    cartridges: Mapping[str, Cartridge] | None = None,
    stages: tuple[str, ...] = DEFAULT_STAGES,
    map_variant: str | None = None,
) -> WorldDefinition:
    """`map_variant` escolhe uma variante do mapa do cartucho do topo (ADR-0070)."""
    chain = resolve_chain(top, cartridges if cartridges is not None else discover())
    builder = DefinitionBuilder(stages=stages)
    for cartridge in chain:
        cartridge.contribute(builder)
    return builder.build([c.manifest for c in chain], map_variant)
