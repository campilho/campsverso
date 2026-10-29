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

Um modelo com rota na tabela do ambiente (`openrouter:`) vai pela OpenRouter (ADR-0074) e pede
OPENROUTER_API_KEY. Ali a fumaça dá também o segundo turno: o resultado da ferramenta volta com
a resposta inteira (o raciocínio e os argumentos como vieram), que é a tradução que mais pode
falhar; e mostra quem atendeu, o modelo que a resposta disse ser e o custo que ela trouxe ao
lado do da tabela.
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
    OpenRouterModel,
    RecordingModel,
    SystemWallClock,
    Uuid7Ids,
    ValidatingBus,
    cost_usd,
    load_env,
    model_port,
)
from campsverso_ports import IdGenerator, ModelPort, ModelRequest, ModelResponse, WallClock

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
    follow: bool = False,
    max_tokens: int = 256,
) -> dict[str, Any]:
    """Duas vezes o mesmo pedido: a primeira ao vivo e gravada, a segunda da fita. Com `follow`,
    um segundo turno ao vivo, com o resultado da ferramenta."""
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
        max_tokens=max_tokens if advisor is None else 2048,
        effort="low",
        purpose="probe",
    )
    live = await metered.complete(request)
    replayed = await metered.complete(request)
    result: dict[str, Any] = {
        "live": {
            **_seen(live, prices[model]),
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
    }
    if follow and live.tool_uses():
        answer = {
            "type": "tool_result",
            "tool_use_id": str(live.tool_uses()[0]["id"]),
            "content": "Feito. Agora é meio-dia, o sol está forte e a cesta está cheia.",
        }
        after = ModelRequest(
            model=model,
            system=SYSTEM,
            messages=[
                *request.messages,
                {"role": "assistant", "content": [dict(b) for b in live.content]},
                {"role": "user", "content": [answer]},
            ],
            tools=tools,
            max_tokens=max_tokens,
            effort="low",
            purpose="probe",
        )
        result["follow"] = _seen(await metered.complete(after), prices[model])
    result["spent_usd"] = metered.spent_usd
    result["events"] = [envelope for _, envelope in bus.published]
    return result


def _seen(response: ModelResponse, prices: ModelPrices) -> dict[str, Any]:
    """O que uma resposta ao vivo mostra: a parada, a ferramenta, os tokens, quem atendeu e o
    custo que ela trouxe ao lado do da tabela."""
    return {
        "stop_reason": response.stop_reason,
        "tool_uses": response.tool_uses(),
        "text": response.text(),
        "blocks": [str(b.get("type")) for b in response.content],
        "usage": response.usage.as_dict(),
        "cost_reported_usd": response.usage.cost_usd,
        "cost_by_table_usd": cost_usd(response.usage, prices),
        "model": response.model,
        "served_by": response.served_by,
        "latency_ms": response.latency_ms,
        "request_id": response.request_id,
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
    parser.add_argument("--max-tokens", type=int, default=None, help="256; 1024 na OpenRouter")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse(argv)
    env = load_env(args.env)
    clock = SystemWallClock()
    model = str(args.model)
    routed = model in env.routes  # pela OpenRouter (ADR-0074): o raciocínio conta no max_tokens
    result = asyncio.run(
        _run(
            model_port(model, routes=env.routes, clock=clock),
            env.models,
            model=model,
            prompt=str(args.prompt),
            cassette=args.cassette,
            clock=clock,
            advisor=args.advisor,
            follow=routed,
            max_tokens=args.max_tokens or (1024 if routed else 256),
        )
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


async def _run(
    port: AnthropicModel | OpenRouterModel, prices: Mapping[str, ModelPrices], **options: Any
) -> dict[str, Any]:
    """A fumaça e o fechamento do cliente HTTP no mesmo laço."""
    try:
        return await smoke(port, prices, ids=Uuid7Ids(), **options)
    finally:
        await port.aclose()


if __name__ == "__main__":
    sys.exit(main())
