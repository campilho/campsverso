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
    COFFEE_MACHINE,
    COPA_TABLE,
    DESK,
    DEV,
    FRIDGE,
    LIGHT_SWITCH,
    MANAGER,
    MICROWAVE,
    RESTROOM_DOOR,
    SOFA,
    TICKET,
    TRASH,
    WATER_COOLER,
    at_lunch,
    in_window,
    lunch_end,
    lunch_tail,
    office_hours,
    on_call,
    section,
    tick_ms,
)
from campsverso_office_sim.systems import (
    LIGHT_SWITCHED,
    SUMMON_REASON,
    end_summon,
    start_summon,
    summon_of,
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


def devs(view: WorldView) -> list[str]:
    """Os devs do elenco, pelo id."""
    return sorted(e.entity_id for e in view.entities("avatar") if e.attributes.get("papel") == DEV)


def open_to(entity: EntityView, avatar_id: str) -> bool:
    """O pedido que o dev pode pegar (ADR-0093, decisão 8): o dele, ou o de ninguém."""
    return entity.attributes.get("para") in (None, avatar_id)


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
        if self.role and role(ctx.view, ctx.avatar_id) != self.role:
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
    state = found.attributes.get("estado")
    if state != DELIVERED:
        number = found.attributes["numero"]
        # Dois cliques em aceitar saíam juntos da fila; o segundo dizia "não foi entregue" (18/nov).
        why = "já foi aceito" if state == ACCEPTED else "ainda não foi entregue"
        return Rejection("wrong_state", f"o pedido {number} {why}")
    return found


def choice(params: Mapping[str, Any], key: str, allowed: object) -> str | Rejection | None:
    """Uma escolha da prancheta, entre as que o cartucho oferece; vazia, o padrão do mundo."""
    raw = params.get(key)
    if raw is None or raw == "":
        return None
    options = [str(o) for o in cast(list[Any], allowed or [])]
    if raw not in options:
        return Rejection("invalid_params", f"{key} é um de {options}")
    return str(raw)


def system(
    params: Mapping[str, Any], systems: Mapping[str, Any]
) -> tuple[str | None, str | None] | Rejection:
    """O sistema do pedido (ADR-0093, decisão 18): o harness e o modelo, conferidos como par. Sem
    harness, nenhum dos dois (o padrão do dev); o harness sem o modelo leva o primeiro da lista
    dele; o modelo sozinho, não."""
    harness = choice(params, "harness", list(systems))
    if isinstance(harness, Rejection):
        return harness
    if harness is None:
        if params.get("model") not in (None, ""):
            return Rejection("invalid_params", "o modelo vem com quem programa (harness)")
        return None, None
    models = [str(m) for m in cast(list[Any], systems[harness] or [])]
    model = choice(params, "model", models)
    if isinstance(model, Rejection):
        return Rejection("invalid_params", f"o {harness} programa com um de {models}")
    return harness, model if model is not None else models[0]


@dataclass(frozen=True)
class WriteTicket(OfficeAction):
    """O gerente escreve um pedido no quadro: o título, a descrição, o teste de aceite e o
    tamanho; e, se quiser, quem programa e o modelo (ADR-0089)."""

    name: str = "write_ticket"
    role: ClassVar[str] = MANAGER

    def _fields(self, ctx: ActionContext) -> dict[str, str | None] | Rejection:
        limits = section(ctx.view, "ticket")
        found: dict[str, str | None] = {}
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
        picked = system(ctx.params, cast(Mapping[str, Any], limits.get("systems") or {}))
        if isinstance(picked, Rejection):
            return picked
        found["harness"], found["model"] = picked
        # Para quem e para todos (ADR-0093, decisão 8): um dev do elenco, ou uma ficha para cada.
        cast_devs = devs(ctx.view)
        assignee = ctx.params.get("assignee")
        everyone = ctx.params.get("everyone")
        if everyone not in (None, False, True):
            return Rejection("invalid_params", "everyone é sim ou não")
        if assignee in (None, ""):
            found["assignee"] = None
        elif everyone:
            return Rejection("invalid_params", "o pedido é para todos ou para um dev, não os dois")
        elif assignee not in cast_devs:
            return Rejection("invalid_params", f"assignee é um dev do elenco: {cast_devs}")
        else:
            found["assignee"] = str(assignee)
        found["everyone"] = "sim" if everyone else None
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
        if fields["everyone"] is None:
            self._spawn(ctx, ops, board, fields, fields["assignee"], None)
            return
        # Para todos: uma ficha por dev, com o mesmo texto, ligadas pelo grupo do primeiro número.
        group: str | None = None
        for dev in devs(ctx.view):
            number = self._spawn(ctx, ops, board, fields, dev, group)
            group = group or f"grupo-{number:03d}"

    def _spawn(
        self,
        ctx: ActionContext,
        ops: WorldOps,
        board: EntityView,
        fields: Mapping[str, str | None],
        assignee: str | None,
        group: str | None,
    ) -> int:
        """Uma ficha no quadro e o fato dela; devolve o número."""
        number = ops.next_seq("pedido")
        ticket_id = f"pedido-{number:03d}"
        group = group or (f"grupo-{number:03d}" if fields["everyone"] else None)
        attributes: dict[str, Any] = {
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
            "patch": None,  # a referência da entrega da oficina (ADR-0080)
        }
        # Quem programa e o modelo (ADR-0089), para quem e o grupo (ADR-0093), só quando o gerente
        # escolheu: sem eles, o padrão, e o pedido fica igual ao de antes.
        chosen = {
            "maos": fields["harness"],
            "modelo": fields["model"],
            "para": assignee,
            "grupo": group,
        }
        attributes.update({k: v for k, v in chosen.items() if v is not None})
        ops.spawn(
            SpawnDef(
                ticket_id,
                TICKET,
                container_id=board.entity_id,
                display_name=_name(str(fields["title"])),
                attributes=attributes,
            )
        )
        created: dict[str, Any] = {
            "ticket_id": ticket_id,
            "number": number,
            "title": fields["title"],
            "description": fields["description"],
            "acceptance": fields["acceptance"],
            "size": fields["size"],
            "author": ctx.avatar_id,
        }
        optional = {
            "harness": fields["harness"],
            "model": fields["model"],
            "assignee": assignee,
            "group": group,
        }
        created.update({k: v for k, v in optional.items() if v is not None})
        ops.emit("campsverso.office.ticket.created.v1", created)
        return number


@dataclass(frozen=True)
class TakeTicket(OfficeAction):
    """O dev pega um pedido do quadro: o escolhido, ou o mais antigo a fazer. Um de cada vez, e só
    o dele ou o de ninguém (ADR-0093, decisão 8)."""

    name: str = "take_ticket"
    role: ClassVar[str] = DEV

    def _ticket(self, ctx: ActionContext) -> EntityView | Rejection:
        target = ctx.params.get("target")
        if target is None:
            todo = [
                t
                for t in tickets(ctx.view)
                if t.attributes.get("estado") == TODO and open_to(t, ctx.avatar_id)
            ]
            return todo[0] if todo else Rejection("no_ticket", "não há pedido a fazer")
        found = ticket(ctx.view, target)
        if isinstance(found, Rejection):
            return found
        number = found.attributes["numero"]
        if found.attributes.get("estado") != TODO:
            return Rejection("wrong_state", f"o pedido {number} não está a fazer")
        if not open_to(found, ctx.avatar_id):
            owner = str(found.attributes["para"])
            name = ctx.view.entity(owner).display_name or owner
            return Rejection("not_allowed", f"o pedido {number} é do {name}")
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
        worked = min(
            total_seconds(ctx.view, mine), done + elapsed_ticks * tick_ms(ctx.view) // 1000
        )
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
        if _patch(ctx.params.get("patch")) is not None:
            return None  # quem entrega um patch da oficina não precisa do tempo simulado (ADR-0080)
        if int(cast(int, mine.attributes.get("trabalho", 0))) < total_seconds(ctx.view, mine):
            return Rejection("not_done", "o trabalho deste pedido ainda não acabou")
        return None

    def apply(self, ctx: ActionContext, ops: WorldOps) -> None:
        mine = doing(ctx.view, ctx.avatar_id)
        assert mine is not None
        patch = _patch(ctx.params.get("patch"))
        visible: dict[str, Any] = {"estado": DELIVERED}
        if patch is not None:
            visible["patch"] = patch["ref"]  # o quadro mostra o "ver o patch" (ADR-0080)
        ops.set_attributes(mine.entity_id, visible=visible)
        data: dict[str, Any] = {
            "ticket_id": mine.entity_id,
            "number": int(cast(int, mine.attributes["numero"])),
            "by": ctx.avatar_id,
            "worked_seconds": int(cast(int, mine.attributes.get("trabalho", 0))),
        }
        if patch is not None:
            data["patch"] = patch
        ops.emit("campsverso.office.ticket.delivered.v1", data)


def _patch(raw: object) -> dict[str, Any] | None:
    """O resumo do patch da oficina, quando a entrega o traz (ADR-0080). O patch fica no depósito
    de entregas; o mundo guarda só a referência e o resumo. Um resumo malformado fica de fora."""
    if not isinstance(raw, Mapping):
        return None
    patch = cast(Mapping[str, Any], raw)
    ref, base = patch.get("ref"), patch.get("base")
    files = patch.get("files")
    added, removed = patch.get("added"), patch.get("removed")
    if not (isinstance(ref, str) and isinstance(base, str) and isinstance(files, list)):
        return None
    if not (isinstance(added, int) and isinstance(removed, int)):
        return None
    names = [str(f) for f in cast(list[Any], files)][:200]
    return {"ref": ref, "base": base, "files": names, "added": added, "removed": removed}


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
        if isinstance(found, Rejection):
            return found
        if found.attributes.get("pr_estado") == "aberto":  # o aceite é mesclar (ADR-0083)
            number, pr = found.attributes["numero"], found.attributes["pr"]
            return Rejection("pr_open", f"o pedido {number} se aceita mesclando o PR #{pr}")
        return None

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


# O nome de uma entidade no contrato (`entity.spawned.v1`) vai até 64 caracteres; o título do
# pedido, até 80 (`ticket.title_max`). Um título longo publicava um evento inválido, e o kernel
# parava (achado em 22/nov, ADR-0092). O título inteiro fica no atributo `titulo`.
NAME_MAX = 64


def _name(title: str) -> str:
    """O nome da ficha: o título, abreviado com reticências quando passa do limite do contrato."""
    return title if len(title) <= NAME_MAX else title[: NAME_MAX - 1].rstrip() + "…"


@dataclass(frozen=True)
class ReturnTicket(OfficeAction):
    """O gerente devolve um pedido entregue, com o comentário do que falta: ele volta para "a
    fazer", sem dono, e o trabalho recomeça. Se quiser, troca quem programa a volta (ADR-0093,
    decisão 12): o harness e o modelo, como um par que o kernel confere. O "para quem" fica."""

    name: str = "return_ticket"
    role: ClassVar[str] = MANAGER

    def _comment(self, ctx: ActionContext) -> str | Rejection:
        limit = int(section(ctx.view, "ticket")["comment_max"])
        return text(ctx.params, "comment", limit, required=True)

    def _system(self, ctx: ActionContext) -> tuple[str | None, str | None] | Rejection:
        systems = cast(Mapping[str, Any], section(ctx.view, "ticket").get("systems") or {})
        return system(ctx.params, systems)

    def check(self, ctx: ActionContext) -> Rejection | None:
        board = _at_board(ctx)
        if isinstance(board, Rejection):
            return board
        found = _delivered(ctx)
        if isinstance(found, Rejection):
            return found
        comment = self._comment(ctx)
        if isinstance(comment, Rejection):
            return comment
        picked = self._system(ctx)
        return picked if isinstance(picked, Rejection) else None

    def apply(self, ctx: ActionContext, ops: WorldOps) -> None:
        found, comment, picked = _delivered(ctx), self._comment(ctx), self._system(ctx)
        assert not isinstance(found, Rejection)
        assert not isinstance(comment, Rejection)
        assert not isinstance(picked, Rejection)
        harness, model = picked
        visible: dict[str, Any] = {
            "estado": TODO,
            "dono": None,
            "trabalho": 0,
            "comentario": comment,
        }
        returned: dict[str, Any] = {
            "ticket_id": found.entity_id,
            "number": int(cast(int, found.attributes["numero"])),
            "by": ctx.avatar_id,
            "comment": comment,
        }
        if harness is not None:
            visible.update({"maos": harness, "modelo": model})
            returned.update({"harness": harness, "model": model})
        ops.set_attributes(found.entity_id, visible=visible)
        ops.emit("campsverso.office.ticket.returned.v2", returned)


def _dev(ctx: ActionContext) -> str | Rejection:
    """O dev que o gerente convoca ou dispensa: o dado, ou o único dev do elenco."""
    cast_devs = devs(ctx.view)
    target = ctx.params.get("target") or (cast_devs[0] if len(cast_devs) == 1 else None)
    if target not in cast_devs:
        return Rejection("invalid_params", f"target é um dev do elenco: {cast_devs}")
    return str(target)


@dataclass(frozen=True)
class SummonDev(OfficeAction):
    """O gerente convoca um dev fora do expediente (a parte 5 do M25), de qualquer lugar da sala:
    ele chega pela porta depois do deslocamento."""

    name: str = "summon"
    role: ClassVar[str] = MANAGER

    def check(self, ctx: ActionContext) -> Rejection | None:
        dev = _dev(ctx)
        if isinstance(dev, Rejection):
            return dev
        rules = on_call(ctx.view, dev)
        name = ctx.view.entity(dev).display_name or dev
        if not rules.get("enabled"):
            return Rejection("not_allowed", f"o acordo do {name} não tem convocação")
        if office_hours(ctx.view):
            return Rejection("wrong_state", f"o {name} está no expediente")
        if not in_window(ctx.view, rules):
            start, end = rules.get("window") or ("00:00", "24:00")
            return Rejection("wrong_state", f"a convocação vale das {start} às {end}")
        if summon_of(ctx.view, dev) is not None:
            return Rejection("wrong_state", f"o {name} já foi convocado")
        return None

    def apply(self, ctx: ActionContext, ops: WorldOps) -> None:
        dev = _dev(ctx)
        assert not isinstance(dev, Rejection)
        start_summon(ctx.view, ops, dev, ctx.avatar_id, "gerente")


@dataclass(frozen=True)
class DismissDev(OfficeAction):
    """O gerente dispensa o dev convocado: ele vai embora, e o vigia volta. O dev não volta
    sozinho nesta visita do gerente; o botão o chama de novo."""

    name: str = "dismiss"
    role: ClassVar[str] = MANAGER

    def check(self, ctx: ActionContext) -> Rejection | None:
        dev = _dev(ctx)
        if isinstance(dev, Rejection):
            return dev
        if summon_of(ctx.view, dev) is None:
            name = ctx.view.entity(dev).display_name or dev
            return Rejection("wrong_state", f"o {name} não está convocado")
        return None

    def apply(self, ctx: ActionContext, ops: WorldOps) -> None:
        dev = _dev(ctx)
        assert not isinstance(dev, Rejection)
        end_summon(ops, dev, "dispensado", ctx.avatar_id)
        if ctx.view.present(dev):
            ops.leave(dev, SUMMON_REASON)


@dataclass(frozen=True)
class GoHome(OfficeAction):
    """O dev convocado vai para casa (ADR-0093, decisão 10), quando o gerente diz que pode ir e ele
    concorda na conversa: a dispensa pelo próprio dev, como o "Dispensar" do chip, com ele no
    `by`. Só fora do expediente, e só convocado."""

    name: str = "go_home"
    role: ClassVar[str] = DEV

    def check(self, ctx: ActionContext) -> Rejection | None:
        if summon_of(ctx.view, ctx.avatar_id) is None:
            return Rejection("wrong_state", "só vai para casa assim quem foi convocado")
        return None

    def apply(self, ctx: ActionContext, ops: WorldOps) -> None:
        end_summon(ops, ctx.avatar_id, "dispensado", ctx.avatar_id)
        if ctx.view.present(ctx.avatar_id):
            ops.leave(ctx.avatar_id, SUMMON_REASON)


@dataclass(frozen=True)
class Break(OfficeAction):
    """Uma pausa da rotina (ADR-0080): beber água, um café, o banheiro, as etapas do almoço. É
    ilustrativa: não mexe em nada do mundo, e qualquer um faz, ao lado da coisa."""

    kind: str = ""
    role: ClassVar[str] = ""  # qualquer um
    shared: ClassVar[bool] = False

    def check(self, ctx: ActionContext) -> Rejection | None:
        things = ctx.view.entities(self.kind)
        if not things:
            return Rejection("invalid_params", f"não há {self.kind} no escritório")
        if not any(adjacent(ctx.view, ctx.avatar_id, thing) for thing in things):
            return Rejection("not_adjacent", f"longe de {self.kind}")
        return None

    def apply(self, ctx: ActionContext, ops: WorldOps) -> None:
        # A marmita (ADR-0082): pega na geladeira, carrega até o micro-ondas e a mesinha, e sai no
        # lixo. Só um atributo visível do avatar, para a tela desenhá-lo carregando.
        if self.name == "fridge":
            ops.set_attributes(ctx.avatar_id, visible={"carregando": "marmita"})
        elif self.name == "trash":
            ops.set_attributes(ctx.avatar_id, visible={"carregando": None})


@dataclass(frozen=True)
class SofaBreak(Break):
    """No sofá da sala de descompressão (ADR-0082): ver TV ou jogar videogame. O avatar fica no
    tapete, logo acima ou logo abaixo do sofá, e a tela o desenha sentado nele, virado para a TV."""

    def check(self, ctx: ActionContext) -> Rejection | None:
        here = ctx.view.entity(ctx.avatar_id).position
        sofas = [s for s in ctx.view.entities(self.kind) if s.position is not None]
        if not sofas:
            return Rejection("invalid_params", f"não há {self.kind} no escritório")
        if here is None or not any(
            abs(here.y - s.position.y) == 1 and abs(here.x - s.position.x) <= 1
            for s in sofas
            if s.position is not None
        ):
            return Rejection("not_adjacent", "sente no sofá: no tapete, logo acima ou abaixo dele")
        return None


@dataclass(frozen=True)
class Lunch(Break):
    """Comer na mesinha da copa, só na hora do almoço, até uns minutos antes de ela acabar (o
    resto é para jogar fora e voltar à mesa)."""

    def check(self, ctx: ActionContext) -> Rejection | None:
        if not at_lunch(ctx.view):
            return Rejection("invalid_params", "fora da hora do almoço")
        return super().check(ctx)

    def seconds(self, ctx: ActionContext) -> float:
        until = lunch_end(ctx.view) - lunch_tail(ctx.view)
        return float(max(60, (until - ctx.view.minute_of_day) * 60))


@dataclass(frozen=True)
class SwitchLight(OfficeAction):
    """Acender ou apagar a luz da sala no interruptor (ADR-0088): qualquer um que esteja ao lado
    dele (o gerente, o dev, o vigia). O estado é do mundo, igual para todos; a tela só o desenha."""

    on: bool = True
    role: ClassVar[str] = ""  # qualquer um
    shared: ClassVar[bool] = True  # duas mãos no mesmo interruptor: confere de novo ao concluir

    def _switch(self, ctx: ActionContext) -> EntityView | Rejection:
        switches = ctx.view.entities(LIGHT_SWITCH)
        if not switches:
            return Rejection("invalid_params", "não há interruptor no escritório")
        near = [s for s in switches if adjacent(ctx.view, ctx.avatar_id, s)]
        if not near:
            return Rejection("not_adjacent", "longe do interruptor")
        return near[0]

    def check(self, ctx: ActionContext) -> Rejection | None:
        switch = self._switch(ctx)
        if isinstance(switch, Rejection):
            return switch
        if bool(switch.attributes.get("acesa")) == self.on:
            already = "a luz já está acesa" if self.on else "a luz já está apagada"
            return Rejection("invalid_params", already)
        return None

    def apply(self, ctx: ActionContext, ops: WorldOps) -> None:
        switch = self._switch(ctx)
        assert not isinstance(switch, Rejection)
        ops.set_attributes(switch.entity_id, visible={"acesa": self.on}, cause=self.name)
        fact = {"switch_id": switch.entity_id, "on": self.on, "by": ctx.avatar_id}
        ops.emit(LIGHT_SWITCHED, fact)


BREAKS: tuple[OfficeAction, ...] = (
    Break("drink", WATER_COOLER),
    Break("coffee", COFFEE_MACHINE),
    Break("restroom", RESTROOM_DOOR),
    # O almoço em etapas (ADR-0082): pegar na geladeira, esquentar, comer na mesinha, jogar fora.
    Break("fridge", FRIDGE),
    Break("microwave", MICROWAVE),
    Lunch("lunch", COPA_TABLE),
    Break("trash", TRASH),
    SofaBreak("tv", SOFA),
    SofaBreak("videogame", SOFA),
)

ALL_ACTIONS: tuple[OfficeAction, ...] = (
    WriteTicket(),
    TakeTicket(),
    Work(),
    Deliver(),
    AcceptTicket(),
    ReturnTicket(),
    SummonDev(),
    DismissDev(),
    GoHome(),
    SwitchLight("light_on", on=True),
    SwitchLight("light_off", on=False),
    *BREAKS,
)
