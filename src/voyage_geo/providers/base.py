"""Base provider with shared functionality."""

from __future__ import annotations

import abc
import asyncio
import time

from voyage_geo.config.schema import ProviderConfig
from voyage_geo.core.errors import GeoProviderError, GeoTimeoutError


class ProviderResponse:
    __slots__ = ("text", "model", "provider", "latency_ms", "token_usage")

    def __init__(
        self,
        text: str,
        model: str,
        provider: str,
        latency_ms: int,
        token_usage: dict | None = None,
    ) -> None:
        self.text = text
        self.model = model
        self.provider = provider
        self.latency_ms = latency_ms
        self.token_usage = token_usage


class BaseProvider(abc.ABC):
    name: str
    display_name: str

    def __init__(self, config: ProviderConfig) -> None:
        self.config = config

    @abc.abstractmethod
    async def query(self, prompt: str) -> ProviderResponse: ...

    def is_configured(self) -> bool:
        return bool(self.config.api_key)

    async def health_check(self) -> dict:
        start = time.perf_counter()
        try:
            resp = await asyncio.wait_for(
                self.query("Say 'ok'"),
                timeout=15.0,
            )
            latency = int((time.perf_counter() - start) * 1000)
            return {"provider": self.name, "healthy": True, "latency_ms": latency, "model": resp.model}
        except Exception as e:
            latency = int((time.perf_counter() - start) * 1000)
            return {"provider": self.name, "healthy": False, "latency_ms": latency, "model": "", "error": str(e)}

    async def _with_timeout(self, coro, timeout_ms: int | None = None):
        timeout = (timeout_ms or 30000) / 1000
        timeout = max(timeout, 15.0)
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except TimeoutError:
            raise GeoTimeoutError(f"Request timed out after {timeout}s", self.name)

    def _wrap_error(self, err: Exception) -> GeoProviderError:
        return GeoProviderError(str(err), self.name)
