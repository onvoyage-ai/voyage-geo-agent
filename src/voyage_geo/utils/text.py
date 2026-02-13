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


async def extract_narratives_with_llm(
    responses: list[str],
    target_brand: str,
    category: str,
    provider: BaseProvider,
) -> list[dict]:
    """Extract structured brand claims from AI responses using an LLM.

    Returns a list of dicts with keys: brand, attribute, sentiment, claim.
    Retries once with a smaller output constraint if JSON parsing fails.
    """
    combined = "\n---\n".join(responses)
    combined = truncate(combined, 15000)

    base_prompt = f"""Analyze the following AI responses about the "{category}" industry.
For every brand or company mentioned, extract each specific claim being made about it.

Return a JSON array of objects with these fields:
- "brand": the company/brand name
- "attribute": one of: pricing, features, security, ease-of-use, integration, support, scalability, performance, reliability, market-position
- "sentiment": "positive", "negative", or "neutral"
- "claim": a short summary of the specific claim (one sentence)

RULES:
- Extract ALL claims about ALL brands mentioned (including "{target_brand}")
- Each claim should be a distinct, specific assertion (not a vague statement)
- If a response says "X is known for great security", that's a positive security claim
- If a response says "X can be expensive", that's a negative pricing claim
- Return ONLY a valid JSON array, nothing else

AI RESPONSES:
{combined}

JSON array of claims:"""

    retry_suffix = "\nReturn at most 30 claims. Keep each claim summary under 10 words."

    for attempt in range(2):
        prompt = base_prompt if attempt == 0 else base_prompt + retry_suffix
        try:
            resp = await provider.query(prompt)
            text = resp.text.strip()
            # Extract JSON array from response (handle markdown fences)
            if "```" in text:
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
                text = text.strip()
            start = text.find("[")
            end = text.rfind("]")
            if start != -1 and end != -1:
                text = text[start : end + 1]
            claims = json.loads(text)
            if isinstance(claims, list):
                # Validate structure
                valid_claims = []
                for c in claims:
                    if (
                        isinstance(c, dict)
                        and "brand" in c
                        and "attribute" in c
                        and "sentiment" in c
                        and "claim" in c
                    ):
                        # Normalize sentiment
                        if c["sentiment"] not in ("positive", "negative", "neutral"):
                            c["sentiment"] = "neutral"
                        valid_claims.append(c)
                return valid_claims
        except json.JSONDecodeError as exc:
            logger.warning(
                "llm_narrative_json_parse_failed",
                target=target_brand,
                attempt=attempt + 1,
                error=str(exc),
            )
            if attempt == 0:
                continue  # retry with smaller output constraint
        except Exception as exc:
            logger.warning("llm_narrative_extraction_failed", target=target_brand, error=str(exc))
            break  # non-JSON errors don't benefit from retry
    return []
