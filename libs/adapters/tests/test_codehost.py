"""A porta do repositório de fora (ADR-0083): o GitHub falso, o GitHub pela API e os arquivos de
uma entrega. Nenhum teste fala com o GitHub de verdade."""

import base64
import json
import subprocess
from pathlib import Path
from typing import Any

import httpx2
import pytest

from campsverso_adapters.codehost_github import GitHubApp, GitHubCodeHost
from campsverso_adapters.codehost_memory import MemoryCodeHost
from campsverso_adapters.git_patch import files_after_patch
from campsverso_ports import CodeHostError

BASE = "a" * 40


async def test_o_github_falso_guarda_os_ramos_e_os_prs() -> None:
    host = MemoryCodeHost()
    first = await host.publish_branch("dev/pedido-1", BASE, {"a.md": "um\n"}, "pedido 1")
    pull = await host.open_pull_request("dev/pedido-1", "Pedido 1", "corpo")
    assert (pull.number, pull.head, pull.state, pull.ci) == (1, first, "open", None)
    # De novo, depois de uma queda: o mesmo PR, e nenhum outro.
    assert (await host.open_pull_request("dev/pedido-1", "de novo", "")).number == 1
    assert len(host.pulls) == 1
    # O pedido devolvido e refeito: o commit novo vai sobre o topo, e o PR acompanha.
    second = await host.publish_branch("dev/pedido-1", BASE, {"a.md": "dois\n"}, "refeito")
    assert host.branches["dev/pedido-1"][-1].parent == first
    assert (await host.pull_request(1)).head == second
    host.set_ci(1, "success")
    host.merge(1)
    merged = await host.pull_request(1)
    assert (merged.state, merged.ci) == ("merged", "success")
    await host.comment(1, "revisado")
    assert host.comments[1] == ["revisado"]


def _key(tmp_path: Path) -> Path:
    key = tmp_path / "app.pem"
    subprocess.run(["openssl", "genrsa", "-out", str(key), "2048"], check=True, capture_output=True)
    return key


def _verify(token: str, key: Path, tmp_path: Path) -> dict[str, Any]:
    """Confere a assinatura RS256 do JWT com a chave pública, pelo openssl, e devolve os dados."""
    header, payload, signature = token.split(".")
    public = tmp_path / "app.pub"
    subprocess.run(
        ["openssl", "rsa", "-in", str(key), "-pubout", "-out", str(public)],
        check=True,
        capture_output=True,
    )
    sig = tmp_path / "sig.bin"
    sig.write_bytes(base64.urlsafe_b64decode(signature + "=" * (-len(signature) % 4)))
    checked = subprocess.run(
        ["openssl", "dgst", "-sha256", "-verify", str(public), "-signature", str(sig)],
        input=f"{header}.{payload}".encode(),
        capture_output=True,
        check=False,
    )
    assert checked.returncode == 0, checked.stderr
    return json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))


class FakeApi:
    """O GitHub do outro lado do transporte: guarda os pedidos e responde o mínimo."""

    def __init__(self, *, branch_exists: bool = False, open_pulls: int = 0) -> None:
        self.calls: list[tuple[str, str, Any]] = []
        self.branch_exists = branch_exists
        self.open_pulls = [{"number": 12}] if open_pulls else []
        self.authorization: list[str] = []

    def __call__(self, request: httpx2.Request) -> httpx2.Response:
        body = json.loads(request.content) if request.content else None
        path = request.url.path
        self.calls.append((request.method, path, body))
        self.authorization.append(request.headers.get("Authorization", ""))
        repo = "/repos/campilho/campsverso"
        routes: dict[tuple[str, str], tuple[int, Any]] = {
            ("POST", "/app/installations/7/access_tokens"): (201, {"token": "ghs_teste"}),
            ("GET", f"{repo}/git/commits/{BASE}"): (200, {"tree": {"sha": "t" * 40}}),
            ("POST", f"{repo}/git/blobs"): (201, {"sha": "b" * 40}),
            ("POST", f"{repo}/git/trees"): (201, {"sha": "n" * 40}),
            ("POST", f"{repo}/git/commits"): (201, {"sha": "c" * 40}),
            ("POST", f"{repo}/git/refs"): (201, {}),
            ("PATCH", f"{repo}/git/refs/heads/dev/pedido-1"): (200, {}),
            ("GET", f"{repo}/pulls"): (200, self.open_pulls),
            ("POST", f"{repo}/pulls"): (
                201,
                {
                    "number": 12,
                    "html_url": "https://github.com/campilho/campsverso/pull/12",
                    "head": {"sha": "c" * 40, "ref": "dev/pedido-1"},
                },
            ),
            ("GET", f"{repo}/pulls/12"): (
                200,
                {
                    "html_url": "https://github.com/campilho/campsverso/pull/12",
                    "state": "closed",
                    "merged_at": "2026-11-21T12:00:00Z",
                    "head": {"sha": "c" * 40, "ref": "dev/pedido-1"},
                },
            ),
            ("GET", f"{repo}/commits/{'c' * 40}/check-runs"): (
                200,
                {
                    "check_runs": [
                        {"status": "completed", "conclusion": "success"},
                        {"status": "completed", "conclusion": "failure"},
                    ]
                },
            ),
            ("POST", f"{repo}/issues/12/comments"): (201, {}),
        }
        if self.branch_exists:
            routes[("GET", f"{repo}/git/ref/heads/dev/pedido-1")] = (
                200,
                {"object": {"sha": "p" * 40}},
            )
        status, answer = routes.get((request.method, path), (404, {"message": "Not Found"}))
        return httpx2.Response(status, json=answer)


def _host(api: FakeApi, key: Path) -> GitHubCodeHost:
    client = httpx2.AsyncClient(
        base_url="https://api.github.com", transport=httpx2.MockTransport(api)
    )
    app = GitHubApp(5854989, 7, key, client, now=lambda: 1_795_000_000.0)
    return GitHubCodeHost("campilho/campsverso", app, client)


async def test_o_app_assina_o_jwt_e_troca_por_um_token_guardado(tmp_path: Path) -> None:
    key = _key(tmp_path)
    api = FakeApi()
    host = _host(api, key)
    await host.comment(12, "oi")
    await host.comment(12, "de novo")
    exchanges = [c for c in api.calls if c[1].endswith("/access_tokens")]
    assert len(exchanges) == 1  # o token fica guardado até perto de vencer
    claims = _verify(api.authorization[0].removeprefix("Bearer "), key, tmp_path)
    assert (claims["iss"], claims["exp"] - claims["iat"]) == ("5854989", 600)
    assert api.authorization[1:] == ["Bearer ghs_teste", "Bearer ghs_teste"]


async def test_o_commit_vai_pela_api_e_cria_o_ramo_do_dev(tmp_path: Path) -> None:
    api = FakeApi()
    host = _host(api, _key(tmp_path))
    sha = await host.publish_branch(
        "dev/pedido-1", BASE, {"novo.md": "oi\n", "velho.md": None}, "Pedido 1"
    )
    assert sha == "c" * 40
    calls = [(m, p.removeprefix("/repos/campilho/campsverso")) for m, p, _ in api.calls]
    assert calls[1:] == [
        ("GET", f"/git/commits/{BASE}"),
        ("POST", "/git/blobs"),
        ("POST", "/git/trees"),
        ("GET", "/git/ref/heads/dev/pedido-1"),
        ("POST", "/git/commits"),
        ("POST", "/git/refs"),
    ]
    tree = next(b for _, p, b in api.calls if p.endswith("/git/trees"))
    assert tree["base_tree"] == "t" * 40
    assert tree["tree"] == [
        {"path": "novo.md", "mode": "100644", "type": "blob", "sha": "b" * 40},
        {"path": "velho.md", "mode": "100644", "type": "blob", "sha": None},
    ]
    commit = next(b for _, p, b in api.calls if p.endswith("/git/commits"))
    assert commit["parents"] == [BASE]
    ref = next(b for _, p, b in api.calls if p.endswith("/git/refs"))
    assert ref == {"ref": "refs/heads/dev/pedido-1", "sha": "c" * 40}


async def test_o_ramo_que_existe_avanca_sobre_o_topo(tmp_path: Path) -> None:
    api = FakeApi(branch_exists=True)
    host = _host(api, _key(tmp_path))
    await host.publish_branch("dev/pedido-1", BASE, {"a.md": "x\n"}, "refeito")
    commit = next(b for _, p, b in api.calls if p.endswith("/git/commits"))
    assert commit["parents"] == ["p" * 40]
    patched = next(b for m, _, b in api.calls if m == "PATCH")
    assert patched == {"sha": "c" * 40, "force": False}


async def test_o_pedido_novo_reescreve_o_ramo_velho_a_partir_da_base(tmp_path: Path) -> None:
    """O PR #3 (21/nov): o ramo `dev/pedido-1` do primeiro PR de todos ainda existia, e o pedido 1
    do escritório vivo foi por cima dele. Com `fresh`, o pai é a base, e o ramo é reescrito."""
    api = FakeApi(branch_exists=True)
    host = _host(api, _key(tmp_path))
    await host.publish_branch("dev/pedido-1", BASE, {"a.md": "x\n"}, "pedido 1", fresh=True)
    commit = next(b for _, p, b in api.calls if p.endswith("/git/commits"))
    assert commit["parents"] == [BASE]
    patched = next(b for m, _, b in api.calls if m == "PATCH")
    assert patched == {"sha": "c" * 40, "force": True}
    memory = MemoryCodeHost()
    await memory.publish_branch("dev/pedido-1", "o" * 40, {"a.md": "velho\n"}, "o de ontem")
    fresh = await memory.publish_branch("dev/pedido-1", BASE, {"a.md": "x\n"}, "hoje", fresh=True)
    assert [(c.sha, c.parent) for c in memory.branches["dev/pedido-1"]] == [(fresh, BASE)]


async def test_o_pr_o_estado_e_o_ci(tmp_path: Path) -> None:
    api = FakeApi()
    host = _host(api, _key(tmp_path))
    pull = await host.open_pull_request("dev/pedido-1", "Pedido 1: Briefing", "corpo")
    assert (pull.number, pull.state, pull.branch) == (12, "open", "dev/pedido-1")
    opened = next(b for m, p, b in api.calls if m == "POST" and p.endswith("/pulls"))
    assert opened == {
        "title": "Pedido 1: Briefing",
        "head": "dev/pedido-1",
        "base": "main",
        "body": "corpo",
    }
    now = await host.pull_request(12)
    assert (now.state, now.ci) == ("merged", "failure")
    with pytest.raises(CodeHostError, match="404"):
        await host.pull_request(99)
    # O CI de um commit qualquer, para o supervisor (a parte 5 do M25); sem verificação, None.
    assert await host.commit_ci("c" * 40) == "failure"
    with pytest.raises(CodeHostError, match="404"):
        await host.commit_ci("d" * 40)


async def test_o_ramo_com_pr_aberto_devolve_o_mesmo(tmp_path: Path) -> None:
    api = FakeApi(open_pulls=1)
    host = _host(api, _key(tmp_path))
    pull = await host.open_pull_request("dev/pedido-1", "Pedido 1", "corpo")
    assert pull.number == 12
    assert not [p for m, p, _ in api.calls if m == "POST" and p.endswith("/pulls")]
    listed = next(c for c in api.calls if c[0] == "GET" and c[1].endswith("/pulls"))
    assert listed[1] == "/repos/campilho/campsverso/pulls"


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), "-c", "user.name=T", "-c", "user.email=t@t", *args],
        check=True,
        capture_output=True,
        text=True,
    ).stdout


async def test_os_arquivos_da_entrega_saem_do_patch_sobre_a_base(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "fica.md").write_text("um\n")
    (repo / "sai.md").write_text("tchau\n")
    (repo / "velho.md").write_text("nome velho\n")
    subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)
    _git(repo, "add", "-A")
    _git(repo, "-c", "commit.gpgsign=false", "commit", "-q", "-m", "base")
    base = _git(repo, "rev-parse", "HEAD").strip()
    (repo / "fica.md").write_text("um\ndois\n")
    (repo / "sai.md").unlink()
    (repo / "novo.md").write_text("novo\n")
    (repo / "velho.md").rename(repo / "renomeado.md")
    _git(repo, "add", "-A")
    patch = _git(repo, "diff", "--cached", base)
    assert "rename from" in patch  # o git do dev junta o renomeado; o publicador separa
    _git(repo, "reset", "-q", "--hard", base)  # o repositório volta à base: o patch é que conta
    files = await files_after_patch(repo, base, patch)
    assert files == {
        "fica.md": "um\ndois\n",
        "novo.md": "novo\n",
        "renomeado.md": "nome velho\n",
        "sai.md": None,
        "velho.md": None,
    }
    assert (repo / "fica.md").read_text() == "um\n"  # o repositório não mudou
    assert await files_after_patch(repo, base, "") == {}
    with pytest.raises(CodeHostError, match="git apply"):
        await files_after_patch(repo, base, "diff --git a/x b/x\nlixo\n")


async def test_o_github_que_responde_sem_json_ou_cai_vira_codehost_error(tmp_path: Path) -> None:
    """Um 502 do GitHub com o corpo vazio derrubou o publicador do sandbox em 21/nov: agora é um
    `CodeHostError`, como a rede que cai, e o vigia tenta de novo na volta seguinte."""

    def answer(request: httpx2.Request) -> httpx2.Response:
        path = request.url.path
        if path.endswith("/access_tokens"):
            return httpx2.Response(201, json={"token": "t"})
        if path.endswith(f"/commits/{'e' * 40}/check-runs"):
            return httpx2.Response(502, text="")
        if path.endswith(f"/commits/{'f' * 40}/check-runs"):
            raise httpx2.ConnectError("sem rede", request=request)
        return httpx2.Response(200, text="<html>não é json</html>")

    client = httpx2.AsyncClient(
        base_url="https://api.github.com", transport=httpx2.MockTransport(answer)
    )
    app = GitHubApp(5854989, 7, _key(tmp_path), client, now=lambda: 1_795_000_000.0)
    host = GitHubCodeHost("campilho/campsverso", app, client)
    with pytest.raises(CodeHostError, match="502"):
        await host.commit_ci("e" * 40)
    with pytest.raises(CodeHostError, match="ConnectError"):
        await host.commit_ci("f" * 40)
    with pytest.raises(CodeHostError, match="não é JSON"):
        await host.commit_ci("a" * 40)
