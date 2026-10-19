"""Métricas da bíblia §13 a partir do arquivo de eventos (ADR-0047, decisão 6).

    uv run python -m campsverso_tools.metrics data/archive/farm-camps-01 [--json]

Lê só o arquivo JSONL, como qualquer leitor externo: não importa o kernel nem os cartuchos.
O dia agrícola sai do tick (ticks por dia = 86.400 / tick_seconds da sessão), o que vale para
mundos que começam na hora em que o dia vira, como a fazenda (06:00). Os totais contam só os dias
completos: o último dia de uma execução costuma parar no meio, e as moedas dele enganam.
"""

import argparse
import gzip
import json
import statistics
import sys
from collections import Counter
from collections.abc import Iterable, Iterator, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

# Grupos de canteiros da Fazenda do Camps (bíblia §4): o leste fica perto do rio (R-001).
GROUPS = {"plot-w-": "oeste", "plot-e-": "leste"}
AVATAR = "camps"


def read_archive(folder: Path) -> Iterator[dict[str, Any]]:
    """Eventos e comandos de um mundo, de todos os dias, inclusive os comprimidos."""
    for path in sorted(folder.glob("*.jsonl*")):
        data = gzip.decompress(path.read_bytes()) if path.suffix == ".gz" else path.read_bytes()
        for line in data.splitlines():
            yield json.loads(line)


def _group(plot: str) -> str:
    return next((name for prefix, name in GROUPS.items() if plot.startswith(prefix)), "outro")


@dataclass
class DayMetrics:
    day: int
    harvests: dict[str, int] = field(default_factory=dict[str, int])
    plantings: dict[str, int] = field(default_factory=dict[str, int])  # por grupo (ADR-0061)
    matured_days: dict[str, list[int]] = field(default_factory=dict[str, list[int]])
    coins_end: int = 0
    rejections: dict[str, int] = field(default_factory=dict[str, int])
    withered: int = 0
    hunger_peak: float = 0.0
    faints: int = 0
    real_seconds: float = 0.0
    complete: bool = True
    # O modelo no dia (ADR-0059), a partir dos `llm.call.*` do arquivo: chamadas, custo cobrado,
    # tokens (entrada, saída, cache lido e gravado) e latências.
    calls: int = 0
    calls_failed: int = 0
    cost_usd: float = 0.0
    tokens: dict[str, int] = field(default_factory=dict[str, int])
    latencies: list[int] = field(default_factory=list[int])


@dataclass
class Report:
    days: list[DayMetrics]

    @property
    def complete_days(self) -> list[DayMetrics]:
        return [d for d in self.days if d.complete]

    def totals(self) -> dict[str, Any]:
        """Totais dos dias completos; o dia parcial, se houver, só aparece como `partial_day`."""
        days = self.complete_days
        partial = next((d.day for d in self.days if not d.complete), None)
        matured: dict[str, list[int]] = {}
        for d in days:
            for group, values in d.matured_days.items():
                matured.setdefault(group, []).extend(values)
        harvests = Counter[str]()
        plantings = Counter[str]()
        rejections = Counter[str]()
        for d in days:
            harvests.update(d.harvests)
            plantings.update(d.plantings)
            rejections.update(d.rejections)
        return {
            "days": len(days),
            "partial_day": partial,
            "coins_end": days[-1].coins_end if days else 0,
            "harvests": dict(sorted(harvests.items())),
            "plantings": dict(sorted(plantings.items())),
            "mean_days_to_mature": {
                g: round(sum(v) / len(v), 2) for g, v in sorted(matured.items()) if v
            },
            "rejections": dict(sorted(rejections.items())),
            "withered": sum(d.withered for d in days),
            "hunger_peak": max((d.hunger_peak for d in days), default=0.0),
            "faints": sum(d.faints for d in days),
            "real_seconds_per_day": round(sum(d.real_seconds for d in days) / max(1, len(days)), 3),
            **self.llm_totals(days),
        }

    @staticmethod
    def llm_totals(days: Sequence[DayMetrics]) -> dict[str, Any]:
        """As métricas do modelo, só quando houve chamadas: o script não tem (ADR-0059)."""
        if not any(d.calls or d.calls_failed for d in days):
            return {}
        tokens = Counter[str]()
        for d in days:
            tokens.update(d.tokens)
        latencies = [latency for d in days for latency in d.latencies]
        cost = round(sum(d.cost_usd for d in days), 4)
        return {
            "llm": {
                "calls": sum(d.calls for d in days),
                "calls_failed": sum(d.calls_failed for d in days),
                "cost_usd": cost,
                "cost_usd_per_day": round(cost / max(1, len(days)), 4),
                "tokens": dict(sorted(tokens.items())),
                "latency_ms_median": int(statistics.median(latencies)) if latencies else 0,
            }
        }


def _seconds(time: str) -> float:
    return datetime.fromisoformat(time.replace("Z", "+00:00")).timestamp()


def compute(envelopes: Iterable[Mapping[str, Any]], avatar: str = AVATAR) -> Report:
    everything = list(envelopes)
    kernel = sorted(
        (e for e in everything if str(e.get("source", "")).startswith("/kernel/")),
        key=lambda e: int(e["seq"]),
    )
    ticks_per_day = 1440
    days: dict[int, DayMetrics] = {}
    first_time: dict[int, float] = {}
    last_time: dict[int, float] = {}
    coins, last_tick = 0, 0
    for envelope in kernel:
        kind, data = str(envelope["type"]), envelope["data"]
        if kind == "campsverso.world.session.started.v1":
            ticks_per_day = 86400 // int(data["tick_seconds"])
        last_tick = max(last_tick, int(envelope["tick"]))
        day = int(envelope["tick"]) // ticks_per_day + 1
        metrics = days.setdefault(day, DayMetrics(day, coins_end=coins))
        stamp = _seconds(str(envelope["time"]))
        first_time.setdefault(day, stamp)
        last_time[day] = stamp
        if kind == "campsverso.action.completed.v1" and data["action"] in ("harvest", "plant"):
            group = _group(str(data["params"]["target"]))
            counter = metrics.harvests if data["action"] == "harvest" else metrics.plantings
            counter[group] = counter.get(group, 0) + 1
        elif kind == "campsverso.farm.crop.matured.v1":
            metrics.matured_days.setdefault(_group(str(data["plot_id"])), []).append(
                int(data["days"])
            )
        elif kind == "campsverso.farm.crop.withered.v1":
            metrics.withered += 1
        elif kind == "campsverso.action.rejected.v1":
            reason = str(data["reason"])
            metrics.rejections[reason] = metrics.rejections.get(reason, 0) + 1
        elif kind == "campsverso.avatar.fainted.v1":
            metrics.faints += 1
        elif kind == "campsverso.world.need.changed.v1" and data["need"] == "fome":
            metrics.hunger_peak = max(metrics.hunger_peak, float(data["value"]))
        elif kind == "campsverso.avatar.decision_requested.v1":
            metrics.hunger_peak = max(metrics.hunger_peak, float(data["needs"].get("fome", 0)))
        elif kind.startswith("campsverso.world.item.") and data["item"] == "moeda":
            qty = int(data["qty"])
            if kind.endswith("created.v1") and data["container_id"] == avatar:
                coins += qty
            elif kind.endswith("consumed.v1") and data["container_id"] == avatar:
                coins -= qty
            elif kind.endswith("transferred.v1"):
                coins += qty * (
                    (data["to_container"] == avatar) - (data["from_container"] == avatar)
                )
        metrics.coins_end = coins
    for day, metrics in days.items():
        metrics.real_seconds = round(last_time[day] - first_time[day], 3)
        metrics.complete = last_tick >= day * ticks_per_day  # o mundo chegou ao dia seguinte
    # As chamadas de modelo (ADR-0058) vêm do medidor, não do kernel; o dia é o do tick delas.
    calls = sorted(
        (e for e in everything if str(e.get("type", "")).startswith("campsverso.llm.call.")),
        key=lambda e: (int(e.get("tick") or 0), str(e.get("time", ""))),
    )
    for envelope in calls:
        kind, data = str(envelope["type"]), envelope["data"]
        day = int(envelope.get("tick") or 0) // ticks_per_day + 1
        if day not in days:  # um dia sem fato do kernel: só acontece em testes
            days[day] = DayMetrics(day, complete=last_tick >= day * ticks_per_day)
        metrics = days[day]
        if kind == "campsverso.llm.call.completed.v1":
            metrics.calls += 1
            metrics.latencies.append(int(data["latency_ms"]))
            if data.get("charged", True):
                metrics.cost_usd = round(metrics.cost_usd + float(data["cost_usd"]), 6)
            for key, value in data["usage"].items():
                metrics.tokens[str(key)] = metrics.tokens.get(str(key), 0) + int(value)
        else:
            metrics.calls_failed += 1
    return Report([days[d] for d in sorted(days)])


def table(report: Report) -> str:
    with_llm = any(d.calls or d.calls_failed for d in report.days)
    header = "dia  moedas  colheitas(o/l)  maduras-em(o/l)  fome-máx  desmaios  recusas  s-reais"
    lines = [header + ("  chamadas  US$-dia  ms-med" if with_llm else "")]
    for d in report.days:
        mature = "/".join(
            str(round(sum(d.matured_days.get(g, [])) / len(d.matured_days[g]), 1))
            if d.matured_days.get(g)
            else "-"
            for g in ("oeste", "leste")
        )
        harvests = f"{d.harvests.get('oeste', 0)}/{d.harvests.get('leste', 0)}"
        mark = " " if d.complete else "*"
        line = (
            f"{d.day:3d}{mark} {d.coins_end:6d}  {harvests:>14}  {mature:>15}  {d.hunger_peak:8.1f}"
            f"  {d.faints:8d}  {sum(d.rejections.values()):7d}  {d.real_seconds:7.2f}"
        )
        if with_llm:
            median = int(statistics.median(d.latencies)) if d.latencies else 0
            line += f"  {d.calls:8d}  {d.cost_usd:7.4f}  {median:6d}"
        lines.append(line)
    if any(not d.complete for d in report.days):
        lines.append("* dia incompleto: fica fora dos totais")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="campsverso_tools.metrics")
    parser.add_argument(
        "archive", type=Path, help="pasta do mundo no arquivo, ex.: data/archive/farm-camps-01"
    )
    parser.add_argument("--json", action="store_true", help="saída em JSON")
    args = parser.parse_args(argv)
    report = compute(read_archive(args.archive))
    if args.json:
        print(
            json.dumps(
                {"days": [asdict(d) for d in report.days], "totals": report.totals()},
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(table(report))
        print(json.dumps(report.totals(), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
