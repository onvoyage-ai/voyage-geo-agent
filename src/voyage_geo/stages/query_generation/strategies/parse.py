"""Parse AI-generated query text into GeneratedQuery objects."""

from __future__ import annotations

import secrets
from typing import get_args

from voyage_geo.types.query import GeneratedQuery, QueryCategory, QueryStrategy

VALID_CATEGORIES: set[str] = set(get_args(QueryCategory))


def parse_ai_queries(
    text: str,
    strategy: QueryStrategy,
    prefix: str,
    max_count: int,
) -> list[GeneratedQuery]:
    queries: list[GeneratedQuery] = []
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    for line in lines:
        if len(queries) >= max_count:
            break

        # Strip numbering and bullets
        import re
        cleaned = re.sub(r"^\d+[.)]\s*", "", line)
        cleaned = re.sub(r"^[-*]\s*", "", cleaned).strip()
        if not cleaned or cleaned.startswith("#") or cleaned.startswith("```"):
            continue

        parts = [p.strip() for p in cleaned.split("|")]
        if len(parts) < 2:
            continue

        query_text = parts[0]
        if not query_text or len(query_text) < 10:
            continue

        raw_category = parts[1].lower().strip()
        category: QueryCategory = raw_category if raw_category in VALID_CATEGORIES else "general"  # type: ignore[assignment]
        intent = parts[2].lower().strip() if len(parts) > 2 else "general"
        persona = parts[3].lower().strip() if len(parts) > 3 else None

        metadata: dict = {}
        if persona:
            metadata["persona"] = persona

        queries.append(
            GeneratedQuery(
                id=f"{prefix}-{secrets.token_hex(4)}",
                text=query_text,
                category=category,
                strategy=strategy,
                intent=intent,
                metadata=metadata or None,
            )
        )

    return queries
