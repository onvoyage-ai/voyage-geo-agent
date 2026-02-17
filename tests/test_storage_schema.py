"""Tests for persisted schema helpers."""

from voyage_geo.config.schema import ProviderConfig, VoyageGeoConfig
from voyage_geo.storage.schema import build_config_hash


def test_build_config_hash_is_stable_and_ignores_api_key_values():
    cfg_a = VoyageGeoConfig(
        brand="Acme",
        providers={
            "openai": ProviderConfig(name="openai", enabled=True, api_key="sk-one"),
        },
    )
    cfg_b = VoyageGeoConfig(
        brand="Acme",
        providers={
            "openai": ProviderConfig(name="openai", enabled=True, api_key="sk-two"),
        },
    )

    assert build_config_hash(cfg_a) == build_config_hash(cfg_b)


def test_build_config_hash_changes_when_non_secret_config_changes():
    cfg_a = VoyageGeoConfig(brand="Acme", queries={"count": 20})
    cfg_b = VoyageGeoConfig(brand="Acme", queries={"count": 30})

    assert build_config_hash(cfg_a) != build_config_hash(cfg_b)
