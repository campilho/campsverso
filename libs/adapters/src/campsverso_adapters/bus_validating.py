"""Decorador de EventBus que valida cada envelope antes de publicar (critério A2)."""

from campsverso_adapters.contract_validation import ContractValidator, Problem
from campsverso_ports import BatchHandler, Consumer, Envelope, EventBus, Handler, Subscription


class ContractViolationError(Exception):
    def __init__(self, subject: str, problems: list[Problem]) -> None:
        details = "; ".join(str(p) for p in problems)
        super().__init__(f"evento recusado em {subject}: {details}")
        self.problems = problems


class ValidatingBus:
    """Usado em desenvolvimento e nos testes: nenhum evento sai sem passar pelo contrato."""

    def __init__(self, inner: EventBus, validator: ContractValidator | None = None) -> None:
        self._inner = inner
        self._validator = validator or ContractValidator()

    async def publish(self, subject: str, envelope: Envelope) -> None:
        problems = self._validator.validate(envelope, published_subject=subject)
        if problems:
            raise ContractViolationError(subject, problems)
        await self._inner.publish(subject, envelope)

    async def subscribe(self, pattern: str, handler: Handler) -> Subscription:
        return await self._inner.subscribe(pattern, handler)

    async def consume(self, pattern: str, durable: str, handler: BatchHandler) -> Consumer:
        return await self._inner.consume(pattern, durable, handler)
