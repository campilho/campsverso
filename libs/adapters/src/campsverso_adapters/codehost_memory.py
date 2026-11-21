"""O GitHub falso, em memória (ADR-0083): os testes, o soak e o sandbox sem a chave do App.

Guarda os ramos, com os arquivos de cada commit, e os PRs. Os commits têm um hash de 40
caracteres tirado do que eles levam, igual a cada vez, para os testes e o replay. Os testes mesclam,
fecham e mudam o CI à mão.
"""

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, field, replace

from campsverso_ports import CiState, CodeHostError, PullRequest

URL = "https://github.com/exemplo/campsverso/pull/{number}"


@dataclass
class Commit:
    sha: str
    parent: str
    files: dict[str, str | None]
    message: str


@dataclass
class MemoryCodeHost:
    branches: dict[str, list[Commit]] = field(default_factory=dict[str, list[Commit]])
    pulls: dict[int, PullRequest] = field(default_factory=dict[int, PullRequest])
    titles: dict[int, str] = field(default_factory=dict[int, str])
    bodies: dict[int, str] = field(default_factory=dict[int, str])
    comments: dict[int, list[str]] = field(default_factory=dict[int, list[str]])
    commit_cis: dict[str, CiState] = field(default_factory=dict[str, CiState])

    async def publish_branch(
        self, branch: str, base: str, files: Mapping[str, str | None], message: str
    ) -> str:
        commits = self.branches.setdefault(branch, [])
        parent = commits[-1].sha if commits else base
        body = json.dumps([branch, parent, dict(sorted(files.items())), message])
        sha = hashlib.sha1(body.encode()).hexdigest()
        commits.append(Commit(sha, parent, dict(files), message))
        return sha

    async def open_pull_request(self, branch: str, title: str, body: str) -> PullRequest:
        if not self.branches.get(branch):
            raise CodeHostError(f"o ramo {branch} não existe")
        for pull in self.pulls.values():
            if pull.branch == branch and pull.state == "open":
                return await self.pull_request(pull.number)  # o aberto, de novo: o mesmo PR
        number = len(self.pulls) + 1
        head = self.branches[branch][-1].sha
        pull = PullRequest(number, URL.format(number=number), branch, head, "open", None)
        self.pulls[number] = pull
        self.titles[number], self.bodies[number] = title, body
        return pull

    async def pull_request(self, number: int) -> PullRequest:
        pull = self._pull(number)
        head = self.branches[pull.branch][-1].sha
        if head != pull.head:
            pull = self.pulls[number] = replace(pull, head=head, ci=None)
        return pull

    async def comment(self, number: int, body: str) -> None:
        self._pull(number)
        self.comments.setdefault(number, []).append(body)

    async def commit_ci(self, sha: str) -> CiState | None:
        return self.commit_cis.get(sha)

    # ------------------------------------------------------------- o que os testes fazem à mão

    def merge(self, number: int) -> None:
        self.pulls[number] = replace(self._pull(number), state="merged")

    def close(self, number: int) -> None:
        self.pulls[number] = replace(self._pull(number), state="closed")

    def set_ci(self, number: int, ci: CiState) -> None:
        self.pulls[number] = replace(self._pull(number), ci=ci)

    def _pull(self, number: int) -> PullRequest:
        if number not in self.pulls:
            raise CodeHostError(f"o PR #{number} não existe")
        return self.pulls[number]
