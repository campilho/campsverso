"""Fumaça da porta de modelo (ADR-0058): uma chamada real, medida e publicada pelo contrato.

    uv run --env-file .env python -m campsverso_tools.llm_smoke [--model MODELO] [--prompt ...]

Chama o modelo pela porta inteira (fita em modo `record` + decorador que mede), num barramento em
memória com validação de contrato, e repete o mesmo pedido: a segunda resposta vem da fita, com
`charged: false`. Imprime tokens, custo, latência e os eventos. Precisa de ANTHROPIC_API_KEY no
ambiente (o `.env`, carregado pelo `--env-file`); o CI nunca roda isto.

Com uma fita que já tem o pedido, a primeira resposta também vem dela e nada é chamado; por isso
o `make llm-smoke` passa uma fita nova a cada execução (`--cassette`). Com `--advisor MODELO`, o
pedido oferece o conselheiro (ADR-0074) e pede uma consulta antes de propor: a fumaça mostra o
conselho, o uso dele e o custo na tarifa dele.
"""

import argparse
import asyncio
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from campsverso_adapters import (
    AnthropicModel,
    InMemoryBus,
    MeteredModel,
    ModelPrices,
    RecordingModel,
    SystemWallClock,
    Uuid7Ids,
    ValidatingBus,
    load_env,
)
from campsverso_ports import IdGenerator, ModelPort, ModelRequest, WallClock

SYSTEM = (
    "Você é o Camps, um fazendeiro numa fazenda pequena. Responda chamando a ferramenta "
    "`propose` com a próxima ação, e nada mais."
)
ADVISED = (
    " Antes de propor, consulte uma vez o conselheiro (a ferramenta `advisor`) e pese o que ele "
    "disser. (Conselheiro: responda em português, em até 60 palavras.)"
)
PROPOSE_TOOL: dict[str, Any] = {
    "name": "propose",
    "description": "Propõe a próxima ação do avatar.",
    "strict": True,
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["water", "plant", "harvest", "eat", "wait"]},
            "intent": {"type": "string", "description": "O motivo, numa frase curta."},
        },
        "required": ["action", "intent"],
        "additionalProperties": False,
    },
}


async def smoke(
    port: ModelPort,
    prices: Mapping[str, ModelPrices],
    *,
    model: str,
    prompt: str,
    cassette: Path,
    clock: WallClock,
    ids: IdGenerator,
    advisor: str | None = None,
) -> dict[str, Any]:
    """Duas vezes o mesmo pedido: a primeira ao vivo e gravada, a segunda da fita."""
    bus = InMemoryBus()
    metered = MeteredModel(
        RecordingModel(port, cassette, "record", clock=clock),
        bus=ValidatingBus(bus),
        worldid="llm-smoke",
        cartridge="farm_camps",
        controller={"type": "llm", "id": "llm/smoke"},
        prices=prices,
        clock=clock,
        ids=ids,
    )
    metered.assert_priced(model)
    tools: list[dict[str, Any]] = [PROPOSE_TOOL]
    if advisor is not None:
        metered.assert_priced(advisor)
        tools.insert(
            0,
            {
                "type": "advisor_20260301",
                "name": "advisor",
                "model": advisor,
                "max_uses": 1,
                "max_tokens": 1024,
            },
        )
    request = ModelRequest(
        model=model,
        system=SYSTEM + (ADVISED if advisor is not None else ""),
        messages=[{"role": "user", "content": prompt}],
        tools=tools,
        max_tokens=256 if advisor is None else 2048,
        effort="low",
        purpose="probe",
    )
    live = await metered.complete(request)
    replayed = await metered.complete(request)
    return {
        "live": {
            "stop_reason": live.stop_reason,
            "tool_uses": live.tool_uses(),
            "text": live.text(),
            "usage": live.usage.as_dict(),
            "latency_ms": live.latency_ms,
            "request_id": live.request_id,
            "advisor": None
            if live.advisor is None
            else {
                "model": live.advisor.model,
                "calls": live.advisor.calls,
                "usage": live.advisor.usage.as_dict(),
                "advice": [
                    b.get("content")
                    for b in live.content
                    if b.get("type") in ("server_tool_use", "advisor_tool_result")
                ],
            },
        },
        "replayed": replayed.replayed,
        "spent_usd": metered.spent_usd,
        "events": [envelope for _, envelope in bus.published],
    }


def _parse(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="campsverso_tools.llm_smoke")
    parser.add_argument("--env", type=Path, default=Path("config/env/local.yaml"))
    parser.add_argument("--model", default="claude-haiku-5-5")
    parser.add_argument(
        "--prompt",
        default=(
            "É manhã, o canteiro leste tem rabanetes maduros e o regador está cheio. "
            "O que você faz?"
        ),
    )
    parser.add_argument("--cassette", type=Path, default=Path("data/llm/smoke.jsonl"))
    parser.add_argument("--advisor", default=None, help="o conselheiro (ADR-0074), se houver")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse(argv)
    env = load_env(args.env)
    clock = SystemWallClock()
    result = asyncio.run(
        smoke(
            AnthropicModel(clock=clock),
            env.models,
            model=str(args.model),
            prompt=str(args.prompt),
            cassette=args.cassette,
            clock=clock,
            ids=Uuid7Ids(),
            advisor=args.advisor,
        )
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
