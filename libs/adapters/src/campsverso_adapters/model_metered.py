"""Decorador da porta de modelo (ADR-0058): toda chamada vira um evento, com tokens e custo.

É o decorador, não o adaptador do provedor, que publica `llm.call.completed.v1` ou
`llm.call.failed.v1` (contratos §12.1). O custo sai de uma tabela de preços que é dado do
ambiente; um modelo sem preço é recusado antes de gastar. O prompt nunca sai: vai o hash. O
conselheiro (ADR-0074) é cobrado na tarifa dele, e o `cost_usd` do evento é o total; o campo
`advisor` diz quanto foi dele.
"""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from campsverso_contracts import CONTRACT_TYPES, subject
from campsverso_ports import (
    EventBus,
    IdGenerator,
    ModelCallError,
    ModelCapabilities,
    ModelPort,
    ModelRequest,
    ModelResponse,
    ModelUsage,
    WallClock,
    request_sha256,
)

COMPLETED = "campsverso.llm.call.completed.v1"
FAILED = "campsverso.llm.call.failed.v1"
type SimClock = Callable[[], tuple[int, str]]  # (tick, sim_time) do mundo, para o envelope


@dataclass(frozen=True, slots=True)
class ModelPrices:
    """Dólares por milhão de tokens: entrada, saída, cache lido e cache gravado."""

    input_per_mtok: float
    output_per_mtok: float
    cache_read_per_mtok: float
    cache_write_per_mtok: float


def cost_usd(usage: ModelUsage, prices: ModelPrices) -> float:
    total = (
        usage.input_tokens * prices.input_per_mtok
        + usage.output_tokens * prices.output_per_mtok
        + usage.cache_read_input_tokens * prices.cache_read_per_mtok
        + usage.cache_creation_input_tokens * prices.cache_write_per_mtok
    )
    return round(total / 1_000_000, 8)


def _advisors(request: ModelRequest) -> list[str]:
    """Os modelos de conselheiro que o pedido oferece (ADR-0074): precisam de preço também."""
    return [
        str(t["model"])
        for t in request.tools
        if str(t.get("type", "")).startswith("advisor_") and t.get("model")
    ]


class MeteredModel:
    def __init__(
        self,
        inner: ModelPort,
        *,
        bus: EventBus,
        worldid: str,
        cartridge: str,
        controller: Mapping[str, str],  # {type, id}, como no controller_ref dos contratos
        prices: Mapping[str, ModelPrices],
        clock: WallClock,
        ids: IdGenerator,
        sim_clock: SimClock | None = None,
    ) -> None:
        self._inner = inner
        self._bus = bus
        self._worldid = worldid
        self._cartridge = cartridge
        self._controller = dict(controller)
        self._prices = dict(prices)
        self._clock = clock
        self._ids = ids
        self._sim_clock = sim_clock
        self._seq = 0
        self.spent_usd = 0.0  # soma das chamadas cobradas neste processo

    @property
    def provider(self) -> str:
        return self._inner.provider

    def capabilities(self) -> ModelCapabilities:
        return self._inner.capabilities()

    def assert_priced(self, model: str) -> None:
        """Para a partida de quem compõe: modelo sem preço derruba o processo, nunca uma chamada."""
        if model not in self._prices:
            raise LookupError(f"modelo sem preço na tabela do ambiente: {model}")

    async def complete(self, request: ModelRequest) -> ModelResponse:
        for model in (request.model, *_advisors(request)):
            if model not in self._prices:
                raise ModelCallError(
                    "bad_request", f"modelo sem preço na tabela: {model}", retryable=False
                )
        started = self._clock.monotonic()
        try:
            response = await self._inner.complete(request)
        except ModelCallError as error:
            await self._publish(
                FAILED,
                request,
                round((self._clock.monotonic() - started) * 1000),
                {
                    "error": error.kind,
                    "message": error.message[:1000],
                    "retryable": error.retryable,
                },
            )
            raise
        cost = cost_usd(response.usage, self._prices[request.model])
        advised: dict[str, Any] | None = None
        if response.advisor is not None:
            advisor = response.advisor
            paid = cost_usd(advisor.usage, self._prices[advisor.model])
            advised = {
                "model": advisor.model,
                "calls": advisor.calls,
                "usage": advisor.usage.as_dict(),
                "cost_usd": paid,
            }
            cost = round(cost + paid, 8)
        charged = not response.replayed
        if charged:
            self.spent_usd += cost
        data: dict[str, Any] = {
            "usage": response.usage.as_dict(),
            "cost_usd": cost,
            "charged": charged,
            "stop_reason": response.stop_reason,
        }
        if response.request_id:
            data["request_id"] = response.request_id
        if request.effort is not None:
            data["effort"] = request.effort
        if advised is not None:
            data["advisor"] = advised
        await self._publish(COMPLETED, request, response.latency_ms, data)
        return response

    async def count_tokens(self, request: ModelRequest) -> int:
        return await self._inner.count_tokens(request)  # contar não custa nem vira evento

    async def _publish(
        self, event_type: str, request: ModelRequest, latency_ms: int, extra: Mapping[str, Any]
    ) -> None:
        info = CONTRACT_TYPES[event_type]
        tick, sim_time = (
            self._sim_clock() if self._sim_clock else (0, self._clock.now().isoformat())
        )
        data: dict[str, Any] = {
            "controller": dict(self._controller),
            "purpose": request.purpose,
            "provider": self._inner.provider,
            "model": request.model,
            "prompt_sha256": request_sha256(request),
            "latency_ms": latency_ms,
            **extra,
        }
        if request.avatar_id is not None:
            data["avatar_id"] = request.avatar_id
        envelope: dict[str, Any] = {
            "specversion": "1.0",
            "id": self._ids.new_id(),
            "source": f"/controller-runner/{self._controller['id']}",
            "type": event_type,
            "time": self._clock.now().isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            "datacontenttype": "application/json",
            "dataschema": info.dataschema,
            "worldid": self._worldid,
            "cartridge": self._cartridge,
            "tick": tick,
            "simtime": sim_time,
            "seq": self._seq,
            "actor": "system/controller-runner",
            "provenance": "simulated",
            "visibility": info.visibility,
            "data": data,
        }
        if request.avatar_id is not None:
            envelope["subject"] = f"avatar/{request.avatar_id}"
        self._seq += 1
        await self._bus.publish(subject(event_type, self._worldid), envelope)
