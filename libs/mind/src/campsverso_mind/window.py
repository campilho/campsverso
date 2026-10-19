"""A janela de conversa (ADR-0059): segue a política da percepção (ADR-0056).

Uma foto abre a janela; cada delta é o resultado (`tool_result`) da ferramenta que o modelo
escolheu antes; a foto seguinte fecha a janela e a conversa recomeça. Entregas que chegam sem o
modelo ter sido chamado (pedidos superados) se acumulam no próximo turno do usuário: nada se perde,
porque cada delta é a única cópia do que aconteceu no meio-tempo.

Tudo o que vai para o modelo é função só das entregas: nenhum relógio de parede, nenhum id de
evento, para a mesma sessão produzir os mesmos pedidos (e a fita reproduzi-los).
"""

import json
from collections.abc import Mapping, Sequence
from typing import Any, cast

REJECTED = "campsverso.action.rejected.v1"
FAILED = "campsverso.action.failed.v1"
CACHE = {"type": "ephemeral"}

_REASONS = {
    "session_started": "A sessão começou.",
    "possessed": "Você assumiu o corpo.",
    "action_completed": "Sua ação terminou.",
    "action_rejected": "Sua ação foi recusada",
    "action_interrupted": "Sua ação foi interrompida",
    "phase_changed": "A fase do dia mudou.",
    "need_threshold": "Uma necessidade passou de um limiar.",
    "woke_up": "Você acordou.",
}
_IGNORED = "Ignorada: uma ação por vez; só a primeira ferramenta foi proposta."


def _trim(value: Any) -> Any:
    """Os números de ponto flutuante com uma casa: `99.96666666666667` são tokens jogados fora."""
    if isinstance(value, float):
        return round(value, 1)
    if isinstance(value, Mapping):
        return {str(k): _trim(v) for k, v in cast(Mapping[str, Any], value).items()}
    if isinstance(value, list | tuple):
        return [_trim(v) for v in cast(Sequence[Any], value)]
    return value


def _json(value: Any) -> str:
    return json.dumps(_trim(value), ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _last(events: Sequence[Mapping[str, Any]], event_type: str) -> Mapping[str, Any] | None:
    for event in reversed(events):
        if event.get("type") == event_type:
            return cast(Mapping[str, Any], event.get("data") or {})
    return None


def reason_text(delivery: Mapping[str, Any]) -> str:
    """O motivo do pedido em uma linha; a recusa e a interrupção trazem o motivo do kernel."""
    decision = cast(Mapping[str, Any], delivery.get("decision") or {})
    reason = str(decision.get("reason", ""))
    head = _REASONS.get(reason, f"Pedido de decisão: {reason}.")
    events = cast(Sequence[Mapping[str, Any]], delivery.get("events") or ())
    if reason == "action_rejected":
        rejected = _last(events, REJECTED)
        if rejected is None:
            return head + "."
        detail = f" {rejected['detail']}" if rejected.get("detail") else ""
        return f"{head}: {rejected.get('reason', '?')}.{detail}"
    if reason == "action_interrupted":
        failed = _last(events, FAILED)
        return head + (f": {failed.get('reason', '?')}." if failed is not None else ".")
    return head


def is_snapshot(delivery: Mapping[str, Any]) -> bool:
    return "view" in delivery


def render_snapshot(delivery: Mapping[str, Any]) -> str:
    return (
        f"{reason_text(delivery)}\n"
        f"Foto do mundo no tick {delivery.get('as_of_tick')}:\n{_json(delivery['view'])}"
    )


def render_delta(delivery: Mapping[str, Any]) -> str:
    body = {
        k: v
        for k, v in delivery.items()
        if k not in ("avatar_id", "decision", "since_tick", "as_of_tick")
    }
    return (
        f"{reason_text(delivery)}\n"
        f"O que mudou do tick {delivery.get('since_tick')} ao {delivery.get('as_of_tick')}:\n"
        f"{_json(body)}"
    )


class Window:
    def __init__(self) -> None:
        self.messages: list[dict[str, Any]] = []  # turnos já respondidos
        self.pending: list[str] = []  # o próximo turno do usuário, por entrega
        self.pending_error = False  # a entrega pendente traz uma recusa
        self.open_tools: list[
            str
        ] = []  # ids das ferramentas do último turno, à espera do resultado
        self.deliveries = 0
        self.snapshots = 0

    @property
    def is_open(self) -> bool:
        return bool(self.messages or self.pending)

    def observe(self, delivery: Mapping[str, Any]) -> None:
        """Uma entrega da percepção: a foto abre uma janela nova; o delta entra no próximo turno."""
        self.deliveries += 1
        if is_snapshot(delivery):
            self.snapshots += 1
            self.messages, self.open_tools = [], []
            self.pending, self.pending_error = [render_snapshot(delivery)], False
            return
        self.pending.append(render_delta(delivery))
        decision = cast(Mapping[str, Any], delivery.get("decision") or {})
        if decision.get("reason") == "action_rejected":
            self.pending_error = True

    def user_turn(self) -> dict[str, Any]:
        """O turno do usuário com o que está pendente: resultado da ferramenta aberta, ou texto."""
        text = "\n\n".join(self.pending)
        blocks: list[dict[str, Any]] = []
        if self.open_tools:
            first, *extra = self.open_tools
            blocks.append({"type": "tool_result", "tool_use_id": first, "content": text})
            if self.pending_error:
                blocks[0]["is_error"] = True
            blocks.extend(
                {"type": "tool_result", "tool_use_id": t, "content": _IGNORED, "is_error": True}
                for t in extra
            )
        else:
            blocks.append({"type": "text", "text": text})
        return {"role": "user", "content": blocks}

    def request_messages(self) -> list[dict[str, Any]]:
        """As mensagens de um pedido: os turnos respondidos mais o pendente, com o marcador de
        cache no último bloco (o prefixo cresce; o marcador anda com ele)."""
        if not self.pending:
            raise ValueError("nada pendente: nenhuma entrega desde a última resposta")
        turn = self.user_turn()
        last = dict(cast(Sequence[Mapping[str, Any]], turn["content"])[-1])
        last["cache_control"] = dict(CACHE)
        turn["content"] = [*cast(list[dict[str, Any]], turn["content"])[:-1], last]
        return [*self.messages, turn]

    def answered(self, content: Sequence[Mapping[str, Any]]) -> None:
        """O modelo respondeu: o turno pendente e a resposta inteira (com os blocos `thinking`,
        que precisam voltar) entram na janela; as ferramentas da resposta ficam abertas."""
        self.messages.append(self.user_turn())
        self.messages.append({"role": "assistant", "content": [dict(b) for b in content]})
        self.pending, self.pending_error = [], False
        self.open_tools = [str(b["id"]) for b in content if b.get("type") == "tool_use"]
