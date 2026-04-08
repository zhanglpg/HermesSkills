#!/bin/bash
# Review an essay draft using a separate Hermes agent with a different model.
#
# Usage:
#   bash scripts/review.sh <draft_path> [model]
#
# Example:
#   bash scripts/review.sh workspace/essays/my-essay/draft-1.md zai/glm-5.1
#
# Output: Prints the review to stdout and saves to review-N.md alongside the draft.

set -euo pipefail

DRAFT_PATH="${1:?Usage: review.sh <draft_path> [model]}"
MODEL="${2:-glm-5.1}"
PROVIDER="${3:-zai}"

if [ ! -f "$DRAFT_PATH" ]; then
    echo "Error: Draft not found: $DRAFT_PATH" >&2
    exit 1
fi

# Derive review output path: draft-1.md -> review-1.md
DRAFT_DIR="$(dirname "$DRAFT_PATH")"
DRAFT_NAME="$(basename "$DRAFT_PATH")"
REVIEW_NAME="${DRAFT_NAME/draft/review}"
REVIEW_PATH="${DRAFT_DIR}/${REVIEW_NAME}"

ESSAY_CONTENT="$(cat "$DRAFT_PATH")"

# Build the review prompt
REVIEW_PROMPT="You are a demanding but constructive essay reviewer. Read the following essay and provide a structured review.

## Essay

${ESSAY_CONTENT}

## Review Instructions

Score each dimension 1-10 and explain briefly:

1. **Thesis & Argument** — Is the central claim clear? Is the reasoning sound?
2. **Structure** — Does it flow logically? Are transitions smooth?
3. **Evidence & Depth** — Are claims supported? Is analysis substantive?
4. **Prose Quality** — Is the writing clear, precise, and engaging?
5. **Originality** — Does it offer fresh insight, or just restate common knowledge?

Then provide:
- **Top 3 Strengths** — What works well
- **Top 3 Weaknesses** — What needs the most work (be specific, quote passages)
- **Concrete Suggestions** — Specific rewrites, restructuring, or additions
- **Overall Score** — Average of the 5 dimensions
- **Verdict** — PUBLISH (score >= 8), REVISE (score 5-7), or RETHINK (score < 5)

Be honest. Vague praise is useless. Specific critique is valuable."

# Run the reviewer agent
# Note: Do NOT use -Q flag alone — it can cause exit code 1 on some setups.
# Instead, capture full output and strip the banner.
echo "Sending draft to reviewer (model: ${MODEL}, provider: ${PROVIDER})..." >&2
RAW_OUTPUT="$(hermes chat -m "$MODEL" --provider "$PROVIDER" -q "$REVIEW_PROMPT" 2>/dev/null)"

# Strip Hermes banner: extract from first markdown header onward
REVIEW_OUTPUT="$(echo "$RAW_OUTPUT" | sed -n '/^#/,$p')"

# Handle GLM-5.1 duplication: if the review header appears twice, keep only the first occurrence
# GLM-5.1 sometimes outputs the full review twice in one response
FIRST_HEADER="$(echo "$REVIEW_OUTPUT" | head -1)"
SECOND_OCCURRENCE="$(echo "$REVIEW_OUTPUT" | grep -n "^${FIRST_HEADER}$" | tail -1 | cut -d: -f1)"
FIRST_OCCURRENCE="$(echo "$REVIEW_OUTPUT" | grep -n "^${FIRST_HEADER}$" | head -1 | cut -d: -f1)"
if [ "$SECOND_OCCURRENCE" != "$FIRST_OCCURRENCE" ] 2>/dev/null; then
    # Duplicate detected — keep only up to the line before the second occurrence
    REVIEW_OUTPUT="$(echo "$REVIEW_OUTPUT" | head -$((SECOND_OCCURRENCE - 1)))"
    echo "Note: Duplicate review detected and trimmed." >&2
fi

# Save and print
echo "$REVIEW_OUTPUT" > "$REVIEW_PATH"
echo "Review saved to: ${REVIEW_PATH}" >&2
echo ""
echo "$REVIEW_OUTPUT"
