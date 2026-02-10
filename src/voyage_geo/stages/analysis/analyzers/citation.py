"""Citation analyzer — detects URLs and sources cited in responses."""

from __future__ import annotations

import re
from collections import Counter
from urllib.parse import urlparse

from voyage_geo.types.analysis import CitationScore, CitationSource
from voyage_geo.types.brand import BrandProfile
from voyage_geo.types.result import QueryResult

URL_PATTERN = re.compile(r"https?://[^\s<>\"')\]]+")


class CitationAnalyzer:
    name = "citation"

    def analyze(self, results: list[QueryResult], profile: BrandProfile) -> CitationScore:
        valid = [r for r in results if not r.error and r.response]
        if not valid:
            return CitationScore()

        source_counter: Counter[str] = Counter()
        source_providers: dict[str, set[str]] = {}
        responses_with_citations = 0

        for r in valid:
            urls = URL_PATTERN.findall(r.response)
            if urls:
                responses_with_citations += 1
            for url in urls:
                try:
                    domain = urlparse(url).netloc
                    if domain:
                        source_counter[domain] += 1
                        source_providers.setdefault(domain, set()).add(r.provider)
                except Exception:
                    pass

        total = sum(source_counter.values())
        citation_rate = responses_with_citations / len(valid) * 100 if valid else 0

        by_provider: dict[str, int] = {}
        provider_groups: dict[str, list[QueryResult]] = {}
        for r in valid:
            provider_groups.setdefault(r.provider, []).append(r)
        for prov, prov_results in provider_groups.items():
            by_provider[prov] = sum(1 for r in prov_results if URL_PATTERN.search(r.response))

        top_sources = [
            CitationSource(
                source=domain,
                count=count,
                providers=sorted(source_providers.get(domain, set())),
            )
            for domain, count in source_counter.most_common(10)
        ]

        return CitationScore(
            total_citations=total,
            unique_sources_cited=len(source_counter),
            citation_rate=round(citation_rate, 1),
            by_provider=by_provider,
            top_sources=top_sources,
        )
