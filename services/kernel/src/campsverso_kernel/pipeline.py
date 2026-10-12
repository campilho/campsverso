"""Etapas do tick, em ordem configurável (ADR-0037)."""

DEFAULT_STAGES: tuple[str, ...] = (
    "scheduled",  # sistemas agendados para este horário
    "clock",  # kernel: fases do dia
    "needs",  # kernel: necessidades avançam e cruzam limiares
    "wake",  # kernel: avatares acordam
    "actions",  # kernel: ações que terminam neste tick
    "commands",  # kernel: ações propostas pelos controladores
    "reactions",  # sistemas disparados por limiar cruzado neste tick
    "decisions",  # kernel: pedidos de decisão para avatares ociosos
)

KERNEL_STAGES = frozenset({"clock", "needs", "wake", "actions", "commands", "decisions"})
