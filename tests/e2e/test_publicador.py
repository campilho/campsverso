"""O ciclo fecha (ADR-0083), em memória: a entrega do dev vira um PR no GitHub falso, o vigia relata
o CI, a mesclagem aceita o pedido, e o PR fechado sem mesclar devolve o pedido, que o dev refaz no
mesmo ramo. O kernel guarda os relatos no diário, e o dia se reexecuta sem perguntar ao GitHub."""

from pathlib import Path
from typing import Any

from campsverso_kernel.replay import replay_day
from campsverso_testkit.oficina import example_office_repo
from campsverso_testkit.pipeline import Pipeline

REPORT = "campsverso.cmd.office.pull_request.report.v1"


# A devolução está na v2 desde a ADR-0092 (o comentário até 1.000 caracteres); o resto, na v1.
VERSIONS = {"returned": 2}


def _facts(pipeline: Pipeline, name: str) -> list[dict[str, Any]]:
    return pipeline.of_type(f"office.ticket.{name}.v{VERSIONS.get(name, 1)}")


async def _until(pipeline: Pipeline, name: str, count: int) -> None:
    """Roda o mundo, de meia em meia hora, até o fato aparecer `count` vezes (no máximo um dia)."""
    end = pipeline.core.tick + pipeline.day
    while len(_facts(pipeline, name)) < count:
        assert pipeline.core.tick < end, f"{name} não chegou a {count} em um dia"
        await pipeline.run_until(pipeline.core.tick + pipeline.day // 48)


async def _watch(pipeline: Pipeline) -> int:
    """Uma volta do vigia e um minuto de mundo, para o kernel aplicar o relato."""
    assert pipeline.codehost is not None
    reports = await pipeline.codehost.watch()
    await pipeline.run_until(pipeline.core.tick + pipeline.day // 1440)
    return reports


async def test_a_entrega_vira_pr_e_a_mesclagem_aceita(tmp_path: Path) -> None:
    pipeline = Pipeline(
        cartridge="office_campsverso", workshop_repo=example_office_repo(tmp_path), codehost=True
    )
    host, service = pipeline.host, pipeline.codehost
    assert host is not None
    assert service is not None
    await pipeline.start()

    # A entrega do pedido 1 sai do depósito, vira um commit no ramo do dev e um PR.
    await _until(pipeline, "pr_opened", 1)
    opened = _facts(pipeline, "pr_opened")[0]
    assert (opened["ticket_id"], opened["pull_request"], opened["branch"]) == (
        "pedido-001",
        1,
        "dev/pedido-1",
    )
    commit = host.branches["dev/pedido-1"][-1]
    delivered = _facts(pipeline, "delivered")[0]
    assert sorted(commit.files) == sorted(delivered["patch"]["files"])
    assert commit.parent == delivered["patch"]["base"]
    assert opened["head"] == commit.sha
    assert host.titles[1].startswith("Pedido 1: ")
    assert "Mesclar aceita o pedido" in host.bodies[1]
    cause = next(e for e in pipeline.envelopes if e["type"] == REPORT)
    assert cause["actor"] == "system/codehost"
    assert cause["causationid"] == next(
        e["id"] for e in pipeline.envelopes if e["type"].endswith("ticket.delivered.v1")
    )
    # Com o PR aberto, o gerente-script espera o GitHub: ninguém aceita no quadro.
    assert _facts(pipeline, "accepted") == []

    # O CI do topo, uma vez; a mesma volta sem novidade não relata de novo.
    host.set_ci(1, "success")
    assert await _watch(pipeline) == 1
    assert _facts(pipeline, "pr_updated")[-1]["ci"] == "success"
    assert await _watch(pipeline) == 0

    # Quem mescla é o humano: o pedido vai para aceito, assinado pelo gerente.
    host.merge(1)
    assert await _watch(pipeline) == 1
    assert _facts(pipeline, "pr_merged") == [
        {"ticket_id": "pedido-001", "number": 1, "pull_request": 1}
    ]
    accepted = _facts(pipeline, "accepted")
    assert accepted == [{"ticket_id": "pedido-001", "number": 1, "by": "gerente"}]
    assert "pedido-001" not in service.open

    # O pedido 2: o PR fechado sem mesclar devolve o pedido, e o dev o refaz no mesmo ramo, num
    # PR novo. Sem PR aberto, o ramo recomeça da base: o PR novo não arrasta o histórico do fechado
    # (o PR #3 de 21/nov foi por cima de um ramo velho e mostrava o que não era do dev).
    await _until(pipeline, "pr_opened", 2)
    second = _facts(pipeline, "pr_opened")[1]
    assert (second["ticket_id"], second["pull_request"]) == ("pedido-002", 2)
    host.close(2)
    assert await _watch(pipeline) == 1
    returned = _facts(pipeline, "returned")[-1]
    assert returned["comment"] == "O PR #2 foi fechado sem mesclar."
    await _until(pipeline, "pr_opened", 3)
    again = _facts(pipeline, "pr_opened")[2]
    assert (again["ticket_id"], again["pull_request"], again["branch"]) == (
        "pedido-002",
        3,
        "dev/pedido-2",
    )
    (commit,) = host.branches["dev/pedido-2"]
    assert commit.parent == _facts(pipeline, "delivered")[-1]["patch"]["base"]
    assert pipeline.of_type("world.command.rejected.v1") == []

    # O replay do dia: os relatos estão no diário, e o GitHub não é consultado de novo.
    await pipeline.run_until(pipeline.day)  # o dia inteiro: o replay compara o dia todo
    core = pipeline.core
    result = replay_day(
        core.definition,
        core.config,
        pipeline.version,
        pipeline.store,
        pipeline.blobs,
        pipeline.envelopes,
        1,
        pipeline.validator,
    )
    assert result.equal, result.first_difference()
