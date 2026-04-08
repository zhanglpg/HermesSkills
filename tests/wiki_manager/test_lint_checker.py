"""Tests for wiki-manager lint_checker module."""

from pathlib import Path

from lint_checker import (
    LintIssue,
    _extract_wikilinks,
    check_broken_links,
    check_duplicate_concepts,
    check_frontmatter,
    check_orphans,
    check_stale_concepts,
    format_lint_report,
)
from vault_index import PageInfo


def _page(title, page_type="concept", date_updated="2024-01-01", tags=None):
    return PageInfo(
        path=Path(f"gen-notes/{page_type}s/{title.lower()}.md"),
        title=title,
        page_type=page_type,
        tags=tags or [],
        date_created=date_updated,
        date_updated=date_updated,
    )


# ---------------------------------------------------------------------------
# _extract_wikilinks
# ---------------------------------------------------------------------------


class TestExtractWikilinks:
    def test_basic(self):
        result = _extract_wikilinks("See [[Transformer]] and [[BERT]].")
        assert result == ["Transformer", "BERT"]

    def test_with_display_text(self):
        result = _extract_wikilinks("[[Transformer|the model]]")
        assert result == ["Transformer"]

    def test_no_links(self):
        assert _extract_wikilinks("Plain text with no links.") == []

    def test_multiple_on_same_line(self):
        result = _extract_wikilinks("[[A]] then [[B]] then [[C]]")
        assert len(result) == 3


# ---------------------------------------------------------------------------
# check_orphans
# ---------------------------------------------------------------------------


class TestCheckOrphans:
    def test_finds_unreferenced(self):
        pages = [_page("Transformer"), _page("BERT")]
        content = {Path("gen-notes/digests/d.md"): "Mentions [[Transformer]] only."}
        issues = check_orphans(pages, content)
        assert len(issues) == 1
        assert "BERT" in issues[0].message

    def test_all_linked(self):
        pages = [_page("Transformer")]
        content = {Path("gen-notes/digests/d.md"): "See [[Transformer]]."}
        issues = check_orphans(pages, content)
        assert len(issues) == 0


# ---------------------------------------------------------------------------
# check_broken_links
# ---------------------------------------------------------------------------


class TestCheckBrokenLinks:
    def test_finds_missing(self):
        content = {Path("gen-notes/d.md"): "See [[NonExistent]]."}
        issues = check_broken_links(content, {"transformer"}, {"Transformer"})
        assert len(issues) == 1
        assert "NonExistent" in issues[0].message

    def test_all_valid(self):
        content = {Path("gen-notes/d.md"): "See [[Transformer]]."}
        issues = check_broken_links(content, {"Transformer"}, {"Transformer"})
        assert len(issues) == 0

    def test_matches_stem_or_title(self):
        content = {Path("gen-notes/d.md"): "See [[my-page]]."}
        issues = check_broken_links(content, {"my-page"}, set())
        assert len(issues) == 0


# ---------------------------------------------------------------------------
# check_stale_concepts
# ---------------------------------------------------------------------------


class TestCheckStaleConcepts:
    def test_finds_old(self):
        pages = [_page("Old Concept", date_updated="2020-01-01")]
        issues = check_stale_concepts(pages, max_age_days=90)
        assert len(issues) == 1
        assert "stale" in issues[0].check

    def test_recent_ok(self):
        pages = [_page("Fresh", date_updated="2099-01-01")]
        issues = check_stale_concepts(pages, max_age_days=90)
        assert len(issues) == 0

    def test_ignores_non_concepts(self):
        pages = [_page("Old Digest", page_type="digest", date_updated="2020-01-01")]
        issues = check_stale_concepts(pages, max_age_days=90)
        assert len(issues) == 0


# ---------------------------------------------------------------------------
# check_frontmatter
# ---------------------------------------------------------------------------


class TestCheckFrontmatter:
    def test_missing_title(self):
        page = PageInfo(
            path=Path("gen-notes/concepts/x.md"),
            title="",
            page_type="concept",
            date_created="2024-01-01",
        )
        issues = check_frontmatter([page])
        assert len(issues) == 1
        assert "title" in issues[0].message

    def test_digest_missing_tags(self):
        page = PageInfo(
            path=Path("gen-notes/digests/x.md"),
            title="X",
            page_type="digest",
            tags=[],
        )
        issues = check_frontmatter([page])
        assert len(issues) == 1
        assert "tags" in issues[0].message

    def test_complete_no_issues(self):
        page = PageInfo(
            path=Path("gen-notes/digests/x.md"),
            title="X",
            page_type="digest",
            tags=["ai"],
        )
        issues = check_frontmatter([page])
        assert len(issues) == 0


# ---------------------------------------------------------------------------
# check_duplicate_concepts
# ---------------------------------------------------------------------------


class TestCheckDuplicateConcepts:
    def test_finds_duplicates(self):
        pages = [_page("Chain-of-Thought"), _page("chain of thought")]
        issues = check_duplicate_concepts(pages)
        assert len(issues) == 1
        assert "duplicate" in issues[0].check

    def test_no_duplicates(self):
        pages = [_page("Transformer"), _page("BERT")]
        issues = check_duplicate_concepts(pages)
        assert len(issues) == 0


# ---------------------------------------------------------------------------
# format_lint_report
# ---------------------------------------------------------------------------


class TestFormatLintReport:
    def test_empty_report(self):
        result = format_lint_report([])
        assert "All checks passed" in result

    def test_with_issues(self):
        issues = [
            LintIssue(severity="error", check="test", page="p.md", message="Error!"),
            LintIssue(severity="warning", check="test2", page="q.md", message="Warn"),
        ]
        result = format_lint_report(issues)
        assert "2 issues found" in result
        assert "1 errors" in result
        assert "1 warnings" in result
