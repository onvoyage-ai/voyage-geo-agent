"""Config loader — merges defaults < env < file < CLI overrides."""

from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv

from voyage_geo.config.defaults import DEFAULT_PROVIDERS
from voyage_geo.config.schema import ProviderConfig, VoyageGeoConfig

ENV_KEY_MAP = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "google": "GOOGLE_API_KEY",
    "perplexity": "PERPLEXITY_API_KEY",
    "chatgpt": "OPENROUTER_API_KEY",
    "gemini": "OPENROUTER_API_KEY",
    "claude": "OPENROUTER_API_KEY",
    "perplexity-or": "OPENROUTER_API_KEY",
    "deepseek": "OPENROUTER_API_KEY",
    "grok": "OPENROUTER_API_KEY",
    "llama": "OPENROUTER_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "mistral": "OPENROUTER_API_KEY",
    "cohere": "OPENROUTER_API_KEY",
    "qwen": "OPENROUTER_API_KEY",
    "kimi": "OPENROUTER_API_KEY",
    "glm": "OPENROUTER_API_KEY",
}

# Fallback chain for auto-detecting a processing provider (by capability).
# Each entry: (provider_name, model, env_key, base_url_or_None)
_PROCESSING_FALLBACKS = [
    ("anthropic", "claude-opus-4-6", "ANTHROPIC_API_KEY", None),
    ("openai", "gpt-5-mini", "OPENAI_API_KEY", None),
    ("google", "gemini-3-flash-preview", "GOOGLE_API_KEY", None),
    ("chatgpt", "openai/gpt-5-mini", "OPENROUTER_API_KEY", "https://openrouter.ai/api/v1"),
]


def load_config(
    config_path: str | None = None,
    overrides: dict | None = None,
) -> VoyageGeoConfig:
    load_dotenv()

    # Start with defaults
    providers: dict[str, ProviderConfig] = {}
    for name, default in DEFAULT_PROVIDERS.items():
        env_key = ENV_KEY_MAP.get(name)
        api_key = os.getenv(env_key) if env_key else None
        providers[name] = default.model_copy(update={"api_key": api_key} if api_key else {})

    config_data: dict = {"providers": {n: p.model_dump() for n, p in providers.items()}}

    # Merge file config
    if config_path:
        path = Path(config_path)
        if path.exists():
            with open(path) as f:
                file_data = json.load(f)
            _deep_merge(config_data, file_data)

    # Merge CLI overrides
    if overrides:
        _deep_merge(config_data, overrides)

    config = VoyageGeoConfig(**config_data)

    # Allow env var overrides for processing config
    env_proc_provider = os.getenv("PROCESSING_PROVIDER")
    env_proc_model = os.getenv("PROCESSING_MODEL")
    if env_proc_provider:
        config.processing.provider = env_proc_provider
    if env_proc_model:
        config.processing.model = env_proc_model

    # Resolve processing provider API key from env vars (if not already set)
    if not config.processing.api_key:
        processing_env_key = ENV_KEY_MAP.get(config.processing.provider)
        if processing_env_key:
            config.processing.api_key = os.getenv(processing_env_key)

    # Auto-fallback: if the default provider has no key AND the user didn't
    # explicitly set PROCESSING_PROVIDER, try the fallback chain.
    if not config.processing.api_key and not env_proc_provider:
        for prov, model, env_key, base_url in _PROCESSING_FALLBACKS:
            key = os.getenv(env_key)
            if key:
                config.processing.provider = prov
                config.processing.model = model
                config.processing.api_key = key
                config.processing.base_url = base_url
                break

    return config


def _deep_merge(base: dict, override: dict) -> dict:
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
    return base
