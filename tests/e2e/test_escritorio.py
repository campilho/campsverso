"""O escritório de ponta a ponta, em memória (M23, ADR-0078): o dev-script, o vigia e o
gerente-script trocam envelopes pelo barramento, como trocariam pelo NATS."""

import asyncio
from typing import Any

import pytest

from campsverso_kernel.loader import build_world
from campsverso_testkit.escritorio import office_report
from campsverso_testkit.pipeline import Pipeline


async def _day() -> Pipeline:
    pipeline = Pipeline(cartridge="office_campsverso")
    await pipeline.start()
    await pipeline.run_days(1)
    return pipeline


@pytest.fixture(scope="module")
def day() -> Pipeline:
    """Um dia do escritório, rodado uma vez para os testes do módulo: cada dia leva quase um minuto,
    e quatro deles passavam de sete minutos no CI (19/nov). Os testes só leem os fatos."""
    return asyncio.run(_day())


def _count(pipeline: Pipeline, event: str) -> int:
    return len(pipeline.of_type(event.removeprefix("campsverso.")))


def test_um_dia_de_pedidos_do_quadro_a_entrega(day: Pipeline) -> None:
    pipeline = day
    # O roteiro do gerente: três pedidos; o terceiro volta uma vez e é refeito.
    assert _count(pipeline, "campsverso.office.ticket.created.v1") == 3
    assert _count(pipeline, "campsverso.office.ticket.returned.v1") == 1
    assert _count(pipeline, "campsverso.office.ticket.delivered.v1") == 4
    assert _count(pipeline, "campsverso.office.ticket.accepted.v1") == 3
    assert pipeline.of_type("action.rejected.v1") == []
    spoken = [d["text"] for d in pipeline.of_type("avatar.spoke.v1")]
    assert "Entreguei o pedido 1: Ferramenta de busca no código (dia 1)." in spoken
    # Os invariantes do soak (o plano do M24, §8) já no primeiro dia: os pedidos entregues, as
    # pausas e o almoço do dev, e ninguém na copa fora do expediente.
    schedule = build_world("office_campsverso").data["office"]["schedule"]
    report = office_report(pipeline.kernel_events(), schedule)
    assert report.problems == []
    assert report.workdays == ["2026-11-16"]
    assert report.pauses["2026-11-16"] >= 1
    assert report.lunches["2026-11-16"] == 1


def test_o_vigia_so_esta_quando_o_dev_nao_esta(day: Pipeline) -> None:
    inside: set[str] = set()
    for envelope in day.kernel_events():
        data: dict[str, Any] = envelope["data"]
        if envelope["type"] == "campsverso.avatar.entered.v1":
            inside.add(str(data["avatar_id"]))
        elif envelope["type"] == "campsverso.avatar.left.v1":
            inside.discard(str(data["avatar_id"]))
        assert not {"camps", "vigia"} <= inside, f"os dois no escritório no tick {envelope['tick']}"


async def test_o_mesmo_dia_duas_vezes_da_os_mesmos_fatos(day: Pipeline) -> None:
    first, second = day, await _day()

    def facts(pipeline: Pipeline) -> list[tuple[int, str, Any]]:
        return [(e["tick"], e["type"], e["data"]) for e in pipeline.kernel_events()]

    assert facts(first) == facts(second)
