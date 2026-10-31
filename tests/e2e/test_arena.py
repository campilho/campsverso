"""A arena em processo (ADR-0061): a corrida do script, sem API, e a composição das pastas."""

import json
from pathlib import Path

import pytest

from campsverso_budget.ledger import BudgetLimits
from campsverso_mind import Clock
from campsverso_ports import ModelCapabilities, ModelRequest, ModelResponse, ModelUsage
from campsverso_testkit.arena import (
    ROUNDS,
    SEED,
    SEED_BOAVISTA,
    SEED_MORADA,
    SPECS,
    SPECS_AJUDANTES,
    SPECS_BOAVISTA,
    SPECS_MORADA,
    SPECS_PLAYBOOK,
    SPECS_TERCEIRA,
    Spec,
    main,
    run_spec,
)
from campsverso_testkit.pipeline import Pipeline


async def test_a_corrida_do_script_grava_a_pasta(tmp_path: Path) -> None:
    folder = tmp_path / "script"
    result = await run_spec(Spec("script", "script"), 2, folder)
    assert result["spec"] == {
        "name": "script",
        "controller": "script",
        "memory": False,
        "river_bonus": True,
        "seed": SEED,
        "cartridge": "farm_camps",
        "model": "claude-haiku-5-5",
        "days": None,
        "limits": None,
        "script": None,
        "map": None,
        "playbook": 0,
        "hire": None,
        "hire_from": 8,
        "compare": False,
        "advisor": None,
    }
    assert result["totals"]["days"] == 2
    card = result["card"]  # a ficha (ADR-0074): o script e o commit
    assert (card["controller"], card["harness"]["script"]) == ("script", "o do cartucho")
    assert len(card["harness"]["commit"]) == 40
    assert (result["calls"], result["gave_up"], result["aborted_day"]) == (0, False, None)
    assert result["budget_day"] is None
    assert "plantings" in result["totals"]
    assert (result["east"]["first_note"], result["east"]["beliefs"]) == (None, [])
    assert {p.name for p in folder.iterdir()} == {
        "summary.json",
        "metrics.txt",
        "archive.jsonl",
        "progresso.txt",
        "estado.json",
    }
    assert "script dia 2:" in (folder / "progresso.txt").read_text(encoding="utf-8")
    # O modo de assistir lê o arquivo enquanto ele cresce e o estado diz se acabou (ADR-0068).
    state = json.loads((folder / "estado.json").read_text(encoding="utf-8"))
    lines = (folder / "archive.jsonl").read_text(encoding="utf-8").splitlines()
    assert (state["day"], state["done"], state["events"]) == (2, True, len(lines))


def test_a_arena_so_completa_o_que_falta(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out = tmp_path / "arena"
    assert main(["--only", "script", "--days", "1", "--out", str(out)]) == 0
    stamp = (out / "script" / "summary.json").stat().st_mtime_ns
    assert main(["--only", "script", "--days", "1", "--out", str(out)]) == 0
    assert (out / "script" / "summary.json").stat().st_mtime_ns == stamp
    assert "script: feita, pulando" in capsys.readouterr().out


def test_as_corridas_da_arena() -> None:
    """ADR-0061, decisões 2 e 3: script, Haiku sem memória, Haiku com memória em quatro seeds e
    Haiku com memória sem a regra, todos no mesmo mundo."""
    assert [s.name for s in SPECS][:3] == ["script", "haiku", "haiku-memoria"]
    assert sum(s.memory for s in SPECS) == 5
    assert [s.name for s in SPECS if not s.river_bonus] == ["haiku-memoria-sem-regra"]
    assert len({s.seed for s in SPECS if s.name.startswith("haiku-memoria")}) == 4
    assert [s.name for s in SPECS if s.seed == SEED] == [
        "script",
        "haiku",
        "haiku-memoria",
        "haiku-memoria-sem-regra",
    ]


# ----------------------------------------------------------------- a segunda rodada (ADR-0063)


def test_as_corridas_da_boa_vista() -> None:
    """ADR-0063: o script 2, o Haiku com memória em quatro seeds e sem a regra, o Sonnet e o
    Opus, todos na Boa Vista por 30 dias, cada um com o seu teto."""
    assert [s.name for s in SPECS_BOAVISTA] == [
        "script2",
        "haiku-memoria",
        "haiku-memoria-s2",
        "haiku-memoria-s3",
        "haiku-memoria-s4",
        "haiku-memoria-sem-regra",
        "sonnet-memoria",
        "opus-memoria",
    ]
    assert {s.cartridge for s in SPECS_BOAVISTA} == {"farm_boavista"}
    assert {s.days for s in SPECS_BOAVISTA} == {30}
    assert all(s.memory for s in SPECS_BOAVISTA if s.controller == "llm")
    by = {s.name: s for s in SPECS_BOAVISTA}
    assert (by["sonnet-memoria"].model, by["sonnet-memoria"].limits) == (
        "claude-sonnet-5-5",
        BudgetLimits(1.5, 25.0),
    )
    assert (by["opus-memoria"].model, by["opus-memoria"].limits) == (
        "claude-opus-5-5",
        BudgetLimits(2.5, 35.0),
    )
    assert by["haiku-memoria"].limits is None  # o teto do Haiku, o mesmo do M12
    assert [s.name for s in SPECS_BOAVISTA if s.seed == SEED_BOAVISTA] == [
        "script2",
        "haiku-memoria",
        "haiku-memoria-sem-regra",
        "sonnet-memoria",
        "opus-memoria",
    ]
    assert ROUNDS == {
        "camps": SPECS,
        "boavista": SPECS_BOAVISTA,
        "morada": SPECS_MORADA,
        "playbook": SPECS_PLAYBOOK,
        "ajudantes": SPECS_AJUDANTES,
        "terceira": SPECS_TERCEIRA,
    }


def test_a_rodada_dos_ajudantes_compara_cada_contrato_com_a_mesma_regua() -> None:
    # ADR-0073: o script 3 e o oráculo nos mapas a e b, sem ajudante e com a contratação forçada.
    names = [s.name for s in SPECS_AJUDANTES]
    assert len(names) == 20
    assert {"script3-a", "oraculo-b", "oraculo-a-tiao7", "script3-b-dita1"} <= set(names)
    hired = [s for s in SPECS_AJUDANTES if s.hire is not None]
    assert {s.hire for s in hired} == {"tiao:1", "tiao:7", "nina:3", "dita:1"}
    assert {s.hire_from for s in hired} == {8}
    assert {s.days for s in SPECS_AJUDANTES} == {28}


def test_a_rodada_de_verificacao_da_morada_do_sol() -> None:
    """ADR-0070, decisão 14: as três réguas nos três mapas, o script 3 sem as regras do arquivo e
    o Haiku com memória no mapa a, um ano cada, na seed do mundo."""
    by = {s.name: s for s in SPECS_MORADA}
    assert list(by) == [
        "script2-a",
        "script2-b",
        "script2-c",
        "script3-a",
        "script3-b",
        "script3-c",
        "oraculo-a",
        "oraculo-b",
        "oraculo-c",
        "script3-sem-regras",
        "haiku-memoria",
    ]
    assert {(s.cartridge, s.seed, s.days) for s in SPECS_MORADA} == {
        ("farm_morada_do_sol", 20261022, 28)
    }
    assert (by["script3-a"].script, by["script3-a"].map) == ("farmer3", None)
    assert (by["oraculo-c"].script, by["oraculo-c"].map) == ("oracle", "c")
    assert by["script2-b"].script == "farmer2"
    assert not by["script3-sem-regras"].river_bonus
    assert (by["haiku-memoria"].controller, by["haiku-memoria"].memory) == ("llm", True)
    assert by["haiku-memoria"].map is None


def test_a_terceira_rodada_poe_as_quatro_reguas_nos_quatro_mapas() -> None:
    """ADR-0074: o script 2, o script 3, o script 3 fixo e o oráculo nos mapas a, b, c e d; depois,
    as corridas dos modelos no mapa d, uma por vez: o Haiku três vezes, com memória, e os braços."""
    by = {s.name: s for s in SPECS_TERCEIRA}
    assert len(by) == 22
    assert (by["script3-fixo-d"].script, by["script3-fixo-d"].map) == ("farmer3-fixo", "d")
    assert (by["oraculo-a"].script, by["oraculo-a"].map) == ("oracle", None)
    assert {(s.cartridge, s.seed, s.days) for s in SPECS_TERCEIRA} == {
        ("farm_morada_do_sol", 20261022, 28)
    }
    haikus = [s for s in SPECS_TERCEIRA if s.controller == "llm"]
    assert [s.name for s in haikus] == [
        "haiku",
        "haiku-r2",
        "haiku-r3",
        "haiku-comparar",
        "haiku-comparar-r2",
        "haiku-conselheiro",
    ]
    assert {(s.model, s.map, s.memory, s.playbook) for s in haikus} == {
        ("claude-haiku-5-5", "d", True, 0)
    }
    arms = {s.name: (s.compare, s.advisor, s.limits) for s in haikus}
    assert arms["haiku"] == (False, None, None)
    assert arms["haiku-comparar-r2"] == (True, None, None)
    assert arms["haiku-conselheiro"] == (False, "claude-opus-4-8", BudgetLimits(1.00, 12.0))


def test_a_rodada_do_agricultor_treinado() -> None:
    """ADR-0071: o Haiku com o playbook no mapa a, sem e com no mapa b, e a dupla do Sonnet de 14
    dias com teto de US$ 15, todos com memória, na Morada do Sol."""
    by = {s.name: s for s in SPECS_PLAYBOOK}
    assert [(s.name, s.map, s.playbook) for s in SPECS_PLAYBOOK] == [
        ("haiku-playbook", None, 1),
        ("haiku-memoria-b", "b", 0),
        ("haiku-playbook-b", "b", 1),
        ("haiku-playbook2", None, 2),
        ("haiku-playbook2-r2", None, 2),
        ("haiku-playbook2-b", "b", 2),
        ("haiku-playbook2-b-r2", "b", 2),
        ("sonnet-memoria-14d", None, 0),
        ("sonnet-playbook-14d", None, 2),
    ]
    assert all(s.memory and s.cartridge == "farm_morada_do_sol" for s in SPECS_PLAYBOOK)
    assert {s.days for s in SPECS_PLAYBOOK if s.model == "claude-haiku-5-5"} == {28}
    sonnet = by["sonnet-playbook-14d"]
    assert (sonnet.model, sonnet.days, sonnet.limits) == (
        "claude-sonnet-5-5",
        14,
        BudgetLimits(1.5, 15.0),
    )


async def test_um_playbook_antigo_nao_roda_mais(tmp_path: Path) -> None:
    """ADR-0071: a corrida grava a versão do playbook; uma versão que saiu do código é recusada
    antes de gastar, e as antigas ficam no git."""
    old = Spec("velho", "llm", memory=True, cartridge="farm_morada_do_sol", playbook=1)
    with pytest.raises(ValueError, match="o playbook 1 não está mais no código"):
        await run_spec(old, 1, tmp_path / "velho")
    assert not (tmp_path / "velho").exists()


def test_a_reserva_ao_comecar_e_o_script_2_na_boa_vista(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out = tmp_path / "arena"
    (out / "script2").mkdir(parents=True)  # outro processo tomou a corrida
    args = ["--rodada", "boavista", "--only", "script2", "--days", "1", "--out", str(out)]
    assert main(args) == 0
    assert "script2: tomada por outro processo" in capsys.readouterr().out
    assert not (out / "script2" / "summary.json").exists()
    (out / "script2").rmdir()  # abandonada: apagar a pasta devolve a corrida
    assert main(args) == 0
    summary = json.loads((out / "script2" / "summary.json").read_text(encoding="utf-8"))
    assert (summary["spec"]["cartridge"], summary["totals"]["days"]) == ("farm_boavista", 1)
    assert summary["east"]["river"] == "rio"
    assert summary["totals"]["plots_dug"] == {"fora": 16}  # o script 2 cava ao redor do poço


def test_uma_corrida_fora_da_rodada_e_erro(tmp_path: Path) -> None:
    with pytest.raises(SystemExit):
        main(["--rodada", "boavista", "--only", "haiku", "--days", "1", "--out", str(tmp_path)])


class SpendingPort:
    """Uma porta que só espera e cobra caro: dez milhões de tokens por pedido."""

    provider = "fake"

    def capabilities(self) -> ModelCapabilities:
        return ModelCapabilities()

    async def count_tokens(self, request: ModelRequest) -> int:
        return 1

    async def complete(self, request: ModelRequest) -> ModelResponse:
        return ModelResponse(
            content=[
                {
                    "type": "tool_use",
                    "id": "toolu_1",
                    "name": "wait",
                    "input": {"ticks": 15, "intent": "esperar"},
                }
            ],
            stop_reason="tool_use",
            usage=ModelUsage(10_000_000, 40, 0, 0),
            model=request.model,
            latency_ms=1,
        )


async def test_a_corrida_para_no_teto_de_orcamento(tmp_path: Path) -> None:
    """ADR-0063, decisão 2: a guarda pausa o mundo no teto e a corrida para ali, marcada."""
    spec = Spec(
        "cara",
        "llm",
        memory=True,
        seed=SEED_BOAVISTA,
        cartridge="farm_boavista",
        days=2,
        limits=BudgetLimits(usd_per_sim_day=0.5, usd_total=0.5),
    )
    result = await run_spec(spec, 2, tmp_path / "cara", port=SpendingPort())
    assert result["budget_day"] == 1
    assert result["budget_exceeded"] >= 1
    assert result["spec"]["limits"] == {"usd_per_sim_day": 0.5, "usd_total": 0.5}
    assert "bateu no teto" in (tmp_path / "cara" / "progresso.txt").read_text(encoding="utf-8")


def test_a_comparacao_liga_por_corrida_e_so_com_memoria() -> None:
    """ADR-0074, decisão 7: o braço da comparação liga a ferramenta na reflexão da mente da
    Morada do Sol, com as colunas do gênero; sem memória, não há caderno para ler."""
    assert Spec("haiku", "llm").compare is False
    on = Pipeline(
        SEED_MORADA,
        controller="llm",
        port=SpendingPort(),
        cartridge="farm_morada_do_sol",
        compare=True,
    )
    assert on.mind is not None
    assert on.mind.memory is not None
    memory = on.mind.memory
    assert memory.columns is not None
    assert set(memory.columns.names) == {"água", "mata", "caminho", "porta", "espantalho"}
    tools = memory.reflect_request("x", Clock(900, 1, ""), 1, "m").tools
    assert [t["name"] for t in tools] == ["comparar", "reflect"]
    off = Pipeline(
        SEED_MORADA, controller="llm", port=SpendingPort(), cartridge="farm_morada_do_sol"
    )
    assert off.mind is not None
    assert off.mind.memory is not None
    assert off.mind.memory.columns is None
    with pytest.raises(ValueError, match="precisam de memória"):
        Pipeline(
            SEED_MORADA,
            controller="llm",
            port=SpendingPort(),
            cartridge="farm_morada_do_sol",
            memory=False,
            compare=True,
        )


def test_o_conselheiro_liga_por_corrida_e_precisa_de_preco() -> None:
    """ADR-0074, decisões 8 e 9: o braço do conselheiro põe o Opus 4.8 na reflexão; um
    conselheiro sem preço na tabela derruba a montagem, nunca uma chamada."""
    assert Spec("haiku", "llm").advisor is None
    on = Pipeline(
        SEED_MORADA,
        controller="llm",
        port=SpendingPort(),
        cartridge="farm_morada_do_sol",
        advisor="claude-opus-4-8",
    )
    assert on.mind is not None
    assert on.mind.memory is not None
    tools = on.mind.memory.reflect_request("x", Clock(900, 1, ""), 1, "m").tools
    assert [t["name"] for t in tools] == ["advisor", "reflect"]
    with pytest.raises(LookupError, match="modelo-sem-preco"):
        Pipeline(
            SEED_MORADA,
            controller="llm",
            port=SpendingPort(),
            cartridge="farm_morada_do_sol",
            advisor="modelo-sem-preco",
        )
