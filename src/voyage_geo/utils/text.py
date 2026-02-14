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


async def extract_all_brands_with_llm(
    responses: list[str],
    category: str,
    provider: BaseProvider,
    max_brands: int = 50,
    *,
    industry: str = "",
    keywords: list[str] | None = None,
    sample_queries: list[str] | None = None,
) -> list[str]:
    """Extract ALL brand/company names from AI responses — for leaderboard mode.

    Unlike extract_competitors_with_llm, this does NOT exclude any target brand.
    It extracts every brand mentioned, ordered by frequency, for ranking.
    Uses batched extraction for large response sets to avoid truncation.
    """
    # Build context block for the prompt
    context_parts = [f'Category: "{category}"']
    if industry:
        context_parts.append(f"Industry: {industry}")
    if keywords:
        context_parts.append(f"Keywords: {', '.join(keywords[:10])}")
    if sample_queries:
        q_list = "\n".join(f"  - {q}" for q in sample_queries[:5])
        context_parts.append(f"Sample queries we asked AI models:\n{q_list}")
    context_block = "\n".join(context_parts)

    # Split responses into chunks that fit context
    chunks: list[str] = []
    current_chunk: list[str] = []
    current_len = 0
    for resp in responses:
        if current_len + len(resp) > 12000 and current_chunk:
            chunks.append("\n---\n".join(current_chunk))
            current_chunk = []
            current_len = 0
        current_chunk.append(resp)
        current_len += len(resp)
    if current_chunk:
        chunks.append("\n---\n".join(current_chunk))

    all_names: list[str] = []
    seen: set[str] = set()

    for i, chunk in enumerate(chunks):
        prompt = f"""You are building a competitive leaderboard. We asked AI models questions about "{category}" and now need to extract which brands/companies WITHIN that category were recommended.

CONTEXT:
{context_block}

GOAL: Extract ONLY the names of entities that are actual competitors in the "{category}" category — the ones being ranked and recommended.

CRITICAL RULES:
- ONLY include brands that ARE "{category}" themselves — entities that directly compete in this space
- EXCLUDE companies mentioned as customers, portfolio companies, success stories, case studies, or examples from other industries
  Example: For "venture capital firms" → include "Sequoia Capital", "Andreessen Horowitz" — exclude "Airbnb", "Uber", "Stripe" (those are startups VCs invested in, not VCs)
  Example: For "CRM tools" → include "Salesforce", "HubSpot" — exclude "Amazon", "Tesla" (those are customers, not CRM tools)
- EXCLUDE generic terms, technologies, acronyms, people's names, and non-brand words
- Order by how frequently they appear (most frequent first)
- Return at most {max_brands} names
- Return ONLY a valid JSON array of strings, nothing else

AI RESPONSES:
{chunk}

JSON array of "{category}" brand names only:"""

        try:
            resp = await provider.query(prompt)
            text = resp.text.strip()
            if "```" in text:
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
                text = text.strip()
            start = text.find("[")
            end = text.rfind("]")
            if start != -1 and end != -1:
                text = text[start : end + 1]
            names = json.loads(text)
            if isinstance(names, list):
                for name in names:
                    if isinstance(name, str) and name.lower() not in seen:
                        seen.add(name.lower())
                        all_names.append(name)
        except Exception:
            logger.warning("llm_brand_extraction_failed", chunk=i + 1)

    return all_names[:max_brands]


async def deduplicate_brands(
    brands: list[str],
    category: str,
    provider: BaseProvider,
) -> tuple[list[str], dict[str, str]]:
    """Deduplicate brand list via substring matching + LLM alias resolution.

    Returns (canonical_brands, alias_map) where alias_map maps
    every original name to its canonical form.
    """
    if len(brands) <= 1:
        return brands, {b: b for b in brands}

    # Layer 1: Fuzzy substring dedup — group names where one contains the other
    alias_map: dict[str, str] = {}
    canonical_set: list[str] = []  # preserves order
    merged: set[str] = set()

    for i, name in enumerate(brands):
        if name in merged:
            continue
        group = [name]
        for j, other in enumerate(brands):
            if j == i or other in merged:
                continue
            if name.lower() in other.lower() or other.lower() in name.lower():
                group.append(other)
        # Pick longest name as canonical (most specific / recognizable)
        canonical = max(group, key=len)
        for member in group:
            alias_map[member] = canonical
            if member != canonical:
                merged.add(member)
        if canonical not in merged:
            canonical_set.append(canonical)
            merged.add(canonical)

    # Layer 2: LLM alias resolution for semantic aliases (zero lexical overlap)
    if len(canonical_set) >= 2:
        names_block = "\n".join(f"- {n}" for n in canonical_set)
        prompt = f"""These are brand/company names extracted from AI responses about "{category}".

Some of these may be the SAME company known by different names, abbreviations, or aliases.
For example, "a16z crypto" and "Andreessen Horowitz" are the same firm.

BRANDS:
{names_block}

Which brands are alternate names for the same company?
Return ONLY a JSON object mapping each alias to the canonical (most recognizable) name.
If there are no aliases, return {{}}.
Only include pairs where you are confident they refer to the same entity.

Example: {{"a16z crypto": "Andreessen Horowitz", "GS": "Goldman Sachs"}}

JSON object:"""

        try:
            resp = await provider.query(prompt)
            text = resp.text.strip()
            if "```" in text:
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
                text = text.strip()
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1:
                text = text[start : end + 1]
            llm_aliases = json.loads(text)
            if isinstance(llm_aliases, dict):
                # Validate both alias and canonical exist in our canonical_set
                canonical_lower_map = {c.lower(): c for c in canonical_set}
                for alias_raw, canon_raw in llm_aliases.items():
                    if not isinstance(alias_raw, str) or not isinstance(canon_raw, str):
                        continue
                    alias_match = canonical_lower_map.get(alias_raw.lower())
                    canon_match = canonical_lower_map.get(canon_raw.lower())
                    if alias_match and canon_match and alias_match != canon_match:
                        # Merge: remove alias from canonical_set, update alias_map
                        if alias_match in canonical_set:
                            canonical_set.remove(alias_match)
                        # Update all entries pointing to the old alias canonical
                        for k, v in alias_map.items():
                            if v == alias_match:
                                alias_map[k] = canon_match
                        alias_map[alias_match] = canon_match
        except Exception:
            logger.warning("llm_brand_dedup_failed", category=category)

    # Ensure every original brand has an alias_map entry
    for b in brands:
        if b not in alias_map:
            alias_map[b] = b

    return canonical_set, alias_map


_RANKING_SIGNAL_PATTERNS = [
    r"(?im)^\s*\d+\s*[\.\)]\s+\S+",
    r"(?im)^\s*[-*]\s+\*\*?\w+",
    r"(?i)\btop\s+\d+\b",
    r"(?i)\brank(?:ed|ing)?\b",
    r"(?i)\btier\b",
    r"(?i)\bS-Tier\b|\bA-Tier\b|\bB-Tier\b|\bC-Tier\b",
]


def likely_contains_ranking_signal(text: str) -> bool:
    return any(re.search(pat, text) for pat in _RANKING_SIGNAL_PATTERNS)


def _normalize_entity_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", name.lower())


def _build_candidate_lookup(candidate_brands: list[str]) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    by_lower = {c.lower(): c for c in candidate_brands}
    by_norm = {_normalize_entity_name(c): c for c in candidate_brands}

    # Build a simple acronym map for multi-word brands (e.g., "New Enterprise Associates" -> "nea")
    acronym_counts: dict[str, int] = {}
    acronym_to_brand: dict[str, str] = {}
    for brand in candidate_brands:
        words = [w for w in re.split(r"[^A-Za-z0-9]+", brand) if w]
        if len(words) < 2:
            continue
        acronym = "".join(w[0].lower() for w in words if w and w[0].isalnum())
        if 2 <= len(acronym) <= 6:
            acronym_counts[acronym] = acronym_counts.get(acronym, 0) + 1
            acronym_to_brand[acronym] = brand

    unique_acronyms = {a: b for a, b in acronym_to_brand.items() if acronym_counts.get(a, 0) == 1}
    return by_lower, by_norm, unique_acronyms


def _canonicalize_brand_name(
    raw_name: str,
    by_lower: dict[str, str],
    by_norm: dict[str, str],
    by_acronym: dict[str, str],
) -> str | None:
    s = raw_name.strip()
    if not s:
        return None

    lower = s.lower()
    if lower in by_lower:
        return by_lower[lower]

    norm = _normalize_entity_name(s)
    if norm in by_norm:
        return by_norm[norm]

    if lower in by_acronym:
        return by_acronym[lower]

    # Fuzzy containment fallback for small naming variants
    for cand_lower, canonical in by_lower.items():
        if lower in cand_lower or cand_lower in lower:
            return canonical

    return None


async def extract_ranked_brands_with_llm(
    response_items: list[tuple[str, str]],
    category: str,
    provider: BaseProvider,
    candidate_brands: list[str],
    *,
    batch_size: int = 8,
    max_brands_per_response: int = 15,
) -> dict[str, list[str]]:
    """Extract ordered ranked brands from responses using batched LLM calls.

    Returns a mapping response_id -> ordered list of canonical brand names.
    Only responses with ranking/tier signals are sent to the LLM.
    """
    if not response_items or not candidate_brands:
        return {}

    by_lower, by_norm, by_acronym = _build_candidate_lookup(candidate_brands)

    # Keep output keys stable for all responses
    ranked_map: dict[str, list[str]] = {rid: [] for rid, _ in response_items}

    # Only attempt extraction on likely ranking responses
    likely_ranked = [(rid, txt) for rid, txt in response_items if likely_contains_ranking_signal(txt)]
    if not likely_ranked:
        return ranked_map

    candidates_block = "\n".join(f"- {c}" for c in candidate_brands)

    for i in range(0, len(likely_ranked), batch_size):
        batch = likely_ranked[i : i + batch_size]
        response_block_parts = []
        for rid, text in batch:
            response_block_parts.append(
                f"RESPONSE_ID: {rid}\n{text[:1800]}"
            )
        response_block = "\n\n---\n\n".join(response_block_parts)

        prompt = f"""You are extracting explicit ranking order from AI responses in category "{category}".

CANDIDATE BRANDS (canonical names):
{candidates_block}

TASK:
- For each RESPONSE_ID, return the ordered brands ONLY when the response explicitly ranks, tiers, or orders brands.
- If no explicit ranking/tier/order exists, return [] for that RESPONSE_ID.
- Keep order exactly as written in the response (best/highest first).
- Normalize aliases and abbreviations to canonical candidate names whenever possible.
- Use only candidate brands in outputs.
- Return at most {max_brands_per_response} brands per response.
- Return ONLY a valid JSON object of shape:
  {{"response_id": ["Brand A", "Brand B"], "...": []}}

RESPONSES:
{response_block}

JSON object:"""

        try:
            resp = await provider.query(prompt)
            text = resp.text.strip()
            if "```" in text:
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
                text = text.strip()

            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1:
                text = text[start : end + 1]

            parsed = json.loads(text)
            if not isinstance(parsed, dict):
                continue

            for rid, raw_brands in parsed.items():
                if not isinstance(rid, str) or not isinstance(raw_brands, list):
                    continue

                canonical_list: list[str] = []
                seen: set[str] = set()
                for raw_name in raw_brands:
                    if not isinstance(raw_name, str):
                        continue
                    canonical = _canonicalize_brand_name(raw_name, by_lower, by_norm, by_acronym)
                    if canonical and canonical not in seen:
                        seen.add(canonical)
                        canonical_list.append(canonical)
                    if len(canonical_list) >= max_brands_per_response:
                        break

                ranked_map[rid] = canonical_list
        except Exception as exc:
            logger.warning("llm_rank_position_extraction_failed", batch=i // batch_size + 1, error=str(exc))

    return ranked_map


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
