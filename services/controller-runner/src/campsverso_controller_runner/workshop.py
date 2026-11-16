"""A sessão do dev na oficina (ADR-0080): os passos que o controlador roda pela porta antes de
propor a entrega, um `workshop.step.v1` por passo, e o patch revisado no depósito de entregas.

Quem pede os passos é o controlador do dev: o dev-script de reserva, com uma sessão fixa, e a mente,
na parte 3 do M24. O kernel nunca vê a oficina: ele recebe a proposta de entrega com o resumo do
patch, e a tela e o `make aplicar` buscam o patch pela referência.
"""

import json
import time
from collections.abc import Awaitable, Callable, Mapping, Sequence
from typing import Any, cast

from campsverso_ports import TOOLS, BlobStore, ToolResult, WorkshopPort, Workspace

type Review = Callable[[str], list[str]]
type Publish = Callable[[str, Mapping[str, Any]], Awaitable[None]]

STEP = "campsverso.workshop.step.v1"
MAX_STEPS = 200  # o limite de passos de uma sessão (o plano do M24, §3.4)


async def call(space: Workspace, tool: str, args: Mapping[str, Any]) -> ToolResult:
    """Uma ferramenta da oficina pelo nome que a mente vê; argumento errado vira uma recusa."""
    try:
        match tool:
            case "ver_arquivos":
                return await space.list_files(str(args.get("path", ".")))
            case "ler":
                end = args.get("end")
                return await space.read(
                    str(args["path"]),
                    int(args.get("start", 1)),
                    None if end is None else int(end),
                )
            case "buscar":
                return await space.search(str(args["pattern"]), str(args.get("path", ".")))
            case "escrever":
                return await space.write(str(args["path"]), str(args["content"]))
            case "editar":
                return await space.edit(str(args["path"]), str(args["old"]), str(args["new"]))
            case "rodar_testes":
                return await space.run_tests(str(args.get("path", ".")))
            case "ver_mudancas":
                return await space.diff()
            case "pronto":
                return ToolResult(True, "pronto", "pronto para entregar")
            case _:
                return ToolResult(
                    False, f"ferramenta desconhecida: {tool}", f"{tool}: desconhecida"
                )
    except (KeyError, TypeError, ValueError) as error:
        return ToolResult(False, f"argumentos inválidos: {error}", f"{tool}: argumentos inválidos")


class WorkshopSession:
    """Roda a sessão de um pedido e devolve a proposta de entrega com o patch, ou a fala com o
    motivo da recusa."""

    def __init__(
        self,
        worldid: str,
        avatar_id: str,
        workshop: WorkshopPort,
        deliveries: BlobStore,
        review: Review,
        publish: Publish | None = None,
    ) -> None:
        self._worldid = worldid
        self._avatar = avatar_id
        self._workshop = workshop
        self._deliveries = deliveries
        self._review = review
        self.publish = publish  # quem publica os passos: o runner, que é montado depois
        self.delivered = 0

    async def begin(self, ticket: str) -> Workspace:
        """Abre o espaço do pedido (ou retoma o que já existe)."""
        return await self._workshop.open(self._worldid, ticket)

    async def step(self, space: Workspace, tool: str, args: Mapping[str, Any]) -> ToolResult:
        """Um passo: a ferramenta pela porta e o `workshop.step.v1` dele."""
        started = time.monotonic()
        result = await call(space, tool, args)
        data: dict[str, Any] = {
            "avatar_id": self._avatar,
            "ticket_id": space.ticket_id,
            "tool": tool if tool in TOOLS else "pronto",
            "summary": (result.summary or tool)[:200],
            "ok": result.ok,
            "duration_ms": int((time.monotonic() - started) * 1000),
        }
        if result.path:
            data["path"] = result.path[:300]
        if self.publish is not None and tool in TOOLS:
            await self.publish(STEP, data)
        return result

    async def finish(
        self, space: Workspace, proposal: Mapping[str, Any], stamp: str
    ) -> dict[str, Any]:
        """O patch do espaço, revisado: a proposta de entrega com o resumo, ou a fala com o motivo
        da recusa."""
        patch = await space.patch()
        reasons = self._review(patch.text)
        if reasons:
            text = "Não posso entregar este pedido: " + "; ".join(reasons[:3]) + "."
            return {
                "action": "say",
                "params": {"text": text[:280]},
                "intent": "a revisão da oficina recusou a entrega",
            }
        self.delivered += 1
        ticket = space.ticket_id
        ref = f"{self._worldid}/{ticket}/{stamp.lower()}.patch"
        summary = patch.summary
        self._deliveries.put(ref, patch.text.encode("utf-8"))
        about = {
            "ticket_id": ticket,
            "base": summary.base,
            "files": list(summary.files),
            "added": summary.added,
            "removed": summary.removed,
        }
        self._deliveries.put(ref.removesuffix(".patch") + ".json", json.dumps(about).encode())
        params = dict(cast(Mapping[str, Any], proposal.get("params") or {}))
        params["patch"] = {
            "ref": ref,
            "base": summary.base,
            "files": list(summary.files)[:200],
            "added": summary.added,
            "removed": summary.removed,
        }
        return {**proposal, "params": params}

    async def run(
        self, proposal: Mapping[str, Any], session: Mapping[str, Any], stamp: str
    ) -> dict[str, Any]:
        """Roda a sessão fixa de um script; `stamp` distingue as entregas de um mesmo pedido."""
        space = await self.begin(str(session["ticket_id"]))
        steps = cast(Sequence[Mapping[str, Any]], session.get("steps") or ())
        ready = False
        for step in steps[:MAX_STEPS]:
            tool = str(step["tool"])
            await self.step(space, tool, cast(Mapping[str, Any], step.get("args") or {}))
            if tool == "pronto":
                ready = True
                break
        if not ready:
            return dict(proposal)  # a sessão acabou sem pronto: a entrega vai sem patch
        return await self.finish(space, proposal, stamp)
