"""O que vem de fora do escritório (ADR-0083, ADR-0084): o vigia do GitHub relata cada mudança num
PR do dev, e o cartucho confere e muda o pedido.

O PR fica nos atributos do pedido, para o quadro e para o dev: o número (`pr`), o endereço, o ramo,
o topo, o CI e o estado (`pr_estado`: aberto, mesclado ou fechado).

- **Aberto:** a entrega virou um PR. Só um pedido entregue, sem outro PR aberto.
- **Mudou:** um commit novo no ramo (o dev refez o pedido devolvido) ou o resultado do CI.
- **Mesclado:** o aceite. O pedido vai para "aceito", e sai também o `ticket.accepted`, como se o
  gerente aceitasse no quadro: quem mescla é o humano, que é o gerente lá dentro.
- **Fechado sem mesclar:** o pedido volta a "a fazer", e sai também o `ticket.returned`.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, cast

from campsverso_cartridge_api import (
    CommandContext,
    EntityView,
    Rejection,
    WorldOps,
    WorldView,
)
from campsverso_office_sim.actions import ACCEPTED, TODO, role, ticket
from campsverso_office_sim.config import MANAGER

REPORT = "campsverso.cmd.office.pull_request.report.v1"
OPEN, MERGED, CLOSED = "aberto", "mesclado", "fechado"
PR = "campsverso.office.ticket.pr_"


def _manager(view: WorldView) -> str:
    """Quem assina o aceite e a devolução que vêm do GitHub: o gerente do elenco."""
    managers = sorted(
        e.entity_id for e in view.entities("avatar") if role(view, e.entity_id) == MANAGER
    )
    return managers[0] if managers else MANAGER


def _number(found: EntityView) -> int:
    return int(cast(int, found.attributes["numero"]))


@dataclass(frozen=True)
class PullRequestReport:
    """`cmd.office.pull_request.report.v1`: uma mudança num PR do dev."""

    type: str = REPORT

    def apply(self, ctx: CommandContext, ops: WorldOps) -> Rejection | None:
        data = ctx.data
        found = ticket(ctx.view, data.get("ticket_id"))
        if isinstance(found, Rejection):
            return found
        pr = int(data["pull_request"])
        state = str(data["state"])
        current = found.attributes.get("pr")
        if state == "opened":
            return self._opened(found, pr, data, ops)
        if current != pr:
            return Rejection("other_pr", f"o pedido {_number(found)} não está no PR #{pr}")
        if found.attributes.get("pr_estado") != OPEN:
            return Rejection("pr_not_open", f"o PR #{pr} já foi {found.attributes['pr_estado']}")
        if state == "updated":
            return self._updated(found, pr, data, ops)
        if state == "merged":
            return self._merged(ctx.view, found, pr, ops)
        return self._closed(ctx.view, found, pr, ops)

    def _opened(
        self, found: EntityView, pr: int, data: Mapping[str, Any], ops: WorldOps
    ) -> Rejection | None:
        number = _number(found)
        if found.attributes.get("estado") != "entregue":
            return Rejection("wrong_state", f"o pedido {number} não está entregue")
        if found.attributes.get("pr_estado") == OPEN:
            open_pr = found.attributes["pr"]
            return Rejection("pr_exists", f"o pedido {number} já está no PR #{open_pr}")
        missing = [key for key in ("url", "branch", "head") if not data.get(key)]
        if missing:
            return Rejection("missing_field", f"o PR aberto precisa de {', '.join(missing)}")
        url, branch, head = str(data["url"]), str(data["branch"]), str(data["head"])
        ops.set_attributes(
            found.entity_id,
            visible={
                "pr": pr,
                "pr_url": url,
                "pr_ramo": branch,
                "pr_topo": head,
                "pr_ci": "pending",
                "pr_estado": OPEN,
            },
        )
        ops.emit(
            f"{PR}opened.v1",
            {
                "ticket_id": found.entity_id,
                "number": number,
                "pull_request": pr,
                "url": url,
                "branch": branch,
                "head": head,
            },
        )
        return None

    def _updated(
        self, found: EntityView, pr: int, data: Mapping[str, Any], ops: WorldOps
    ) -> Rejection | None:
        changes: dict[str, Any] = {}
        event: dict[str, Any] = {
            "ticket_id": found.entity_id,
            "number": _number(found),
            "pull_request": pr,
        }
        if data.get("head"):
            changes["pr_topo"] = event["head"] = str(data["head"])
        if data.get("ci"):
            changes["pr_ci"] = event["ci"] = str(data["ci"])
        if not changes:
            return Rejection("nothing_changed", f"o relato do PR #{pr} não traz o topo nem o CI")
        ops.set_attributes(found.entity_id, visible=changes)
        ops.emit(f"{PR}updated.v1", event)
        return None

    def _merged(self, view: WorldView, found: EntityView, pr: int, ops: WorldOps) -> None:
        number = _number(found)
        ops.set_attributes(found.entity_id, visible={"estado": ACCEPTED, "pr_estado": MERGED})
        event = {"ticket_id": found.entity_id, "number": number, "pull_request": pr}
        ops.emit(f"{PR}merged.v1", event)
        ops.emit(
            "campsverso.office.ticket.accepted.v1",
            {"ticket_id": found.entity_id, "number": number, "by": _manager(view)},
        )

    def _closed(self, view: WorldView, found: EntityView, pr: int, ops: WorldOps) -> None:
        number = _number(found)
        comment = f"O PR #{pr} foi fechado sem mesclar."
        ops.set_attributes(
            found.entity_id,
            visible={
                "estado": TODO,
                "dono": None,
                "trabalho": 0,
                "comentario": comment,
                "pr_estado": CLOSED,
            },
        )
        event = {"ticket_id": found.entity_id, "number": number, "pull_request": pr}
        ops.emit(f"{PR}closed.v1", event)
        ops.emit(
            "campsverso.office.ticket.returned.v2",
            {
                "ticket_id": found.entity_id,
                "number": number,
                "by": _manager(view),
                "comment": comment,
            },
        )


COMMANDS = (PullRequestReport(),)
