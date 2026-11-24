"""As ferramentas do mundo no `/mcp` da porta das mãos (ADR-0093, decisão 18): o mínimo do MCP pelo
HTTP que o Codex pede, com a chave da sessão, diante de um mundo de teste."""

from collections.abc import Sequence
from typing import Any

import httpx2

from campsverso_adapters.hands_gate import HandsGate
from campsverso_adapters.hands_world_tools import NOTE, ROBOT, mcp_answer
from campsverso_ports import HandsStep, ModelRequest, ModelResponse, Robot, ToolResult


class Meter:
    def assert_priced(self, model: str) -> None:
        return None

    async def observed(
        self, request: ModelRequest, response: ModelResponse, *, harness: str
    ) -> float:
        return 0.0


class World:
    def __init__(self) -> None:
        self.calls: list[tuple[str, Sequence[str]]] = []
        self.notes: list[str] = []

    @property
    def robots(self) -> Sequence[Robot]:
        return [Robot("testador", "Roda os testes.")]

    async def robot(self, name: str, args: Sequence[str]) -> ToolResult:
        self.calls.append((name, list(args)))
        return ToolResult(True, "2 passaram", "testador: 2 passaram")

    async def note(self, text: str) -> ToolResult:
        self.notes.append(text)
        return ToolResult(False, "sem memória", "anotar: sem memória")

    async def step(self, step: HandsStep) -> None:
        return None

    def should_stop(self) -> bool:
        return False


def _rpc(ident: int, method: str, **params: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": ident, "method": method, "params": params}


async def test_o_mcp_da_porta_serve_as_ferramentas_do_mundo() -> None:
    world = World()
    gate = HandsGate(
        Meter(), api_key="k", harness="codex", avatar_id="kenji", ticket_id="pedido-1", world=world
    )
    async with gate, httpx2.AsyncClient(base_url=gate.url) as client:
        auth = {"Authorization": f"Bearer {gate.token}"}
        start = await client.post(
            "/mcp", json=_rpc(1, "initialize", protocolVersion="2025-03-26"), headers=auth
        )
        assert start.json()["result"]["protocolVersion"] == "2025-03-26"
        assert start.json()["result"]["capabilities"] == {"tools": {"listChanged": False}}
        ready = {"jsonrpc": "2.0", "method": "notifications/initialized"}
        assert (await client.post("/mcp", json=ready, headers=auth)).status_code == 202
        listed = (await client.post("/mcp", json=_rpc(2, "tools/list"), headers=auth)).json()
        tools = {t["name"]: t for t in listed["result"]["tools"]}
        assert set(tools) == {ROBOT, NOTE}
        assert tools[ROBOT]["inputSchema"]["properties"]["nome"]["enum"] == ["testador"]
        call = _rpc(
            3, "tools/call", name=ROBOT, arguments={"nome": "testador", "argumentos": ["a"]}
        )
        answer = (await client.post("/mcp", json=call, headers=auth)).json()["result"]
        assert answer == {"content": [{"type": "text", "text": "2 passaram"}]}
        assert world.calls == [("testador", ["a"])]
        note = _rpc(4, "tools/call", name=NOTE, arguments={"texto": "lembrar"})
        refused = (await client.post("/mcp", json=note, headers=auth)).json()["result"]
        assert refused["isError"] is True
        assert world.notes == ["lembrar"]
        # Sem a chave da sessão, nada; e só o POST.
        wrong = {"Authorization": "Bearer outra"}
        assert (await client.post("/mcp", json=_rpc(5, "ping"), headers=wrong)).status_code == 401
        assert (await client.get("/mcp", headers=auth)).status_code == 405
        # A porta continua a mesma para o modelo: sem a chave do dialeto, recusa.
        assert (await client.post("/v1/responses", json={})).status_code == 401


async def test_o_mcp_responde_um_lote_e_recusa_o_que_nao_conhece() -> None:
    world = World()
    batch = [_rpc(1, "ping"), {"jsonrpc": "2.0", "method": "notifications/initialized"}]
    assert await mcp_answer(world, batch) == [{"jsonrpc": "2.0", "id": 1, "result": {}}]
    unknown = await mcp_answer(world, _rpc(2, "resources/list"))
    assert isinstance(unknown, dict)
    assert unknown["error"]["code"] == -32601  # pyright: ignore[reportUnknownMemberType]
    tool = await mcp_answer(world, _rpc(3, "tools/call", name="apagar_tudo", arguments={}))
    assert isinstance(tool, dict)
    assert tool["error"]["code"] == -32602  # pyright: ignore[reportUnknownMemberType]
    assert await mcp_answer(world, [{"jsonrpc": "2.0", "method": "x"}]) is None
    bad = await mcp_answer(world, "texto")
    assert isinstance(bad, dict)
    assert bad["error"]["code"] == -32600  # pyright: ignore[reportUnknownMemberType]
