"""As ações do gênero office (ADR-0078): o pedido no quadro, do gerente ao dev e de volta.

O gerente (que o humano assume) escreve o pedido e o aceita ou devolve; o dev (sempre um LLM ou um
script) o pega, trabalha na mesa e entrega. Cada papel faz só o que é dele, e o kernel recusa o
resto. A duração vem em segundos, e o kernel converte em ticks.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, ClassVar, cast

from campsverso_cartridge_api import (
    Accepted,
    ActionContext,
    EntityView,
    Interrupt,
    Rejection,
    SpawnDef,
    Validation,
    WorldOps,
    WorldView,
)
from campsverso_office_sim.config import (
    BOARD,
    DESK,
    DEV,
    MANAGER,
    TICKET,
    section,
    tick_seconds,
)

# Os estados do pedido, no atributo `estado`.
TODO, DOING, DELIVERED, ACCEPTED = "a_fazer", "fazendo", "entregue", "aceito"
SIZES = ("P", "M", "G")


def role(view: WorldView, avatar_id: str) -> str | None:
    value = view.entity(avatar_id).attributes.get("papel")
    return None if value is None else str(value)


def adjacent(view: WorldView, avatar_id: str, entity: EntityView) -> bool:
    me = view.entity(avatar_id).position
    return me is not None and entity.position is not None and me.chebyshev(entity.position) <= 1


def the_board(view: WorldView) -> EntityView | Rejection:
    boards = view.entities(BOARD)
    return boards[0] if boards else Rejection("invalid_params", "não há quadro")


def desk_of(view: WorldView, avatar_id: str) -> EntityView | None:
    """A mesa do avatar (o atributo `dono`), ou a primeira, se nenhuma tem dono."""
    desks = view.entities(DESK)
    mine = [d for d in desks if d.attributes.get("dono") == avatar_id]
    return (mine or list(desks) or [None])[0]


def tickets(view: WorldView) -> list[EntityView]:
    """Os pedidos do quadro, na ordem em que foram escritos."""
    return sorted(view.entities(TICKET), key=lambda t: int(cast(int, t.attributes["numero"])))


def ticket(view: WorldView, target: object) -> EntityView | Rejection:
    found = next((t for t in view.entities(TICKET) if t.entity_id == target), None)
    return found or Rejection("invalid_params", f"{target!r} não é um pedido")


def doing(view: WorldView, avatar_id: str) -> EntityView | None:
    """O pedido que o dev está fazendo, se há."""
    return next(
        (
            t
            for t in tickets(view)
            if t.attributes.get("estado") == DOING and t.attributes.get("dono") == avatar_id
        ),
        None,
    )


def total_seconds(view: WorldView, entity: EntityView) -> int:
    """O trabalho simulado do pedido, pelo tamanho (no M23, o dev-script; ADR-0078, decisão 11)."""
    sizes = cast(Mapping[str, Any], section(view, "ticket")["sizes"])
    return int(sizes[str(entity.attributes["tamanho"])]) * 60


def text(params: Mapping[str, Any], key: str, limit: int, *, required: bool) -> str | Rejection:
    raw = params.get(key, "")
    if not isinstance(raw, str):
        return Rejection("invalid_params", f"{key} precisa ser texto")
    value = raw.strip()
    if required and not value:
        return Rejection("invalid_params", f"{key} não pode ficar vazio")
    if len(value) > limit:
        return Rejection("invalid_params", f"{key} passa de {limit} caracteres")
    return value


@dataclass(frozen=True)
class OfficeAction:
    """Uma ação do escritório: um papel, um lugar e uma duração em segundos."""

    name: str = ""
    role: ClassVar[str] = ""  # quem pode
    # O dev e o gerente mexem nos mesmos pedidos: a conferência se repete na conclusão (ADR-0072).
    shared: ClassVar[bool] = True

    def check(self, ctx: ActionContext) -> Rejection | None:
        raise NotImplementedError

    def recheck(self, ctx: ActionContext) -> Rejection | None:
        return self.check(ctx) if self.shared else None

    def apply(self, ctx: ActionContext, ops: WorldOps) -> None:
        raise NotImplementedError

    def seconds(self, ctx: ActionContext) -> float:
        return float(section(ctx.view, "actions", self.name)["seconds"])

    def validate(self, ctx: ActionContext) -> Validation:
        if role(ctx.view, ctx.avatar_id) != self.role:
            return Rejection("not_allowed", f"só o {self.role} faz {self.name}")
        rejection = self.check(ctx)
        if rejection is not None:
            return rejection
        interrupt = cast(Interrupt, section(ctx.view, "actions", self.name)["interrupt"])
        return Accepted(0, interrupt, seconds=self.seconds(ctx))

    def complete(self, ctx: ActionContext, ops: WorldOps) -> None:
        self.apply(ctx, ops)

    def interrupted(self, ctx: ActionContext, ops: WorldOps, elapsed_ticks: int) -> None:
        pass


def _at_board(ctx: ActionContext) -> EntityView | Rejection:
    board = the_board(ctx.view)
    if isinstance(board, Rejection):
        return board
    if not adjacent(ctx.view, ctx.avatar_id, board):
        return Rejection("not_adjacent", "longe do quadro")
    return board


def _at_desk(ctx: ActionContext) -> Rejection | None:
    desk = desk_of(ctx.view, ctx.avatar_id)
    if desk is None:
        return Rejection("invalid_params", "não há mesa")
    return (
        None
        if adjacent(ctx.view, ctx.avatar_id, desk)
        else Rejection("not_adjacent", "longe da mesa")
    )


def _delivered(ctx: ActionContext) -> EntityView | Rejection:
    """O pedido entregue que o gerente vai aceitar ou devolver."""
    found = ticket(ctx.view, ctx.params.get("target"))
    if isinstance(found, Rejection):
        return found
    if found.attributes.get("estado") != DELIVERED:
        return Rejection("wrong_state", f"o pedido {found.attributes['numero']} não foi entregue")
    return found


@dataclass(frozen=True)
class WriteTicket(OfficeAction):
    """O gerente escreve um pedido no quadro: o título, a descrição, o teste de aceite e o
    tamanho."""

    name: str = "write_ticket"
    role: ClassVar[str] = MANAGER

    def _fields(self, ctx: ActionContext) -> dict[str, str] | Rejection:
        limits = section(ctx.view, "ticket")
        found: dict[str, str] = {}
        for key, limit, required in (
            ("title", "title_max", True),
            ("description", "description_max", False),
            ("acceptance", "acceptance_max", False),
        ):
            value = text(ctx.params, key, int(limits[limit]), required=required)
            if isinstance(value, Rejection):
                return value
            found[key] = value
        size = ctx.params.get("size", "P")
        if size not in SIZES:
            return Rejection("invalid_params", f"size é um de {list(SIZES)}")
        found["size"] = str(size)
        return found

    def check(self, ctx: ActionContext) -> Rejection | None:
        board = _at_board(ctx)
        if isinstance(board, Rejection):
            return board
        fields = self._fields(ctx)
        return fields if isinstance(fields, Rejection) else None

    def apply(self, ctx: ActionContext, ops: WorldOps) -> None:
        board, fields = _at_board(ctx), self._fields(ctx)
        assert not isinstance(board, Rejection)
        assert not isinstance(fields, Rejection)
        number = ops.next_seq("pedido")
        ticket_id = f"pedido-{number:03d}"
        ops.spawn(
            SpawnDef(
                ticket_id,
                TICKET,
                container_id=board.entity_id,
                display_name=fields["title"],
                attributes={
                    "numero": number,
                    "titulo": fields["title"],
                    "descricao": fields["description"],
                    "aceite": fields["acceptance"],
                    "tamanho": fields["size"],
                    "estado": TODO,
                    "autor": ctx.avatar_id,
                    "dono": None,
                    "trabalho": 0,
                    "comentario": None,
                },
            )
        )
        ops.emit(
            "campsverso.office.ticket.created.v1",
            {
                "ticket_id": ticket_id,
                "number": number,
                "title": fields["title"],
                "description": fields["description"],
                "acceptance": fields["acceptance"],
                "size": fields["size"],
                "author": ctx.avatar_id,
            },
        )


@dataclass(frozen=True)
class TakeTicket(OfficeAction):
    """O dev pega um pedido do quadro: o escolhido, ou o mais antigo a fazer. Um de cada vez."""

    name: str = "take_ticket"
    role: ClassVar[str] = DEV

    def _ticket(self, ctx: ActionContext) -> EntityView | Rejection:
        target = ctx.params.get("target")
        if target is None:
            todo = [t for t in tickets(ctx.view) if t.attributes.get("estado") == TODO]
            return todo[0] if todo else Rejection("no_ticket", "não há pedido a fazer")
        found = ticket(ctx.view, target)
        if isinstance(found, Rejection):
            return found
        if found.attributes.get("estado") != TODO:
            return Rejection(
                "wrong_state", f"o pedido {found.attributes['numero']} não está a fazer"
            )
        return found

    def check(self, ctx: ActionContext) -> Rejection | None:
        board = _at_board(ctx)
        if isinstance(board, Rejection):
            return board
        if doing(ctx.view, ctx.avatar_id) is not None:
            return Rejection("busy", "já há um pedido em andamento: um de cada vez")
        found = self._ticket(ctx)
        return found if isinstance(found, Rejection) else None

    def apply(self, ctx: ActionContext, ops: WorldOps) -> None:
        found = self._ticket(ctx)
        assert not isinstance(found, Rejection)
        ops.set_attributes(found.entity_id, visible={"estado": DOING, "dono": ctx.avatar_id})
        ops.emit(
            "campsverso.office.ticket.taken.v1",
            {
                "ticket_id": found.entity_id,
                "number": int(cast(int, found.attributes["numero"])),
                "by": ctx.avatar_id,
            },
        )


@dataclass(frozen=True)
class Work(OfficeAction):
    """O dev trabalha no pedido, na mesa. A ação é `partial`: parar no meio (o almoço, o fim do
    expediente, outra ação) guarda o que foi feito (ADR-0052). No M23 o trabalho é simulado.

    `seconds` limita o bloco desta vez: o dev-script trabalha um minuto por vez e, entre um bloco
    e outro, responde a quem falou com ele (interromper na hora em que alguém fala fica para o
    M24)."""

    name: str = "work"
    role: ClassVar[str] = DEV

    def _check(self, ctx: ActionContext) -> Rejection | None:
        rejection = _at_desk(ctx)
        if rejection is not None:
            return rejection
        mine = doing(ctx.view, ctx.avatar_id)
        if mine is None:
            return Rejection("no_ticket", "pegue um pedido no quadro antes")
        if self._left(ctx, mine) <= 0:
            return Rejection("done", "o trabalho deste pedido acabou: entregue")
        return None

    def _left(self, ctx: ActionContext, entity: EntityView) -> int:
        return total_seconds(ctx.view, entity) - int(
            cast(int, entity.attributes.get("trabalho", 0))
        )

    def _chunk(self, ctx: ActionContext, entity: EntityView) -> int:
        """Os segundos desta vez: o que falta, ou menos, se a proposta pediu um bloco."""
        left = self._left(ctx, entity)
        cap = ctx.params.get("seconds")
        whole = isinstance(cap, int) and not isinstance(cap, bool) and cap >= 1
        return min(left, int(cast(int, cap))) if whole else left

    def check(self, ctx: ActionContext) -> Rejection | None:
        cap = ctx.params.get("seconds")
        if cap is not None and (not isinstance(cap, int) or isinstance(cap, bool) or cap < 1):
            return Rejection(
                "invalid_params", "seconds é um número inteiro de segundos, a partir de 1"
            )
        return self._check(ctx)

    def seconds(self, ctx: ActionContext) -> float:
        mine = doing(ctx.view, ctx.avatar_id)
        return 1.0 if mine is None else float(self._chunk(ctx, mine))

    def apply(self, ctx: ActionContext, ops: WorldOps) -> None:
        mine = doing(ctx.view, ctx.avatar_id)
        if mine is not None:
            done = int(cast(int, mine.attributes.get("trabalho", 0))) + self._chunk(ctx, mine)
            ops.set_attributes(mine.entity_id, visible={"trabalho": done})

    def interrupted(self, ctx: ActionContext, ops: WorldOps, elapsed_ticks: int) -> None:
        mine = doing(ctx.view, ctx.avatar_id)
        if mine is None:
            return
        done = int(cast(int, mine.attributes.get("trabalho", 0)))
        worked = min(total_seconds(ctx.view, mine), done + elapsed_ticks * tick_seconds(ctx.view))
        ops.set_attributes(mine.entity_id, visible={"trabalho": worked})


@dataclass(frozen=True)
class Deliver(OfficeAction):
    """O dev entrega o pedido em que acabou de trabalhar: ele vai para "entregue" e espera o
    gerente."""

    name: str = "deliver"
    role: ClassVar[str] = DEV

    def check(self, ctx: ActionContext) -> Rejection | None:
        rejection = _at_desk(ctx)
        if rejection is not None:
            return rejection
        mine = doing(ctx.view, ctx.avatar_id)
        if mine is None:
            return Rejection("no_ticket", "não há pedido em andamento")
        if int(cast(int, mine.attributes.get("trabalho", 0))) < total_seconds(ctx.view, mine):
            return Rejection("not_done", "o trabalho deste pedido ainda não acabou")
        return None

    def apply(self, ctx: ActionContext, ops: WorldOps) -> None:
        mine = doing(ctx.view, ctx.avatar_id)
        assert mine is not None
        ops.set_attributes(mine.entity_id, visible={"estado": DELIVERED})
        ops.emit(
            "campsverso.office.ticket.delivered.v1",
            {
                "ticket_id": mine.entity_id,
                "number": int(cast(int, mine.attributes["numero"])),
                "by": ctx.avatar_id,
                "worked_seconds": int(cast(int, mine.attributes.get("trabalho", 0))),
            },
        )


@dataclass(frozen=True)
class AcceptTicket(OfficeAction):
    """O gerente aceita um pedido entregue: ele está pronto."""

    name: str = "accept_ticket"
    role: ClassVar[str] = MANAGER

    def check(self, ctx: ActionContext) -> Rejection | None:
        board = _at_board(ctx)
        if isinstance(board, Rejection):
            return board
        found = _delivered(ctx)
        return found if isinstance(found, Rejection) else None

    def apply(self, ctx: ActionContext, ops: WorldOps) -> None:
        found = _delivered(ctx)
        assert not isinstance(found, Rejection)
        ops.set_attributes(found.entity_id, visible={"estado": ACCEPTED})
        ops.emit(
            "campsverso.office.ticket.accepted.v1",
            {
                "ticket_id": found.entity_id,
                "number": int(cast(int, found.attributes["numero"])),
                "by": ctx.avatar_id,
            },
        )


@dataclass(frozen=True)
class ReturnTicket(OfficeAction):
    """O gerente devolve um pedido entregue, com o comentário do que falta: ele volta para "a
    fazer", sem dono, e o trabalho recomeça."""

    name: str = "return_ticket"
    role: ClassVar[str] = MANAGER

    def _comment(self, ctx: ActionContext) -> str | Rejection:
        limit = int(section(ctx.view, "ticket")["comment_max"])
        return text(ctx.params, "comment", limit, required=True)

    def check(self, ctx: ActionContext) -> Rejection | None:
        board = _at_board(ctx)
        if isinstance(board, Rejection):
            return board
        found = _delivered(ctx)
        if isinstance(found, Rejection):
            return found
        comment = self._comment(ctx)
        return comment if isinstance(comment, Rejection) else None

    def apply(self, ctx: ActionContext, ops: WorldOps) -> None:
        found, comment = _delivered(ctx), self._comment(ctx)
        assert not isinstance(found, Rejection)
        assert not isinstance(comment, Rejection)
        ops.set_attributes(
            found.entity_id,
            visible={"estado": TODO, "dono": None, "trabalho": 0, "comentario": comment},
        )
        ops.emit(
            "campsverso.office.ticket.returned.v1",
            {
                "ticket_id": found.entity_id,
                "number": int(cast(int, found.attributes["numero"])),
                "by": ctx.avatar_id,
                "comment": comment,
            },
        )


ALL_ACTIONS: tuple[OfficeAction, ...] = (
    WriteTicket(),
    TakeTicket(),
    Work(),
    Deliver(),
    AcceptTicket(),
    ReturnTicket(),
)
