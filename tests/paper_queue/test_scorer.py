"""Tests for paper-queue scorer module."""

import json
from datetime import datetime, timedelta, timezone

from scorer import (
    score_citations,
    score_paper,
    score_queue_affinity,
    score_recency,
)

# ---------------------------------------------------------------------------
# score_citations
# ---------------------------------------------------------------------------


class TestScoreCitations:
    def test_zero(self):
        score, detail = score_citations(0)
        assert score == 0.0
        assert "No citations" in detail

    def test_negative(self):
        score, detail = score_citations(-5)
        assert score == 0.0

    def test_small(self):
        score, _ = score_citations(10)
        assert 3.0 < score < 4.5

    def test_medium(self):
        score, _ = score_citations(100)
        assert 7.0 < score < 8.0

    def test_large_at_500(self):
        score, _ = score_citations(500)
        assert score == 10.0

    def test_above_cap(self):
        score, _ = score_citations(1000)
        assert score == 10.0

    def test_detail_includes_count(self):
        _, detail = score_citations(42)
        assert "42" in detail


# ---------------------------------------------------------------------------
# score_recency
# ---------------------------------------------------------------------------


class TestScoreRecency:
    def _iso(self, days_ago: int) -> str:
        dt = datetime.now(timezone.utc) - timedelta(days=days_ago)
        return dt.isoformat()

    def test_none_date(self):
        score, detail = score_recency(None)
        assert score == 5.0
        assert "Unknown" in detail

    def test_invalid_date(self):
        score, _ = score_recency("not-a-date")
        assert score == 5.0

    def test_this_week(self):
        score, _ = score_recency(self._iso(2))
        assert score == 10.0

    def test_this_month(self):
        score, _ = score_recency(self._iso(15))
        assert score == 8.0

    def test_last_quarter(self):
        score, _ = score_recency(self._iso(60))
        assert score == 6.0

    def test_this_year(self):
        score, _ = score_recency(self._iso(200))
        assert score == 3.0

    def test_older_than_year(self):
        score, _ = score_recency(self._iso(500))
        assert score == 1.0


# ---------------------------------------------------------------------------
# score_queue_affinity
# ---------------------------------------------------------------------------


class TestScoreQueueAffinity:
    def test_no_paper_topics(self):
        score, _ = score_queue_affinity([], ["cs.LG"])
        assert score == 3.0

    def test_empty_queue(self):
        score, _ = score_queue_affinity(["cs.LG"], [])
        assert score == 5.0

    def test_no_overlap(self):
        score, _ = score_queue_affinity(["cs.LG"], ["cs.CL"])
        assert score == 1.0

    def test_full_overlap(self):
        score, _ = score_queue_affinity(["cs.LG", "cs.AI"], ["cs.lg", "cs.ai"])
        assert score > 5.0

    def test_partial_overlap(self):
        score, _ = score_queue_affinity(["cs.LG", "cs.AI"], ["cs.LG", "cs.CL"])
        assert 1.0 < score < 10.0


# ---------------------------------------------------------------------------
# score_paper (combined)
# ---------------------------------------------------------------------------


class TestScorePaper:
    def test_combined_score(self):
        paper = {
            "topics": ["cs.LG", "cs.AI"],
            "published": datetime.now(timezone.utc).isoformat(),
        }
        queue_topics = ["cs.LG"]
        total, components = score_paper(paper, queue_topics, citation_count=50)
        assert total > 0
        assert len(components) == 3
        names = {c["component"] for c in components}
        assert names == {"citations", "recency", "queue_affinity"}

    def test_custom_weights(self):
        paper = {"topics": [], "published": None}
        weights = {"citations": 1.0, "recency": 0.0, "queue_affinity": 0.0}
        total, _ = score_paper(paper, [], weights=weights, citation_count=500)
        assert total == 10.0

    def test_topics_as_json_string(self):
        paper = {
            "topics": json.dumps(["cs.LG"]),
            "published": None,
        }
        total, components = score_paper(paper, ["cs.LG"], citation_count=0)
        assert total >= 0
        aff = [c for c in components if c["component"] == "queue_affinity"][0]
        assert aff["value"] > 1.0
