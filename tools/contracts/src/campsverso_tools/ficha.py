"""A ficha de cada corrida e de cada juiz (ADR-0074, decisão 12): o que jogou e com o quê.

- **O modelo:** o pedido e o que as respostas disseram ser (o id exato, da fita), com o conselheiro.
- **A data** em que a corrida começou, e **a rota:** o provedor de cada chamada, pelos eventos
  `llm.call.completed` (a API da Anthropic; com a OpenRouter, o passo 8 acrescenta quem atendeu).
- **O esforço** pedido em cada tipo de chamada (a decisão, a reflexão, a prova).
- **O harness**, o que este repositório põe em volta do modelo: o commit (e se havia mudança fora
  dele), a versão do SDK, o hash do prompt de sistema e o das ferramentas, a memória, o playbook e
  os braços. No juiz, o hash da rubrica e o do pedido.

Nada aqui chama um modelo: a ficha é lida do que a corrida já gravou.
"""

import hashlib
import json
import subprocess
from collections.abc import Iterable, Mapping
from importlib import metadata
from pathlib import Path
from typing import Any, cast

COMPLETED = "campsverso.llm.call.completed.v1"


def sha256_of(value: Any) -> str:
    """O hash de um texto, ou de um valor em JSON canônico (chaves ordenadas)."""
    text = (
        value if isinstance(value, str) else json.dumps(value, sort_keys=True, ensure_ascii=False)
    )
    return hashlib.sha256(text.encode()).hexdigest()


def source_state(root: Path) -> dict[str, Any]:
    """O commit do repositório e se havia mudança fora dele (os arquivos do git, sem `data/`)."""
    try:
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True
        ).stdout.strip()
        changed = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=no"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except OSError, subprocess.CalledProcessError:
        return {"commit": None}
    return {"commit": head, "dirty": bool(changed)}


def sdk_version(package: str = "anthropic") -> str | None:
    try:
        return f"{package} {metadata.version(package)}"
    except metadata.PackageNotFoundError:
        return None


def answered_models(tape: Path) -> list[str]:
    """Os ids que as respostas da fita trouxeram, de quem jogou e do conselheiro."""
    if not tape.is_file():
        return []
    found: set[str] = set()
    for line in tape.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        response = cast(Mapping[str, Any], json.loads(line).get("response") or {})
        if response.get("model"):
            found.add(str(response["model"]))
        advisor = cast(Mapping[str, Any] | None, response.get("advisor"))
        if advisor is not None and advisor.get("model"):
            found.add(str(advisor["model"]))
    return sorted(found)


def calls_of(envelopes: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """A rota e o esforço, pelos eventos das chamadas: os provedores e o esforço por propósito."""
    providers: set[str] = set()
    efforts: dict[str, set[str]] = {}
    for envelope in envelopes:
        if envelope.get("type") != COMPLETED:
            continue
        data = cast(Mapping[str, Any], envelope.get("data") or {})
        providers.add(str(data.get("provider")))
        purpose = efforts.setdefault(str(data.get("purpose")), set())
        if data.get("effort"):
            purpose.add(str(data["effort"]))
    return {
        "route": sorted(providers),
        "effort": {k: sorted(v) for k, v in sorted(efforts.items())},
    }


def run_card(
    *,
    started: str,
    spec: Mapping[str, Any],
    envelopes: Iterable[Mapping[str, Any]],
    tape: Path,
    root: Path,
    mind: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """A ficha de uma corrida da arena. `mind` traz o que só a mente montada sabe: o nome, o
    prompt de sistema e as ferramentas; um script não tem."""
    card: dict[str, Any] = {"date": started[:10], "controller": spec.get("controller")}
    harness: dict[str, Any] = {**source_state(root)}
    if spec.get("controller") == "llm":
        card |= {"model": spec.get("model"), "answered": answered_models(tape)}
        card |= calls_of(envelopes)
        if spec.get("advisor"):
            card["advisor"] = spec["advisor"]
        harness["sdk"] = sdk_version()
        if mind is not None:
            harness |= {
                "mind": mind.get("name"),
                "prompt_sha256": sha256_of(mind.get("system")),
                "tools": len(cast(list[Any], mind.get("tools") or [])),
                "tools_sha256": sha256_of(mind.get("tools") or []),
            }
        harness |= {
            "memory": bool(spec.get("memory")),
            "playbook": int(spec.get("playbook") or 0),
            "compare": bool(spec.get("compare")),
        }
    else:
        harness["script"] = spec.get("script") or "o do cartucho"
    card["harness"] = harness
    return card


def judge_card(*, date: str, rubric: Path, root: Path) -> dict[str, Any]:
    """O que a ficha de um veredito acrescenta ao que a chamada já diz (o modelo que respondeu, a
    rota e o hash do pedido): a data, a rubrica e o harness."""
    return {
        "date": date[:10],
        "rubric_sha256": sha256_of(rubric.read_text(encoding="utf-8")),
        "harness": {**source_state(root), "sdk": sdk_version()},
    }
