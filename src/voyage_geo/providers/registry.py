"""Provider registry with factory pattern."""

from __future__ import annotations

from typing import TYPE_CHECKING

from voyage_geo.core.errors import GeoConfigError

if TYPE_CHECKING:
    from voyage_geo.config.schema import ProviderConfig
    from voyage_geo.providers.base import BaseProvider


def create_provider(name: str, config: ProviderConfig) -> BaseProvider:
    """Create a provider instance from a name and config without registering it."""
    from voyage_geo.providers.anthropic_provider import AnthropicProvider
    from voyage_geo.providers.google_provider import GoogleProvider
    from voyage_geo.providers.openai_provider import OpenAIProvider
    from voyage_geo.providers.openrouter_provider import OpenRouterProvider
    from voyage_geo.providers.perplexity_provider import PerplexityProvider

    factories: dict[str, type[BaseProvider]] = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "google": GoogleProvider,
        "perplexity": PerplexityProvider,
        "chatgpt": OpenRouterProvider,
        "gemini": OpenRouterProvider,
        "claude": OpenRouterProvider,
        "perplexity-or": OpenRouterProvider,
        "deepseek": OpenRouterProvider,
        "grok": OpenRouterProvider,
        "llama": OpenRouterProvider,
    }

    factory = factories.get(name)
    if not factory:
        raise GeoConfigError(f"Unknown provider: {name}. Available: {list(factories.keys())}")
    return factory(config)


class ProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, BaseProvider] = {}

    def register(self, name: str, config: ProviderConfig) -> None:
        self._providers[name] = create_provider(name, config)

    def get(self, name: str) -> BaseProvider:
        provider = self._providers.get(name)
        if not provider:
            raise GeoConfigError(f"Provider not registered: {name}")
        return provider

    def get_all(self) -> list[BaseProvider]:
        return list(self._providers.values())

    def get_enabled(self) -> list[BaseProvider]:
        return [p for p in self._providers.values() if p.is_configured()]

    def names(self) -> list[str]:
        return list(self._providers.keys())
