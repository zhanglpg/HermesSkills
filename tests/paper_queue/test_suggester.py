"""Tests for paper-queue suggester module."""

from suggester import _build_arxiv_query


class TestBuildArxivQuery:
    def test_empty(self):
        assert _build_arxiv_query([]) == ""

    def test_single_topic(self):
        result = _build_arxiv_query(["cs.LG"])
        assert result == "cat:cs.lg"

    def test_dedup_and_rank(self):
        topics = ["cs.LG", "cs.AI", "cs.LG", "cs.LG"]
        result = _build_arxiv_query(topics)
        parts = result.split(" OR ")
        # cs.lg should come first (highest frequency)
        assert parts[0] == "cat:cs.lg"

    def test_max_terms(self):
        topics = [f"cs.T{i}" for i in range(20)]
        result = _build_arxiv_query(topics, max_terms=3)
        parts = result.split(" OR ")
        assert len(parts) == 3
