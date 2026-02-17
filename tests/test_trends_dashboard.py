"""Tests for trends dashboard generation."""

from voyage_geo.trends_dashboard import build_dashboard_payload, render_dashboard_html


def test_render_dashboard_html_smoke():
    records = [
        {
            "run_id": "run-1",
            "as_of_date": "2026-02-15",
            "overall_score": 10,
            "mention_rate": 0.1,
            "mindshare": 0.05,
            "sentiment_score": 0.2,
            "competitor_relative": {
                "mindshare_gap_to_leader": -0.2,
                "mention_rate_gap_to_leader": -0.3,
                "share_of_voice_top5": 0.1,
                "top_competitors": [
                    {"name": "CompA", "mindshare": 0.3, "mention_rate": 0.4, "sentiment": 0.1}
                ],
            },
        }
    ]
    payload = build_dashboard_payload(records)
    html = render_dashboard_html("Acme", payload)
    assert '"Acme"' in html
    assert "CompA" in html
    assert "metric-chart" in html
