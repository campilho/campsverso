"""A ferramenta de comparação (ADR-0074, decisão 7): o braço do Haiku que faz a conta do caderno.

Lê o caderno de campo do próprio avatar e devolve os plantios que fugiram do normal: os que
levaram mais ou menos dias que os outros daquela cultura na mesma estação, e os que se
perderam maduros. Cada um vem com os plantios mais parecidos que não fugiram e com as colunas em que
eles diferem. As colunas são as suspeitas do script 3, com distratores (ADR-0070): a quantos
tiles o canteiro fica de cada tipo de terreno e de coisa que o cenário nomeia, o que havia antes
no canteiro, o adubo, a rega e a estação. A ferramenta não diz qual coluna explica nada: só
calcula, com fatos que o avatar viu, e o modelo escolhe o teste. O teste de palavras proibidas
de cada cenário lê a descrição e as instruções.

Fica desligada fora do braço (`MemorySettings.compare`): sem ela, o pedido da reflexão é o de
sempre, e as fitas não mudam.
"""

import statistics
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, cast

from campsverso_ports import Place, Planting, Tile

COMPARE = "comparar"
LOST = ("comida", "derrubada", "sumiu")  # as perdas que o caderno anota
GROUP_MIN = 3  # plantios maduros de uma cultura e estação para haver um normal
DAYS_OFF = 0.2  # quanto do normal um plantio precisa fugir (e pelo menos um dia)
SHOWN = 6  # plantios fora do ritmo mostrados
SHOWN_LOST = 4  # perdas mostradas
PEERS = 3  # parecidos de cada um
COMPARISONS = 2  # comparações por noite; depois delas, a reflexão precisa fechar o dia

COMPARE_TOOL: dict[str, Any] = {
    "name": COMPARE,
    "description": (
        "Compara os plantios do seu caderno de campo. Devolve os que fugiram do normal (os que "
        "levaram mais ou menos dias que os outros plantios daquela cultura na mesma estação, e "
        "os que se perderam maduros, antes da colheita), cada um com os plantios mais "
        "parecidos que não fugiram e as colunas em que eles diferem. As colunas dizem a quantos "
        "tiles o canteiro fica de cada coisa do terreno que você viu, o que havia antes no "
        "canteiro, o adubo, a rega e a estação. A ferramenta só faz a conta: o que ela quer "
        "dizer, você decide."
    ),
    "strict": True,
    "input_schema": {
        "type": "object",
        "properties": {
            "crop": {
                "type": "string",
                "description": 'A cultura a comparar, como no caderno; ou "" para todas.',
            }
        },
        "required": ["crop"],
        "additionalProperties": False,
    },
}

COMPARE_INSTRUCTIONS = """\
Antes de fechar o dia, você pode usar a ferramenta `comparar`: ela lê o seu caderno de campo e \
mostra os plantios que fugiram do normal, com os parecidos e as colunas em que diferem. Use o que \
ela mostrar para revisar as crenças e escolher o experimento de amanhã; depois feche o dia com \
`reflect`."""


@dataclass(frozen=True, slots=True)
class Columns:
    """O que a ferramenta mede a partir de cada canteiro, dado pela mente do cenário: o nome de
    cada coluna e os tipos de terreno (`terrain`) ou de coisa vista (`things`) que ela mede; e as
    faixas, em tiles, que decidem se dois plantios diferem numa coluna."""

    terrain: Mapping[str, frozenset[str]]
    things: Mapping[str, frozenset[str]]
    bins: tuple[int, ...] = (2, 4, 8, 16)

    @classmethod
    def of(cls, raw: Mapping[str, Any]) -> Columns:
        """De um `comparar.yaml` (`terrain: {nome: [tipos]}, things: {nome: [tipos]}, bins`)."""

        def kinds(section: str) -> dict[str, frozenset[str]]:
            found = cast(Mapping[str, Sequence[str]], raw.get(section) or {})
            return {str(k): frozenset(str(v) for v in vs) for k, vs in found.items()}

        bins = cast(Sequence[int], raw.get("bins") or (2, 4, 8, 16))
        return cls(kinds("terrain"), kinds("things"), tuple(int(b) for b in bins))

    @property
    def names(self) -> tuple[str, ...]:
        return (*self.terrain, *self.things)


type Row = dict[str, str]  # o valor de cada coluna, em texto
type Key = dict[str, object]  # o que decide se dois plantios diferem em cada coluna


def _chebyshev(x: int, y: int, tiles: Sequence[tuple[int, int]]) -> int | None:
    return min((max(abs(x - tx), abs(y - ty)) for tx, ty in tiles), default=None)


class Comparison:
    """A conta da ferramenta sobre o caderno, o terreno e os lugares vistos."""

    def __init__(
        self,
        columns: Columns,
        plantings: Sequence[Planting],
        terrain: Sequence[Tile],
        places: Sequence[Place],
    ) -> None:
        self.columns = columns
        self.plantings = [p for p in plantings if p.x is not None and p.y is not None]
        self._rows: dict[tuple[str, int], tuple[Row, Key]] = {}
        self.sources: dict[str, list[tuple[int, int]]] = {}
        for name, kinds in columns.terrain.items():
            self.sources[name] = [(t.x, t.y) for t in terrain if t.kind in kinds]
        for name, kinds in columns.things.items():
            self.sources[name] = sorted((p.x, p.y) for p in places if p.kind in kinds)

    def _band(self, tiles: int | None) -> int | None:
        if tiles is None:
            return None
        for i, edge in enumerate(self.columns.bins):
            if tiles <= edge:
                return i
        return len(self.columns.bins)

    def row(self, p: Planting) -> tuple[Row, Key]:
        """O valor de cada coluna de um plantio e o que decide a diferença: a faixa, para os
        tiles; o próprio valor, para o resto."""
        cached = self._rows.get((p.plot_id, p.tick))
        if cached is not None:
            return cached
        assert p.x is not None
        assert p.y is not None
        row: Row = {}
        key: Key = {}
        for name in self.columns.names:
            tiles = _chebyshev(p.x, p.y, self.sources[name])
            row[name] = "não visto" if tiles is None else f"{tiles} tile{'s' if tiles != 1 else ''}"
            key[name] = self._band(tiles)
        row["antes"] = p.previous or "nada (canteiro novo)"
        key["antes"] = p.previous
        row["adubo"] = "sim" if p.fertilized else "não"
        key["adubo"] = p.fertilized
        if p.matured_day is not None:
            span = range(p.day, p.matured_day)
            dry = sum(1 for d in span if d not in p.watered_days)
            row["rega"] = "todos os dias" if dry == 0 else f"faltou em {dry} de {len(span)} dias"
            key["rega"] = dry == 0
        else:
            row["rega"] = f"em {len(p.watered_days)} dias"
            key["rega"] = None
        season = p.season or "?"
        if p.matured_season and p.matured_season != p.season:
            season = f"{season} até {p.matured_season}"
        row["estação"] = season
        key["estação"] = (p.season, p.matured_season)
        self._rows[(p.plot_id, p.tick)] = (row, key)
        return row, key

    def _peers(self, p: Planting, others: Sequence[Planting]) -> tuple[list[Planting], list[str]]:
        """Os mais parecidos (os que diferem em menos colunas; empate pelo mais recente) e as
        colunas em que o plantio difere de todos eles."""
        _, mine = self.row(p)
        ranked = sorted(
            others,
            key=lambda o: (sum(1 for k, v in self.row(o)[1].items() if v != mine[k]), -o.tick),
        )[:PEERS]
        keys = [self.row(o)[1] for o in ranked]
        differ = [k for k in mine if keys and all(other[k] != mine[k] for other in keys)]
        return ranked, differ

    def _line(self, p: Planting) -> str:
        row, _ = self.row(p)
        return ", ".join(f"{name} {value}" for name, value in row.items())

    def pace(self, crop: str) -> list[str]:
        """Os plantios que levaram mais ou menos dias que o normal da cultura e da estação."""
        matured = [
            p for p in self.plantings if p.matured_day is not None and (not crop or p.crop == crop)
        ]
        groups: dict[tuple[str, str | None], list[Planting]] = {}
        for p in matured:
            groups.setdefault((p.crop, p.season), []).append(p)
        found: list[tuple[float, Planting, float, list[Planting]]] = []
        for group in groups.values():
            if len(group) < GROUP_MIN:
                continue
            days = {id(p): float(cast(int, p.matured_day) - p.day) for p in group}
            normal = statistics.median(days.values())
            off = [p for p in group if abs(days[id(p)] - normal) >= max(1.0, DAYS_OFF * normal)]
            usual = [p for p in group if p not in off]
            found.extend(
                (abs(days[id(p)] - normal) / normal, p, normal, usual) for p in off if usual
            )
        found.sort(key=lambda f: (-f[0], f[1].tick, f[1].plot_id))
        lines: list[str] = []
        for _, p, normal, usual in found[:SHOWN]:
            took = cast(int, p.matured_day) - p.day
            peers, differ = self._peers(p, usual)
            normal_text = f"{normal:g}".replace(".", ",")
            lines.append(
                f"- {p.plot_id} ({p.x},{p.y}) {p.crop}, plantado no dia {p.day}: {took} dias; o "
                f"normal desta cultura e estação é {normal_text} dias"
            )
            lines.append(f"  este: {self._line(p)}")
            lines.extend(
                f"  {o.plot_id}, plantado no dia {o.day} ({cast(int, o.matured_day) - o.day} "
                f"dias): {self._line(o)}"
                for o in peers
            )
            lines.append(f"  diferem em: {', '.join(differ) if differ else 'nenhuma coluna'}")
        if not lines:
            return []
        head = f"O ritmo: {len(found)} de {len(matured)} plantios maduros fugiram do normal"
        shown = f" (os {SHOWN} que mais fugiram)" if len(found) > SHOWN else ""
        return [f"{head}{shown}:", *lines]

    def losses(self, crop: str) -> list[str]:
        """As plantas que se perderam antes da colheita, ao lado das colhidas mais parecidas."""
        mine = [p for p in self.plantings if not crop or p.crop == crop]
        lost = [p for p in mine if p.outcome in LOST]
        harvested = [p for p in self.plantings if p.outcome == "colhida"]
        if not lost or not harvested:
            return []
        one = len(lost) == 1
        lines = [
            f"As perdas: {len(lost)} planta{'' if one else 's'} se perde{'u' if one else 'ram'} "
            f"antes da colheita, e {len(harvested)} foram colhidas"
            + (f" (as {SHOWN_LOST} mais recentes):" if len(lost) > SHOWN_LOST else ":")
        ]
        for p in sorted(lost, key=lambda q: (-q.tick, q.plot_id))[:SHOWN_LOST]:
            peers, differ = self._peers(p, harvested)
            when = f"no dia {p.outcome_day}" if p.outcome_day is not None else ""
            lines.append(f"- {p.plot_id} ({p.x},{p.y}) {p.crop}, {p.outcome} {when}".rstrip())
            lines.append(f"  este: {self._line(p)}")
            lines.extend(
                f"  {o.plot_id} {o.crop}, plantado no dia {o.day} (colhido): {self._line(o)}"
                for o in peers
            )
            lines.append(f"  diferem em: {', '.join(differ) if differ else 'nenhuma coluna'}")
        return lines

    def text(self, crop: str, day: int) -> str:
        crop = crop.strip()
        parts = self.pace(crop)
        lost = self.losses(crop)
        if parts and lost:
            parts.append("")
        parts.extend(lost)
        which = f" de {crop}" if crop else ""
        head = f"Comparação do caderno de campo{which}, até o dia {day}."
        if not parts:
            return (
                f"{head} Ainda não há o que comparar: o normal pede {GROUP_MIN} plantios maduros "
                "de uma cultura numa estação, e uma perda pede alguma colheita ao lado."
            )
        return "\n".join([head, *parts])
