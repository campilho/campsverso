"""As ferramentas do mundo que as mãos de fora oferecem ao modelo (ADR-0089; ADR-0093, decisão 18):
chamar um robô da bancada e anotar na memória do dev. A definição fica aqui, uma só para todas as
mãos. O Claude Code as recebe por um servidor MCP no processo, pelo SDK; o Codex (e o Antigravity,
no M28), pelo `/mcp` da porta das mãos, o único endereço que o cercado deixa alcançar.

O `/mcp` fala o MCP pelo HTTP (o "streamable HTTP" de 2025-06-18) no mínimo que um cliente pede:
o `initialize`, o `ping`, o `tools/list` e o `tools/call`, cada resposta num JSON; as notificações
não têm resposta. Sem a corrente de eventos (o `GET`), que o servidor pode recusar.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, cast

from campsverso_ports import HandsWorld, ToolResult

ROBOT = "chamar_robo"
NOTE = "anotar"
# O nome do servidor, o mesmo em todas as mãos: o modelo vê `mcp__oficina__chamar_robo`.
SERVER = "oficina"
PROTOCOL = "2025-06-18"
PROTOCOLS = ("2025-06-18", "2025-03-26", "2024-11-05")


@dataclass(frozen=True, slots=True)
class WorldTool:
    """Uma ferramenta do mundo: o nome, a descrição e o esquema da entrada."""

    name: str
    description: str
    schema: Mapping[str, Any]


def world_tools(world: HandsWorld) -> list[WorldTool]:
    """As ferramentas do mundo deste pedido, com os robôs que estão na bancada agora."""
    robots = list(world.robots)
    names = [r.name for r in robots]
    present = "; ".join(f"{r.name}: {r.description}" if r.description else r.name for r in robots)
    return [
        WorldTool(
            ROBOT,
            "Chama um robô da bancada do escritório no espaço do pedido e devolve o que ele disse."
            + (f" Na bancada agora: {present}." if present else " A bancada está vazia."),
            {
                "type": "object",
                "properties": {
                    "nome": {"type": "string", "enum": names or [""]},
                    "argumentos": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["nome"],
            },
        ),
        WorldTool(
            NOTE,
            "Anota na sua memória algo para lembrar nos próximos dias: uma decisão, um cuidado,"
            " o que aprendeu sobre o projeto.",
            {"type": "object", "properties": {"texto": {"type": "string"}}, "required": ["texto"]},
        ),
    ]


async def call_world_tool(world: HandsWorld, name: str, args: Mapping[str, Any]) -> ToolResult:
    """Uma chamada de ferramenta do mundo, com os argumentos que o modelo deu."""
    if name == ROBOT:
        given = args.get("argumentos")
        argv = [str(a) for a in cast(list[Any], given)] if isinstance(given, list) else []
        return await world.robot(str(args.get("nome") or ""), argv)
    if name == NOTE:
        return await world.note(str(args.get("texto") or ""))
    return ToolResult(False, f"ferramenta desconhecida: {name}", f"{name}: desconhecida")


def _error(ident: object, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": ident, "error": {"code": code, "message": message}}


async def _answer(world: HandsWorld, message: Mapping[str, Any]) -> dict[str, Any] | None:
    method = message.get("method")
    if "id" not in message:
        return None  # uma notificação (o `notifications/initialized`): sem resposta
    ident = message["id"]
    params = cast(Mapping[str, Any], message.get("params") or {})
    if method == "initialize":
        asked = params.get("protocolVersion")
        result: dict[str, Any] = {
            "protocolVersion": asked if asked in PROTOCOLS else PROTOCOL,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": SERVER, "version": "1"},
        }
    elif method == "ping":
        result = {}
    elif method == "tools/list":
        result = {
            "tools": [
                {"name": t.name, "description": t.description, "inputSchema": dict(t.schema)}
                for t in world_tools(world)
            ]
        }
    elif method == "tools/call":
        name = str(params.get("name") or "")
        if name not in (ROBOT, NOTE):
            return _error(ident, -32602, f"ferramenta desconhecida: {name}")
        arguments = cast(Mapping[str, Any], params.get("arguments") or {})
        done = await call_world_tool(world, name, arguments)
        result = {"content": [{"type": "text", "text": done.text or "(vazio)"}]}
        if not done.ok:
            result["isError"] = True
    else:
        return _error(ident, -32601, f"método desconhecido: {method}")
    return {"jsonrpc": "2.0", "id": ident, "result": result}


async def mcp_answer(world: HandsWorld, body: object) -> object | None:
    """A resposta do `/mcp` a um corpo JSON-RPC: uma mensagem ou um lote. None quando só havia
    notificações (o HTTP responde 202, sem corpo)."""
    if isinstance(body, Sequence) and not isinstance(body, str | bytes):
        answers = [
            a
            for a in [
                await _answer(world, cast(Mapping[str, Any], m))
                for m in cast(Sequence[Any], body)
                if isinstance(m, Mapping)
            ]
            if a is not None
        ]
        return answers or None
    if not isinstance(body, Mapping):
        return _error(None, -32600, "o corpo não é uma mensagem JSON-RPC")
    return await _answer(world, cast(Mapping[str, Any], body))
