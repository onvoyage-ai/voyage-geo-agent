"""Default provider configurations."""

from voyage_geo.config.schema import ProviderConfig

DEFAULT_PROVIDERS: dict[str, ProviderConfig] = {
    "openai": ProviderConfig(
        name="openai",
        model="gpt-5-mini",
    ),
    "anthropic": ProviderConfig(
        name="anthropic",
        model="claude-haiku-4-5-20251001",
    ),
    "google": ProviderConfig(
        name="google",
        model="gemini-3-flash-preview",
    ),
    "perplexity": ProviderConfig(
        name="perplexity",
        model="sonar-pro",
        base_url="https://api.perplexity.ai",
    ),
    "chatgpt": ProviderConfig(
        name="chatgpt",
        base_url="https://openrouter.ai/api/v1",
    ),
    "gemini": ProviderConfig(
        name="gemini",
        base_url="https://openrouter.ai/api/v1",
    ),
    "claude": ProviderConfig(
        name="claude",
        base_url="https://openrouter.ai/api/v1",
    ),
    "perplexity-or": ProviderConfig(
        name="perplexity-or",
        base_url="https://openrouter.ai/api/v1",
    ),
    "deepseek": ProviderConfig(
        name="deepseek",
        base_url="https://openrouter.ai/api/v1",
    ),
    "grok": ProviderConfig(
        name="grok",
        base_url="https://openrouter.ai/api/v1",
    ),
    "llama": ProviderConfig(
        name="llama",
        base_url="https://openrouter.ai/api/v1",
    ),
    "mistral": ProviderConfig(
        name="mistral",
        base_url="https://openrouter.ai/api/v1",
    ),
    "cohere": ProviderConfig(
        name="cohere",
        base_url="https://openrouter.ai/api/v1",
    ),
    "qwen": ProviderConfig(
        name="qwen",
        base_url="https://openrouter.ai/api/v1",
    ),
    "kimi": ProviderConfig(
        name="kimi",
        base_url="https://openrouter.ai/api/v1",
    ),
    "glm": ProviderConfig(
        name="glm",
        base_url="https://openrouter.ai/api/v1",
    ),
}
