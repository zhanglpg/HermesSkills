"""Tests for paper-queue storage module."""

import sqlite3

import pytest
from storage import QueueDB

# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------


class TestQueueDBInit:
    def test_init_creates_file(self, tmp_path):
        db_path = str(tmp_path / "new.db")
        db = QueueDB.init_db(db_path)
        assert (tmp_path / "new.db").exists()
        db.close()

    def test_init_already_exists(self, tmp_path):
        db_path = str(tmp_path / "exists.db")
        db = QueueDB.init_db(db_path)
        db.close()
        with pytest.raises(FileExistsError):
            QueueDB.init_db(db_path)

    def test_open_nonexistent(self):
        with pytest.raises(FileNotFoundError):
            QueueDB("/tmp/does_not_exist_12345.db")


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


class TestQueueDBCrud:
    def test_add_paper(self, queue_db):
        pid = queue_db.add_paper(title="Test Paper")
        assert isinstance(pid, int)
        assert pid > 0

    def test_get_paper(self, queue_db):
        pid = queue_db.add_paper(title="My Paper", arxiv_id="2401.00001", authors="Alice")
        paper = queue_db.get_paper(pid)
        assert paper is not None
        assert paper["title"] == "My Paper"
        assert paper["arxiv_id"] == "2401.00001"
        assert paper["authors"] == "Alice"
        assert paper["status"] == "to-read"

    def test_get_paper_not_found(self, queue_db):
        assert queue_db.get_paper(999) is None

    def test_get_by_arxiv_id(self, queue_db):
        queue_db.add_paper(title="Paper A", arxiv_id="2401.11111")
        result = queue_db.get_by_arxiv_id("2401.11111")
        assert result is not None
        assert result["title"] == "Paper A"

    def test_duplicate_arxiv_id_raises(self, queue_db):
        queue_db.add_paper(title="First", arxiv_id="2401.99999")
        with pytest.raises(sqlite3.IntegrityError):
            queue_db.add_paper(title="Second", arxiv_id="2401.99999")

    def test_add_paper_with_topics(self, queue_db):
        pid = queue_db.add_paper(title="Topics Paper", topics=["cs.LG", "cs.AI"])
        paper = queue_db.get_paper(pid)
        assert paper["topics"] == ["cs.LG", "cs.AI"]


# ---------------------------------------------------------------------------
# Listing / Filtering
# ---------------------------------------------------------------------------


class TestQueueDBList:
    def test_list_empty(self, queue_db):
        assert queue_db.list_papers() == []

    def test_list_all(self, queue_db):
        queue_db.add_paper(title="A")
        queue_db.add_paper(title="B")
        assert len(queue_db.list_papers()) == 2

    def test_list_filter_by_status(self, queue_db):
        pid = queue_db.add_paper(title="Reading")
        queue_db.add_paper(title="Unread")
        queue_db.update_status(pid, "reading")
        result = queue_db.list_papers(status="reading")
        assert len(result) == 1
        assert result[0]["title"] == "Reading"

    def test_list_filter_by_topic(self, queue_db):
        queue_db.add_paper(title="ML Paper", topics=["cs.LG"])
        queue_db.add_paper(title="NLP Paper", topics=["cs.CL"])
        result = queue_db.list_papers(topic="cs.LG")
        assert len(result) == 1

    def test_search(self, queue_db):
        queue_db.add_paper(title="Transformers for NLP")
        queue_db.add_paper(title="CNN for Vision")
        result = queue_db.search("Transformers")
        assert len(result) == 1
        assert "Transformers" in result[0]["title"]


# ---------------------------------------------------------------------------
# Updates
# ---------------------------------------------------------------------------


class TestQueueDBUpdates:
    def test_update_status(self, queue_db):
        pid = queue_db.add_paper(title="Paper")
        queue_db.update_status(pid, "reading")
        paper = queue_db.get_paper(pid)
        assert paper["status"] == "reading"

    def test_update_status_invalid(self, queue_db):
        pid = queue_db.add_paper(title="Paper")
        with pytest.raises(ValueError, match="Invalid status"):
            queue_db.update_status(pid, "invalid-status")

    def test_update_score(self, queue_db):
        pid = queue_db.add_paper(title="Paper")
        components = [
            {"component": "citations", "value": 5.0, "detail": "50 citations"},
            {"component": "recency", "value": 8.0, "detail": "Recent"},
        ]
        queue_db.update_score(pid, 6.5, components)
        paper = queue_db.get_paper(pid)
        assert paper["priority_score"] == 6.5
        stored = queue_db.get_score_components(pid)
        assert len(stored) == 2

    def test_update_digest_path(self, queue_db):
        pid = queue_db.add_paper(title="Paper")
        queue_db.update_digest_path(pid, "/notes/digest.md")
        paper = queue_db.get_paper(pid)
        assert paper["digest_path"] == "/notes/digest.md"
        assert paper["status"] == "digested"


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------


class TestQueueDBAggregation:
    def test_get_all_topics(self, queue_db):
        queue_db.add_paper(title="A", topics=["cs.LG", "cs.AI"])
        queue_db.add_paper(title="B", topics=["cs.AI", "cs.CL"])
        topics = queue_db.get_all_topics()
        assert set(topics) == {"cs.ai", "cs.cl", "cs.lg"}

    def test_get_stats(self, queue_db):
        queue_db.add_paper(title="A")
        pid = queue_db.add_paper(title="B")
        queue_db.update_status(pid, "reading")
        stats = queue_db.get_stats()
        assert stats["total"] == 2
        assert stats["by_status"]["to-read"] == 1
        assert stats["by_status"]["reading"] == 1
