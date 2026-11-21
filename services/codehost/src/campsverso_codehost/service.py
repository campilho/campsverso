"""O publicador e o vigia do GitHub (ADR-0083): a ponte entre o escritório e o repositório de fora.

**O publicador** lê os pedidos do escritório num consumidor durável. A cada entrega com patch, ele
lê o patch no depósito de entregas, confere de novo (a constituição, os testes e a lista de
palavras proibidas, como o `make aplicar`), calcula o texto de cada arquivo mudado sobre a base e
manda tudo num commit ao ramo `dev/pedido-N`. Se o pedido ainda não tem PR aberto, abre um e relata
`opened`; se tem (o gerente devolveu no quadro e o dev refez), o PR acompanha o ramo, e o relato é
`updated` com o topo novo. Uma entrega recusada não sai: fica no registro do serviço, e o gerente
devolve o pedido no quadro.

**O vigia**, a cada volta, pergunta ao repositório de fora o estado de cada PR aberto que o mundo
conhece e relata o que mudou: o topo, o CI, mesclado ou fechado. O mundo conhece os PRs pelos fatos
`office.ticket.pr_*` que o kernel publica, e não pelo que o serviço mandou: um relato recusado não
muda nada, e o mesmo relato não sai duas vezes seguidas.

Quem decide é o kernel: o serviço só propõe (`cmd.office.pull_request.report.v1`), como qualquer
controlador (princípio 2). O modelo nunca vê o GitHub, e o serviço nunca mescla. O estado (os
títulos dos pedidos, os PRs abertos e o último relato de cada um) vai para um arquivo antes de cada
confirmação; depois de uma queda, o serviço retoma dele, e o PR aberto de novo é o mesmo.

**O revisor de outra família** (parte 3 do M25): cada entrega publicada, aberta ou atualizada, entra
numa fila (no mesmo arquivo), e o laço do serviço a esvazia fora do consumidor, porque uma revisão
leva minutos e o lote do barramento não pode esperar tanto. A revisão vira um comentário no PR; o
comentário passa pela lista de palavras proibidas antes de sair, e não chega ao mundo.
"""

import json
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import asdict, dataclass
from typing import Any, cast

from campsverso_codehost.reviewer import Review, ReviewInput, comment_body
from campsverso_contracts import CONTRACT_TYPES, subject
from campsverso_ports import (
    BlobStore,
    CodeHostError,
    CodeHostPort,
    Consumer,
    Envelope,
    EventBus,
    IdGenerator,
    PullRequest,
    Telemetry,
    WallClock,
)

CREATED = "campsverso.office.ticket.created.v1"
DELIVERED = "campsverso.office.ticket.delivered.v1"
PR_OPENED = "campsverso.office.ticket.pr_opened.v1"
PR_UPDATED = "campsverso.office.ticket.pr_updated.v1"
PR_MERGED = "campsverso.office.ticket.pr_merged.v1"
PR_CLOSED = "campsverso.office.ticket.pr_closed.v1"
REPORT = "campsverso.cmd.office.pull_request.report.v1"
ACTOR = "system/codehost"

# O texto de cada arquivo mudado sobre a base, a partir do patch: o git, na raiz de composição.
type PatchFiles = Callable[[str, str], Awaitable[Mapping[str, str | None]]]
# A revisão do patch (a da oficina): os motivos para recusar, vazio quando pode sair.
type PatchReview = Callable[[str], Sequence[str]]
# O revisor de outra família: a revisão de uma entrega, ou None quando todos os modelos falham.
type ReviewFn = Callable[[ReviewInput], Awaitable[Review | None]]


@dataclass
class OpenPullRequest:
    """Um PR aberto, como o mundo o conhece."""

    pull_request: int
    number: int  # o número do pedido
    branch: str
    head: str
    ci: str | None = "pending"


@dataclass(frozen=True)
class Ticket:
    number: int
    title: str
    description: str
    acceptance: str


def branch_of(number: int, prefix: str = "dev/") -> str:
    return f"{prefix}pedido-{number}"


class CodeHostService:
    def __init__(
        self,
        worldid: str,
        bus: EventBus,
        host: CodeHostPort,
        deliveries: BlobStore,
        state: BlobStore,
        files: PatchFiles,
        review: PatchReview,
        forbidden: Sequence[str],
        clock: WallClock,
        ids: IdGenerator,
        telemetry: Telemetry,
        *,
        reviewer: ReviewFn | None = None,
        branch_prefix: str = "dev/",
    ) -> None:
        self._worldid = worldid
        self._bus = bus
        self._host = host
        self._deliveries = deliveries
        self._state = state
        self._files = files
        self._review = review
        self._forbidden = [w.strip().lower() for w in forbidden if w.strip()]
        self._clock = clock
        self._ids = ids
        self._telemetry = telemetry
        self._reviewer = reviewer
        self._branch_prefix = branch_prefix
        self._key = f"{worldid}/codehost.json"
        self.tickets: dict[str, Ticket] = {}
        self.open: dict[str, OpenPullRequest] = {}
        self.sent: dict[str, list[Any]] = {}
        self.refused: list[str] = []
        self.reviews: list[dict[str, Any]] = []  # a fila do revisor: o PR, o topo e a entrega
        # A última entrega publicada de cada pedido, para revisar de novo à mão (make revisar).
        self.published: dict[str, dict[str, Any]] = {}
        self._cartridge = ""
        self._load()
        self._consumer: Consumer | None = None
        self._seq = 0
        self.failure: BaseException | None = None

    # ------------------------------------------------------------------ o estado em arquivo

    def _load(self) -> None:
        try:
            saved = json.loads(self._state.get(self._key))
        except FileNotFoundError, KeyError:
            return
        self.tickets = {k: Ticket(**v) for k, v in saved["tickets"].items()}
        self.open = {k: OpenPullRequest(**v) for k, v in saved["open"].items()}
        self.sent = saved["sent"]
        self.reviews = list(saved.get("reviews") or [])
        self.published = dict(saved.get("published") or {})
        self._cartridge = saved["cartridge"]

    def _save(self) -> None:
        saved = {
            "tickets": {k: asdict(v) for k, v in self.tickets.items()},
            "open": {k: asdict(v) for k, v in self.open.items()},
            "sent": self.sent,
            "reviews": self.reviews,
            "published": self.published,
            "cartridge": self._cartridge,
        }
        self._state.put(self._key, json.dumps(saved, ensure_ascii=False).encode())

    # ------------------------------------------------------------------ o publicador

    async def start(self) -> None:
        w = self._worldid
        self._consumer = await self._bus.consume(
            f"campsverso.{w}.world.office.ticket.>", f"codehost-{w}-tickets", self._on_tickets
        )

    async def stop(self) -> None:
        if self._consumer is not None:
            await self._consumer.unsubscribe()

    async def _on_tickets(self, batch: Sequence[tuple[str, Envelope]]) -> None:
        try:
            for _, envelope in batch:
                await self._on_ticket(envelope)
            self._save()
        except Exception as error:
            self.failure = error
            raise

    async def _on_ticket(self, envelope: Envelope) -> None:
        kind, data = str(envelope["type"]), cast(Mapping[str, Any], envelope["data"])
        self._cartridge = str(envelope["cartridge"])
        ticket_id = str(data.get("ticket_id"))
        if kind == CREATED:
            self.tickets[ticket_id] = Ticket(
                int(data["number"]),
                str(data["title"]),
                str(data.get("description") or ""),
                str(data.get("acceptance") or ""),
            )
        elif kind == PR_OPENED:
            self.open[ticket_id] = OpenPullRequest(
                int(data["pull_request"]),
                int(data["number"]),
                str(data["branch"]),
                str(data["head"]),
            )
        elif kind == PR_UPDATED and ticket_id in self.open:
            known = self.open[ticket_id]
            known.head = str(data.get("head") or known.head)
            known.ci = str(data.get("ci") or known.ci)
        elif kind in (PR_MERGED, PR_CLOSED):
            self.open.pop(ticket_id, None)
        elif kind == DELIVERED and data.get("patch"):
            await self._publish(envelope, ticket_id, data)

    async def _publish(self, cause: Envelope, ticket_id: str, data: Mapping[str, Any]) -> None:
        number = int(data["number"])
        patch = cast(Mapping[str, Any], data["patch"])
        ticket = self.tickets.get(ticket_id, Ticket(number, f"pedido {number}", "", ""))
        text = self._deliveries.get(str(patch["ref"])).decode("utf-8")
        title = f"Pedido {number}: {ticket.title}"
        body = _body(ticket, str(data.get("by") or "dev"), patch)
        reasons = [*self._review(text)]
        if self._has_forbidden(f"{title}\n{body}"):
            reasons.append("o título ou a descrição tem uma palavra da lista proibida")
        if reasons:
            self.refused.append(ticket_id)
            self._telemetry.warning(
                "codehost.refused", ticket_id=ticket_id, number=number, reasons=reasons
            )
            return
        branch = branch_of(number, self._branch_prefix)
        try:
            files = await self._files(str(patch["base"]), text)
            head = await self._host.publish_branch(
                branch, str(patch["base"]), files, _message(number, ticket.title)
            )
            known = self.open.get(ticket_id)
            if known is not None:  # o pedido devolvido e refeito: o PR acompanha o ramo
                known.head = head
                await self._report(ticket_id, known.pull_request, "updated", {"head": head}, cause)
                self._queue_review(ticket_id, known.pull_request, head, str(patch["ref"]))
                return
            pull = await self._host.open_pull_request(branch, title, body)
        except CodeHostError as error:
            self.refused.append(ticket_id)
            self._telemetry.error(
                "codehost.publish_failed", ticket_id=ticket_id, number=number, error=str(error)
            )
            return
        self._telemetry.info(
            "codehost.opened", ticket_id=ticket_id, number=number, pull_request=pull.number
        )
        opened = {"url": pull.url, "branch": pull.branch, "head": pull.head}
        await self._report(ticket_id, pull.number, "opened", opened, cause)
        self._queue_review(ticket_id, pull.number, pull.head, str(patch["ref"]))

    def _has_forbidden(self, text: str) -> bool:
        lowered = text.lower()
        return any(word in lowered for word in self._forbidden)

    # ------------------------------------------------------------------ o revisor

    def _queue_review(self, ticket_id: str, pull_request: int, head: str, ref: str) -> None:
        """Põe a entrega na fila do revisor; um topo novo do mesmo PR toma o lugar do antigo."""
        self.published[ticket_id] = {"pull_request": pull_request, "head": head, "ref": ref}
        if self._reviewer is None:
            return
        self.reviews = [r for r in self.reviews if r["pull_request"] != pull_request]
        self.reviews.append(
            {"ticket_id": ticket_id, "pull_request": pull_request, "head": head, "ref": ref}
        )

    async def review_pending(self) -> int:
        """Revisa a fila, um PR por vez, e comenta cada revisão. Devolve quantas saíram da fila.

        Uma revisão que falha em todos os modelos sai da fila com um aviso: `make revisar PR=N` a
        roda de novo à mão. Uma que cai no meio volta da fila na próxima subida, e a fita do
        revisor responde de graça o pedido que já foi pago."""
        if self._reviewer is None:
            return 0
        done = 0
        for item in list(self.reviews):
            pull_request = int(item["pull_request"])
            ticket = self._ticket(str(item["ticket_id"]))
            try:
                diff = self._deliveries.get(str(item["ref"])).decode("utf-8")
            except FileNotFoundError, KeyError:
                diff = None
            result = None
            if diff is not None:
                given = ReviewInput(
                    ticket.number,
                    ticket.title,
                    ticket.description,
                    ticket.acceptance,
                    diff,
                    str(item["head"]),
                )
                result = await self._reviewer(given)
                if result is not None:
                    await self._comment(pull_request, result, comment_body(result, given))
            if result is None:
                self._telemetry.warning(
                    "codehost.review_failed",
                    pull_request=pull_request,
                    reason="sem a entrega" if diff is None else "nenhum modelo respondeu",
                )
            if item in self.reviews:  # um topo novo pode ter tomado o lugar durante a revisão
                self.reviews.remove(item)
            self._save()
            done += 1
        return done

    def _ticket(self, ticket_id: str) -> Ticket:
        known = self.tickets.get(ticket_id)
        if known is not None:
            return known
        return Ticket(0, ticket_id, "", "")

    async def _comment(self, pull_request: int, review: Review, body: str) -> None:
        facts = {
            "pull_request": pull_request,
            "model": review.model,
            "verdict": review.verdict,
            "findings": review.findings,
            "cost_usd": review.cost_usd,
            "replayed": review.replayed,
            "failed": [list(f) for f in review.failed],
        }
        if self._has_forbidden(body):
            self._telemetry.warning("codehost.review_withheld", **facts)
            return
        try:
            await self._host.comment(pull_request, body)
        except CodeHostError as error:
            self._telemetry.error("codehost.comment_failed", error=str(error), **facts)
            return
        self._telemetry.info("codehost.reviewed", **facts)

    # ------------------------------------------------------------------ o vigia

    async def watch(self) -> int:
        """Uma volta do vigia: relata o que mudou em cada PR aberto. Devolve quantos relatos."""
        reports = 0
        for ticket_id, known in sorted(self.open.items()):
            try:
                now = await self._host.pull_request(known.pull_request)
            except CodeHostError as error:  # o GitHub fora do ar: a próxima volta tenta de novo
                self._telemetry.warning(
                    "codehost.watch_failed", pull_request=known.pull_request, error=str(error)
                )
                continue
            reports += await self._compare(ticket_id, known, now)
        if reports:
            self._save()
        return reports

    async def _compare(self, ticket_id: str, known: OpenPullRequest, now: PullRequest) -> int:
        if now.state == "merged":
            return await self._report(ticket_id, known.pull_request, "merged")
        if now.state == "closed":
            return await self._report(ticket_id, known.pull_request, "closed")
        changed: dict[str, str] = {}
        if now.head != known.head:
            changed["head"] = now.head
        if now.ci is not None and now.ci != known.ci:
            changed["ci"] = now.ci
        if not changed:
            return 0
        return await self._report(ticket_id, known.pull_request, "updated", changed)

    async def _report(
        self,
        ticket_id: str,
        pull_request: int,
        state: str,
        extra: Mapping[str, str] | None = None,
        cause: Envelope | None = None,
    ) -> int:
        extra = extra or {}
        data: dict[str, Any] = {
            "ticket_id": ticket_id,
            "pull_request": pull_request,
            "state": state,
            **extra,
        }
        mark = [pull_request, state, extra.get("head"), extra.get("ci")]
        if self.sent.get(ticket_id) == mark:
            return 0  # o mesmo relato, de novo: o kernel já o tem, ou já o recusou
        self.sent[ticket_id] = mark
        info = CONTRACT_TYPES[REPORT]
        envelope: dict[str, Any] = {
            "specversion": "1.0",
            "id": self._ids.new_id(),
            "source": f"/codehost/{self._worldid}",
            "type": REPORT,
            "time": self._clock.now().isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            "datacontenttype": "application/json",
            "dataschema": info.dataschema,
            "worldid": self._worldid,
            "cartridge": self._cartridge,
            "seq": self._seq,
            "actor": ACTOR,
            "provenance": "simulated",
            "visibility": info.visibility,
            "data": data,
        }
        if cause is not None:
            envelope["causationid"] = cause["id"]
        self._seq += 1
        await self._bus.publish(subject(REPORT, self._worldid), envelope)
        self._telemetry.info("codehost.report", **{k: v for k, v in data.items() if k != "url"})
        return 1


def _message(number: int, title: str) -> str:
    return (
        f"feat: o pedido {number} do escritório\n\n{title}\n\n"
        "Entregue pelo dev do escritório na oficina e publicado pelo publicador (ADR-0083)."
    )


def _body(ticket: Ticket, by: str, patch: Mapping[str, Any]) -> str:
    files = [str(f) for f in cast(list[Any], patch.get("files") or [])]
    lines = [f"**Pedido {ticket.number}: {ticket.title}**", ""]
    if ticket.description:
        lines += [ticket.description, ""]
    if ticket.acceptance:
        lines += [f"**Aceite:** {ticket.acceptance}", ""]
    lines += [
        "---",
        "",
        f"Entregue pelo dev do escritório (`{by}`) na oficina, sobre `{str(patch['base'])[:8]}`: "
        f"{len(files)} arquivo(s), +{patch['added']} -{patch['removed']}.",
        "",
        *[f"- `{name}`" for name in files[:50]],
        *([f"- e mais {len(files) - 50}"] if len(files) > 50 else []),
        "",
        "Aberto pelo publicador do escritório (ADR-0083). Mesclar aceita o pedido no quadro; "
        "fechar sem mesclar o devolve ao dev.",
    ]
    return "\n".join(lines)
