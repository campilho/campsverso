"""A arena em processo (ADR-0061): a corrida do script, sem API, e a composição das pastas."""

import json
from pathlib import Path

import pytest

from campsverso_budget.ledger import BudgetLimits
from campsverso_ports import ModelCapabilities, ModelRequest, ModelResponse, ModelUsage
from campsverso_testkit.arena import (
    ROUNDS,
    SEED,
    SEED_BOAVISTA,
    SPECS,
    SPECS_BOAVISTA,
    SPECS_MORADA,
    SPECS_PLAYBOOK,
    Spec,
    main,
    run_spec,
)


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
        "playbook": False,
    }
    assert result["totals"]["days"] == 2
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
    }


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


def test_a_rodada_do_agricultor_treinado() -> None:
    """ADR-0071: o Haiku com o playbook no mapa a, sem e com no mapa b, e a dupla do Sonnet de 14
    dias com teto de US$ 15, todos com memória, na Morada do Sol."""
    by = {s.name: s for s in SPECS_PLAYBOOK}
    assert [(s.name, s.map, s.playbook) for s in SPECS_PLAYBOOK] == [
        ("haiku-playbook", None, True),
        ("haiku-memoria-b", "b", False),
        ("haiku-playbook-b", "b", True),
        ("sonnet-memoria-14d", None, False),
        ("sonnet-playbook-14d", None, True),
    ]
    assert all(s.memory and s.cartridge == "farm_morada_do_sol" for s in SPECS_PLAYBOOK)
    assert {s.days for s in SPECS_PLAYBOOK if s.model == "claude-haiku-5-5"} == {28}
    sonnet = by["sonnet-playbook-14d"]
    assert (sonnet.model, sonnet.days, sonnet.limits) == (
        "claude-sonnet-5-5",
        14,
        BudgetLimits(1.5, 15.0),
    )


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
