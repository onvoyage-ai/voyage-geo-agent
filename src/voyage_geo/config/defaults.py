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
    "chatgpt": ProviderConfig(
        name="chatgpt",
        max_tokens=512,
        temperature=0.7,
        base_url="https://openrouter.ai/api/v1",
    ),
    "gemini": ProviderConfig(
        name="gemini",
        max_tokens=512,
        temperature=0.7,
        base_url="https://openrouter.ai/api/v1",
    ),
    "claude": ProviderConfig(
        name="claude",
        max_tokens=512,
        temperature=0.7,
        base_url="https://openrouter.ai/api/v1",
    ),
    "perplexity-or": ProviderConfig(
        name="perplexity-or",
        max_tokens=512,
        temperature=0.7,
        base_url="https://openrouter.ai/api/v1",
    ),
    "deepseek": ProviderConfig(
        name="deepseek",
        max_tokens=512,
        temperature=0.7,
        base_url="https://openrouter.ai/api/v1",
    ),
    "grok": ProviderConfig(
        name="grok",
        max_tokens=512,
        temperature=0.7,
        base_url="https://openrouter.ai/api/v1",
    ),
    "llama": ProviderConfig(
        name="llama",
        max_tokens=512,
        temperature=0.7,
        base_url="https://openrouter.ai/api/v1",
    ),
}
