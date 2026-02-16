"""OpenRouter provider — single API key for all major AI models."""

from __future__ import annotations

import time

from openai import AsyncOpenAI, RateLimitError

from voyage_geo.config.schema import ProviderConfig
from voyage_geo.core.errors import GeoProviderError, GeoRateLimitError
from voyage_geo.providers.base import BaseProvider, ProviderResponse

# CLI name → (OpenRouter model ID, display name)
OPENROUTER_MODELS: dict[str, tuple[str, str]] = {
    "chatgpt": ("openai/gpt-5-mini", "ChatGPT"),
    "gemini": ("google/gemini-3-flash-preview", "Gemini"),
    "claude": ("anthropic/claude-sonnet-4.5", "Claude"),
    "perplexity-or": ("perplexity/sonar-pro", "Perplexity"),
    "deepseek": ("deepseek/deepseek-v3.2", "DeepSeek"),
    "grok": ("x-ai/grok-3", "Grok"),
    "llama": ("meta-llama/llama-4-maverick", "Llama"),
    "mistral": ("mistralai/mistral-large-2512", "Mistral"),
    "cohere": ("cohere/command-a-03-2025", "Cohere"),
    "qwen": ("qwen/qwen3-235b-a22b-07-25", "Qwen"),
    "kimi": ("moonshotai/kimi-k2.5-0127", "Kimi"),
    "glm": ("thudm/glm-4-32b", "GLM"),
}


class OpenRouterProvider(BaseProvider):
    name = "openrouter"
    display_name = "OpenRouter"

    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)
        # Resolve identity from the config name
        model_id, display = OPENROUTER_MODELS.get(config.name, (None, None))
        if model_id:
            self.name = config.name
            self.display_name = display  # type: ignore[assignment]
            self._model_id = model_id
        else:
            self._model_id = config.model or "openai/gpt-5-mini"

        self.client = AsyncOpenAI(
            api_key=config.api_key,
            base_url=config.base_url or "https://openrouter.ai/api/v1",
        )

    async def query(self, prompt: str) -> ProviderResponse:
        start = time.perf_counter()
        try:
            kwargs: dict = {
                "model": self._model_id,
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
                text=text, model=response.model, provider=self.name,
                latency_ms=latency, token_usage=usage,
            )
        except RateLimitError as e:
            raise GeoRateLimitError(str(e), self.name)
        except GeoProviderError:
            raise
        except Exception as e:
            raise self._wrap_error(e)
