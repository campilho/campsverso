"""O GitHub do escritório vivo (ADR-0083), pela API REST, como o GitHub App do dev.

**A identidade:** o App `campsverso-dev`, instalado só neste repositório. Um JWT assinado pela chave
do App vira um token de instalação de uma hora, guardado até perto de vencer. A chave fica num
arquivo fora do git e só o `openssl` a lê, para assinar: nenhuma biblioteca nova, e a chave nunca
passa por uma variável do Python.

**O commit sem `git push`:** os arquivos viram blobs, os blobs uma árvore sobre a da base, a árvore
um commit sobre a base (ou sobre o topo do ramo, num pedido devolvido), e o commit move o ramo.
O ramo principal nunca é tocado: o App só escreve em `dev/*`, pelo ruleset do repositório.

**O CI:** os check-runs do topo do ramo. Algum rodando é `pending`; todos acabados, um que não
passou é `failure`; o resto, `success`.
"""

import asyncio
import base64
import json
import time
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any, cast

import httpx2

from campsverso_ports import CiState, CodeHostError, PullRequest, PullRequestState

API = "https://api.github.com"
VERSION = "2022-11-28"
RENEW_SECONDS = 300  # renova o token cinco minutos antes de vencer
FAILED = frozenset({"failure", "cancelled", "timed_out", "action_required", "startup_failure"})


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


class GitHubApp:
    """O token de instalação do App, renovado antes de vencer."""

    def __init__(
        self,
        app_id: int,
        installation_id: int,
        key_path: Path,
        client: httpx2.AsyncClient,
        now: Callable[[], float] = time.time,
    ) -> None:
        self._app_id = app_id
        self._installation = installation_id
        self._key = key_path
        self._client = client
        self._now = now
        self._token: str | None = None
        self._expires = 0.0

    async def jwt(self) -> str:
        """O JWT do App (RS256), de dez minutos, assinado pelo `openssl`."""
        issued = int(self._now()) - 60  # o relógio do GitHub pode estar um pouco atrás
        header = _b64url(json.dumps({"alg": "RS256", "typ": "JWT"}).encode())
        claims = {"iat": issued, "exp": issued + 600, "iss": str(self._app_id)}
        payload = _b64url(json.dumps(claims).encode())
        signing = f"{header}.{payload}".encode()
        process = await asyncio.create_subprocess_exec(
            "openssl",
            "dgst",
            "-sha256",
            "-sign",
            str(self._key),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        signature, error = await process.communicate(signing)
        if process.returncode != 0:
            raise CodeHostError(f"a assinatura do App falhou: {error.decode()[:200]}")
        return f"{header}.{payload}.{_b64url(signature)}"

    async def token(self) -> str:
        if self._token is not None and self._now() < self._expires - RENEW_SECONDS:
            return self._token
        try:
            response = await self._client.post(
                f"/app/installations/{self._installation}/access_tokens",
                headers={
                    "Authorization": f"Bearer {await self.jwt()}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": VERSION,
                },
            )
        except httpx2.HTTPError as error:
            raise CodeHostError(f"o token do App não veio: {type(error).__name__}") from error
        if response.status_code != 201:
            raise CodeHostError(f"o token do App foi recusado ({response.status_code})")
        body = cast(dict[str, Any], _json(response, "o token do App"))
        self._token = str(body["token"])
        self._expires = self._now() + 3600
        return self._token


class GitHubCodeHost:
    def __init__(
        self,
        repo: str,
        app: GitHubApp,
        client: httpx2.AsyncClient,
        main: str = "main",
    ) -> None:
        self._repo = repo
        self._app = app
        self._client = client
        self._main = main

    @classmethod
    def connect(
        cls, repo: str, app_id: int, installation_id: int, key_path: Path
    ) -> GitHubCodeHost:
        client = httpx2.AsyncClient(base_url=API, timeout=30.0)
        return cls(repo, GitHubApp(app_id, installation_id, key_path, client), client)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def _call(
        self,
        method: str,
        path: str,
        body: Mapping[str, Any] | None = None,
        *,
        missing: bool = False,
    ) -> Any:
        """Uma chamada ao repositório; com `missing`, um 404 devolve None. A rede que cai e a
        resposta que não é JSON (um 502 do GitHub com o corpo vazio derrubou o publicador do
        sandbox em 21/nov) viram `CodeHostError`, que quem chama já trata."""
        token = await self._app.token()
        try:
            response = await self._client.request(
                method,
                f"/repos/{self._repo}{path}",
                json=None if body is None else dict(body),
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": VERSION,
                },
            )
        except httpx2.HTTPError as error:
            raise CodeHostError(f"{method} {path}: {type(error).__name__}") from error
        if missing and response.status_code == 404:
            return None
        if response.status_code >= 400:
            try:
                message = str(cast(dict[str, Any], response.json()).get("message", ""))
            except ValueError:
                message = response.text.strip()
            raise CodeHostError(f"{method} {path}: {response.status_code} {message[:200]}")
        return _json(response, f"{method} {path}")

    async def publish_branch(
        self,
        branch: str,
        base: str,
        files: Mapping[str, str | None],
        message: str,
        *,
        fresh: bool = False,
    ) -> str:
        base_commit = await self._call("GET", f"/git/commits/{base}")
        tree: list[dict[str, Any]] = []
        for path, text in sorted(files.items()):
            entry: dict[str, Any] = {"path": path, "mode": "100644", "type": "blob"}
            if text is None:
                entry["sha"] = None  # apagado
            else:
                blob = await self._call(
                    "POST", "/git/blobs", {"content": text, "encoding": "utf-8"}
                )
                entry["sha"] = blob["sha"]
            tree.append(entry)
        new_tree = await self._call(
            "POST", "/git/trees", {"base_tree": base_commit["tree"]["sha"], "tree": tree}
        )
        ref = await self._call("GET", f"/git/ref/heads/{branch}", missing=True)
        parent = base if ref is None or fresh else str(ref["object"]["sha"])
        commit = await self._call(
            "POST",
            "/git/commits",
            {"message": message, "tree": new_tree["sha"], "parents": [parent]},
        )
        sha = str(commit["sha"])
        if ref is None:
            await self._call("POST", "/git/refs", {"ref": f"refs/heads/{branch}", "sha": sha})
        else:
            await self._call("PATCH", f"/git/refs/heads/{branch}", {"sha": sha, "force": fresh})
        return sha

    async def open_pull_request(self, branch: str, title: str, body: str) -> PullRequest:
        owner = self._repo.split("/", 1)[0]
        found = await self._call("GET", f"/pulls?head={owner}:{branch}&state=open")
        if found:  # o ramo já tem um PR aberto: o mesmo, depois de uma queda
            return await self.pull_request(int(found[0]["number"]))
        pull = await self._call(
            "POST", "/pulls", {"title": title, "head": branch, "base": self._main, "body": body}
        )
        return PullRequest(
            int(pull["number"]),
            str(pull["html_url"]),
            branch,
            str(pull["head"]["sha"]),
            "open",
            None,
        )

    async def pull_request(self, number: int) -> PullRequest:
        pull = await self._call("GET", f"/pulls/{number}")
        head = str(pull["head"]["sha"])
        state: PullRequestState = (
            "merged" if pull.get("merged_at") else "open" if pull["state"] == "open" else "closed"
        )
        runs = await self._call("GET", f"/commits/{head}/check-runs")
        return PullRequest(
            number,
            str(pull["html_url"]),
            str(pull["head"]["ref"]),
            head,
            state,
            _ci(cast(list[Mapping[str, Any]], runs.get("check_runs") or [])),
        )

    async def comment(self, number: int, body: str) -> None:
        await self._call("POST", f"/issues/{number}/comments", {"body": body})

    async def commit_ci(self, sha: str) -> CiState | None:
        runs = await self._call("GET", f"/commits/{sha}/check-runs")
        return _ci(cast(list[Mapping[str, Any]], runs.get("check_runs") or []))


def _json(response: httpx2.Response, what: str) -> Any:
    try:
        return response.json()
    except ValueError as error:
        raise CodeHostError(f"{what}: a resposta não é JSON ({response.status_code})") from error


def _ci(runs: list[Mapping[str, Any]]) -> CiState | None:
    if not runs:
        return None
    if any(run.get("status") != "completed" for run in runs):
        return "pending"
    if any(run.get("conclusion") in FAILED for run in runs):
        return "failure"
    return "success"
