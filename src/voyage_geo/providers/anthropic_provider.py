"""Anthropic / Claude provider."""

from __future__ import annotations

import time

import anthropic

from voyage_geo.config.schema import ProviderConfig
from voyage_geo.core.errors import GeoProviderError, GeoRateLimitError
from voyage_geo.providers.base import BaseProvider, ProviderResponse


class AnthropicProvider(BaseProvider):
    name = "anthropic"
    display_name = "Anthropic"

    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)
        self.client = anthropic.AsyncAnthropic(api_key=config.api_key)

    async def query(self, prompt: str) -> ProviderResponse:
        model = self.config.model or "claude-haiku-4-5-20251001"
        start = time.perf_counter()
        try:
            response = await self.client.messages.create(
                model=model,
                max_tokens=self.config.max_tokens or 4096,
                messages=[{"role": "user", "content": prompt}],
            )
            block = response.content[0] if response.content else None
            text = block.text if block and hasattr(block, "text") else ""
            latency = int((time.perf_counter() - start) * 1000)
            usage = {
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
            }
            return ProviderResponse(
                text=text, model=response.model, provider=self.name,
                latency_ms=latency, token_usage=usage,
            )
        except anthropic.RateLimitError as e:
            raise GeoRateLimitError(str(e), self.name)
        except GeoProviderError:
            raise
        except Exception as e:
            raise self._wrap_error(e)
