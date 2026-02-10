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
}


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

    return VoyageGeoConfig(**config_data)


def _deep_merge(base: dict, override: dict) -> dict:
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
    return base
