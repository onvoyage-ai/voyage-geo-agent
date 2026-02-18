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
    "blockrun": ProviderConfig(
        name="blockrun",
        model="openai/gpt-4o",
        base_url="https://blockrun.ai/api/v1",
    ),
    "blockrun-gpt5": ProviderConfig(
        name="blockrun-gpt5",
        base_url="https://blockrun.ai/api/v1",
    ),
    "blockrun-gpt4o": ProviderConfig(
        name="blockrun-gpt4o",
        base_url="https://blockrun.ai/api/v1",
    ),
    "blockrun-claude": ProviderConfig(
        name="blockrun-claude",
        base_url="https://blockrun.ai/api/v1",
    ),
    "blockrun-gemini": ProviderConfig(
        name="blockrun-gemini",
        base_url="https://blockrun.ai/api/v1",
    ),
    "blockrun-grok": ProviderConfig(
        name="blockrun-grok",
        base_url="https://blockrun.ai/api/v1",
    ),
    "blockrun-deepseek": ProviderConfig(
        name="blockrun-deepseek",
        base_url="https://blockrun.ai/api/v1",
    ),
    "blockrun-llama": ProviderConfig(
        name="blockrun-llama",
        base_url="https://blockrun.ai/api/v1",
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
