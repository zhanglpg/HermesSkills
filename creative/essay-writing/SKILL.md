---
name: essay-writing
description: "Multi-agent essay writing workflow. The main agent (Claude Opus) drafts and revises, a reviewer agent (GLM-5.1 via Z.AI) critiques each draft. Iterates until the essay meets quality standards. Use when asked to write an essay, article, blog post, or long-form piece."
---

# Essay Writing — Multi-Agent Workflow

Write essays through an iterative draft-review cycle using two models:
- **Writer:** Current agent (Claude Opus) — drafts, revises, polishes
- **Reviewer:** GLM-5.1 (via `hermes chat -m glm-5.1 --provider zai`) — critiques, scores, suggests improvements

## Pitfalls

- **Provider routing:** `hermes chat -m zai/glm-5.1` does NOT work — Hermes sends it to Anthropic. Must use `-m glm-5.1 --provider zai` (model and provider as separate flags).
- **GLM-5.1 duplication:** GLM-5.1 sometimes outputs the full review twice in one response. The review script captures the raw output; when parsing, use only the first occurrence (split on the second `# Essay Review` header if present).
- **Long essays:** The review script passes essay content inline via shell argument. For essays >15K chars, this may hit shell argument limits. In that case, use `hermes chat` with a tempfile-based approach or truncate to the most important sections.
- **`-Q` flag:** The quiet flag (`-Q`) suppresses the banner but may cause exit code 1 on some setups. The review script omits it and filters the output. If banner noise appears in reviews, pipe through `sed -n '/^#/,$p'` to extract from the first markdown header onward.

## Workflow

### Phase 0: Starting from an Existing Draft

When the user already has a draft (e.g., in Obsidian, a workspace, or a previous session):
1. Copy it to `workspace/essays/<slug>/draft-1.md`
2. Skip directly to Phase 2b (review) — do NOT rewrite or outline first
3. The review will identify what needs improving; revise in draft-2

### Phase 1: Outline (new essays only)

1. Clarify the topic, audience, tone, and length with the user
2. Produce a structured outline with thesis, sections, and key arguments
3. Save outline to `workspace/essays/<slug>/outline.md`
4. Get user approval before drafting

### Phase 2: Draft → Review Loop (max 3 rounds)

Each round:

**2a. Write/Revise Draft**

Write (or revise) the full essay. Save to:
```
workspace/essays/<slug>/draft-N.md
```

**2b. Send to Reviewer**

Spawn a reviewer agent via terminal:

```bash
hermes chat -m glm-5.1 --provider zai -q "$(cat <<'PROMPT'
You are a demanding but constructive essay reviewer. Read the following essay and provide a structured review.

## Essay
<contents of draft-N.md>

## Review Instructions

Score each dimension 1-10 and explain:

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

Be honest. Vague praise is useless. Specific critique is valuable.
PROMPT
)"
```

**Important implementation notes:**
- The essay content must be passed inline in the prompt (not as a file path — the reviewer agent has no file context)
- For long essays, truncate to fit within context limits or split into sections
- Parse the reviewer's output for the verdict and specific suggestions

**2c. Process Feedback**

- If verdict is **PUBLISH**: proceed to Phase 3
- If verdict is **REVISE**: address the specific weaknesses, write next draft
- If verdict is **RETHINK**: discuss fundamental issues with the user before continuing
- After 3 rounds, present the best draft to the user regardless

### Phase 3: Polish & Deliver

1. Final proofread pass (grammar, flow, word choice)
2. Save final version to `workspace/essays/<slug>/final.md`
3. Present to the user with a summary of the review journey:
   - How many rounds
   - Score progression (e.g., 5.8 → 7.2 → 8.4)
   - Key improvements made

## File Structure

```
workspace/essays/<slug>/
  outline.md        — Approved outline
  draft-1.md        — First draft
  review-1.md       — First review feedback
  draft-2.md        — Revised draft
  review-2.md       — Second review feedback
  draft-N.md        — Nth draft
  review-N.md       — Nth review feedback
  final.md          — Polished final version
```

## Guidelines for the Writer

- **Lead with the interesting part.** Don't warm up. The first paragraph should make the reader want the second.
- **One idea per paragraph.** If you need a topic sentence to hold it together, split it.
- **Be specific.** "Many companies" → "Google, Meta, and Anthropic." "Recently" → "In March 2026."
- **Cut filler.** "It is important to note that" → delete. "In order to" → "to."
- **Earn your abstractions.** Start concrete, then generalize. Never the reverse.
- **End strong.** The last paragraph should land, not trail off.

## Guidelines for Interpreting Reviews

- Prioritize fixing weaknesses scored below 6
- If the reviewer contradicts the user's intent, side with the user
- Structural feedback (reorder sections, cut tangents) matters more than surface edits
- If the same weakness persists across rounds, try a fundamentally different approach rather than incremental fixes

## Configuration

| Setting | Default | Notes |
|---------|---------|-------|
| Writer model | Current session model | Claude Opus recommended |
| Reviewer model | `zai/glm-5.1` | Change via reviewer_model below |
| Max rounds | 3 | Increase for critical pieces |
| Target score | 8.0 | Minimum for PUBLISH verdict |

To use a different reviewer model, adjust the `-m` flag in the hermes chat command.
