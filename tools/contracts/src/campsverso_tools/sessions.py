"""Tempo e tokens de cada turno das sessões do Claude Code neste projeto (ADR-0051, decisão 7).

    uv run python -m campsverso_tools.sessions [--marco M5]   # ou: make sessoes MARCO=M5

Lê o histórico das sessões (`~/.claude/projects/<projeto>/*.jsonl`) só para tirar números e grava
em `docs/custos/`:

- `sessoes.csv`: uma linha por turno (sessão, início, fim, minutos ativos, chamadas e tokens) e o
  marco. Rodar de novo atualiza as linhas que já existem e acrescenta as novas, com o marco de
  `--marco`; o marco de uma linha já gravada não muda.
- `README.md`: os totais por marco e o uso do plano anotado em `plano.csv` ao fechar cada marco.

O texto das conversas nunca sai do histórico: aqui só entram horários e contagens.
"""

import argparse
import csv
import json
import sys
from collections.abc import Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass, fields
from datetime import datetime
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[4]
OUT = REPO / "docs" / "custos"
IDLE_SECONDS = 300  # esperas maiores (aprovação, pausa) não contam como tempo ativo
COMMAND_MARKERS = ("<command-name>", "<local-command", "<system-reminder>")


@dataclass
class Turn:
    sessao: str
    inicio: str
    fim: str
    minutos_ativos: float
    chamadas: int
    entrada: int
    saida: int
    cache_lido: int
    cache_escrito: int
    marco: str = ""

    @property
    def key(self) -> tuple[str, str]:
        return self.sessao, self.inicio


COLUMNS = [f.name for f in fields(Turn)]


def transcripts_dir(repo: Path = REPO) -> Path:
    """Onde o Claude Code guarda as sessões deste projeto: o caminho com `/` trocado por `-`."""
    return Path.home() / ".claude" / "projects" / str(repo).replace("/", "-")


def _when(stamp: str) -> datetime:
    return datetime.fromisoformat(stamp.replace("Z", "+00:00"))


def _local(moment: datetime) -> str:
    return moment.astimezone().isoformat(timespec="minutes")


def _is_prompt(entry: Mapping[str, Any]) -> bool:
    """Um pedido de quem usa: texto digitado, não resultado de ferramenta nem aviso do sistema."""
    if entry.get("type") != "user" or entry.get("isMeta") or entry.get("isCompactSummary"):
        return False
    content = entry.get("message", {}).get("content")
    if isinstance(content, list):
        parts: list[Mapping[str, Any]] = [p for p in content if isinstance(p, dict)]  # pyright: ignore[reportUnknownVariableType]
        if any(p.get("type") == "tool_result" for p in parts):
            return False
        content = " ".join(str(p.get("text", "")) for p in parts if p.get("type") == "text")
    text = str(content or "").lstrip()
    return bool(text) and not text.startswith(COMMAND_MARKERS)


def turns(path: Path) -> list[Turn]:
    """Os turnos de uma sessão: de um pedido até a última resposta antes do pedido seguinte."""
    result: list[Turn] = []
    seen: set[str] = set()
    last: datetime | None = None
    active = 0.0
    current: Turn | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        entry: dict[str, Any] = json.loads(line)
        stamp = entry.get("timestamp")
        if not isinstance(stamp, str):
            continue
        moment = _when(stamp)
        if _is_prompt(entry):
            if current is not None:
                current.minutos_ativos = round(active / 60, 1)
            current = Turn(path.stem[:8], _local(moment), _local(moment), 0.0, 0, 0, 0, 0, 0)
            result.append(current)
            last, active = moment, 0.0
            continue
        if current is None or entry.get("type") not in ("assistant", "user"):
            continue
        if last is not None and (gap := (moment - last).total_seconds()) <= IDLE_SECONDS:
            active += max(gap, 0.0)
        last = moment
        if entry.get("type") != "assistant":
            continue
        message: Mapping[str, Any] = entry.get("message", {})
        current.fim = _local(moment)
        call = str(message.get("id") or entry.get("requestId") or "")
        if call in seen:
            continue  # uma chamada aparece uma vez por bloco de conteúdo
        seen.add(call)
        usage: Mapping[str, Any] = message.get("usage", {})
        current.chamadas += 1
        current.entrada += int(usage.get("input_tokens", 0))
        current.saida += int(usage.get("output_tokens", 0))
        current.cache_lido += int(usage.get("cache_read_input_tokens", 0))
        current.cache_escrito += int(usage.get("cache_creation_input_tokens", 0))
    if current is not None:
        current.minutos_ativos = round(active / 60, 1)
    return result


def read_csv(path: Path) -> list[Turn]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return [
            Turn(
                row["sessao"],
                row["inicio"],
                row["fim"],
                float(row["minutos_ativos"]),
                int(row["chamadas"]),
                int(row["entrada"]),
                int(row["saida"]),
                int(row["cache_lido"]),
                int(row["cache_escrito"]),
                row["marco"],
            )
            for row in csv.DictReader(handle)
        ]


def merge(saved: Iterable[Turn], fresh: Iterable[Turn], marco: str = "") -> list[Turn]:
    """Números novos para os turnos conhecidos (um turno pode ter crescido); o marco fica."""
    by_key = {t.key: t for t in saved}
    for turn in fresh:
        known = by_key.get(turn.key)
        turn.marco = known.marco if known is not None and known.marco else marco
        by_key[turn.key] = turn
    return sorted(by_key.values(), key=lambda t: t.inicio)


def write_csv(path: Path, rows: Sequence[Turn]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(COLUMNS)
        for t in rows:
            writer.writerow([getattr(t, c) for c in COLUMNS])


# ---------------------------------------------------------------- resumo


def _groups(rows: Sequence[Turn]) -> Iterator[tuple[str, list[Turn]]]:
    order: list[str] = []
    for t in rows:
        if (t.marco or "?") not in order:
            order.append(t.marco or "?")
    for marco in order:
        yield marco, [t for t in rows if (t.marco or "?") == marco]


def _millions(value: int) -> str:
    return f"{value / 1e6:.1f}".replace(".", ",")


def _thousands(value: int) -> str:
    return f"{value / 1e3:,.0f}".replace(",", ".")


def summary(rows: Sequence[Turn]) -> list[list[str]]:
    table: list[list[str]] = []
    for marco, group in _groups(rows):
        table.append(
            [
                marco,
                str(len(group)),
                f"{sum(t.minutos_ativos for t in group):.0f}",
                str(sum(t.chamadas for t in group)),
                _thousands(sum(t.saida for t in group)),
                _millions(sum(t.cache_lido for t in group)),
                _thousands(sum(t.cache_escrito for t in group)),
            ]
        )
    return table


HEADER = ["Marco", "Turnos", "Min. ativos", "Chamadas", "Saída (mil)", "Cache lido (mi)",
          "Cache escrito (mil)"]  # fmt: skip


def _markdown(header: Sequence[str], table: Sequence[Sequence[str]]) -> list[str]:
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    lines += ["| " + " | ".join(row) + " |" for row in table]
    return lines


def readme(rows: Sequence[Turn], plan: Path) -> str:
    lines = [
        "# Custos de desenvolvimento",
        "",
        "GERADO por `make sessoes` a partir de `sessoes.csv` e `plano.csv`: não editar à mão.",
        "",
        "Tempo e tokens do Claude Code em cada marco (ADR-0051).",
        "",
        f"- **Minutos ativos** descontam as esperas de mais de {IDLE_SECONDS // 60} minutos entre",
        "  uma chamada e outra (aprovações e pausas).",
        "- **Saída** são os tokens escritos pelo modelo.",
        "- **Cache lido** é o contexto relido a cada chamada: fica em cache e custa bem menos.",
        "- Só números: o texto das conversas nunca entra aqui.",
        "",
        "## Por marco",
        "",
        *_markdown(HEADER, summary(rows)),
    ]
    if plan.exists():
        with plan.open(encoding="utf-8", newline="") as handle:
            records = list(csv.reader(handle))
        if len(records) > 1:
            lines += [
                "",
                "## Uso do plano Max",
                "",
                "Anotado ao fechar cada marco, como o app mostra: a janela de 5 horas e a semana.",
                "",
                *_markdown(records[0], records[1:]),
            ]
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="campsverso_tools.sessions")
    parser.add_argument("--marco", default="", help="marco dos turnos novos, ex.: M5")
    parser.add_argument("--dir", type=Path, help="pasta das sessões (padrão: a do Claude Code)")
    parser.add_argument("--out", type=Path, default=OUT, help="pasta de saída (docs/custos)")
    args = parser.parse_args(argv)
    folder: Path = args.dir or transcripts_dir()
    fresh = [t for path in sorted(folder.glob("*.jsonl")) for t in turns(path)]
    rows = merge(read_csv(args.out / "sessoes.csv"), fresh, args.marco)
    write_csv(args.out / "sessoes.csv", rows)
    (args.out / "README.md").write_text(readme(rows, args.out / "plano.csv"), encoding="utf-8")
    for line in _markdown(HEADER, summary(rows)):
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
