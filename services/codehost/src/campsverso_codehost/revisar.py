"""O revisor de outra família de novo, à mão, num PR do dev (ADR-0083, parte 3 do M25).

    make revisar PR=N [DADOS=../campsverso-vivo/dados]

É uma raiz de composição, como o `main.py`. Ela lê o estado do publicador (só lê: quem escreve nele
é o serviço que está rodando), acha o pedido e a última entrega publicada no PR, revisa com os
modelos do mundo, na mesma fita, e comenta no PR pelo App. Serve para quando a revisão automática
falhou nos dois modelos, ou para ver de novo um PR que o dev refez.
"""

import argparse
import asyncio
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, cast

from campsverso_adapters import (
    DiskBlobStore,
    GitHubCodeHost,
    JsonTelemetry,
    SystemWallClock,
    load_env,
    load_world,
)
from campsverso_codehost.main import reviewer_for
from campsverso_codehost.reviewer import ReviewInput, comment_body


def _parse(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="campsverso_codehost.revisar")
    parser.add_argument("--pr", type=int, required=True, help="o número do PR")
    parser.add_argument("--env", type=Path, default=Path("config/env/local.yaml"))
    parser.add_argument(
        "--world", type=Path, default=Path("config/worlds/office-campsverso-02.yaml")
    )
    parser.add_argument("--data-dir", type=Path, help="a pasta de dados do mundo (o vivo)")
    parser.add_argument("--dry-run", action="store_true", help="imprime o comentário, sem postar")
    return parser.parse_args(argv)


def find(saved: Mapping[str, Any], pull_request: int) -> tuple[str, Mapping[str, Any]] | None:
    """O pedido e a última entrega publicada no PR, pelo estado do publicador."""
    published = cast(Mapping[str, Mapping[str, Any]], saved.get("published") or {})
    for ticket_id, item in sorted(published.items()):
        if int(item["pull_request"]) == pull_request:
            return ticket_id, item
    return None


async def run(args: argparse.Namespace) -> int:
    telemetry = JsonTelemetry("revisar")
    env, world = load_env(args.env), load_world(args.world)
    settings = world.codehost
    if settings is None or env.workshop is None or not settings.reviewers:
        print("o mundo não tem `codehost.reviewers`", file=sys.stderr)
        return 2
    data_dir: Path = args.data_dir or env.data_dir
    state = data_dir / "codehost" / world.worldid / "codehost.json"
    if not state.is_file():
        print(f"sem o estado do publicador em {state}", file=sys.stderr)
        return 2
    saved = cast(Mapping[str, Any], json.loads(state.read_text(encoding="utf-8")))
    found = find(saved, args.pr)
    if found is None:
        print(f"o PR #{args.pr} não tem entrega publicada em {state}", file=sys.stderr)
        return 2
    ticket_id, item = found
    tickets = cast(Mapping[str, Mapping[str, Any]], saved.get("tickets") or {})
    ticket = tickets.get(ticket_id) or {}
    deliveries = env.workshop.deliveries if args.data_dir is None else data_dir / "entregas"
    diff = DiskBlobStore(deliveries).get(str(item["ref"])).decode("utf-8")
    clock = SystemWallClock()
    tape = data_dir / "codehost" / world.worldid / "revisor.jsonl"
    built = reviewer_for(settings.reviewers, env, tape, clock, telemetry, Path.cwd())
    if built is None:
        return 2
    reviewer, ports = built
    given = ReviewInput(
        int(ticket.get("number") or 0),
        str(ticket.get("title") or ticket_id),
        str(ticket.get("description") or ""),
        str(ticket.get("acceptance") or ""),
        diff,
        str(item["head"]),
    )
    try:
        result = await reviewer.review(given)
    finally:
        await ports.aclose()
    if result is None:
        print("nenhum modelo respondeu", file=sys.stderr)
        return 1
    body = comment_body(result, given)
    print(body)
    words_file = env.workshop.forbidden_words
    words: list[str] = []
    if words_file is not None and words_file.is_file():
        lines = words_file.read_text(encoding="utf-8").splitlines()
        words = [w.strip().lower() for w in lines if w.strip()]
    if any(word in body.lower() for word in words):
        print("o comentário tem uma palavra da lista proibida: não sai", file=sys.stderr)
        return 1
    if args.dry_run:
        return 0
    if settings.host != "github" or settings.key is None:
        print("o mundo não fala com o GitHub", file=sys.stderr)
        return 2
    assert settings.app_id is not None
    assert settings.installation_id is not None
    host = GitHubCodeHost.connect(
        settings.repo, settings.app_id, settings.installation_id, settings.key
    )
    try:
        await host.comment(args.pr, body)
    finally:
        await host.aclose()
    telemetry.info("revisar.commented", pull_request=args.pr, model=result.model)
    return 0


def main() -> None:
    sys.exit(asyncio.run(run(_parse(sys.argv[1:]))))


if __name__ == "__main__":
    main()
