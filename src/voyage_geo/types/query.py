from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel

QueryCategory = Literal[
    "recommendation",
    "comparison",
    "best-of",
    "how-to",
    "review",
    "alternative",
    "general",
]

QueryStrategy = Literal["keyword", "persona", "competitor", "intent", "direct-rec", "vertical", "comparison", "scenario"]


class GeneratedQuery(BaseModel):
    id: str
    text: str
    category: QueryCategory
    strategy: QueryStrategy
    intent: str
    metadata: dict[str, Any] | None = None


class QuerySet(BaseModel):
    brand: str
    queries: list[GeneratedQuery]
    generated_at: str
    total_count: int
