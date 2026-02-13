# Adding a New Provider

Voyage GEO uses a plugin system for AI providers. Follow these steps to add a new one.

## 1. Create the Provider File

Create `src/voyage_geo/providers/<name>_provider.py`:

```python
"""My Provider — description."""

from __future__ import annotations

import time

from voyage_geo.config.schema import ProviderConfig
from voyage_geo.core.errors import GeoProviderError
from voyage_geo.providers.base import BaseProvider, ProviderResponse


class MyProvider(BaseProvider):
    name = "myprovider"
    display_name = "My Provider"

    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)
        # Initialize your SDK client here
        self.client = SomeSDK(api_key=config.api_key)

    async def query(self, prompt: str) -> ProviderResponse:
        start = time.perf_counter()
        try:
            response = await self.client.chat(prompt)
            latency = int((time.perf_counter() - start) * 1000)

            return ProviderResponse(
                text=response.text,
                model=config.model or "default-model",
                provider=self.name,
                latency_ms=latency,
                token_usage={
                    "prompt_tokens": response.usage.input,
                    "completion_tokens": response.usage.output,
                    "total_tokens": response.usage.total,
                },
            )
        except Exception as e:
            raise self._wrap_error(e)
```

## 2. Register the Provider

In `src/voyage_geo/providers/registry.py`, add your provider to `PROVIDER_FACTORIES`:

```python
from voyage_geo.providers.my_provider import MyProvider

PROVIDER_FACTORIES: dict[str, type[BaseProvider]] = {
    # ... existing providers
    "myprovider": MyProvider,
}
```

## 3. Add Default Config

In `src/voyage_geo/config/defaults.py`:

```python
"myprovider": ProviderConfig(
    name="myprovider",
    model="default-model",
    max_tokens=512,
    temperature=0.7,
),
```

## 4. Add Environment Variable

In `.env.example`:

```
MYPROVIDER_API_KEY=...
```

In `src/voyage_geo/config/loader.py`, add env variable loading in the `_load_env_keys()` section.

## Key Interfaces

- `BaseProvider` — abstract class with `query()`, `health_check()`, and `_wrap_error()` helpers
- `ProviderResponse` — dataclass returned by `query()`: text, model, provider, latency_ms, token_usage
- `ProviderConfig` — Pydantic model for provider configuration (name, model, api_key, max_tokens, temperature)
