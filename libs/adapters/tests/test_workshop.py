"""A oficina local (ADR-0080; o plano do M24, §3): o clone isolado, as ferramentas com os limites,
os caminhos que escapam recusados, os testes sem rede e sem escrita fora, e o patch revisado."""

import socket
import subprocess
import sys
from pathlib import Path

import pytest

from campsverso_adapters.workshop_local import LocalWorkshop
from campsverso_adapters.workshop_review import review

GIT = [
    "git",
    "-c",
    "user.name=Teste",
    "-c",
    "user.email=teste@exemplo",
    "-c",
    "commit.gpgsign=false",
]


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """Um repositório de exemplo, com um commit, e um `.env` fora do git."""
    root = tmp_path / "repo"
    (root / "tools").mkdir(parents=True)
    (root / "tools" / "soma.py").write_text("def soma(a, b):\n    return a + b\n")
    (root / "README.md").write_text("Um repositório de exemplo.\n")
    (root / ".gitignore").write_text(".env\n__pycache__/\n")
    subprocess.run(["git", "init", "-q", "-b", "main", str(root)], check=True)
    subprocess.run([*GIT, "-C", str(root), "add", "-A"], check=True)
    subprocess.run([*GIT, "-C", str(root), "commit", "-q", "-m", "base"], check=True)
    (root / ".env").write_text("SEGREDO=nao\n")
    return root


def _workshop(repo: Path, tmp_path: Path, *, sandbox: bool = False) -> LocalWorkshop:
    return LocalWorkshop(
        repo, tmp_path / "oficina", python_env=False, python=Path(sys.executable), sandbox=sandbox
    )


async def test_o_clone_e_isolado_e_as_ferramentas_leem_e_escrevem(
    repo: Path, tmp_path: Path
) -> None:
    space = await _workshop(repo, tmp_path).open("office-teste", "pedido-001")
    head = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True, check=True
    ).stdout.strip()
    assert space.base == head
    assert not (space.root / ".env").exists()  # fora do git, fora do espaço
    assert (space.root / ".git").is_dir()  # o próprio .git
    listing = await space.list_files()
    assert listing.text.splitlines() == [".gitignore", "README.md", "tools/soma.py"]
    read = await space.read("tools/soma.py")
    assert "    1| def soma(a, b):" in read.text
    assert read.summary == "lendo tools/soma.py (1-2)"
    found = await space.search(r"return", "tools")
    assert found.text == "tools/soma.py:2: return a + b"
    wrote = await space.write("tools/dobro.py", "def dobro(x):\n    return 2 * x\n")
    assert wrote.ok
    edited = await space.edit("tools/soma.py", "a + b", "b + a")
    assert edited.ok
    twice = await space.edit("tools/dobro.py", "x", "y")
    assert not twice.ok
    assert "aparece" in twice.text
    patch = await space.patch()
    assert patch.summary.files == ("tools/dobro.py", "tools/soma.py")
    assert (patch.summary.added, patch.summary.removed) == (3, 1)
    assert "+def dobro(x):" in patch.text
    diff = await space.diff()
    assert diff.summary == "vendo as mudanças: 2 arquivo(s), +3 -1"
    again = await _workshop(repo, tmp_path).open("office-teste", "pedido-001")
    assert (again.root / "tools" / "dobro.py").exists()  # o dev volta ao pedido
    await _workshop(repo, tmp_path).close("office-teste", "pedido-001")
    assert not space.root.exists()


async def test_o_caminho_que_sai_do_espaco_e_recusado(repo: Path, tmp_path: Path) -> None:
    space = await _workshop(repo, tmp_path).open("office-teste", "pedido-002")
    (space.root / "atalho").symlink_to(repo)
    for path in ("../repo/README.md", "/etc/hosts", "atalho/.env", ".git/config"):
        assert not (await space.read(path)).ok, path
        assert not (await space.write(path, "x")).ok, path
    assert not (repo / "x").exists()
    assert (await space.write("muito.txt", "x\n" * 2001)).ok is False


async def test_os_testes_rodam_e_resumem(repo: Path, tmp_path: Path) -> None:
    space = await _workshop(repo, tmp_path).open("office-teste", "pedido-003")
    await space.write(
        "tests/test_soma.py",
        "from tools.soma import soma\n\n"
        "def test_soma():\n    assert soma(1, 2) == 3\n\n"
        "def test_errado():\n    assert soma(1, 1) == 3\n",
    )
    await space.write("tests/__init__.py", "")
    await space.write("tools/__init__.py", "")
    result = await space.run_tests("tests")
    assert not result.ok
    assert result.summary == "rodando os testes: 1 falharam, 1 passaram"
    assert "FAILED tests/test_soma.py::test_errado" in result.text


@pytest.mark.skipif(sys.platform != "darwin", reason="o sandbox-exec é do macOS")
async def test_os_testes_nao_tem_rede_nem_escrevem_fora(repo: Path, tmp_path: Path) -> None:
    server = socket.socket()
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    port = server.getsockname()[1]
    outside = tmp_path / "fora.txt"
    space = await _workshop(repo, tmp_path, sandbox=True).open("office-teste", "pedido-004")
    await space.write(
        "tests/test_fuga.py",
        "import socket\nfrom pathlib import Path\n\n"
        f"def test_rede():\n    socket.create_connection(('127.0.0.1', {port}), timeout=2)\n\n"
        f"def test_escrever_fora():\n    Path({str(outside)!r}).write_text('x')\n\n"
        "def test_escrever_dentro(tmp_path):\n    (tmp_path / 'a.txt').write_text('ok')\n",
    )
    result = await space.run_tests("tests/test_fuga.py")
    server.close()
    assert result.summary == "rodando os testes: 2 falharam, 1 passaram", result.text
    assert not outside.exists()


async def test_o_robo_da_bancada_roda_um_modulo_com_argumentos(repo: Path, tmp_path: Path) -> None:
    """O plano do M24, §4: `python -m <módulo> <argumentos>` no espaço, e a saída de volta."""
    space = await _workshop(repo, tmp_path).open("office-teste", "pedido-010")
    await space.write("tools/__init__.py", "")
    await space.write(
        "tools/eco.py",
        "import sys\n\nprint('robô:', ' '.join(sys.argv[1:]))\n"
        "sys.exit(1 if 'falhe' in sys.argv else 0)\n",
    )
    ok = await space.run_robot("tools.eco", ["tools/soma.py", "tests"])
    assert ok.ok
    assert ok.summary == "chamando o robô tools.eco: saída 0"
    assert "robô: tools/soma.py tests" in ok.text
    failed = await space.run_robot("tools.eco", ["falhe"])
    assert (failed.ok, failed.summary) == (False, "chamando o robô tools.eco: saída 1")
    assert not (await space.run_robot("tools.nada")).ok  # o módulo não existe
    refused = await space.run_robot("tools.eco; rm -rf /")
    assert (refused.ok, refused.summary) == (False, "chamando o robô tools.eco; rm -rf /: recusado")
    assert not (await space.run_robot("tools.eco", ["x" * 400])).ok


@pytest.mark.skipif(sys.platform != "darwin", reason="o sandbox-exec é do macOS")
async def test_o_robo_nao_tem_rede_nem_escreve_fora(repo: Path, tmp_path: Path) -> None:
    server = socket.socket()
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    port = server.getsockname()[1]
    outside = tmp_path / "fora-robo.txt"
    space = await _workshop(repo, tmp_path, sandbox=True).open("office-teste", "pedido-011")
    await space.write("tools/__init__.py", "")
    await space.write(
        "tools/fuga.py",
        "import socket\nfrom pathlib import Path\n\n"
        "try:\n"
        f"    socket.create_connection(('127.0.0.1', {port}), timeout=2)\n"
        "    print('rede: sim')\n"
        "except OSError:\n"
        "    print('rede: não')\n"
        "try:\n"
        f"    Path({str(outside)!r}).write_text('x')\n"
        "    print('fora: sim')\n"
        "except OSError:\n"
        "    print('fora: não')\n",
    )
    result = await space.run_robot("tools.fuga")
    server.close()
    assert "rede: não" in result.text, result.text
    assert "fora: não" in result.text, result.text
    assert not outside.exists()


def test_a_revisao_recusa_a_constituicao_os_testes_e_as_palavras() -> None:
    def diff(path: str, *added: str, removed: tuple[str, ...] = (), mode: str = "") -> str:
        head = f"diff --git a/{path} b/{path}\n{mode}--- a/{path}\n+++ b/{path}\n@@ -1 +1 @@\n"
        return head + "".join(f"-{r}\n" for r in removed) + "".join(f"+{a}\n" for a in added)

    assert review(diff("tools/robos/testador.py", "def rodar():", "    pass")) == []
    assert review(diff("CLAUDE.md", "x")) == ["CLAUDE.md: a constituição não muda pela oficina"]
    assert review(diff("contracts/events/a.json", "{}"))[0].startswith("contracts/")
    assert review(diff("docs/decisoes/0080-x.md", "x")) == [
        "docs/decisoes/0080-x.md: uma ADR aceita não muda"
    ]
    assert review(diff("docs/decisoes/0090-novo.md", "x", mode="new file mode 100644\n")) == []
    deleted = diff("tests/test_a.py", removed=("def test_a():",), mode="deleted file mode 100644\n")
    assert review(deleted) == ["tests/test_a.py: um teste apagado"]
    fewer = diff("tools/tests/test_b.py", "x = 1", removed=("def test_b():",))
    assert review(fewer) == ["tools/tests/test_b.py: 1 teste(s) a menos"]
    skip = diff("tools/c.py", "import os  # noqa: F401")
    assert review(skip) == ["tools/c.py: desliga uma verificação (noqa)"]
    words = review(diff("tools/d.py", "nome = 'Palavrona'"), ["palavrona"])
    assert words == ["tools/d.py: tem uma palavra da lista proibida"]


async def test_a_raiz_relativa_vira_absoluta(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """O sandbox passa a pasta de dados relativa: o espaço fica nela, e não aninhado."""
    monkeypatch.chdir(tmp_path)
    shop = LocalWorkshop(repo, Path("dados/oficina"), python_env=False, python=Path(sys.executable))
    space = await shop.open("office-teste", "pedido-009")
    assert space.root == (tmp_path / "dados/oficina/office-teste/pedido-009").resolve()
    assert (space.root / "README.md").exists()
