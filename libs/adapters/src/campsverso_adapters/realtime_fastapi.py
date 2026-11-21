"""Tempo real com FastAPI e uvicorn: o WebSocket da UI e os arquivos de conteúdo (ADR-0050).

- `/ws?view=player|operator`: uma conexão por UI; mensagens JSON de `contracts/realtime`.
- `/content/maps/<id>.tmj`: o mapa do cartucho, pelo id que vem no `session.started`.
- `/content/art/index.json` e `/content/art/<camada>/<arquivo>`: a arte dos cartuchos, em camadas
  do gênero ao cenário (ADR-0053). A tela junta os manifestos na ordem do índice.
- `/content/locale/<camada>/<língua>.json`: os nomes que quem joga lê, por língua (ADR-0075), na
  pasta `locale/` ao lado da `art/` de cada camada; a tela os junta na ordem do índice da arte.
- `/content/entregas/<mundo>/<pedido>/<carimbo>.patch` e `.json`: o patch que o dev entregou da
  oficina e o resumo dele (ADR-0080), para o gerente ver antes de aceitar. Só leitura, e só esses.
- `/`: a UI compilada, quando há uma pasta para ela (fora do modo de desenvolvimento).

Só escuta no endereço dado (127.0.0.1 na v0.1): não há login. Escutar só na própria máquina não
basta contra o navegador: uma página de qualquer site pode abrir um WebSocket para 127.0.0.1. Por
isso o `/ws` confere a origem, e só aceita a tela servida por esta máquina.
"""

import contextlib
import json
import re
from collections.abc import AsyncIterator, Callable, Mapping, Sequence
from pathlib import Path
from typing import Any, cast
from urllib.parse import urlsplit

import uvicorn
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from campsverso_ports import ConnectionClosedError, ConnectionHandler, Message, View

VIEWS: tuple[View, ...] = ("player", "operator")
POLICY_VIOLATION = 1008  # código WebSocket para pedido fora das regras
LOOPBACK = frozenset({"localhost", "127.0.0.1", "::1"})  # os nomes desta máquina
LANGUAGE_FILE = re.compile(r"[a-z]{2}(-[A-Z]{2})?\.json")  # pt-BR.json, en.json
# O que o depósito de entregas mostra (ADR-0080): o patch, em texto, e o resumo dele.
DELIVERY_TYPES = {".patch": "text/plain; charset=utf-8", ".json": "application/json"}


# Os mapas e a arte mudam com o repositório (as margens da água do ADR-0070 ficaram pretas numa
# tela com o terrain.png antigo no cache): o navegador confere a cada vez, e o ETag responde 304.
REVALIDATE = {"Cache-Control": "no-cache"}


def local_origin(origin: str | None, host: str) -> bool:
    """A origem do pedido de WebSocket é esta máquina (ou o endereço em que o gateway escuta)?

    Todo navegador manda `Origin` ao abrir um WebSocket, e a página não consegue trocá-lo: a tela
    do gateway e a do Vite chegam de `localhost` ou `127.0.0.1`, em qualquer porta, e a página de
    outro site chega com o nome dele (inclusive um nome que aponta para 127.0.0.1). Sem `Origin`
    não é um navegador, e sim um processo desta máquina, como os testes: esse a origem não segura.
    """
    if origin is None:
        return True
    try:
        name = urlsplit(origin).hostname
    except ValueError:
        return False
    return name is not None and (name in LOOPBACK or name == host)


class _WsConnection:
    def __init__(self, websocket: WebSocket, view: View, run: str | None = None) -> None:
        self._ws = websocket
        self._view: View = view
        self._run = run

    @property
    def view(self) -> View:
        return self._view

    @property
    def run(self) -> str | None:
        return self._run

    async def send(self, message: Message) -> None:
        try:
            await self._ws.send_text(json.dumps(message, ensure_ascii=False, separators=(",", ":")))
        except Exception as error:  # desconectou: qualquer falha ao mandar significa isso
            raise ConnectionClosedError from error

    async def messages(self) -> AsyncIterator[Message]:
        while True:
            try:
                text = await self._ws.receive_text()
            except WebSocketDisconnect, RuntimeError:
                return
            try:
                data = json.loads(text)
            except ValueError:
                data = {}
            yield cast(Message, data) if isinstance(data, dict) else {}

    async def close(self) -> None:
        with contextlib.suppress(Exception):
            await self._ws.close()


class FastApiRealtime:
    def __init__(
        self,
        host: str,
        port: int,
        maps: Mapping[str, Path] | None = None,
        ui_dir: Path | None = None,
        art: Sequence[tuple[str, Path]] = (),
        runs: Callable[[], list[dict[str, Any]]] | None = None,
        deliveries: Path | None = None,
        status: Callable[[], Mapping[str, Any]] | None = None,
        notice: Callable[[Mapping[str, Any]], str | None] | None = None,
    ) -> None:
        self.host, self.port = host, port
        self._status = status  # o que o /health diz além do ok (o supervisor, ADR-0083)
        self._notice = notice  # o aviso do supervisor às telas (a parte 5 do M25)
        self._deliveries = None if deliveries is None else deliveries.resolve()
        self._runs = runs  # o modo de assistir lista as corridas em /arena/runs (ADR-0068)
        self._maps = dict(maps or {})
        self._ui_dir = ui_dir
        self._art = [(name, folder.resolve()) for name, folder in art]
        self._server: uvicorn.Server | None = None

    def app(self, handler: ConnectionHandler) -> FastAPI:
        app = FastAPI(title="Campsverso gateway", docs_url=None, redoc_url=None)

        @app.websocket("/ws")
        async def ws(  # pyright: ignore[reportUnusedFunction]
            websocket: WebSocket, view: str = "player", run: str | None = None
        ) -> None:
            if view not in VIEWS or not local_origin(websocket.headers.get("origin"), self.host):
                await websocket.close(code=POLICY_VIOLATION)
                return
            await websocket.accept()
            connection = _WsConnection(websocket, view, run)
            try:
                await handler(connection)
            finally:
                await connection.close()

        @app.get("/arena/runs")
        async def runs() -> list[dict[str, Any]]:  # pyright: ignore[reportUnusedFunction]
            return [] if self._runs is None else self._runs()

        @app.get("/content/maps/{name}")
        async def map_file(name: str) -> FileResponse:  # pyright: ignore[reportUnusedFunction]
            path = self._maps.get(name.removesuffix(".tmj"))
            if path is None or not path.is_file():
                raise HTTPException(status_code=404, detail=f"mapa {name!r} desconhecido")
            return FileResponse(path, media_type="application/json", headers=REVALIDATE)

        @app.get("/content/art/index.json")
        async def art_index() -> dict[str, list[str]]:  # pyright: ignore[reportUnusedFunction]
            return {"layers": [name for name, folder in self._art if folder.is_dir()]}

        @app.get("/content/art/{layer}/{path:path}")
        async def art_file(layer: str, path: str) -> FileResponse:  # pyright: ignore[reportUnusedFunction]
            folder = dict(self._art).get(layer)
            target = None if folder is None else (folder / path).resolve()
            if target is None or folder is None or not target.is_relative_to(folder):
                raise HTTPException(status_code=404, detail=f"arte {layer}/{path} desconhecida")
            if not target.is_file():
                raise HTTPException(status_code=404, detail=f"arte {layer}/{path} desconhecida")
            return FileResponse(target, headers=REVALIDATE)

        @app.get("/content/locale/{layer}/{name}")
        async def locale_file(layer: str, name: str) -> FileResponse:  # pyright: ignore[reportUnusedFunction]
            art = dict(self._art).get(layer)
            folder = None if art is None else art.parent / "locale"
            target = None if folder is None else (folder / name).resolve()
            if (
                target is None
                or folder is None
                or not LANGUAGE_FILE.fullmatch(name)
                or not target.is_relative_to(folder)
                or not target.is_file()
            ):
                raise HTTPException(status_code=404, detail=f"língua {layer}/{name} desconhecida")
            return FileResponse(target, media_type="application/json", headers=REVALIDATE)

        @app.get("/content/entregas/{path:path}")
        async def delivery_file(path: str) -> FileResponse:  # pyright: ignore[reportUnusedFunction]
            root = self._deliveries
            target = None if root is None else (root / path).resolve()
            if (
                target is None
                or root is None
                or target.suffix not in DELIVERY_TYPES
                or not target.is_relative_to(root)
                or not target.is_file()
            ):
                raise HTTPException(status_code=404, detail=f"entrega {path} desconhecida")
            return FileResponse(target, media_type=DELIVERY_TYPES[target.suffix])

        @app.get("/health")
        async def health() -> dict[str, Any]:  # pyright: ignore[reportUnusedFunction]
            return {"ok": True, **(self._status() if self._status is not None else {})}

        @app.post("/aviso")
        async def notice(request: Request) -> dict[str, Any]:  # pyright: ignore[reportUnusedFunction]
            # Só da própria máquina: quem avisa é o supervisor, ao lado do gateway.
            client = request.client.host if request.client is not None else ""
            if self._notice is None or client not in ("127.0.0.1", "::1", "localhost"):
                raise HTTPException(status_code=403, detail="o aviso vem só do supervisor local")
            body = await request.json()
            if not isinstance(body, dict):
                raise HTTPException(status_code=422, detail="o aviso é um objeto")
            reason = self._notice(cast(Mapping[str, Any], body))
            if reason is not None:
                raise HTTPException(status_code=422, detail=reason)
            return {"ok": True}

        if self._ui_dir is not None and self._ui_dir.is_dir():
            app.mount("/", StaticFiles(directory=self._ui_dir, html=True), name="ui")
        return app

    async def serve(self, handler: ConnectionHandler) -> None:
        config = uvicorn.Config(
            self.app(handler),
            host=self.host,
            port=self.port,
            ws="websockets-sansio",
            lifespan="off",
            log_level="warning",
        )
        self._server = uvicorn.Server(config)
        await self._server.serve()

    @property
    def started(self) -> bool:
        return self._server is not None and self._server.started

    async def stop(self) -> None:
        if self._server is not None:
            self._server.should_exit = True
