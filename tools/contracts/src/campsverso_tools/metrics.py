"""Métricas da bíblia §13 a partir do arquivo de eventos (ADR-0047 e ADR-0062, decisão 13).

    uv run python -m campsverso_tools.metrics data/archive/farm-camps-01 [--json]

Lê só o arquivo JSONL, como qualquer leitor externo: não importa o kernel nem os cartuchos.
O dia agrícola sai do tick (ticks por dia = 86.400 / tick_seconds da sessão), o que vale para
mundos que começam na hora em que o dia vira, como a fazenda (06:00). Os totais contam só os dias
completos: o último dia de uma execução costuma parar no meio, e as moedas dele enganam.

Na Fazenda Boa Vista (bíblia 2 §13) entram as métricas da arena do M14: canteiros cavados na
faixa do rio, o dia da compra de cada ferramenta, a mistura de culturas por semana, as refeições
por receita, os estragos por item, as murchas da madura e as vendas abaixo de 80% do preço.
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
from typing import Any, cast

# Grupos de canteiros da Fazenda do Camps (bíblia §4): o leste fica perto do rio (R-001).
GROUPS = {"plot-w-": "oeste", "plot-e-": "leste"}
# Na Fazenda Boa Vista o canteiro nasce onde se cava, sem grupo nem rótulo (ADR-0062): é o
# analista que o põe na faixa do rio (a R-001 vale a até 4 tiles da água, bíblia 2 §10) ou fora
# dela, pela posição. O agente nunca vê isso.
RIVER_BAND = 4
GROUP_ORDER = ("oeste", "leste", "rio", "fora")
RIVER_GROUPS = ("leste", "rio")  # o grupo que a R-001 favorece, em cada mundo
SALE_FLOOR = 0.8  # vender abaixo de 80% do preço de tabela é inundar a caixa (bíblia 2 §13)
AVATAR = "camps"


def read_archive(folder: Path) -> Iterator[dict[str, Any]]:
    """Eventos e comandos de um mundo, de todos os dias, inclusive os comprimidos."""
    for path in sorted(folder.glob("*.jsonl*")):
        data = gzip.decompress(path.read_bytes()) if path.suffix == ".gz" else path.read_bytes()
        for line in data.splitlines():
            yield json.loads(line)


def group_of(plot: str, groups: Mapping[str, str] | None = None) -> str:
    """O grupo de um canteiro: o que `compute` lhe deu quando ele nasceu (o atributo `group`, ou
    a faixa do rio pela posição) ou, na fazenda 1, o prefixo do id."""
    if groups and plot in groups:
        return groups[plot]
    return next((name for prefix, name in GROUPS.items() if plot.startswith(prefix)), "outro")


_group = group_of


def water_tiles(terrain: Mapping[str, Any]) -> list[tuple[int, int]]:
    """Os tiles de água do mapa publicado em `session.started` (`rows` e `legend`)."""
    legend = cast(Mapping[str, Mapping[str, Any]], terrain.get("legend") or {})
    wet = {
        symbol
        for symbol, entry in legend.items()
        if bool(cast(Mapping[str, Any], entry.get("properties") or {}).get("water"))
    }
    rows = cast(Sequence[str], terrain.get("rows") or [])
    return [(x, y) for y, row in enumerate(rows) for x, symbol in enumerate(row) if symbol in wet]


def river_group(position: Mapping[str, Any], water: Sequence[tuple[int, int]]) -> str:
    """`rio` a até RIVER_BAND tiles (Chebyshev) de qualquer água; senão `fora`."""
    x, y = int(position["x"]), int(position["y"])
    near = any(max(abs(x - wx), abs(y - wy)) <= RIVER_BAND for wx, wy in water)
    return "rio" if near else "fora"


def plot_groups(envelopes: Iterable[Mapping[str, Any]]) -> dict[str, str]:
    """O grupo de cada canteiro de um arquivo, para quem o lê fora de `compute` (a arena): o
    atributo `group` com que nasceu (fazenda 1) ou a faixa do rio pela posição e pela água do
    mapa do `session.started` (Boa Vista)."""
    groups: dict[str, str] = {}
    water: list[tuple[int, int]] = []
    for envelope in envelopes:
        kind = str(envelope.get("type", ""))
        data = cast(Mapping[str, Any], envelope.get("data") or {})
        if kind == "campsverso.world.session.started.v1":
            water = water_tiles(cast(Mapping[str, Any], data.get("map") or {}))
        elif kind == "campsverso.world.entity.spawned.v1" and data.get("kind") == "plot":
            attributes = cast(Mapping[str, Any], data.get("attributes") or {})
            group, position = attributes.get("group"), data.get("position")
            if isinstance(group, str):
                groups[str(data["entity_id"])] = group
            elif isinstance(position, Mapping) and water:
                groups[str(data["entity_id"])] = river_group(
                    cast(Mapping[str, Any], position), water
                )
    return groups


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
    # A Fazenda Boa Vista (bíblia 2 §13; ADR-0062, decisão 13).
    plots_dug: dict[str, int] = field(default_factory=dict[str, int])  # por grupo (rio/fora)
    tools_bought: dict[str, int] = field(default_factory=dict[str, int])  # por tipo
    plantings_by_crop: dict[str, int] = field(default_factory=dict[str, int])
    cooked: dict[str, int] = field(default_factory=dict[str, int])  # por receita
    spoiled: dict[str, int] = field(default_factory=dict[str, int])  # unidades por item
    withered_ripe: int = 0  # maduras que murcharam sem colher
    sales: int = 0  # unidades postas na caixa
    sales_below_floor: int = 0  # delas, as vendidas com o preço do dia abaixo de 80% da tabela


@dataclass
class Report:
    days: list[DayMetrics]
    market: bool = False  # a caixa mostrou preço do dia (só a Boa Vista)

    @property
    def complete_days(self) -> list[DayMetrics]:
        return [d for d in self.days if d.complete]

    @property
    def groups(self) -> tuple[str, str]:
        """O par de grupos do mundo: oeste/leste na fazenda 1, rio/fora na Boa Vista."""
        seen = {g for d in self.days for g in (*d.harvests, *d.plantings, *d.plots_dug)}
        return ("rio", "fora") if {"rio", "fora"} & seen else ("oeste", "leste")

    @property
    def has_extras(self) -> bool:
        """Houve mecânica da Boa Vista: canteiro cavado, ferramenta, prato, estrago ou mercado."""
        return self.market or any(
            d.plots_dug or d.tools_bought or d.cooked or d.spoiled or d.withered_ripe
            for d in self.days
        )

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
            **self.extra_totals(days),
            **self.llm_totals(days),
        }

    @staticmethod
    def extra_totals(days: Sequence[DayMetrics]) -> dict[str, Any]:
        """As métricas da Boa Vista (bíblia 2 §13): a mistura de culturas vem por semana, e a
        ferramenta pelo dia em que foi comprada pela primeira vez."""
        plots_dug = Counter[str]()
        by_crop = Counter[str]()
        by_week: dict[str, Counter[str]] = {}
        cooked = Counter[str]()
        spoiled = Counter[str]()
        tools: dict[str, int] = {}
        for d in days:
            plots_dug.update(d.plots_dug)
            by_crop.update(d.plantings_by_crop)
            by_week.setdefault(str((d.day - 1) // 7 + 1), Counter[str]()).update(
                d.plantings_by_crop
            )
            cooked.update(d.cooked)
            spoiled.update(d.spoiled)
            for kind in sorted(d.tools_bought):
                tools.setdefault(kind, d.day)
        return {
            "plots_dug": dict(sorted(plots_dug.items())),
            "tools_bought": dict(sorted(tools.items())),
            "plantings_by_crop": dict(sorted(by_crop.items())),
            "plantings_by_week": {
                week: dict(sorted(crops.items())) for week, crops in by_week.items() if crops
            },
            "cooked": dict(sorted(cooked.items())),
            "spoiled": dict(sorted(spoiled.items())),
            "withered_ripe": sum(d.withered_ripe for d in days),
            "sales": sum(d.sales for d in days),
            "sales_below_floor": sum(d.sales_below_floor for d in days),
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


def _bump(counter: dict[str, int], key: object, qty: int = 1) -> None:
    name = str(key)
    counter[name] = counter.get(name, 0) + qty


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
    groups: dict[str, str] = {}  # canteiro -> grupo: o atributo com que nasceu, ou a faixa do rio
    water: list[tuple[int, int]] = []
    prices: dict[str, float] = {}  # o preço do dia que a caixa mostra, por item
    base_prices: dict[str, float] = {}  # o preço de tabela: o que a caixa mostra na virada
    market = False
    for envelope in kernel:
        kind, data = str(envelope["type"]), envelope["data"]
        if kind == "campsverso.world.session.started.v1":
            ticks_per_day = 86400 // int(data["tick_seconds"])
            water = water_tiles(cast(Mapping[str, Any], data.get("map") or {}))
        last_tick = max(last_tick, int(envelope["tick"]))
        day = int(envelope["tick"]) // ticks_per_day + 1
        metrics = days.setdefault(day, DayMetrics(day, coins_end=coins))
        stamp = _seconds(str(envelope["time"]))
        first_time.setdefault(day, stamp)
        last_time[day] = stamp
        if kind == "campsverso.world.entity.spawned.v1":
            entity_id, entity_kind = str(data["entity_id"]), str(data.get("kind"))
            dug = data.get("action_id") is not None  # nasceu de uma ação, não do mapa
            if entity_kind == "plot":
                attributes = cast(Mapping[str, Any], data.get("attributes") or {})
                group, position = attributes.get("group"), data.get("position")
                if isinstance(group, str):
                    groups[entity_id] = group
                elif isinstance(position, Mapping) and water:
                    groups[entity_id] = river_group(cast(Mapping[str, Any], position), water)
                if dug:
                    _bump(metrics.plots_dug, _group(entity_id, groups))
            elif dug:  # uma ferramenta comprada (ADR-0062)
                _bump(metrics.tools_bought, entity_kind)
        elif kind == "campsverso.action.completed.v1":
            action, params = str(data["action"]), cast(Mapping[str, Any], data["params"])
            if action in ("harvest", "plant"):
                group = _group(str(params["target"]), groups)
                counter = metrics.harvests if action == "harvest" else metrics.plantings
                _bump(counter, group)
                if action == "plant" and params.get("crop") is not None:
                    _bump(metrics.plantings_by_crop, params["crop"])
            elif action == "cook" and params.get("recipe") is not None:
                _bump(metrics.cooked, params["recipe"])
        elif kind == "campsverso.farm.crop.matured.v1":
            metrics.matured_days.setdefault(_group(str(data["plot_id"]), groups), []).append(
                int(data["days"])
            )
        elif kind == "campsverso.farm.crop.withered.v1":
            metrics.withered += 1
            if int(data.get("dry_days", 1)) == 0:  # a madura que ninguém colheu (bíblia 2 §6)
                metrics.withered_ripe += 1
        elif kind == "campsverso.action.rejected.v1":
            _bump(metrics.rejections, data["reason"])
        elif kind == "campsverso.avatar.fainted.v1":
            metrics.faints += 1
        elif kind == "campsverso.world.need.changed.v1" and data["need"] == "fome":
            metrics.hunger_peak = max(metrics.hunger_peak, float(data["value"]))
        elif kind == "campsverso.avatar.decision_requested.v1":
            metrics.hunger_peak = max(metrics.hunger_peak, float(data["needs"].get("fome", 0)))
        elif kind == "campsverso.world.entity.state_changed.v1":
            changes = cast(Mapping[str, Any], data.get("changes") or {})
            for key, value in changes.items():
                if str(key).startswith("preco_") and isinstance(value, int | float):
                    item = str(key).removeprefix("preco_")
                    prices[item] = float(value)
                    market = True
                    if data.get("cause") == "market_reset" or item not in base_prices:
                        base_prices[item] = float(value)
        elif kind.startswith("campsverso.world.item."):
            item, qty = str(data["item"]), int(data["qty"])
            if item == "moeda":
                if kind.endswith("created.v1") and data["container_id"] == avatar:
                    coins += qty
                elif kind.endswith("consumed.v1") and data["container_id"] == avatar:
                    coins -= qty
                elif kind.endswith("transferred.v1"):
                    coins += qty * (
                        (data["to_container"] == avatar) - (data["from_container"] == avatar)
                    )
            elif kind.endswith("consumed.v1") and data.get("reason") == "spoiled":
                _bump(metrics.spoiled, item, qty)
            elif kind.endswith("transferred.v1") and data.get("reason") == "sell":
                metrics.sales += qty  # o preço que a caixa mostrava na hora, antes de cair
                price, base = prices.get(item), base_prices.get(item)
                if price is not None and base is not None and price < SALE_FLOOR * base:
                    metrics.sales_below_floor += qty
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
    return Report([days[d] for d in sorted(days)], market=market)


def _pair(mapping: Mapping[str, int], groups: tuple[str, str]) -> str:
    return "/".join(str(mapping.get(g, 0)) for g in groups)


def table(report: Report) -> str:
    with_llm = any(d.calls or d.calls_failed for d in report.days)
    groups = report.groups
    label = "o/l" if groups == ("oeste", "leste") else "/".join(groups)
    width = max(14, len(label) + 10)
    header = (
        f"dia  moedas  {f'colheitas({label})':>{width}}  {f'maduras-em({label})':>{width + 1}}"
        "  fome-máx  desmaios  recusas  s-reais"
    )
    lines = [header + ("  chamadas  US$-dia  ms-med" if with_llm else "")]
    for d in report.days:
        mature = "/".join(
            str(round(sum(d.matured_days.get(g, [])) / len(d.matured_days[g]), 1))
            if d.matured_days.get(g)
            else "-"
            for g in groups
        )
        mark = " " if d.complete else "*"
        line = (
            f"{d.day:3d}{mark} {d.coins_end:6d}  {_pair(d.harvests, groups):>{width}}"
            f"  {mature:>{width + 1}}  {d.hunger_peak:8.1f}"
            f"  {d.faints:8d}  {sum(d.rejections.values()):7d}  {d.real_seconds:7.2f}"
        )
        if with_llm:
            median = int(statistics.median(d.latencies)) if d.latencies else 0
            line += f"  {d.calls:8d}  {d.cost_usd:7.4f}  {median:6d}"
        lines.append(line)
    if any(not d.complete for d in report.days):
        lines.append("* dia incompleto: fica fora dos totais")
    if report.has_extras:
        lines += ["", *_extras(report)]
    return "\n".join(lines)


def _extras(report: Report) -> list[str]:
    """A Fazenda Boa Vista por dia (bíblia 2 §13): o que o agente cavou, comprou, cozinhou,
    deixou estragar e vendeu barato, e o que plantou."""
    groups = report.groups
    label = "/".join(groups)
    width = max(14, len(label) + 9)
    lines = [
        f"dia  {f'cavados({label})':>{width}}  ferramenta-comprada   pratos  estragos"
        "  murchas-mad  vendas(<80%)  plantios por cultura"
    ]
    for d in report.days:
        tools = ", ".join(sorted(d.tools_bought)) or "-"
        crops = ", ".join(f"{c} {n}" for c, n in sorted(d.plantings_by_crop.items())) or "-"
        sales = f"{d.sales}({d.sales_below_floor})"
        lines.append(
            f"{d.day:3d}{' ' if d.complete else '*'} {_pair(d.plots_dug, groups):>{width}}"
            f"  {tools:<20}  {sum(d.cooked.values()):6d}  {sum(d.spoiled.values()):8d}"
            f"  {d.withered_ripe:11d}  {sales:>12}  {crops}"
        )
    return lines


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
