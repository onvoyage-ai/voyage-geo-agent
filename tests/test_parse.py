"""Tests for AI query parser."""

from voyage_geo.stages.query_generation.strategies.parse import parse_ai_queries


def test_parse_basic():
    text = "What is the best CRM? | best-of | discovery\nIs Notion good? | review | evaluation"
    queries = parse_ai_queries(text, "keyword", "kw", 10)
    assert len(queries) == 2
    assert queries[0].text == "What is the best CRM?"
    assert queries[0].category == "best-of"
    assert queries[0].intent == "discovery"
    assert queries[0].strategy == "keyword"
    assert queries[0].id.startswith("kw-")


def test_parse_numbered():
    text = "1. Best CRM for startups? | recommendation | startup\n2) Cheapest tool? | recommendation | budget"
    queries = parse_ai_queries(text, "keyword", "kw", 10)
    assert len(queries) == 2
    assert queries[0].text == "Best CRM for startups?"


def test_parse_with_persona():
    text = "What CRM is best for my startup? | recommendation | startup | startup-founder"
    queries = parse_ai_queries(text, "persona", "ps", 10)
    assert queries[0].metadata is not None
    assert queries[0].metadata["persona"] == "startup-founder"


def test_parse_unknown_category():
    text = "Some query here | unknown-cat | intent"
    queries = parse_ai_queries(text, "keyword", "kw", 10)
    assert queries[0].category == "general"


def test_parse_respects_max_count():
    lines = [f"Query {i} about tools | recommendation | discovery" for i in range(20)]
    text = "\n".join(lines)
    queries = parse_ai_queries(text, "keyword", "kw", 5)
    assert len(queries) == 5


def test_parse_skips_short_lines():
    text = "Short | best-of | x\nThis is a reasonable query about software | recommendation | discovery"
    queries = parse_ai_queries(text, "keyword", "kw", 10)
    assert len(queries) == 1


def test_parse_skips_markdown():
    text = "```\n# Header\nActual query about CRM tools? | recommendation | discovery\n```"
    queries = parse_ai_queries(text, "keyword", "kw", 10)
    assert len(queries) == 1


def test_parse_unique_ids():
    text = "\n".join([f"Query {i} about tools here | recommendation | discovery" for i in range(10)])
    queries = parse_ai_queries(text, "keyword", "kw", 10)
    ids = {q.id for q in queries}
    assert len(ids) == 10
