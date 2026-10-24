"""Tempo real com FastAPI e uvicorn: o WebSocket da UI e os arquivos de conteúdo (ADR-0050).

- `/ws?view=player|operator`: uma conexão por UI; mensagens JSON de `contracts/realtime`.
- `/content/maps/<id>.tmj`: o mapa do cartucho, pelo id que vem no `session.started`.
- `/content/art/index.json` e `/content/art/<camada>/<arquivo>`: a arte dos cartuchos, em camadas
  do gênero ao cenário (ADR-0053). A tela junta os manifestos na ordem do índice.
- `/`: a UI compilada, quando há uma pasta para ela (fora do modo de desenvolvimento).

Só escuta no endereço dado (127.0.0.1 na v0.1): não há login.
"""

import contextlib
import json
from collections.abc import AsyncIterator, Callable, Mapping, Sequence
from pathlib import Path
from typing import Any, cast

import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from campsverso_ports import ConnectionClosedError, ConnectionHandler, Message, View

VIEWS: tuple[View, ...] = ("player", "operator")
POLICY_VIOLATION = 1008  # código WebSocket para pedido fora das regras


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
    ) -> None:
        self.host, self.port = host, port
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
            if view not in VIEWS:
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
            return FileResponse(path, media_type="application/json")

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
            return FileResponse(target)

        @app.get("/health")
        async def health() -> dict[str, bool]:  # pyright: ignore[reportUnusedFunction]
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
