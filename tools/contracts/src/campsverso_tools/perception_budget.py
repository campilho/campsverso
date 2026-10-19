"""Quanto a percepção custaria em tokens (ADR-0056, decisão 8), a partir do arquivo de um mundo.

    uv run python -m campsverso_tools.perception_budget data/archive/<mundo> [--every 20] [--json]

Conta, por dia simulado, as entregas da percepção (fotos `perception.delivered` e deltas
`perception.updated`), os bytes do payload de cada uma e os tokens estimados: bytes dividido por
CHARS_PER_TOKEN, a conta de ordem de grandeza para JSON. A contagem de verdade chega com a ModelPort
no M9, que calibra o fator.

Num arquivo só de fotos (o script recebe sempre a foto), o delta é estimado como a percepção o
faria: a diferença entre duas fotos seguidas do mesmo avatar (libs/world-view) mais os eventos do
meio-tempo. Compara duas políticas: só fotos, e uma foto a cada N deltas.
"""

import argparse
import asyncio
import json
import sys
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from campsverso_ports import ModelPort, ModelRequest
from campsverso_tools.metrics import read_archive
from campsverso_world_view import diff_views

CHARS_PER_TOKEN = (
    2.1  # calibrado em 18/out/2026 com count_tokens (Haiku 5.5): 2,07 foto, 2,05 delta
)
SNAPSHOT = "campsverso.perception.delivered.v1"
DELTA = "campsverso.perception.updated.v1"
# O que não entra em "o que aconteceu": as próprias entregas e o pedido que elas respondem.
NOT_PERCEIVED = ("campsverso.perception.", "campsverso.avatar.decision_requested.")


def _text(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def _size(payload: Mapping[str, Any]) -> int:
    return len(_text(payload).encode())


def tokens(size: int) -> int:
    return round(size / CHARS_PER_TOKEN)


@dataclass
class Delivery:
    tick: int
    snapshot: int  # bytes da foto (a entregue, ou a última conhecida quando chegou um delta)
    delta: int | None  # bytes do delta, real ou estimado; None na primeira entrega do avatar
    snapshot_text: str | None = None  # o JSON, para a calibração com count_tokens
    delta_text: str | None = None


@dataclass
class DayBudget:
    day: int
    deliveries: list[Delivery] = field(default_factory=list[Delivery])

    def snapshots_only(self) -> int:
        return sum(d.snapshot for d in self.deliveries)

    def mean_snapshot(self) -> int:
        return round(self.snapshots_only() / len(self.deliveries)) if self.deliveries else 0

    def mean_delta(self) -> int:
        deltas = [d.delta for d in self.deliveries if d.delta is not None]
        return round(sum(deltas) / len(deltas)) if deltas else 0


@dataclass
class Report:
    days: list[DayBudget]
    every: int

    def with_deltas(self, day: DayBudget, counters: dict[int, int]) -> int:
        """Bytes do dia com uma foto a cada `every` deltas; a conta atravessa os dias."""
        total = 0
        for delivery in day.deliveries:
            since = counters.get(id(day), 0)
            if delivery.delta is None or since >= self.every:
                total += delivery.snapshot
                counters[id(day)] = 0
            else:
                total += delivery.delta
                counters[id(day)] = since + 1
        return total

    def totals(self) -> dict[str, Any]:
        per_day_snapshots = [d.snapshots_only() for d in self.days]
        counter: dict[int, int] = {}
        per_day_deltas: list[int] = []
        carried = 0
        for day in self.days:  # a conta de deltas atravessa os dias
            counter = {id(day): carried}
            per_day_deltas.append(self.with_deltas(day, counter))
            carried = counter[id(day)]
        n = max(1, len(self.days))
        return {
            "days": len(self.days),
            "deliveries": sum(len(d.deliveries) for d in self.days),
            "mean_snapshot_bytes": round(
                sum(d.snapshots_only() for d in self.days)
                / max(1, sum(len(d.deliveries) for d in self.days))
            ),
            "tokens_per_day_snapshots_only": round(tokens(sum(per_day_snapshots)) / n),
            "tokens_per_day_with_deltas": round(tokens(sum(per_day_deltas)) / n),
            "every": self.every,
            "chars_per_token": CHARS_PER_TOKEN,
        }


def compute(envelopes: Iterable[Mapping[str, Any]], every: int = 20) -> Report:
    """Fotos e deltas por dia; com só fotos no arquivo, o delta de cada uma é estimado."""
    ticks_per_day = 1440
    days: dict[int, DayBudget] = {}
    last_view: dict[str, tuple[int, dict[str, Any], int]] = {}  # avatar -> tick, foto, bytes
    pending: dict[str, list[dict[str, Any]]] = {}  # avatar -> eventos desde a última entrega
    for envelope in envelopes:
        kind = str(envelope.get("type", ""))
        if kind == "campsverso.world.session.started.v1":
            ticks_per_day = 86400 // int(envelope["data"]["tick_seconds"])
        tick = int(envelope.get("tick", 0))
        data = envelope.get("data")
        if not isinstance(data, Mapping):
            continue
        payload: Mapping[str, Any] = data  # pyright: ignore[reportUnknownVariableType]
        if kind not in (SNAPSHOT, DELTA):
            # Só o que a percepção vê: eventos world e agent, nunca internal nem comandos.
            visible = str(envelope.get("visibility")) in ("world", "agent")
            if visible and not kind.startswith(NOT_PERCEIVED):
                seen = {"tick": tick, "type": kind, "data": dict(payload)}
                if "avatar_id" in payload and str(envelope.get("visibility")) == "agent":
                    pending.setdefault(str(payload["avatar_id"]), []).append(seen)
                else:
                    for queue in pending.values():
                        queue.append(seen)
            continue
        avatar = str(payload["avatar_id"])
        day = days.setdefault(tick // ticks_per_day + 1, DayBudget(tick // ticks_per_day + 1))
        if kind == DELTA:
            previous = last_view.get(avatar)
            day.deliveries.append(Delivery(tick, previous[2] if previous else 0, _size(payload)))
            pending[avatar] = []
            continue
        view = dict(payload["view"])
        size = _size(payload)
        previous = last_view.get(avatar)
        estimated: int | None = None
        delta_text: str | None = None
        if previous is not None:
            delta = {
                "avatar_id": avatar,
                "since_tick": previous[0],
                "as_of_tick": tick,
                "clock": view["clock"],
                "self": view["self"],
                "events": pending.get(avatar, []),
                "decision": payload.get("decision", {}),
                **diff_views(previous[1], view),
            }
            estimated = _size(delta)
            delta_text = _text(delta)
        day.deliveries.append(Delivery(tick, size, estimated, _text(payload), delta_text))
        last_view[avatar] = (tick, view, size)
        pending[avatar] = []
    return Report([days[d] for d in sorted(days)], every)


async def calibrate(report: Report, port: ModelPort, *, model: str, samples: int) -> dict[str, Any]:
    """Conta com o tokenizador do provedor uma amostra de fotos e deltas guardados no relatório e
    devolve o fator real de caracteres por token (ADR-0058). Contar não custa nem vira evento."""
    chars = {"snapshot": 0, "delta": 0}
    tokens = {"snapshot": 0, "delta": 0}
    counted = {"snapshot": 0, "delta": 0}
    for day in report.days:
        for delivery in day.deliveries:
            for kind, text in (
                ("snapshot", delivery.snapshot_text),
                ("delta", delivery.delta_text),
            ):
                if text is None or counted[kind] >= samples:
                    continue
                request = ModelRequest(model=model, messages=[{"role": "user", "content": text}])
                tokens[kind] += await port.count_tokens(request)
                chars[kind] += len(text)
                counted[kind] += 1
    factors = {k: round(chars[k] / tokens[k], 2) for k in chars if tokens[k]}
    return {
        "model": model,
        "samples": counted,
        "chars_per_token": factors,
        "assumed": CHARS_PER_TOKEN,
    }


def _table(report: Report) -> str:
    lines = [
        "dia  entregas  foto(bytes)  delta(bytes)  tokens/dia só fotos"
        f"  tokens/dia foto+{report.every} deltas"
    ]
    counter: dict[int, int] = {}
    carried = 0
    for d in report.days:
        counter = {id(d): carried}
        mixed = report.with_deltas(d, counter)
        carried = counter[id(d)]
        lines.append(
            f"{d.day:3d}  {len(d.deliveries):8d}  {d.mean_snapshot():11d}  {d.mean_delta():12d}"
            f"  {tokens(d.snapshots_only()):19d}  {tokens(mixed):23d}"
        )
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="campsverso_tools.perception_budget")
    parser.add_argument(
        "archive",
        type=Path,
        nargs="?",
        default=Path("data/archive/farm-camps-01"),
        help="pasta do mundo no arquivo, ex.: data/archive/farm-camps-01",
    )
    parser.add_argument("--every", type=int, default=20, help="uma foto a cada N deltas")
    parser.add_argument("--json", action="store_true", help="saída em JSON")
    parser.add_argument(
        "--contar",
        type=int,
        default=0,
        metavar="N",
        help="conta N fotos e N deltas com o tokenizador da Anthropic (pede ANTHROPIC_API_KEY)",
    )
    parser.add_argument("--model", default="claude-haiku-5-5", help="modelo do tokenizador")
    args = parser.parse_args(argv)
    report = compute(read_archive(args.archive), int(args.every))
    calibration: dict[str, Any] | None = None
    if int(args.contar) > 0:
        from campsverso_adapters import AnthropicModel, SystemWallClock  # raiz de composição

        port = AnthropicModel(clock=SystemWallClock())
        calibration = asyncio.run(
            calibrate(report, port, model=str(args.model), samples=int(args.contar))
        )
    if args.json:
        print(
            json.dumps(
                {
                    "days": [
                        {
                            "day": d.day,
                            "deliveries": [
                                {"tick": x.tick, "snapshot": x.snapshot, "delta": x.delta}
                                for x in d.deliveries
                            ],
                        }
                        for d in report.days
                    ],
                    "totals": report.totals(),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(_table(report))
        print(json.dumps(report.totals(), ensure_ascii=False))
    if calibration is not None:
        print(json.dumps({"calibration": calibration}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
