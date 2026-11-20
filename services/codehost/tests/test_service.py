"""O publicador e o vigia sem o kernel (ADR-0083): o que não sai para o GitHub, e o GitHub fora
do ar. O ciclo inteiro, com o kernel e o dev-script, está em `tests/e2e/test_publicador.py`."""

from collections.abc import Mapping, Sequence
from typing import Any

from campsverso_adapters import (
    FakeWallClock,
    InMemoryBus,
    MemoryBlobStore,
    MemoryCodeHost,
    MemoryTelemetry,
    SequentialUuid7Ids,
)
from campsverso_codehost.service import (
    CREATED,
    DELIVERED,
    PR_OPENED,
    REPORT,
    CodeHostService,
)
from campsverso_contracts import subject
from campsverso_ports import CodeHostError, PullRequest

WORLD = "office-teste"
BASE = "b" * 40


class Offline(MemoryCodeHost):
    """O GitHub fora do ar para o vigia."""

    async def pull_request(self, number: int) -> PullRequest:
        raise CodeHostError("503 Service Unavailable")


async def _files(base: str, patch: str) -> Mapping[str, str | None]:
    return {"docs/oficina/pedido-001.md": f"{base[:4]} {len(patch)}\n"}


def _service(
    host: MemoryCodeHost, review: Sequence[str] = (), forbidden: Sequence[str] = ()
) -> tuple[CodeHostService, InMemoryBus, MemoryTelemetry]:
    bus, telemetry, deliveries = InMemoryBus(), MemoryTelemetry(), MemoryBlobStore()
    deliveries.put(f"{WORLD}/pedido-001/x.patch", b"diff --git a/docs/a.md b/docs/a.md\n")
    service = CodeHostService(
        WORLD,
        bus,
        host,
        deliveries,
        MemoryBlobStore(),
        _files,
        lambda _diff: list(review),
        forbidden,
        FakeWallClock(),
        SequentialUuid7Ids(),
        telemetry,
    )
    return service, bus, telemetry


def _event(kind: str, data: dict[str, Any], seq: int) -> dict[str, Any]:
    return {"id": f"ev-{seq}", "type": kind, "cartridge": "office_campsverso", "data": data}


async def _deliver(bus: InMemoryBus, title: str = "Busca no código") -> None:
    created = {
        "ticket_id": "pedido-001",
        "number": 1,
        "title": title,
        "description": "Uma busca.",
        "acceptance": "Acha o texto.",
    }
    delivered = {
        "ticket_id": "pedido-001",
        "number": 1,
        "by": "camps",
        "patch": {
            "ref": f"{WORLD}/pedido-001/x.patch",
            "base": BASE,
            "files": ["docs/oficina/pedido-001.md"],
            "added": 1,
            "removed": 0,
        },
    }
    await bus.publish(subject(CREATED, WORLD), _event(CREATED, created, 1))
    await bus.publish(subject(DELIVERED, WORLD), _event(DELIVERED, delivered, 2))


def _reports(bus: InMemoryBus) -> list[Mapping[str, Any]]:
    return [e["data"] for _, e in bus.published if e["type"] == REPORT]


async def test_a_entrega_abre_o_pr_e_relata_uma_vez() -> None:
    host = MemoryCodeHost()
    service, bus, _ = _service(host)
    await service.start()
    await _deliver(bus)
    assert host.titles[1] == "Pedido 1: Busca no código"
    assert "**Aceite:** Acha o texto." in host.bodies[1]
    (report,) = _reports(bus)
    assert report["state"] == "opened"
    assert report["branch"] == "dev/pedido-1"
    # O kernel aceitou: o vigia vê o PR aberto, sem novidade, e não relata.
    opened = {
        "ticket_id": "pedido-001",
        "number": 1,
        "pull_request": 1,
        "url": report["url"],
        "branch": "dev/pedido-1",
        "head": report["head"],
    }
    await bus.publish(subject(PR_OPENED, WORLD), _event(PR_OPENED, opened, 3))
    assert await service.watch() == 0
    host.set_ci(1, "failure")
    assert await service.watch() == 1
    assert await service.watch() == 0  # o kernel ainda não publicou: o mesmo relato não repete
    assert _reports(bus)[-1] == {
        "ticket_id": "pedido-001",
        "pull_request": 1,
        "state": "updated",
        "ci": "failure",
    }


async def test_a_entrega_recusada_nao_sai() -> None:
    host = MemoryCodeHost()
    service, bus, telemetry = _service(host, review=["CLAUDE.md: a constituição não muda"])
    await service.start()
    await _deliver(bus)
    assert host.branches == {}
    assert _reports(bus) == []
    assert service.refused == ["pedido-001"]
    assert "codehost.refused" in telemetry.events("warning")


async def test_a_palavra_proibida_no_titulo_nao_vai_ao_pr_publico() -> None:
    host = MemoryCodeHost()
    service, bus, _ = _service(host, forbidden=["segredo"])
    await service.start()
    await _deliver(bus, title="O Segredo da busca")
    assert host.pulls == {}
    assert service.refused == ["pedido-001"]


async def test_o_github_fora_do_ar_nao_derruba_o_vigia() -> None:
    host = Offline()
    service, bus, telemetry = _service(host)
    await service.start()
    await _deliver(bus)
    opened = {
        "ticket_id": "pedido-001",
        "number": 1,
        "pull_request": 1,
        "url": "https://github.com/exemplo/campsverso/pull/1",
        "branch": "dev/pedido-1",
        "head": "c" * 40,
    }
    await bus.publish(subject(PR_OPENED, WORLD), _event(PR_OPENED, opened, 3))
    assert await service.watch() == 0
    assert "codehost.watch_failed" in telemetry.events("warning")
    assert service.failure is None
