"""BlockRun provider — pay-per-request LLM routing with crypto micropayments.

BlockRun (https://blockrun.ai) is a unified AI gateway supporting 30+ models
from OpenAI, Anthropic, Google, xAI, DeepSeek, and more. Uses USDC micropayments
on Base chain instead of API keys — no account creation required.

Env var: BLOCKRUN_WALLET_KEY (Base wallet private key)
"""

from __future__ import annotations

import time

from openai import AsyncOpenAI, RateLimitError

from voyage_geo.config.schema import ProviderConfig
from voyage_geo.core.errors import GeoProviderError, GeoRateLimitError
from voyage_geo.providers.base import BaseProvider, ProviderResponse

# CLI name → (BlockRun model ID, display name)
BLOCKRUN_MODELS: dict[str, tuple[str, str]] = {
    "blockrun-gpt5": ("openai/gpt-5.2", "GPT-5.2"),
    "blockrun-gpt4o": ("openai/gpt-4o", "GPT-4o"),
    "blockrun-claude": ("anthropic/claude-sonnet-4", "Claude Sonnet 4"),
    "blockrun-gemini": ("google/gemini-2.5-flash", "Gemini 2.5 Flash"),
    "blockrun-grok": ("xai/grok-3", "Grok 3"),
    "blockrun-deepseek": ("deepseek/deepseek-chat", "DeepSeek"),
    "blockrun-llama": ("meta-llama/llama-4-maverick", "Llama 4"),
}


class BlockRunProvider(BaseProvider):
    name = "blockrun"
    display_name = "BlockRun"

    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)
        # Resolve identity from the config name (like OpenRouter does)
        model_id, display = BLOCKRUN_MODELS.get(config.name, (None, None))
        if model_id:
            self.name = config.name
            self.display_name = display  # type: ignore[assignment]
            self._model_id = model_id
        else:
            self._model_id = config.model or "openai/gpt-4o"

        self.client = AsyncOpenAI(
            api_key=config.api_key or "unused",  # BlockRun uses wallet key, not API key
            base_url=config.base_url or "https://blockrun.ai/api/v1",
            default_headers={
                "x-wallet-key": config.api_key or "",
            },
        )

    async def query(self, prompt: str) -> ProviderResponse:
        model = self._model_id
        start = time.perf_counter()
        try:
            kwargs: dict = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
            }
            if self.config.temperature is not None:
                kwargs["temperature"] = self.config.temperature
            if self.config.max_tokens is not None:
                kwargs["max_tokens"] = self.config.max_tokens
            response = await self.client.chat.completions.create(**kwargs)
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
                text=text,
                model=response.model,
                provider=self.name,
                latency_ms=latency,
                token_usage=usage,
            )
        except RateLimitError as e:
            raise GeoRateLimitError(str(e), self.name)
        except GeoProviderError:
            raise
        except Exception as e:
            raise self._wrap_error(e)
