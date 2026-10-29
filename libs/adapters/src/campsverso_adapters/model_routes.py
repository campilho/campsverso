"""Qual adaptador atende um modelo (ADR-0074, decisão 10): a OpenRouter, quando a tabela do
ambiente dá ao modelo um provedor fixo nela (`openrouter:`); a API da Anthropic, se não."""

from collections.abc import Mapping

from campsverso_adapters.model_anthropic import AnthropicModel
from campsverso_adapters.model_openrouter import KEY_VARIABLE, OpenRouterModel
from campsverso_ports import WallClock

ANTHROPIC_KEY = "ANTHROPIC_API_KEY"


def model_port(
    model: str, *, routes: Mapping[str, str], clock: WallClock
) -> AnthropicModel | OpenRouterModel:
    """O adaptador do modelo; os dois têm `aclose`, para quem roda várias corridas."""
    if model in routes:
        return OpenRouterModel(routes, clock=clock)
    return AnthropicModel(clock=clock)


def key_variable(model: str, routes: Mapping[str, str]) -> str:
    """A variável de ambiente com a chave de quem atende o modelo."""
    return KEY_VARIABLE if model in routes else ANTHROPIC_KEY
