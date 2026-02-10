"""Tests for text utilities."""

from voyage_geo.utils.text import (
    clean_response_text,
    contains_brand,
    count_occurrences,
    extract_brand_mentions,
    extract_sentences,
    truncate,
)


def test_truncate():
    assert truncate("hello", 10) == "hello"
    assert truncate("hello world foo bar", 10) == "hello w..."


def test_count_occurrences():
    assert count_occurrences("Notion is great. Notion rocks.", "Notion") == 2
    assert count_occurrences("nothing here", "Notion") == 0


def test_count_occurrences_case_insensitive():
    assert count_occurrences("notion and NOTION", "Notion") == 2


def test_extract_sentences():
    text = "Hello world. How are you? I'm fine!"
    sentences = extract_sentences(text)
    assert len(sentences) == 3


def test_contains_brand():
    assert contains_brand("Notion is an all-in-one workspace", "Notion") is True
    assert contains_brand("Nothing to see here", "Notion") is False


def test_contains_brand_case_insensitive():
    assert contains_brand("I use notion daily", "Notion") is True


def test_extract_brand_mentions():
    text = "Notion and Asana are popular. Notion is great."
    mentions = extract_brand_mentions(text, ["Notion", "Asana", "ClickUp"])
    assert mentions["Notion"] == 2
    assert mentions["Asana"] == 1
    assert mentions["ClickUp"] == 0


def test_clean_response_text():
    text = "Hello\n\n\n\nWorld   test"
    cleaned = clean_response_text(text)
    assert "\n\n\n" not in cleaned
    assert "   " not in cleaned
