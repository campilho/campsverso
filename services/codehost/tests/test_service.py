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
from campsverso_codehost.reviewer import Review, ReviewInput
from campsverso_codehost.service import (
    CREATED,
    DELIVERED,
    PR_OPENED,
    REPORT,
    RETRY_LIMIT,
    CodeHostService,
    ReviewFn,
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
    host: MemoryCodeHost,
    review: Sequence[str] = (),
    forbidden: Sequence[str] = (),
    reviewer: ReviewFn | None = None,
    state: MemoryBlobStore | None = None,
) -> tuple[CodeHostService, InMemoryBus, MemoryTelemetry]:
    bus, telemetry, deliveries = InMemoryBus(), MemoryTelemetry(), MemoryBlobStore()
    deliveries.put(f"{WORLD}/pedido-001/x.patch", b"diff --git a/docs/a.md b/docs/a.md\n")
    service = CodeHostService(
        WORLD,
        bus,
        host,
        deliveries,
        state or MemoryBlobStore(),
        _files,
        lambda _diff: list(review),
        forbidden,
        FakeWallClock(),
        SequentialUuid7Ids(),
        telemetry,
        reviewer=reviewer,
    )
    return service, bus, telemetry


class Reviews:
    """O revisor falso: guarda o que leu e responde o texto dado (ou None, a falha)."""

    def __init__(self, text: str | None = "Tudo certo.") -> None:
        self.text = text
        self.read: list[ReviewInput] = []

    async def __call__(self, item: ReviewInput) -> Review | None:
        self.read.append(item)
        if self.text is None:
            return None
        return Review("google/gemini-4-neon", "mesclar", self.text, 0, 0.031, False, None, "h")


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


class FlakyHost(MemoryCodeHost):
    """O GitHub fora do alcance, enquanto `down` (a queda de rede de 21/nov)."""

    down: bool = True

    async def publish_branch(
        self,
        branch: str,
        base: str,
        files: Mapping[str, str | None],
        message: str,
        *,
        fresh: bool = False,
    ) -> str:
        if self.down:
            raise CodeHostError("a rede caiu")
        return await super().publish_branch(branch, base, files, message, fresh=fresh)


async def test_a_entrega_que_a_rede_derrubou_sai_numa_volta_seguinte() -> None:
    host = FlakyHost()
    service, bus, telemetry = _service(host)
    await service.start()
    await _deliver(bus)
    assert _reports(bus) == []
    assert service.refused == []  # não é uma recusa: espera a rede
    assert service.pending["pedido-001"]["attempts"] == 1
    assert await service.retry_pending() == 0  # ainda fora
    assert service.pending["pedido-001"]["attempts"] == 2
    assert telemetry.events().count("codehost.publish_failed") == 2
    host.down = False
    assert await service.retry_pending() == 1
    (report,) = _reports(bus)
    assert report["state"] == "opened"
    assert service.pending == {}


async def test_a_entrega_que_nunca_sai_desiste_no_limite() -> None:
    host = FlakyHost()
    service, bus, telemetry = _service(host)
    await service.start()
    await _deliver(bus)
    service.pending["pedido-001"]["attempts"] = RETRY_LIMIT - 1
    assert await service.retry_pending() == 1  # saiu da espera, mas como recusa
    assert service.pending == {}
    assert service.refused == ["pedido-001"]
    assert "codehost.publish_gave_up" in telemetry.events("error")


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


async def test_a_entrega_publicada_entra_na_fila_e_a_revisao_vira_comentario() -> None:
    host, reviews = MemoryCodeHost(), Reviews()
    state = MemoryBlobStore()
    service, bus, telemetry = _service(host, reviewer=reviews, state=state)
    await service.start()
    await _deliver(bus)
    assert [r["pull_request"] for r in service.reviews] == [1]
    assert '"reviews"' in state.get(f"{WORLD}/codehost.json").decode()  # a fila sobrevive
    assert host.comments == {}  # a revisão é fora do consumidor
    assert await service.review_pending() == 1
    (read,) = reviews.read
    assert (read.number, read.title, read.acceptance) == (1, "Busca no código", "Acha o texto.")
    assert read.diff.startswith("diff --git")
    (comment,) = host.comments[1]
    assert comment.startswith("### Revisão do pedido 1: pode mesclar")
    assert "`google/gemini-4-neon`" in comment
    assert "US$ 0,031" in comment
    assert service.reviews == []
    assert "codehost.reviewed" in telemetry.events("info")
    assert service.published["pedido-001"]["pull_request"] == 1


async def test_a_revisao_com_palavra_proibida_nao_sai() -> None:
    host = MemoryCodeHost()
    service, bus, telemetry = _service(
        host, forbidden=["segredo"], reviewer=Reviews("Achei o Segredo no diff.")
    )
    await service.start()
    await _deliver(bus)
    assert await service.review_pending() == 1
    assert host.comments == {}
    assert "codehost.review_withheld" in telemetry.events("warning")


async def test_a_revisao_que_falha_sai_da_fila_com_um_aviso() -> None:
    host = MemoryCodeHost()
    service, bus, telemetry = _service(host, reviewer=Reviews(None))
    await service.start()
    await _deliver(bus)
    assert await service.review_pending() == 1
    assert host.comments == {}
    assert service.reviews == []
    assert "codehost.review_failed" in telemetry.events("warning")


async def test_a_fila_volta_depois_de_uma_queda_e_sem_revisor_nada_entra() -> None:
    host, state = MemoryCodeHost(), MemoryBlobStore()
    service, bus, _ = _service(host, reviewer=Reviews(), state=state)
    await service.start()
    await _deliver(bus)
    again, _, _ = _service(host, reviewer=Reviews(), state=state)
    assert [r["head"] for r in again.reviews] == [r["head"] for r in service.reviews]
    assert await again.review_pending() == 1
    assert len(host.comments[1]) == 1
    plain, bus2, _ = _service(MemoryCodeHost())
    await plain.start()
    await _deliver(bus2)
    assert plain.reviews == []
    assert await plain.review_pending() == 0


async def test_o_prefixo_dos_ramos_vale_para_o_pr() -> None:
    host = MemoryCodeHost()
    bus, deliveries = InMemoryBus(), MemoryBlobStore()
    deliveries.put(f"{WORLD}/pedido-001/x.patch", b"diff --git a/docs/a.md b/docs/a.md\n")
    service = CodeHostService(
        WORLD,
        bus,
        host,
        deliveries,
        MemoryBlobStore(),
        _files,
        lambda _diff: [],
        [],
        FakeWallClock(),
        SequentialUuid7Ids(),
        MemoryTelemetry(),
        branch_prefix="dev/sandbox-20261121-103000/",
    )
    await service.start()
    await _deliver(bus)
    assert list(host.branches) == ["dev/sandbox-20261121-103000/pedido-1"]
    assert _reports(bus)[-1]["branch"] == "dev/sandbox-20261121-103000/pedido-1"


async def test_com_varios_devs_o_ramo_leva_o_dev_que_entregou() -> None:
    """ADR-0093: no mundo 03, o ramo de cada dev fica sob o nome dele, e o prefixo do mundo não
    deixa colidir com os ramos do mundo 02."""
    host = MemoryCodeHost()
    bus, deliveries = InMemoryBus(), MemoryBlobStore()
    deliveries.put(f"{WORLD}/pedido-001/x.patch", b"diff --git a/docs/a.md b/docs/a.md\n")
    service = CodeHostService(
        WORLD,
        bus,
        host,
        deliveries,
        MemoryBlobStore(),
        _files,
        lambda _diff: [],
        [],
        FakeWallClock(),
        SequentialUuid7Ids(),
        MemoryTelemetry(),
        branch_prefix="dev/m03/",
        branch_by_dev=True,
    )
    await service.start()
    await _deliver(bus)
    assert list(host.branches) == ["dev/m03/camps/pedido-1"]
    assert _reports(bus)[-1]["branch"] == "dev/m03/camps/pedido-1"


async def test_o_pedido_sem_pr_aberto_comeca_da_base_mesmo_com_um_ramo_velho() -> None:
    """O PR #3 (21/nov): o ramo do primeiro PR de todos, fechado, tinha o mesmo nome."""
    host = MemoryCodeHost()
    await host.publish_branch("dev/pedido-1", "o" * 40, {"a.md": "velho\n"}, "o de ontem")
    service, bus, _ = _service(host)
    await service.start()
    await _deliver(bus)
    (commit,) = host.branches["dev/pedido-1"]
    assert commit.parent == BASE
