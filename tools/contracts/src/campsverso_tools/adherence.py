"""A aderência ao procedimento (ADR-0074, decisão 35), a partir do arquivo de uma corrida.

O procedimento (o playbook 4) pede formatos fixos, e eles deixam contar por código se o modelo o
seguiu. Isso separa "o procedimento não ajuda" de "o modelo não seguiu o procedimento":

- **As hipóteses com a suspeita entre colchetes** no começo (`[adubo] rabanete leva ...`).
- **As suspeitas da lista testadas:** o lugar do canteiro, `antes`, `adubo` e `estação`, lidas do
  que está entre os colchetes.
- **Os pares:** os dois canteiros citados no teste (`Par: plot-004 (...) e plot-007 (...)`),
  plantados depois da noite do experimento no mesmo dia, com a mesma semente, e regados nos mesmos
  dias até o primeiro dos dois amadurecer ou se perder. A chuva rega os dois, então só a rega do
  avatar conta.
- **Os vereditos** dados na reflexão: cumpriu, falhou ou inconclusivo.
- **As anotações** `HOJE:` (os dias com uma) e `VI:`.

Como as outras métricas, lê só o arquivo; as corridas sem o procedimento entram como referência.
"""

import re
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, cast

AVATAR = "camps"
TICKS_PER_DAY = 1440
SUSPECTS = ("lugar", "antes", "adubo", "estação")  # a lista do procedimento, na ordem dele
OTHER = "outra"
VERDICTS = ("cumpriu", "falhou", "inconclusivo")
PLANTED = "campsverso.action.completed.v1"
NOTED = "campsverso.memory.noted.v1"
# O fim de uma planta para o par: amadureceu ou se perdeu (a colheita e a limpeza são ações).
ENDS = frozenset(
    {
        "campsverso.farm.crop.matured.v1",
        "campsverso.farm.crop.eaten.v1",
        "campsverso.farm.crop.knocked_down.v1",
        "campsverso.farm.crop.withered.v1",
    }
)
ENDING_ACTIONS = frozenset({"harvest", "clear"})
BRACKET = re.compile(r"\s*\[([^\]]+)\]")
PLOT = re.compile(r"\bplot-\d+\b")
TODAY = re.compile(r"\s*HOJE\s*:")
SAW = re.compile(r"\s*VI\s*:")
# O que está entre os colchetes, pela suspeita da lista. A primeira que casa vence, das palavras
# mais estreitas para as mais largas: o lugar, por último, junta tudo o que fala de onde.
KEYWORDS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("adubo", re.compile(r"adub", re.IGNORECASE)),
    ("antes", re.compile(r"antes|anterior|rota[çc][ãa]o|repet", re.IGNORECASE)),
    ("estação", re.compile(r"esta[çc]|primavera|ver[ãa]o|outono|inverno", re.IGNORECASE)),
    (
        "lugar",
        re.compile(
            r"lugar|local|perto|longe|dist[âa]ncia|posi[çc][ãa]o|coordenada|caminho|[áa]gua|"
            r"margem|x,\s*y|\b(?:po[çc]o|casa|mata|rio|lago)\b",
            re.IGNORECASE,
        ),
    ),
)


def suspect_of(hypothesis: str) -> str | None:
    """A suspeita entre os colchetes do começo da hipótese; `None` sem colchetes."""
    found = BRACKET.match(hypothesis)
    if found is None:
        return None
    inside = found.group(1)
    return next((name for name, pattern in KEYWORDS if pattern.search(inside)), OTHER)


def verdict_of(result: str) -> str:
    word = result.strip().lower()
    return next((v for v in VERDICTS if word.startswith(v[:6])), OTHER)


def _day(envelope: Mapping[str, Any]) -> int:
    return int(envelope.get("tick") or 0) // TICKS_PER_DAY + 1


@dataclass
class Adherence:
    """A aderência de uma corrida ao procedimento."""

    days: int = 0
    experiments: int = 0
    bracketed: int = 0  # hipóteses com a suspeita entre colchetes no começo
    suspects: tuple[str, ...] = ()  # as da lista que foram testadas, na ordem da lista
    others: int = 0  # hipóteses com colchetes fora da lista
    planted: int = 0  # experimentos com os dois canteiros do teste plantados depois da noite
    pairs: int = 0  # e no mesmo dia, com a mesma semente e a mesma rega
    verdicts: dict[str, int] = field(default_factory=dict[str, int])
    today_days: int = 0  # os dias com uma anotação HOJE:
    saw: int = 0  # as anotações VI:

    @property
    def given(self) -> int:
        return sum(self.verdicts.values())


@dataclass
class _Plot:
    plantings: list[tuple[int, str]] = field(default_factory=list[tuple[int, str]])  # dia, semente
    watered: set[int] = field(default_factory=set[int])
    ends: list[int] = field(default_factory=list[int])


def adhere(
    envelopes: Iterable[Mapping[str, Any]],
    experiments: Sequence[Mapping[str, Any]],
    *,
    days: int,
    avatar: str = AVATAR,
) -> Adherence:
    """A aderência, dos fatos do arquivo e dos experimentos lidos da reflexão (`experiments_of`:
    o dia, a hipótese, o teste e o veredito de cada um)."""
    plots: dict[str, _Plot] = {}
    today: set[int] = set()
    saw = 0
    for envelope in envelopes:
        kind = str(envelope.get("type", ""))
        data = cast(Mapping[str, Any], envelope.get("data") or {})
        if kind == PLANTED and data.get("avatar_id") == avatar:
            params = cast(Mapping[str, Any], data.get("params") or {})
            target = params.get("target")
            if not isinstance(target, str):
                continue
            plot = plots.setdefault(target, _Plot())
            action = data.get("action")
            if action == "plant":
                plot.plantings.append((_day(envelope), str(params.get("crop"))))
            elif action == "water":
                plot.watered.add(_day(envelope))
            elif action in ENDING_ACTIONS:
                plot.ends.append(_day(envelope))
        elif kind in ENDS and isinstance(data.get("plot_id"), str):
            plots.setdefault(str(data["plot_id"]), _Plot()).ends.append(_day(envelope))
        elif kind == NOTED and data.get("avatar_id") == avatar:
            text = str(data.get("text", ""))
            if TODAY.match(text):
                today.add(int(data.get("day") or _day(envelope)))
            if SAW.match(text):
                saw += 1
    found = Adherence(days=days, today_days=len(today), saw=saw)
    tested: set[str] = set()
    verdicts = Counter[str]()
    for trial in experiments:
        found.experiments += 1
        suspect = suspect_of(str(trial.get("hypothesis", "")))
        if suspect is not None:
            found.bracketed += 1
            if suspect == OTHER:
                found.others += 1
            else:
                tested.add(suspect)
        planted, same = _pair(str(trial.get("test", "")), int(trial.get("day") or 0), plots, days)
        found.planted += planted
        found.pairs += same
        if trial.get("result") is not None:
            verdicts[verdict_of(str(trial["result"]))] += 1
    found.suspects = tuple(s for s in SUSPECTS if s in tested)
    found.verdicts = dict(verdicts)
    return found


def _pair(test: str, night: int, plots: Mapping[str, _Plot], days: int) -> tuple[bool, bool]:
    """(os dois canteiros do teste foram plantados depois da noite, e o par é um par: mesmo dia,
    mesma semente, mesma rega até o primeiro dos dois acabar)."""
    named = list(dict.fromkeys(PLOT.findall(test)))[:2]
    if len(named) < 2:
        return False, False
    first: list[tuple[int, str]] = []
    for name in named:
        plot = plots.get(name)
        after = [p for p in plot.plantings if p[0] > night] if plot is not None else []
        if not after:
            return False, False
        first.append(after[0])
    (day_a, crop_a), (day_b, crop_b) = first
    if day_a != day_b or crop_a != crop_b:
        return True, False
    end = min(min((d for d in plots[name].ends if d >= day_a), default=days + 1) for name in named)
    a, b = ({d for d in plots[name].watered if day_a <= d < end} for name in named)
    return True, a == b
