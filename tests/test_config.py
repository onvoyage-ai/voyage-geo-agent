"""Tests for config system."""

import os
from unittest.mock import patch

from voyage_geo.config.loader import load_config
from voyage_geo.config.schema import ProviderConfig, QueryConfig, VoyageGeoConfig


def test_default_config():
    config = VoyageGeoConfig()
    assert config.output_dir == "./data/runs"
    assert config.log_level == "info"


def test_provider_config_defaults():
    p = ProviderConfig(name="test")
    assert p.enabled is True
    assert p.max_tokens == 2048
    assert p.temperature == 0.7


def test_query_config_defaults():
    q = QueryConfig()
    assert q.count == 20
    assert len(q.strategies) == 4
    assert "keyword" in q.strategies


def test_config_with_overrides():
    config = VoyageGeoConfig(brand="Test", queries=QueryConfig(count=50))
    assert config.brand == "Test"
    assert config.queries.count == 50


def test_load_config_picks_up_env():
    with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test123"}):
        config = load_config()
        assert config.providers["openai"].api_key == "sk-test123"


def test_load_config_with_overrides():
    config = load_config(overrides={"brand": "Brex", "queries": {"count": 30}})
    assert config.brand == "Brex"
    assert config.queries.count == 30
