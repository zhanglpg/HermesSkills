"""Tests for wiki-manager concept_manager module."""

from concept_manager import (
    _format_existing_pages,
    _normalize_name,
    _sanitize_filename,
    _sanitize_llm_output,
)

# ---------------------------------------------------------------------------
# _normalize_name
# ---------------------------------------------------------------------------


class TestNormalizeName:
    def test_hyphenated(self):
        assert _normalize_name("Chain-of-Thought") == "chainofthought"

    def test_special_chars(self):
        assert _normalize_name("GPT-4 (OpenAI)") == "gpt4openai"

    def test_spaces(self):
        assert _normalize_name("large language model") == "largelanguagemodel"

    def test_already_clean(self):
        assert _normalize_name("bert") == "bert"

    def test_empty(self):
        assert _normalize_name("") == ""


# ---------------------------------------------------------------------------
# _sanitize_llm_output
# ---------------------------------------------------------------------------


class TestSanitizeLlmOutput:
    def test_plain_text(self):
        assert _sanitize_llm_output("Hello world") == "Hello world"

    def test_strips_code_fence(self):
        text = "```markdown\n---\ntitle: X\n---\n\nBody\n```"
        result = _sanitize_llm_output(text)
        assert result.startswith("---")
        assert "```" not in result

    def test_strips_yaml_fence(self):
        text = "```yaml\nkey: val\n```"
        result = _sanitize_llm_output(text)
        assert "```" not in result

    def test_duplicate_frontmatter_keeps_last(self):
        text = "---\ntitle: Old\n---\n\n---\ntitle: New\n---\n\nBody"
        result = _sanitize_llm_output(text)
        assert "title: New" in result
        # Should not contain the old frontmatter as a standalone block
        assert result.startswith("---")


# ---------------------------------------------------------------------------
# _sanitize_filename
# ---------------------------------------------------------------------------


class TestSanitizeFilename:
    def test_strips_colons_and_quotes(self):
        result = _sanitize_filename('Chain-of-Thought: A "Method"')
        assert ":" not in result
        assert '"' not in result

    def test_strips_slashes(self):
        result = _sanitize_filename("Input/Output")
        assert "/" not in result

    def test_normal_name(self):
        assert _sanitize_filename("Transformer") == "Transformer"


# ---------------------------------------------------------------------------
# _format_existing_pages
# ---------------------------------------------------------------------------


class TestFormatExistingPages:
    def test_none_input(self):
        result = _format_existing_pages(None)
        assert result["existing_concepts"] == "(none yet)"
        assert result["existing_names"] == "(none yet)"
        assert result["existing_digests"] == "(none yet)"

    def test_with_data(self):
        data = {
            "concepts": ["Transformer", "BERT"],
            "names": ["Hinton"],
            "digests": [],
        }
        result = _format_existing_pages(data)
        assert "Transformer" in result["existing_concepts"]
        assert "BERT" in result["existing_concepts"]
        assert "Hinton" in result["existing_names"]
        assert result["existing_digests"] == "(none yet)"
