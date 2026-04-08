"""Tests for paper-queue sources module."""

import xml.etree.ElementTree as ET
from unittest.mock import patch

import pytest
from sources import (
    ARXIV_NS,
    ATOM_NS,
    _extract_arxiv_id,
    _parse_arxiv_entry,
    fetch_arxiv_metadata,
    resolve_arxiv,
    resolve_manual,
)

# ---------------------------------------------------------------------------
# _extract_arxiv_id
# ---------------------------------------------------------------------------


class TestExtractArxivId:
    def test_bare_id(self):
        assert _extract_arxiv_id("2401.12345") == "2401.12345"

    def test_with_version(self):
        assert _extract_arxiv_id("2401.12345v2") == "2401.12345v2"

    def test_abs_url(self):
        assert _extract_arxiv_id("https://arxiv.org/abs/2401.12345") == "2401.12345"

    def test_abs_url_with_version(self):
        assert _extract_arxiv_id("https://arxiv.org/abs/2401.12345v3") == "2401.12345v3"

    def test_pdf_url(self):
        assert _extract_arxiv_id("https://arxiv.org/pdf/2401.12345v1") == "2401.12345v1"

    def test_not_arxiv(self):
        assert _extract_arxiv_id("https://example.com/paper") is None

    def test_empty(self):
        assert _extract_arxiv_id("") is None

    def test_five_digit_id(self):
        assert _extract_arxiv_id("2401.00001") == "2401.00001"


# ---------------------------------------------------------------------------
# _parse_arxiv_entry
# ---------------------------------------------------------------------------


def _make_arxiv_entry_xml() -> ET.Element:
    """Build a minimal arXiv Atom entry element."""
    xml_str = f"""
    <entry xmlns="{ATOM_NS[1:-1]}" xmlns:arxiv="{ARXIV_NS[1:-1]}">
        <id>http://arxiv.org/abs/2401.12345v1</id>
        <title>Test Paper Title</title>
        <author><name>Alice Smith</name></author>
        <author><name>Bob Jones</name></author>
        <summary>This is a test abstract.</summary>
        <published>2024-01-15T00:00:00Z</published>
        <arxiv:primary_category term="cs.LG"/>
        <category term="cs.LG"/>
        <category term="cs.AI"/>
    </entry>
    """
    return ET.fromstring(xml_str)


class TestParseArxivEntry:
    def test_extracts_title(self):
        entry = _make_arxiv_entry_xml()
        result = _parse_arxiv_entry(entry)
        assert result["title"] == "Test Paper Title"

    def test_extracts_authors(self):
        entry = _make_arxiv_entry_xml()
        result = _parse_arxiv_entry(entry)
        assert "Alice Smith" in result["authors"]
        assert "Bob Jones" in result["authors"]

    def test_extracts_arxiv_id(self):
        entry = _make_arxiv_entry_xml()
        result = _parse_arxiv_entry(entry)
        assert result["arxiv_id"] == "2401.12345v1"

    def test_extracts_topics(self):
        entry = _make_arxiv_entry_xml()
        result = _parse_arxiv_entry(entry)
        assert "cs.LG" in result["topics"]
        assert "cs.AI" in result["topics"]

    def test_extracts_published(self):
        entry = _make_arxiv_entry_xml()
        result = _parse_arxiv_entry(entry)
        assert result["published"] == "2024-01-15T00:00:00Z"

    def test_source_is_arxiv(self):
        entry = _make_arxiv_entry_xml()
        result = _parse_arxiv_entry(entry)
        assert result["source"] == "arxiv"


# ---------------------------------------------------------------------------
# resolve_manual
# ---------------------------------------------------------------------------


class TestResolveManual:
    def test_full_args(self):
        result = resolve_manual("My Paper", url="https://example.com", authors="Smith")
        assert result["title"] == "My Paper"
        assert result["url"] == "https://example.com"
        assert result["authors"] == "Smith"
        assert result["source"] == "manual"

    def test_minimal(self):
        result = resolve_manual("Title Only")
        assert result["title"] == "Title Only"
        assert result["arxiv_id"] is None
        assert result["topics"] == []


# ---------------------------------------------------------------------------
# fetch_arxiv_metadata (mocked)
# ---------------------------------------------------------------------------


_SAMPLE_ATOM_RESPONSE = f"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="{ATOM_NS[1:-1]}" xmlns:arxiv="{ARXIV_NS[1:-1]}">
    <entry>
        <id>http://arxiv.org/abs/2401.12345v1</id>
        <title>Mocked Paper</title>
        <author><name>Test Author</name></author>
        <summary>Mocked abstract.</summary>
        <published>2024-01-15T00:00:00Z</published>
        <arxiv:primary_category term="cs.LG"/>
        <category term="cs.LG"/>
    </entry>
</feed>
"""


class TestFetchArxivMetadata:
    @patch("sources._fetch_text", return_value=_SAMPLE_ATOM_RESPONSE)
    def test_returns_metadata(self, mock_fetch):
        result = fetch_arxiv_metadata("2401.12345")
        assert result["title"] == "Mocked Paper"
        assert result["arxiv_id"] == "2401.12345v1"
        mock_fetch.assert_called_once()


# ---------------------------------------------------------------------------
# resolve_arxiv
# ---------------------------------------------------------------------------


class TestResolveArxiv:
    @patch("sources.fetch_arxiv_metadata", return_value={"title": "X"})
    def test_valid_id(self, mock_fetch):
        result = resolve_arxiv("2401.12345")
        assert result["title"] == "X"

    def test_invalid_input(self):
        with pytest.raises(ValueError, match="Could not extract arXiv ID"):
            resolve_arxiv("not-an-arxiv-id")
