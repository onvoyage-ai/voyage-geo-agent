"""Competitor analyzer — compares brand performance against competitors."""

from __future__ import annotations

import statistics

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from voyage_geo.types.analysis import CompetitorAnalysis, CompetitorScore
from voyage_geo.types.brand import BrandProfile
from voyage_geo.types.result import QueryResult
from voyage_geo.utils.text import contains_brand, count_occurrences, extract_sentences

vader = SentimentIntensityAnalyzer()


class CompetitorAnalyzer:
    name = "competitor"

    def analyze(
        self,
        results: list[QueryResult],
        profile: BrandProfile,
        extracted_competitors: list[str] | None = None,
    ) -> CompetitorAnalysis:
        valid = [r for r in results if not r.error and r.response]
        if not valid:
            return CompetitorAnalysis()

        competitors = extracted_competitors if extracted_competitors else profile.competitors
        all_brands = [profile.name] + competitors
        brand_scores: dict[str, dict] = {}

        for brand in all_brands:
            mentions = sum(1 for r in valid if contains_brand(r.response, brand))
            mention_rate = mentions / len(valid) if valid else 0

            sentiments: list[float] = []
            total_mentions_count = 0
            for r in valid:
                total_mentions_count += count_occurrences(r.response, brand)
                sentences = [s for s in extract_sentences(r.response) if contains_brand(s, brand)]
                for sentence in sentences:
                    vs = vader.polarity_scores(sentence)
                    sentiments.append(vs["compound"])

            sentiment_avg = statistics.mean(sentiments) if sentiments else 0
            mindshare = total_mentions_count / sum(
                count_occurrences(r.response, b) for r in valid for b in all_brands
            ) if any(count_occurrences(r.response, b) for r in valid for b in all_brands) else 0

            brand_scores[brand] = {
                "mention_rate": round(mention_rate, 4),
                "sentiment": round(sentiment_avg, 4),
                "mindshare": round(mindshare, 4),
            }

        sorted_brands = sorted(brand_scores.items(), key=lambda x: x[1]["mindshare"], reverse=True)
        brand_rank = next((i + 1 for i, (b, _) in enumerate(sorted_brands) if b == profile.name), 0)

        competitors = [
            CompetitorScore(name=brand, **scores)
            for brand, scores in sorted_brands
        ]

        return CompetitorAnalysis(competitors=competitors, brand_rank=brand_rank)
