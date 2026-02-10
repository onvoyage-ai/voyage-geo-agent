"""Text processing helpers."""

from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from voyage_geo.providers.base import BaseProvider

logger = structlog.get_logger()


def truncate(text: str, max_length: int) -> str:
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def count_occurrences(text: str, term: str) -> int:
    return len(re.findall(re.escape(term), text, re.IGNORECASE))


def extract_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in parts if s.strip()]


def contains_brand(text: str, brand: str) -> bool:
    return bool(re.search(rf"\b{re.escape(brand)}\b", text, re.IGNORECASE))


def extract_brand_mentions(text: str, brands: list[str]) -> dict[str, int]:
    return {brand: count_occurrences(text, brand) for brand in brands}


def clean_response_text(text: str) -> str:
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[^\S\n]{2,}", " ", text)
    return text.strip()


async def extract_competitors_with_llm(
    responses: list[str],
    target_brand: str,
    category: str,
    provider: BaseProvider,
    max_competitors: int = 10,
) -> list[str]:
    """Extract competitor brand/company names from AI responses using an LLM.

    Sends concatenated response texts to an LLM and asks it to extract
    real company/brand/product names, excluding the target brand.
    """
    # Concatenate responses, truncating to ~12k chars to fit context
    combined = "\n---\n".join(responses)
    combined = truncate(combined, 12000)

    prompt = f"""Extract all company, brand, and product names mentioned in the following AI responses about the "{category}" industry.

RULES:
- Only include real companies, brands, or product names
- Exclude "{target_brand}" (that is our target brand)
- Exclude generic terms, technologies, acronyms, and non-brand words
- Order by how frequently they appear (most frequent first)
- Return at most {max_competitors} names
- Return ONLY a valid JSON array of strings, nothing else

Example output: ["Ramp", "Divvy", "Expensify"]

AI RESPONSES:
{combined}

JSON array of brand names (no explanation, just the array):"""

    try:
        resp = await provider.query(prompt)
        text = resp.text.strip()
        # Extract JSON array from response (handle markdown fences)
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()
        # Find the array in the text
        start = text.find("[")
        end = text.rfind("]")
        if start != -1 and end != -1:
            text = text[start : end + 1]
        names = json.loads(text)
        if isinstance(names, list):
            # Deduplicate while preserving order, filter out target brand
            seen: set[str] = set()
            result: list[str] = []
            for name in names:
                if isinstance(name, str) and name.lower() != target_brand.lower() and name not in seen:
                    seen.add(name)
                    result.append(name)
            return result[:max_competitors]
    except Exception:
        logger.warning("llm_competitor_extraction_failed", target=target_brand)
    return []
