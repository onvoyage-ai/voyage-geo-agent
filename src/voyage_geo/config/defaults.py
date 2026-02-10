"""Default provider configurations."""

from voyage_geo.config.schema import ProviderConfig

DEFAULT_PROVIDERS: dict[str, ProviderConfig] = {
    "openai": ProviderConfig(
        name="openai",
        model="gpt-4o-mini",
        max_tokens=512,
        temperature=0.7,
    ),
    "anthropic": ProviderConfig(
        name="anthropic",
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        temperature=0.7,
    ),
    "google": ProviderConfig(
        name="google",
        model="gemini-2.0-flash",
        max_tokens=512,
        temperature=0.7,
    ),
    "perplexity": ProviderConfig(
        name="perplexity",
        model="sonar",
        max_tokens=512,
        temperature=0.7,
        base_url="https://api.perplexity.ai",
    ),
}
