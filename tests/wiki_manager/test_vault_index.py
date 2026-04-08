"""Tests for wiki-manager vault_index module."""

from pathlib import Path

from vault_index import (
    PageInfo,
    _extract_summary,
    _infer_page_type,
    _parse_yaml_value,
    build_index,
    parse_frontmatter,
)

# ---------------------------------------------------------------------------
# _parse_yaml_value
# ---------------------------------------------------------------------------


class TestParseYamlValue:
    def test_plain_string(self):
        assert _parse_yaml_value("hello") == "hello"

    def test_quoted_string(self):
        assert _parse_yaml_value('"hello world"') == "hello world"

    def test_single_quoted(self):
        assert _parse_yaml_value("'hello'") == "hello"

    def test_inline_list(self):
        result = _parse_yaml_value("[a, b, c]")
        assert result == ["a", "b", "c"]

    def test_inline_list_with_quotes(self):
        result = _parse_yaml_value('["x", "y"]')
        assert result == ["x", "y"]

    def test_empty_inline_list(self):
        result = _parse_yaml_value("[]")
        assert result == []


# ---------------------------------------------------------------------------
# parse_frontmatter
# ---------------------------------------------------------------------------


class TestParseFrontmatter:
    def test_basic(self):
        text = "---\ntitle: My Page\ntype: concept\n---\n\n# Content"
        fm = parse_frontmatter(text)
        assert fm["title"] == "My Page"
        assert fm["type"] == "concept"

    def test_with_list(self):
        text = "---\ntags:\n  - ai\n  - ml\n---\n\nBody"
        fm = parse_frontmatter(text)
        assert fm["tags"] == ["ai", "ml"]

    def test_inline_list(self):
        text = "---\ntags: [ai, ml, nlp]\n---\n\nBody"
        fm = parse_frontmatter(text)
        assert fm["tags"] == ["ai", "ml", "nlp"]

    def test_quoted_value(self):
        text = '---\ntitle: "My Title"\n---\n\nBody'
        fm = parse_frontmatter(text)
        assert fm["title"] == "My Title"

    def test_empty_no_frontmatter(self):
        assert parse_frontmatter("Just some text") == {}

    def test_no_closing_delimiter(self):
        assert parse_frontmatter("---\ntitle: X\nNo closing") == {}

    def test_mixed_keys(self):
        text = "---\ntitle: Test\nstatus: draft\ntags:\n  - a\n  - b\ndate: 2024-01-01\n---\n"
        fm = parse_frontmatter(text)
        assert fm["title"] == "Test"
        assert fm["status"] == "draft"
        assert fm["tags"] == ["a", "b"]
        assert fm["date"] == "2024-01-01"


# ---------------------------------------------------------------------------
# _extract_summary
# ---------------------------------------------------------------------------


class TestExtractSummary:
    def test_from_frontmatter(self):
        fm = {"summary": "A short summary"}
        result = _extract_summary("---\n---\n\n# Title\nBody", fm)
        assert result == "A short summary"

    def test_from_tldr(self):
        text = "---\ntitle: X\n---\n\n## TL;DR\n\nThis is the gist.\n\n## Details\nMore..."
        result = _extract_summary(text, {})
        assert result == "This is the gist."

    def test_from_main_idea(self):
        text = "---\ntitle: X\n---\n\n## Main Idea\n\nThe main point here.\n\n## More"
        result = _extract_summary(text, {})
        assert result == "The main point here."

    def test_fallback_to_body(self):
        text = "---\ntitle: X\n---\n\nFirst line of body.\n\nSecond paragraph."
        result = _extract_summary(text, {})
        assert result == "First line of body."

    def test_empty_body(self):
        text = "---\ntitle: X\n---\n\n"
        result = _extract_summary(text, {})
        assert result == ""


# ---------------------------------------------------------------------------
# _infer_page_type
# ---------------------------------------------------------------------------


class TestInferPageType:
    def test_from_frontmatter(self):
        assert _infer_page_type(Path("gen-notes/test.md"), {"type": "concept"}) == "concept"

    def test_from_digests_dir(self):
        assert _infer_page_type(Path("gen-notes/digests/paper.md"), {}) == "digest"

    def test_from_concepts_dir(self):
        assert _infer_page_type(Path("gen-notes/concepts/llm.md"), {}) == "concept"

    def test_from_syntheses_dir(self):
        assert _infer_page_type(Path("gen-notes/syntheses/topic.md"), {}) == "synthesis"

    def test_from_names_dir(self):
        assert _infer_page_type(Path("gen-notes/names/hinton.md"), {}) == "name"

    def test_from_categories_paper_digest(self):
        fm = {"categories": ["paper-digest"]}
        assert _infer_page_type(Path("gen-notes/misc/x.md"), fm) == "digest"

    def test_unknown_fallback(self):
        assert _infer_page_type(Path("gen-notes/random.md"), {}) == "unknown"


# ---------------------------------------------------------------------------
# build_index
# ---------------------------------------------------------------------------


class TestBuildIndex:
    def _make_page(self, title, page_type, domain="ai", tags=None):
        return PageInfo(
            path=Path(f"gen-notes/{page_type}s/{title.lower().replace(' ', '-')}.md"),
            title=title,
            page_type=page_type,
            domain=domain,
            tags=tags or [],
            date_created="2024-01-01",
        )

    def test_empty_pages(self):
        result = build_index([])
        assert "# Knowledge Wiki Index" in result
        assert "*No digests yet.*" in result

    def test_sections_present(self):
        pages = [
            self._make_page("Paper A", "digest"),
            self._make_page("LLM", "concept"),
            self._make_page("Hinton", "name"),
        ]
        result = build_index(pages)
        assert "## Recent Digests" in result
        assert "## Concepts" in result
        assert "## Names" in result
        assert "## Stats" in result

    def test_stats_counts(self):
        pages = [
            self._make_page("D1", "digest"),
            self._make_page("D2", "digest"),
            self._make_page("C1", "concept"),
        ]
        result = build_index(pages)
        assert "| Digests | 2 |" in result
        assert "| Concepts | 1 |" in result
        assert "| **Total** | **3** |" in result

    def test_wikilinks_in_output(self):
        pages = [self._make_page("Transformer", "concept")]
        result = build_index(pages)
        # wikilink uses the file stem, which is lowercased by _make_page
        assert "[[transformer]]" in result
