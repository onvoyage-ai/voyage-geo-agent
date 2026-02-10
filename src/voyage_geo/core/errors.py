"""Error hierarchy for Voyage GEO."""


class GeoError(Exception):
    """Base error for all Voyage GEO errors."""

    code: str = "GEO_ERROR"

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class GeoConfigError(GeoError):
    code = "CONFIG_ERROR"


class GeoProviderError(GeoError):
    code = "PROVIDER_ERROR"

    def __init__(self, message: str, provider: str) -> None:
        self.provider = provider
        super().__init__(f"[{provider}] {message}")


class GeoRateLimitError(GeoProviderError):
    code = "RATE_LIMIT_ERROR"


class GeoTimeoutError(GeoProviderError):
    code = "TIMEOUT_ERROR"


class GeoPipelineError(GeoError):
    code = "PIPELINE_ERROR"

    def __init__(self, message: str, stage: str) -> None:
        self.stage = stage
        super().__init__(f"[{stage}] {message}")


class GeoStorageError(GeoError):
    code = "STORAGE_ERROR"
