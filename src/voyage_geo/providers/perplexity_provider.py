"""Perplexity provider (uses OpenAI SDK with custom base URL)."""

from __future__ import annotations

import time

from openai import AsyncOpenAI, RateLimitError

from voyage_geo.config.schema import ProviderConfig
from voyage_geo.core.errors import GeoProviderError, GeoRateLimitError
from voyage_geo.providers.base import BaseProvider, ProviderResponse


class PerplexityProvider(BaseProvider):
    name = "perplexity"
    display_name = "Perplexity"

    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)
        self.client = AsyncOpenAI(
            api_key=config.api_key,
            base_url=config.base_url or "https://api.perplexity.ai",
        )

    async def query(self, prompt: str) -> ProviderResponse:
        model = self.config.model or "sonar-pro"
        start = time.perf_counter()
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
            )
            text = response.choices[0].message.content or ""
            latency = int((time.perf_counter() - start) * 1000)
            usage = None
            if response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }
            return ProviderResponse(
                text=text, model=response.model, provider=self.name,
                latency_ms=latency, token_usage=usage,
            )
        except RateLimitError as e:
            raise GeoRateLimitError(str(e), self.name)
        except GeoProviderError:
            raise
        except Exception as e:
            raise self._wrap_error(e)
