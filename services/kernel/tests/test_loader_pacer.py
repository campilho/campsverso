from dataclasses import dataclass, field
from pathlib import Path

import pytest

from campsverso_cartridge_api import CartridgeManifest, ItemDef, WorldBuilder
from campsverso_kernel import DefinitionError, RealTimePacer, build_world, resolve_chain
from campsverso_kernel.testing import LabCartridge


@dataclass(frozen=True)
class Layer:
    manifest: CartridgeManifest
    items: tuple[str, ...] = ()
    override: bool = False
    calls: list[str] = field(default_factory=list[str])

    def contribute(self, world: WorldBuilder) -> None:
        self.calls.append(self.manifest.id)
        for item in self.items:
            world.define_item(ItemDef(item, "teste"), override=self.override)

    def rules_file(self) -> Path | None:
        return None


def test_cadeia_monta_da_base_para_o_topo() -> None:
    available = {
        "base": Layer(CartridgeManifest("base", "1.0.0")),
        "genero": Layer(CartridgeManifest("genero", "1.0.0", ("base",))),
        "cenario": Layer(CartridgeManifest("cenario", "1.0.0", ("genero",))),
    }
    chain = resolve_chain("cenario", available)
    assert [c.manifest.id for c in chain] == ["base", "genero", "cenario"]


def test_ciclo_e_cartucho_ausente_falham_na_carga() -> None:
    cyclic = {
        "a": Layer(CartridgeManifest("a", "1.0.0", ("b",))),
        "b": Layer(CartridgeManifest("b", "1.0.0", ("a",))),
    }
    with pytest.raises(DefinitionError, match="ciclo"):
        resolve_chain("a", cyclic)
    with pytest.raises(DefinitionError, match="não encontrado"):
        resolve_chain("x", cyclic)


def test_nome_repetido_sem_override_falha_e_com_override_substitui() -> None:
    lab = LabCartridge()
    repeated = {"lab": lab, "top": Layer(CartridgeManifest("top", "1.0.0", ("lab",)), ("pedra",))}
    with pytest.raises(DefinitionError, match="repetido sem override"):
        build_world("top", repeated)
    replaced = {
        "lab": lab,
        "top": Layer(CartridgeManifest("top", "1.0.0", ("lab",)), ("pedra",), override=True),
    }
    definition = build_world("top", replaced)
    assert definition.items["pedra"].category == "teste"
    assert [m.id for m in definition.chain] == ["lab", "top"]


def test_acumulador_converte_tempo_real_em_ticks_sem_perder_o_resto() -> None:
    pacer = RealTimePacer(tick_seconds=60, scale=72)  # 1 tick a cada 0,8333 s reais
    assert pacer.ticks_for(0.5) == 0
    assert pacer.ticks_for(0.5) == 1
    assert sum(pacer.ticks_for(0.1) for _ in range(100)) == 12
