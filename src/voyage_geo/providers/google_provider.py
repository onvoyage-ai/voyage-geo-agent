"""Google Gemini provider."""

from __future__ import annotations

import time

from google import genai
from google.genai import types

from voyage_geo.config.schema import ProviderConfig
from voyage_geo.core.errors import GeoProviderError
from voyage_geo.providers.base import BaseProvider, ProviderResponse


class GoogleProvider(BaseProvider):
    name = "google"
    display_name = "Google Gemini"

    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)
        self.client = genai.Client(api_key=config.api_key)

    async def query(self, prompt: str) -> ProviderResponse:
        model = self.config.model or "gemini-3-flash-preview"
        start = time.perf_counter()
        try:
            gen_config: dict = {}
            if self.config.temperature is not None:
                gen_config["temperature"] = self.config.temperature
            if self.config.max_tokens is not None:
                gen_config["max_output_tokens"] = self.config.max_tokens
            response = await self.client.aio.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(**gen_config),
            )
            text = response.text or ""
            latency = int((time.perf_counter() - start) * 1000)
            usage = None
            if response.usage_metadata:
                usage = {
                    "prompt_tokens": response.usage_metadata.prompt_token_count or 0,
                    "completion_tokens": response.usage_metadata.candidates_token_count or 0,
                    "total_tokens": response.usage_metadata.total_token_count or 0,
                }
            return ProviderResponse(
                text=text, model=model, provider=self.name,
                latency_ms=latency, token_usage=usage,
            )
        except GeoProviderError:
            raise
        except Exception as e:
            raise self._wrap_error(e)
