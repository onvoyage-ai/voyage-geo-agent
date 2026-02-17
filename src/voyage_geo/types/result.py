from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from voyage_geo.storage.schema import SCHEMA_VERSION


class TokenUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class QueryResult(BaseModel):
    query_id: str
    query_text: str
    provider: str
    model: str
    response: str
    latency_ms: int
    token_usage: TokenUsage | None = None
    iteration: int = 1
    timestamp: str = ""
    error: str | None = None


class ExecutionRun(BaseModel):
    schema_version: str = SCHEMA_VERSION
    run_id: str
    brand: str
    providers: list[str]
    total_queries: int
    completed_queries: int = 0
    failed_queries: int = 0
    results: list[QueryResult] = []
    started_at: str = ""
    completed_at: str | None = None
    status: Literal["running", "completed", "failed", "partial"] = "running"
