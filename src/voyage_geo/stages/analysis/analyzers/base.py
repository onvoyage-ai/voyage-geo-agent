"""Analyzer base protocol."""

from __future__ import annotations

from typing import Any, Protocol

from voyage_geo.types.brand import BrandProfile
from voyage_geo.types.result import QueryResult


class Analyzer(Protocol):
    name: str

    def analyze(self, results: list[QueryResult], profile: BrandProfile) -> Any: ...
