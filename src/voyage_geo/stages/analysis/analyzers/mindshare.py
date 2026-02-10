"""Mindshare analyzer — how much of the conversation does the brand own."""

from __future__ import annotations

from collections import Counter

from voyage_geo.types.analysis import MindshareScore
from voyage_geo.types.brand import BrandProfile
from voyage_geo.types.result import QueryResult
from voyage_geo.utils.text import count_occurrences


class MindshareAnalyzer:
    name = "mindshare"

    def analyze(
        self,
        results: list[QueryResult],
        profile: BrandProfile,
        extracted_competitors: list[str] | None = None,
    ) -> MindshareScore:
        valid = [r for r in results if not r.error and r.response]
        if not valid:
            return MindshareScore()

        competitors = extracted_competitors if extracted_competitors else profile.competitors
        all_brands = [profile.name] + competitors
        brand_counts: Counter[str] = Counter()

        for r in valid:
            for brand in all_brands:
                brand_counts[brand] += count_occurrences(r.response, brand)

        total_mentions = sum(brand_counts.values())
        our_mentions = brand_counts.get(profile.name, 0)
        overall = our_mentions / total_mentions if total_mentions > 0 else 0

        # Rank
        sorted_brands = brand_counts.most_common()
        rank = next((i + 1 for i, (b, _) in enumerate(sorted_brands) if b == profile.name), 0)

        # By provider
        by_provider: dict[str, float] = {}
        provider_groups: dict[str, list[QueryResult]] = {}
        for r in valid:
            provider_groups.setdefault(r.provider, []).append(r)
        for prov, prov_results in provider_groups.items():
            prov_total = sum(count_occurrences(r.response, b) for r in prov_results for b in all_brands)
            prov_ours = sum(count_occurrences(r.response, profile.name) for r in prov_results)
            by_provider[prov] = prov_ours / prov_total if prov_total > 0 else 0

        return MindshareScore(
            overall=round(overall, 4),
            by_provider={k: round(v, 4) for k, v in by_provider.items()},
            rank=rank,
            total_brands_detected=len([b for b, c in brand_counts.items() if c > 0]),
        )
