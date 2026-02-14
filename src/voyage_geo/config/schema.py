from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ProviderConfig(BaseModel):
    name: str
    enabled: bool = True
    api_key: str | None = None
    model: str | None = None
    base_url: str | None = None
    max_tokens: int | None = None
    temperature: float = 0.7
    rate_limit_rpm: int = 60


class ExecutionConfig(BaseModel):
    concurrency: int = 10
    retries: int = 3
    retry_delay_ms: int = 1000
    timeout_ms: int = 30000
    iterations: int = 1


class QueryConfig(BaseModel):
    count: int = 20
    strategies: list[Literal["keyword", "persona", "competitor", "intent"]] = Field(
        default=["keyword", "persona", "intent"]
    )


class AnalysisConfig(BaseModel):
    analyzers: list[
        Literal[
            "mindshare",
            "mention-rate",
            "sentiment",
            "positioning",
            "rank-position",
            "citation",
            "competitor",
            "narrative",
        ]
    ] = Field(
        default=[
            "mindshare",
            "mention-rate",
            "sentiment",
            "positioning",
            "rank-position",
            "citation",
            "competitor",
            "narrative",
        ]
    )


class ProcessingConfig(BaseModel):
    """Config for the dedicated processing model used in non-execution LLM calls."""

    provider: str = "anthropic"
    model: str = "claude-opus-4-6"
    api_key: str | None = None
    max_tokens: int = 4096
    temperature: float = 0.7


class ReportConfig(BaseModel):
    formats: list[Literal["html", "json", "csv", "markdown"]] = Field(default=["html", "json"])
    include_charts: bool = True
    include_raw_data: bool = False


class VoyageGeoConfig(BaseModel):
    brand: str | None = None
    website: str | None = None
    competitors: list[str] = []
    providers: dict[str, ProviderConfig] = {}
    processing: ProcessingConfig = ProcessingConfig()
    execution: ExecutionConfig = ExecutionConfig()
    queries: QueryConfig = QueryConfig()
    analysis: AnalysisConfig = AnalysisConfig()
    report: ReportConfig = ReportConfig()
    output_dir: str = "./data/runs"
    log_level: Literal["debug", "info", "warning", "error"] = "info"
