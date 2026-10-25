from dataclasses import dataclass, field
from pathlib import Path

import pytest

from campsverso_cartridge_api import CartridgeManifest, ItemDef, MetricDef, WorldBuilder
from campsverso_kernel import DefinitionError, RealTimePacer, build_world, resolve_chain
from campsverso_kernel.testing import LabCartridge, lab_map


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


@dataclass(frozen=True)
class MetricLayer:
    """Uma camada que só acrescenta métricas (ADR-0054)."""

    manifest: CartridgeManifest
    metrics: tuple[MetricDef, ...]

    def contribute(self, world: WorldBuilder) -> None:
        for metric in self.metrics:
            world.add_metric(metric)

    def rules_file(self) -> Path | None:
        return None


def test_metricas_em_camadas_e_conferidas_na_carga() -> None:
    touches = MetricDef(
        "toques",
        "Toques",
        "count",
        event="campsverso.action.completed.v1",
        where={"action": "touch"},
    )
    energy = MetricDef("energia_max", "Pico de energia", "max_need", need="energia")
    top = MetricLayer(CartridgeManifest("top", "1.0.0", ("lab",)), (touches, energy))
    definition = build_world("top", {"lab": LabCartridge(), "top": top})
    assert [m.id for m in definition.metrics] == ["toques", "energia_max"]

    wrong = (
        MetricDef("x", "X", "count", event="campsverso.farm.inexistente.v1"),
        MetricDef("y", "Y", "max_need", need="sede"),
        MetricDef("z", "Z", "item", item="ouro"),
    )
    for metric, problem in zip(wrong, ("contratos", "necessidade", "item"), strict=True):
        layer = MetricLayer(CartridgeManifest("top", "1.0.0", ("lab",)), (metric,))
        with pytest.raises(DefinitionError, match=problem):
            build_world("top", {"lab": LabCartridge(), "top": layer})


def test_tick_antecipado_desconta_do_tempo_real_e_so_um_por_vez() -> None:
    """ADR-0057: o antecipado não cria tick a mais; com a dívida em aberto, o próximo espera."""
    pacer = RealTimePacer(60, 1.0)
    assert pacer.ticks_for(10) == 0
    assert pacer.advance_early() is True
    assert pacer.advance_early() is False  # dívida em aberto
    assert pacer.ticks_for(50) == 0  # completaria o primeiro tick: ele já rodou antes da hora
    assert pacer.ticks_for(60) == 1  # o segundo vem na hora normal
    assert pacer.advance_early() is True  # dívida paga: pode antecipar de novo


# ----------------------------------------------------------------- variantes do mapa (ADR-0070)


@dataclass(frozen=True)
class Variants:
    """Um cenário sobre o laboratório que oferece outro mapa: o mesmo, sem a caixa."""

    manifest: CartridgeManifest = field(
        default_factory=lambda: CartridgeManifest("sitio", "1.0.0", ("lab",))
    )

    def contribute(self, world: WorldBuilder) -> None:
        other = lab_map()
        other["layers"][1]["objects"] = other["layers"][1]["objects"][:1]
        world.add_map_variant("b", other)

    def rules_file(self) -> Path | None:
        return None


def test_o_mundo_escolhe_a_variante_do_mapa_pelo_nome() -> None:
    chain = {"lab": LabCartridge(), "sitio": Variants()}
    base = build_world("sitio", chain)
    assert base.grid.map_id == "sitio"
    assert "box" in base.spawns
    variant = build_world("sitio", chain, map_variant="b")
    assert variant.grid.map_id == "sitio-b"
    assert "box" not in variant.spawns
    with pytest.raises(DefinitionError, match="não tem a variante de mapa 'z' \\(b\\)"):
        build_world("sitio", chain, map_variant="z")


def test_o_nome_da_variante_cabe_no_id_do_mapa() -> None:
    class Bad(Variants):
        def contribute(self, world: WorldBuilder) -> None:
            world.add_map_variant("Rio Leste", lab_map())

    with pytest.raises(DefinitionError, match="nome de variante do mapa inválido"):
        build_world("sitio", {"lab": LabCartridge(), "sitio": Bad()})
