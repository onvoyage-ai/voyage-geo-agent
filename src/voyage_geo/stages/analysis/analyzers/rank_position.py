"""Rank-position analyzer — how often and how high a brand is explicitly ranked."""

from __future__ import annotations

import statistics

from voyage_geo.types.analysis import RankPositionScore
from voyage_geo.types.brand import BrandProfile
from voyage_geo.types.result import QueryResult


def _normalize(name: str) -> str:
    return "".join(ch for ch in name.lower() if ch.isalnum())


class RankPositionAnalyzer:
    name = "rank-position"

    def analyze(
        self,
        results: list[QueryResult],
        profile: BrandProfile,
        ranked_lists_by_response: dict[str, list[str]] | None = None,
    ) -> RankPositionScore:
        valid = [r for r in results if not r.error and r.response]
        if not valid:
            return RankPositionScore()

        ranked_lists_by_response = ranked_lists_by_response or {}
        target_lower = profile.name.lower()
        target_norm = _normalize(profile.name)

        positions: list[int] = []
        weighted_sum = 0.0
        total_ranked_responses = 0
        mention_in_ranked_lists = 0
        provider_totals: dict[str, int] = {}
        provider_weighted: dict[str, float] = {}

        for r in valid:
            keys = (
                f"{r.provider}:{r.query_id}:{r.iteration}",
                f"{r.provider}:{r.query_id}",
                r.query_id,
            )
            ranked = []
            for key in keys:
                ranked = ranked_lists_by_response.get(key, [])
                if ranked:
                    break

            if not ranked:
                continue

            total_ranked_responses += 1
            provider_totals[r.provider] = provider_totals.get(r.provider, 0) + 1

            found_position = 0
            for idx, name in enumerate(ranked, start=1):
                if name.lower() == target_lower or _normalize(name) == target_norm:
                    found_position = idx
                    break

            if found_position > 0:
                mention_in_ranked_lists += 1
                positions.append(found_position)
                contribution = 1.0 / found_position
                weighted_sum += contribution
                provider_weighted[r.provider] = provider_weighted.get(r.provider, 0.0) + contribution

        by_provider: dict[str, float] = {}
        for provider, total in provider_totals.items():
            by_provider[provider] = round(provider_weighted.get(provider, 0.0) / total, 4) if total > 0 else 0.0

        avg_position = statistics.mean(positions) if positions else 0.0
        median_position = statistics.median(positions) if positions else 0.0
        top3_rate = (
            (sum(1 for p in positions if p <= 3) / mention_in_ranked_lists)
            if mention_in_ranked_lists > 0
            else 0.0
        )
        mention_coverage = (
            (mention_in_ranked_lists / total_ranked_responses) if total_ranked_responses > 0 else 0.0
        )
        weighted_visibility = (weighted_sum / total_ranked_responses) if total_ranked_responses > 0 else 0.0

        return RankPositionScore(
            total_ranked_responses=total_ranked_responses,
            mention_in_ranked_lists=mention_in_ranked_lists,
            mention_coverage=round(mention_coverage, 4),
            avg_position=round(avg_position, 3),
            median_position=round(float(median_position), 3),
            top3_rate=round(top3_rate, 4),
            weighted_visibility=round(weighted_visibility, 4),
            by_provider=by_provider,
        )
