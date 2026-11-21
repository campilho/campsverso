"""A porta do repositório de fora (ADR-0083): onde o PR do dev vive, o GitHub no escritório vivo.

Quem a usa é o publicador e o vigia do GitHub, processos nossos; o modelo nunca a vê. O
publicador põe a entrega do dev num ramo e abre o PR; o vigia lê o estado de cada PR aberto. Nada
aqui mescla nem toca no ramo principal: só o humano mescla, no GitHub.

Os arquivos de um commit são o estado inteiro do que o dev mudou contra a base: o texto de cada
arquivo, ou `None` para um arquivo apagado. No ramo de um pedido devolvido, o commit novo vai
sobre o topo do ramo, e o PR acompanha.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal, Protocol

type PullRequestState = Literal["open", "merged", "closed"]
type CiState = Literal["pending", "success", "failure"]


class CodeHostError(Exception):
    """O repositório de fora recusou ou não respondeu."""


@dataclass(frozen=True, slots=True)
class PullRequest:
    """Um PR como o repositório de fora o mostra agora."""

    number: int
    url: str
    branch: str
    head: str  # o commit do topo do ramo
    state: PullRequestState
    ci: CiState | None  # None: nenhuma verificação no topo ainda


class CodeHostPort(Protocol):
    async def publish_branch(
        self,
        branch: str,
        base: str,
        files: Mapping[str, str | None],
        message: str,
        *,
        fresh: bool = False,
    ) -> str:
        """Um commit com os arquivos mudados contra `base`, no ramo `branch`: cria o ramo sobre a
        base, ou avança o que já existe (o pedido devolvido e refeito, no mesmo PR). Com `fresh`, o
        commit vai sobre a base e reescreve o ramo que já existia: um pedido sem PR aberto começa do
        `main`, e não da ponta de um ramo velho com o mesmo nome (o PR #3, 21/nov). Devolve o
        commit novo."""
        ...

    async def open_pull_request(self, branch: str, title: str, body: str) -> PullRequest:
        """Abre o PR do ramo contra o ramo principal. Se o ramo já tem um PR aberto, devolve esse:
        depois de uma queda, o publicador refaz a entrega sem abrir outro."""
        ...

    async def pull_request(self, number: int) -> PullRequest:
        """O estado de agora: aberto, mesclado ou fechado, o topo e o CI do topo."""
        ...

    async def comment(self, number: int, body: str) -> None:
        """Um comentário na conversa do PR (o revisor, na parte 3 do M25)."""
        ...

    async def commit_ci(self, sha: str) -> CiState | None:
        """O CI de um commit qualquer, como o de um topo de PR: o supervisor só troca o escritório
        vivo para um commit verde (a parte 5 do M25). None: nenhuma verificação ainda."""
        ...
