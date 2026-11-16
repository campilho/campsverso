"""A porta da oficina (ADR-0055, ADR-0080): o espaço de trabalho do dev, fora do mundo.

Cada pedido do escritório ganha um espaço: um clone do repositório, isolado do de verdade. O dev o
usa pelas oito ferramentas (ver, ler, buscar, escrever, editar, rodar os testes, ver as mudanças e
pronto), e a entrega é um patch contra o commit de onde o espaço saiu. São ferramentas do
computador, e não ações do mundo: o kernel nunca as vê, e quem as chama é o controlador do dev.

Toda ferramenta recusa um caminho que sai do espaço, inclusive por link simbólico, e devolve um
texto limitado em tamanho, com um resumo de uma linha para a tela (o `workshop.step.v1`).
"""

from dataclasses import dataclass
from typing import Protocol

# As ferramentas, pelos nomes que a mente vê (o plano do M24, §3.2).
TOOLS = (
    "ver_arquivos",
    "ler",
    "buscar",
    "escrever",
    "editar",
    "rodar_testes",
    "ver_mudancas",
    "pronto",
)


@dataclass(frozen=True, slots=True)
class ToolResult:
    """O que uma ferramenta devolveu: o texto para quem a chamou e uma linha para a tela."""

    ok: bool
    text: str
    summary: str
    path: str | None = None


@dataclass(frozen=True, slots=True)
class PatchSummary:
    """O resumo de uma entrega: o commit de base, os arquivos e as linhas a mais e a menos."""

    base: str
    files: tuple[str, ...]
    added: int
    removed: int


@dataclass(frozen=True, slots=True)
class Patch:
    text: str
    summary: PatchSummary


class WorkshopError(Exception):
    """A oficina não abriu ou não fechou: o clone, o ambiente ou o disco falharam."""


class Workspace(Protocol):
    """Um espaço de trabalho aberto, de um pedido."""

    @property
    def ticket_id(self) -> str: ...

    @property
    def base(self) -> str:
        """O commit de onde o espaço saiu."""
        ...

    async def list_files(self, path: str = ".") -> ToolResult: ...

    async def read(self, path: str, start: int = 1, end: int | None = None) -> ToolResult: ...

    async def search(self, pattern: str, path: str = ".") -> ToolResult: ...

    async def write(self, path: str, content: str) -> ToolResult: ...

    async def edit(self, path: str, old: str, new: str) -> ToolResult: ...

    async def run_tests(self, path: str = ".") -> ToolResult:
        """O `pytest` de um caminho, isolado: sem rede, escrita só no espaço, sem segredos."""
        ...

    async def diff(self) -> ToolResult: ...

    async def patch(self) -> Patch:
        """O diff do espaço contra a base, com o resumo, para a entrega."""
        ...


class WorkshopPort(Protocol):
    async def open(self, worldid: str, ticket_id: str) -> Workspace:
        """Abre o espaço do pedido, ou retoma o que já existe (o dev volta a um pedido)."""
        ...

    async def close(self, worldid: str, ticket_id: str) -> None:
        """Apaga o espaço do pedido, depois da entrega aceita."""
        ...
