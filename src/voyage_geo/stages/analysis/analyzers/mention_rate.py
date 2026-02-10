"""Mention rate analyzer — what percentage of responses mention the brand."""

from __future__ import annotations

from voyage_geo.types.analysis import MentionRateScore
from voyage_geo.types.brand import BrandProfile
from voyage_geo.types.result import QueryResult
from voyage_geo.utils.text import contains_brand


class MentionRateAnalyzer:
    name = "mention-rate"

    def analyze(self, results: list[QueryResult], profile: BrandProfile) -> MentionRateScore:
        valid = [r for r in results if not r.error and r.response]
        if not valid:
            return MentionRateScore(total_responses=len(results))

        mentions = sum(1 for r in valid if contains_brand(r.response, profile.name))
        overall = mentions / len(valid) if valid else 0

        # By provider
        by_provider: dict[str, float] = {}
        provider_groups: dict[str, list[QueryResult]] = {}
        for r in valid:
            provider_groups.setdefault(r.provider, []).append(r)
        for prov, prov_results in provider_groups.items():
            prov_mentions = sum(1 for r in prov_results if contains_brand(r.response, profile.name))
            by_provider[prov] = prov_mentions / len(prov_results) if prov_results else 0

        return MentionRateScore(
            overall=round(overall, 4),
            by_provider={k: round(v, 4) for k, v in by_provider.items()},
            total_mentions=mentions,
            total_responses=len(valid),
        )
