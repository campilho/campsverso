"""`make aplicar PEDIDO=N` (ADR-0080; o plano do M24, §3.5): a entrega do dev num ramo.

    uv run python -m campsverso_testkit.aplicar --pedido 1 [--world config/worlds/<mundo>.yaml]
        [--data-dir data/sandbox/<pasta>/data]

Pega o patch mais recente do pedido no depósito de entregas, confere de novo (a constituição, os
testes e a lista de palavras proibidas), cria o ramo `dev/pedido-N` a partir do commit de onde o
espaço de trabalho saiu, aplica o patch e faz o commit nele, numa worktree temporária: o checkout
de quem roda não muda. O humano revisa, roda o `make check` e decide se junta.
"""

import argparse
import json
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path
from typing import Any, cast

from campsverso_adapters import load_env, load_world
from campsverso_adapters.workshop_review import review

REPO = Path(__file__).resolve().parents[4]
ENV = REPO / "config" / "env" / "local.yaml"


def _git(*args: str, cwd: Path = REPO) -> str:
    done = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=False)
    if done.returncode != 0:
        raise SystemExit(f"git {' '.join(args)}: {done.stderr.strip() or done.stdout.strip()}")
    return done.stdout


def latest(deliveries: Path, worldid: str, number: int) -> tuple[Path, dict[str, object]]:
    """O patch mais recente do pedido e o resumo dele."""
    folder = deliveries / worldid / f"pedido-{number:03d}"
    patches = sorted(folder.glob("*.patch"), key=lambda p: p.stat().st_mtime)
    if not patches:
        raise SystemExit(f"nenhuma entrega do pedido {number} em {folder}")
    patch = patches[-1]
    return patch, json.loads(patch.with_suffix(".json").read_text(encoding="utf-8"))


def apply(
    patch: Path, about: dict[str, object], number: int, words: Sequence[str], repo: Path = REPO
) -> str:
    """Confere, cria o ramo e aplica; devolve o nome do ramo. Se algo falha, o ramo sai."""
    patch = patch.resolve()  # o git apply roda dentro da worktree temporária
    text = patch.read_text(encoding="utf-8")
    reasons = review(text, words)
    if reasons:
        raise SystemExit("a entrega não passa na revisão:\n- " + "\n- ".join(reasons))
    branch = f"dev/pedido-{number}"
    if _git("branch", "--list", branch, cwd=repo).strip():
        raise SystemExit(f"o ramo {branch} já existe: apague-o (git branch -D {branch}) ou junte-o")
    base = str(about["base"])
    with tempfile.TemporaryDirectory(prefix="aplicar-") as temp:
        where = Path(temp) / "ramo"
        _git("worktree", "add", "--quiet", "-b", branch, str(where), base, cwd=repo)
        committed = False
        try:
            _git("apply", "--whitespace=nowarn", str(patch), cwd=where)
            _git("add", "-A", cwd=where)
            message = (
                f"feat: o pedido {number} do escritório\n\n"
                f"Entregue pelo dev do escritório na oficina (ADR-0080), sobre {base[:8]}. "
                "Revise, rode o make check e junte se estiver bom."
            )
            _git("commit", "--quiet", "-m", message, cwd=where)
            committed = True
        finally:
            _git("worktree", "remove", "--force", str(where), cwd=repo)
            if not committed:
                _git("branch", "-D", branch, cwd=repo)  # nada de ramo vazio para trás
    return branch


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="campsverso_testkit.aplicar")
    parser.add_argument("--pedido", type=int, required=True, help="o número do pedido")
    parser.add_argument(
        "--world", type=Path, default=REPO / "config/worlds/office-campsverso-01.yaml"
    )
    parser.add_argument("--data-dir", type=Path, help="a pasta de dados (a de um sandbox)")
    args = parser.parse_args(argv)
    env, world = load_env(ENV, root=REPO), load_world(args.world, root=REPO)
    if env.workshop is None:
        raise SystemExit("o ambiente não tem a oficina (workshop)")
    deliveries = env.workshop.deliveries if args.data_dir is None else args.data_dir / "entregas"
    words: list[str] = []
    path = env.workshop.forbidden_words
    if path is not None and path.is_file():
        words = [w.strip() for w in path.read_text(encoding="utf-8").splitlines() if w.strip()]
    patch, about = latest(deliveries, world.worldid, args.pedido)
    branch = apply(patch, about, args.pedido, words)
    files = [str(f) for f in cast(list[Any], about.get("files") or [])]
    base = str(about["base"])[:8]
    print(f"o pedido {args.pedido} está no ramo {branch}")
    print(f"  {len(files)} arquivo(s), +{about['added']} -{about['removed']}, sobre {base}")
    for name in files:
        print(f"  - {name}")
    print(f"revise com: git diff {base} {branch}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
