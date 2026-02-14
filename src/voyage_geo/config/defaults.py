"""Default provider configurations."""

from voyage_geo.config.schema import ProviderConfig

DEFAULT_PROVIDERS: dict[str, ProviderConfig] = {
    "openai": ProviderConfig(
        name="openai",
        model="gpt-5-mini",
        temperature=0.7,
    ),
    "anthropic": ProviderConfig(
        name="anthropic",
        model="claude-haiku-4-5-20251001",
        temperature=0.7,
    ),
    "google": ProviderConfig(
        name="google",
        model="gemini-3-flash-preview",
        temperature=0.7,
    ),
    "perplexity": ProviderConfig(
        name="perplexity",
        model="sonar-pro",
        temperature=0.7,
        base_url="https://api.perplexity.ai",
    ),
    "chatgpt": ProviderConfig(
        name="chatgpt",
        temperature=0.7,
        base_url="https://openrouter.ai/api/v1",
    ),
    "gemini": ProviderConfig(
        name="gemini",
        temperature=0.7,
        base_url="https://openrouter.ai/api/v1",
    ),
    "claude": ProviderConfig(
        name="claude",
        temperature=0.7,
        base_url="https://openrouter.ai/api/v1",
    ),
    "perplexity-or": ProviderConfig(
        name="perplexity-or",
        temperature=0.7,
        base_url="https://openrouter.ai/api/v1",
    ),
    "deepseek": ProviderConfig(
        name="deepseek",
        temperature=0.7,
        base_url="https://openrouter.ai/api/v1",
    ),
    "grok": ProviderConfig(
        name="grok",
        temperature=0.7,
        base_url="https://openrouter.ai/api/v1",
    ),
    "llama": ProviderConfig(
        name="llama",
        temperature=0.7,
        base_url="https://openrouter.ai/api/v1",
    ),
}
