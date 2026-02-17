"""Schema version helpers for persisted run artifacts."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from voyage_geo.config.schema import VoyageGeoConfig

# Increment when persisted artifact contracts change.
SCHEMA_VERSION = "1.0.0"


def build_config_hash(config: VoyageGeoConfig) -> str:
    """Build a stable hash of non-secret config values for run comparability."""
    payload = config.model_dump()
    sanitized = _redact_secrets(payload)
    encoded = json.dumps(sanitized, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _redact_secrets(value: Any) -> Any:
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for key, item in value.items():
            if "api_key" in key.lower():
                out[key] = "***redacted***"
            else:
                out[key] = _redact_secrets(item)
        return out
    if isinstance(value, list):
        return [_redact_secrets(v) for v in value]
    return value
