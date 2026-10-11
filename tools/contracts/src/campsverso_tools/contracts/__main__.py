"""CLI dos contratos: `python -m campsverso_tools.contracts {check,codegen,compat}`."""

import argparse
import sys
from pathlib import Path

from campsverso_tools.contracts import catalog, checks
from campsverso_tools.contracts.validation import Problem


def _report(title: str, problems: list[Problem]) -> int:
    if not problems:
        return 0
    print(f"{title}: {len(problems)} problema(s)", file=sys.stderr)
    for problem in problems:
        print(f"  {problem}", file=sys.stderr)
    return 1


def _check(contracts: catalog.Contracts) -> int:
    conventions = checks.check_conventions(contracts)
    if _report("convenções", conventions):
        return 1
    if _report("exemplos", checks.check_examples(contracts)):
        return 1
    examples = contracts.examples_dir
    print(
        f"contratos ok: {len(contracts.by_type)} tipos, "
        f"{len(list((examples / 'valid').glob('*.json')))} exemplos válidos, "
        f"{len(list((examples / 'invalid').glob('*.json')))} inválidos recusados"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="campsverso_tools.contracts")
    parser.add_argument(
        "--root", type=Path, default=Path.cwd(), help="ponto de partida para achar contracts/"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("check", help="meta-schema, convenções e exemplos")
    args = parser.parse_args(argv)

    contracts = catalog.load(catalog.find_contracts_dir(args.root.resolve()))
    match args.command:
        case "check":
            return _check(contracts)
        case _:
            parser.error(f"comando desconhecido: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
