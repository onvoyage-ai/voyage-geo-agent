"""Tests for trend aggregation and competitor-relative snapshots."""

from datetime import UTC, datetime

from voyage_geo.stages.analysis.stage import AnalysisStage
from voyage_geo.trends import build_competitor_series, collect_trend_records
from voyage_geo.types.analysis import AnalysisResult, CompetitorAnalysis, CompetitorScore


def test_snapshot_includes_competitor_relative_fields():
    analysis = AnalysisResult(
        run_id="run-1",
        brand="Acme",
        analyzed_at=datetime.now(UTC).isoformat(),
        competitor_analysis=CompetitorAnalysis(
            brand_rank=2,
            competitors=[
                CompetitorScore(name="LeaderCo", mindshare=0.4, mention_rate=0.5, sentiment=0.1),
                CompetitorScore(name="Acme", mindshare=0.25, mention_rate=0.3, sentiment=0.2),
                CompetitorScore(name="OtherCo", mindshare=0.2, mention_rate=0.25, sentiment=0.0),
            ],
        ),
    )

    snap = AnalysisStage._build_snapshot(analysis)
    rel = snap["competitor_relative"]
    assert rel["leader_brand"] == "LeaderCo"
    assert rel["brand_rank"] == 2
    assert rel["mindshare_gap_to_leader"] < 0
    assert rel["share_of_voice_top5"] > 0
    assert len(rel["top_competitors"]) == 2


def test_collect_records_and_competitor_series(tmp_path):
    runs = tmp_path / "runs"
    run1 = runs / "run-20260216-000001-aaaaaa"
    run2 = runs / "run-20260217-000001-bbbbbb"
    (run1 / "analysis").mkdir(parents=True)
    (run2 / "analysis").mkdir(parents=True)

    (run1 / "metadata.json").write_text(
        """{
  "type": "analysis",
  "status": "completed",
  "as_of_date": "2026-02-16",
  "brand": "Acme"
}"""
    )
    (run2 / "metadata.json").write_text(
        """{
  "type": "analysis",
  "status": "completed",
  "as_of_date": "2026-02-17",
  "brand": "Acme"
}"""
    )

    (run1 / "analysis" / "snapshot.json").write_text(
        """{
  "brand": "Acme",
  "overall_score": 30,
  "mention_rate": 0.2,
  "mindshare": 0.15,
  "sentiment_score": 0.1,
  "mindshare_rank": 3,
  "total_brands_detected": 10,
  "competitor_relative": {
    "leader_brand": "LeaderCo",
    "brand_rank": 3,
    "share_of_voice_top5": 0.2,
    "mindshare_gap_to_leader": -0.2,
    "mention_rate_gap_to_leader": -0.2,
    "top_competitors": [
      {"name": "LeaderCo", "mindshare": 0.35, "mention_rate": 0.4, "sentiment": 0.2}
    ]
  }
}"""
    )
    (run2 / "analysis" / "snapshot.json").write_text(
        """{
  "brand": "Acme",
  "overall_score": 35,
  "mention_rate": 0.25,
  "mindshare": 0.2,
  "sentiment_score": 0.12,
  "mindshare_rank": 2,
  "total_brands_detected": 10,
  "competitor_relative": {
    "leader_brand": "LeaderCo",
    "brand_rank": 2,
    "share_of_voice_top5": 0.25,
    "mindshare_gap_to_leader": -0.15,
    "mention_rate_gap_to_leader": -0.1,
    "top_competitors": [
      {"name": "LeaderCo", "mindshare": 0.35, "mention_rate": 0.35, "sentiment": 0.15}
    ]
  }
}"""
    )

    records = collect_trend_records(str(runs), brand="Acme")
    assert len(records) == 2
    assert records[0]["as_of_date"] == "2026-02-16"
    assert records[1]["as_of_date"] == "2026-02-17"

    comps = build_competitor_series(records, ["LeaderCo"])
    assert "LeaderCo" in comps
    assert len(comps["LeaderCo"]) == 2
