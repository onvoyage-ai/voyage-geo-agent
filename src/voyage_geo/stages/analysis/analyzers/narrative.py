"""Narrative analyzer — extracts brand claims, detects USP coverage gaps."""

from __future__ import annotations

from collections import defaultdict

from voyage_geo.types.analysis import BrandClaim, NarrativeAnalysis, NarrativeGap
from voyage_geo.types.brand import BrandProfile
from voyage_geo.types.result import QueryResult


class NarrativeAnalyzer:
    name = "narrative"

    def analyze(
        self,
        results: list[QueryResult],
        profile: BrandProfile,
        extracted_claims: list[dict] | None = None,
    ) -> NarrativeAnalysis:
        if not extracted_claims:
            return NarrativeAnalysis()

        # Parse raw dicts into BrandClaim objects
        claims = []
        for raw in extracted_claims:
            try:
                claims.append(BrandClaim(**raw))
            except Exception:
                continue

        if not claims:
            return NarrativeAnalysis()

        # Filter claims for target brand
        brand_lower = profile.name.lower()
        brand_claims = [c for c in claims if c.brand.lower() == brand_lower]

        # Group brand claims by attribute
        brand_themes: dict[str, list[BrandClaim]] = defaultdict(list)
        for c in brand_claims:
            brand_themes[c.attribute].append(c)

        # Count sentiment
        pos = sum(1 for c in brand_claims if c.sentiment == "positive")
        neg = sum(1 for c in brand_claims if c.sentiment == "negative")
        neu = sum(1 for c in brand_claims if c.sentiment == "neutral")

        # Gap analysis: check if each USP is covered by any claim
        gaps: list[NarrativeGap] = []
        covered_count = 0
        for usp in profile.unique_selling_points:
            usp_lower = usp.lower()
            usp_words = set(usp_lower.split())
            # Check if any brand claim text or attribute covers this USP
            is_covered = False
            matching_detail = ""
            for c in brand_claims:
                claim_text = f"{c.attribute} {c.claim}".lower()
                # Match if any significant USP word appears in claim text
                overlap = usp_words & set(claim_text.split())
                # Require at least one meaningful word match (skip very short words)
                meaningful_overlap = {w for w in overlap if len(w) > 3}
                if meaningful_overlap or usp_lower in claim_text or c.attribute.lower() in usp_lower:
                    is_covered = True
                    matching_detail = c.claim
                    break

            if is_covered:
                covered_count += 1
            gaps.append(NarrativeGap(
                usp=usp,
                covered=is_covered,
                detail=matching_detail if is_covered else "Not mentioned in AI responses",
            ))

        coverage_score = covered_count / len(profile.unique_selling_points) if profile.unique_selling_points else 0.0

        # Competitor themes: count claims per attribute for non-target brands
        competitor_themes: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for c in claims:
            if c.brand.lower() != brand_lower:
                competitor_themes[c.brand][c.attribute] += 1

        return NarrativeAnalysis(
            claims=claims,
            total_claims=len(claims),
            brand_themes=dict(brand_themes),
            brand_positive_count=pos,
            brand_negative_count=neg,
            brand_neutral_count=neu,
            gaps=gaps,
            coverage_score=round(coverage_score, 4),
            competitor_themes={b: dict(attrs) for b, attrs in competitor_themes.items()},
        )
