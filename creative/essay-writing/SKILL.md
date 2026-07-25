---
name: essay-writing
description: "Multi-agent essay writing workflow. The main agent (Claude Opus) drafts and revises, a reviewer agent (GLM-5.1 via Z.AI) critiques each draft. Iterates until the essay meets quality standards. Use when asked to write an essay, article, blog post, or long-form piece."
---

# Essay Writing — Multi-Agent Workflow

Write essays through an iterative draft-review cycle using two models:
- **Writer:** Current agent (Claude Opus) — drafts, revises, polishes
- **Reviewer:** GLM-5.1 (via `hermes chat -m glm-5.1 --provider zai`) — critiques, scores, suggests improvements

## Pitfalls & Reviewer Reliability

### Primary reviewer: `delegate_task` (RECOMMENDED)

The most reliable review approach is `delegate_task` — the subagent has its own API access, reads files directly, and avoids shell escaping issues with long essays:

```python
delegate_task(
    goal="Read and critically review the essay at <path>. Act as a demanding reviewer...",
    context="Essay path: <full_path>\n\nFocus on: fact-check numbers, logical consistency, missing considerations, practical realism. Write review to /tmp/review.md",
    toolsets=["terminal", "file"]
)
```

This works even when the ZAI API is rate-limited or unavailable.

### Fallback: Direct API calls via `execute_code`

If `delegate_task` is unavailable, call the reviewer API directly with streaming:

```python
# In execute_code, use http.client for direct API call
import http.client, json, ssl
conn = http.client.HTTPSConnection("api.z.ai", timeout=300)
body = json.dumps({"model": "glm-5.1", "messages": [...], "stream": True}).encode()
conn.request("POST", "/api/coding/paas/v4/chat/completions", body, headers={...})
# Parse SSE stream
```

### ZAI/GLM-5.1 known issues

- **Rate limiting:** ZAI API returns HTTP 429 ("temporarily overloaded") frequently, especially with long prompts. Retry with 60s backoff, max 3 attempts.
- **Timeout:** Non-streaming requests timeout at ~180s for long essays. Always use `stream: True`.
- **hermes CLI `-q` flag:** Passing long essays via `-q "$(cat file)"` often hangs or fails with shell argument limits. Avoid for essays >10K chars.
- **Provider routing:** `hermes chat -m zai/glm-5.1` does NOT work — routes to Anthropic. Must use `-m glm-5.1 --provider zai`.
- **GLM-5.1 duplication:** Sometimes outputs the review twice. Use only the first occurrence.

### delegate_task for content generation is UNRELIABLE

**Do NOT use delegate_task for large content generation tasks** (translation, drafting, rewriting entire sections). Subagents — especially GLM-5.1 — frequently READ input files but FAIL to call write_file on the output. Observed failure rate: ~75% (3 out of 4 attempts read but never wrote). The subagent completes with empty summary despite having file+terminal toolsets.

**Why this fails:** The subagent reads the source, generates the translation/content in its context, but then "forgets" or hits output token limits before calling write_file. The task appears complete from the outside.

**What works instead:** Write content generation directly in the main agent using write_file. For very long content (>5K chars), write in multiple write_file calls (append mode) or compose the full string and write once. It's slower but reliable.

**delegate_task IS reliable for:** Reviews, analysis, short summaries, file manipulation, code execution — tasks where the output is small or the tool call is simple.

### When all external models fail

Use `delegate_task` without specifying a model — it uses the session's current model. While not a "different model" review, it still provides a fresh-context critique since subagents have no conversation history.

### Translation workflow

For translating essays to another language:
1. Read the full source essay
2. Translate directly in the main agent — do NOT delegate to subagents
3. Keep all LaTeX, Mermaid, tables, and code blocks intact
4. Keep proper nouns and abbreviations in the source language
5. Maintain consistent technical terminology across sections (build a glossary first)
6. Save as a NEW essay file in Obsidian vault (same directory, with language suffix)
7. Publish to Gist as a separate gist (not editing the original)

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

### Phase 1.5: Pre-Review Technical Verification (for systems essays)

Before sending a systems essay draft to the reviewer, verify **all numerical claims** with a quick Python calculation script. This catches errors that reviewers will flag — a 2-minute verification saves a lost review round.

**What to verify:**

1. **KV cache / memory claims:** Confirm per-token, per-batch, and per-GPU numbers match the stated model architecture (layers, KV heads, head dim, precision). GQA vs MHA matters — wrong head count produces 8× errors.
2. **Latency / throughput claims:** Verify stated latencies are physically possible given stated hardware (memory bandwidth, FLOPS).
3. **Model-on-GPU capacity:** Confirm whether the stated model fits on the stated GPU configuration at the stated precision. Tensor parallelism changes per-GPU numbers.
4. **Paper citations:** Confirm each arXiv ID resolves via `http://export.arxiv.org/api/query?id_list=<id>`. Check that author lists and paper titles match.

**Example verification script (from the KV cache congestion essay):**
```python
layers = 80; kv_heads = 8; head_dim = 128; bytes_per = 2  # FP16, GQA
per_token = 2 * layers * kv_heads * head_dim * bytes_per
print(f"Per-token KV: {per_token:,} B = {per_token/1024:.0f} KB")
per_gpu = per_token / 8  # TP=8
print(f"Per-GPU: {per_gpu/1024:.0f} KB")
```

**Pattern:** Use `execute_code` with `from hermes_tools import terminal` for the verification script. Print results to stdout. If any number doesn't match, fix the essay before submitting for review.

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

### Parallelization: Review + Diagrams

After round 1, run subsequent reviews in the **background** to parallelize with other work:

```bash
# Run review in background with notification
terminal(command="hermes chat -m glm-5.1 --provider zai -q '...' 2>/dev/null | sed -n '/^#/,$p'",
         timeout=180, background=true, notify_on_complete=true)
```

While the review runs, create diagrams via `delegate_task` (up to 3 in parallel).

**Use Mermaid diagrams, NOT Excalidraw.** Excalidraw produces separate `.excalidraw` files that don't render inline in Obsidian or GitHub Gist. Mermaid diagrams are self-contained code blocks in the markdown — they render natively in Obsidian, GitHub, and any Mermaid-aware viewer. This matters because essays are typically published to GitHub Gist or shared as markdown.

Useful Mermaid diagram types for essays:
- `flowchart TD` / `graph TD` — **preferred default** for vertical-screen readability (phones, tablets, split-screen). Flows top-to-bottom.
- `flowchart LR` / `graph LR` — use sparingly, only when horizontal flow is semantically essential (e.g., a short pipeline with ≤3 stages). These get too wide on vertical screens.
- `sequenceDiagram` — limit to **3 participants max**. 4+ participants create very wide diagrams. Shorten participant labels.
- `gantt` — acceptable, auto-scales. Keep section names short.
- `timeline` — chronological events
- `pie` — good for budget/proportion breakdowns
- Use consistent color coding across diagrams (e.g., `style X fill:#a5d8ff` for one topic, `fill:#b2f2bb` for another)

**Vertical-screen optimization (learned from experience):**
- Convert `flowchart LR` with subgraphs → `flowchart TD` with subgraphs stacked vertically and explicit flow arrows between them
- For long LR chains (5+ nodes), switch to TD — the chain becomes a column
- Sequence diagrams: reduce participants by combining related actors (e.g., "GPU 0, GPU 1, GPU 2, GPU 31" → "GPU 0, GPU 1, GPU N")
- Shorten node labels: "73 tokens for experts 8-15" → "73 tokens"

**Mermaid patterns that break in Obsidian/GitHub rendering:**
- **Wide fan-out trees (6+ children from one root):** Split into 2 rows of 3 using a hidden second root node (`A2[ ] -->` with `style A2 fill:none,stroke:none`). Prevents horizontal overflow.
- **Side-by-side subgraphs:** Mermaid renders `subgraph` blocks horizontally next to each other, causing overflow. Remove subgraphs and use plain node groups instead -- Mermaid will stack them vertically.
- **Invisible edges for positioning (`-.-` or `-.->`):** Don't use dotted/invisible edges to position nodes. They create visual noise and don't reliably control layout. Use `quadrantChart` for 2D positioning instead.
- **`quadrantChart`:** Use for any "landscape" or positioning diagram (scope vs. maturity, cost vs. quality). Values are `[x, y]` in 0-1 range. Much cleaner than trying to fake a scatter plot with `graph`.
- **`<br><i>...</i>` in subgraph titles:** Subgraph titles with complex formatting may not render. Keep subgraph names simple.
- **Emoji in nodes:** Works in Obsidian but may not render in all Mermaid implementations. Use sparingly.

### Phase 2.5: Reference Material Integration (optional but high-impact)

When the essay compares or analyzes papers, **read the paper digests and source notes** (e.g., from Obsidian gen-notes/digests/) for the referenced foundational works. Weave the intellectual lineage into the essay — explain how the papers build on each other, what each predecessor contributed, and how the lineage clarifies the current dispute or comparison.

This is the single highest-impact improvement step. In practice it produced the biggest quality jump (7.8 → 8.0 PUBLISH) by:
- Making the "why" behind technical choices clear (not just "what")
- Grounding accusations (e.g., "loose analysis") in provable facts (e.g., Alon-Klartag optimality bound)
- Giving the reader the conceptual toolkit to evaluate claims independently

Add a Mermaid lineage flowchart showing the dependency graph between papers.

### Focused Review Prompts for Later Rounds

After round 1's full review, subsequent rounds can use shorter, targeted review prompts that focus on what changed. This is faster and produces more useful feedback:

```
"This is the third revision. Score each dimension 1-10 briefly, give overall
score and verdict (PUBLISH >= 8, REVISE 5-7). Focus on whether the new
Section N successfully [specific goal of the revision]."
```

### Phase 3: Polish & Deliver

1. Final proofread pass (grammar, flow, word choice)
2. Save final version to `workspace/essays/<slug>/final.md`
3. If diagrams were created, save them in `workspace/essays/<slug>/diagrams/`
4. Present to the user with a summary of the review journey:
   - How many rounds
   - Score progression (e.g., 5.8 → 7.2 → 8.4)
   - Key improvements made
   - Diagram links (if created)
5. If delivery to another platform is requested (Discord, Telegram, etc.), use a cron job with `deliver` target for the final report.

### Phase 4: Publishing to GitHub Gist

When essays are published to GitHub Gist:

1. **Publish:** `gh gist create "<filename>.md" --desc "<title>" --public`
2. **Add URL to frontmatter:** Add `published: <gist_url>` to the essay's YAML frontmatter immediately after publishing
3. **Republish on every update:** Whenever an essay with a `published:` field is modified, always republish. Use `gh gist edit` with the local file path — it replaces the Gist content cleanly:

```bash
gh gist edit <gist_id> <path_to_updated_file>
```

This replaces the Gist file with the local file content (verified working May 2026). The `gh gist edit <id> <file>` form does NOT append — it replaces. No TERM issues.

**Alternative (if gh gist edit fails):** Use the GitHub API directly via `gh api`:

```python
import json
from hermes_tools import terminal
content = terminal(f"cat {filepath}")["output"]
payload = json.dumps({
    "description": "Updated",
    "files": {"original-filename.md": {"content": content}}
})
terminal(f"gh api -X PATCH /gists/{gist_id} --input - <<'EOF'\n{payload}\nEOF")
```

Pitfalls:
- The `files` key in the API payload must use the **existing filename** in the gist, not the local filename
- `gh gist edit` with `-f` flag + stdin redirection fails with "TERM environment variable not set" — but `gh gist edit <id> <file>` (no `-f`) works

4. Extract the gist ID from the URL (last path segment)
5. **Author byline:** Format: `*Liping Zhang, assisted by Hermes Agent ([model]) | Date*`. Use the actual model currently running.

This is mandatory — every essay update must be followed by a republish if it has a `published:` URL.

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
  diagrams/         — Excalidraw diagrams (if created)
```

## Obsidian Frontmatter Rules

Obsidian's YAML parser is stricter than standard YAML. Essays saved to the Obsidian vault must follow these rules:

- **Tags must be YAML list format**, not inline arrays:
  ```yaml
  # WRONG — Obsidian won't parse this
  tags: [ai-infrastructure, tpu, google]
  
  # CORRECT
  tags:
    - ai-infrastructure
    - tpu
    - google
  ```
- **No `[[wikilinks]]` in frontmatter.** Wikilinks are an Obsidian markdown extension, not valid YAML. If you need concept links, use them in the body text only.
- **Remove empty/placeholder keys.** Don't leave `published:` with no value — either omit it or fill it in.

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

## Deep Review Checklist (applied at Round 3+)

After the essay passes basic review (score 7+), use this checklist to find issues that earlier rounds typically miss. These are patterns discovered empirically across multiple essay review cycles:

1. **Unexamined Assumptions:** Every technical plan has hidden assumptions. Identify the 3-5 most critical ones and add a dedicated section examining each — what must be true for the plan to work, how to verify, and what happens if disproven. This directly addresses the "causal chain is unexamined" critique.

2. **Operational Gaps:** Look for what happens AFTER the core flow. Essays often terminate at "deploy to production" without addressing version management, gradual rollout, rollback criteria, and production monitoring. Add a §X.4 or similar subsection covering the release lifecycle.

3. **Pre-mortem:** Risk analysis sections tend to be generic. A pre-mortem exercise ("imagine the project failed — write down the 5 most likely specific failure modes, their early warning signals, and concrete interventions") produces far more actionable content than a standard risk matrix.

4. **Failure Mode: "Technology works, behavior doesn't change":** The most common automation project failure is not technical — it's adoption. Add behavioral metrics to go/no-go criteria (e.g., "60% of data requests go through the system within 4 weeks").

5. **Buzzword Density:** Count occurrences of key terms. If any term appears >15 times in a single section, replace 2-3 instances with more specific language. The term "闭环" is a common offender in Chinese essays.

6. **Provider-specific Vision API Failures:** If the essay references images or needs image analysis, note that some providers (DeepSeek custom) don't support `image_url` in message content. Use tesseract OCR as fallback (see ocr-and-documents skill).

## Multi-Perspective Review (for executive-facing documents)

For essays that need executive/VP/CEO approval, a single technical review is insufficient. Run reviews from at least two perspectives after the essay passes basic technical review (score 7+):

**Perspective 1: Technical Reviewer** (standard, covered above)
Scores: thesis, structure, evidence, prose, originality. Focuses on completeness and logical rigor.

**Perspective 2: Executive Reviewer** (for strategic/business documents)
Use `delegate_task` with a role-playing prompt. The executive reviewer's dimensions are completely different:
- Strategic alignment — Does this align with the company's actual priorities?
- Business ROI — Can you trace from technical improvement to revenue/market share?
- Opportunity cost — What are we NOT funding? Why is this the best use of resources?
- Ecosystem moat — What's uniquely ours that competitors can't copy?
- Measurability — What 1-2 outcome metrics should the CEO track?
- Sustainability — What happens in month 13? Maintenance, tech debt, competitive response?

Example CEO review prompt:
```
You are the CEO of [company]. Review this plan strictly from an executive perspective.
Do not score on technical merit — score on strategic alignment, business return,
opportunity cost, organizational readiness, competitive moat, and measurability.
Write review to review-ceo.md.
```

In practice, the CEO review consistently surfaces issues the technical review missed — ecosystem data being treated as an afterthought instead of the core moat, 5 process metrics when the CEO only needs 2 outcome metrics, and no analysis of what happens after the 12-month plan ends.

## Executive-Facing Document Patterns

When writing documents for executive approval, include these elements that are typically absent from technical documents:

1. **Executive Summary (1 page max):** Answer six questions — what problem, why now, why us, what resources, how to measure success, what's the most likely failure mode. The CEO should not need to read 1000 lines to make a decision.

2. **Opportunity Cost Analysis:** The most important section for executives. A table comparing the proposed approach against 3-4 alternative uses of the same resources, with explicit "why not choose this" reasoning for each alternative.

3. **Two CEO Metrics Only:** Process metrics (iteration cycles, experiment throughput, eval time) are for internal team management. The CEO needs 1-2 outcome metrics — a specific benchmark improvement rate and effective experiment verification time. If those don't improve, nothing else matters.

4. **Go/No-Go with Behavioral Metrics:** Technical go/no-go isn't enough. Add behavioral adoption criteria (e.g., "60% of data requests go through the system within 4 weeks of delivery"). Technology working doesn't mean adoption happened.

5. **Quarterly Termination Clause:** "If both CEO metrics show no improvement for two consecutive quarters, the project enters restructuring or termination review."

## Essay Trimming Strategy

When an essay needs aggressive shortening (cutting 50%+), preserve these sections and cut everything else:
- **Keep:** Executive summary, opportunity cost analysis, ecosystem differentiator, pre-mortem, CEO metrics, sustainability plan
- **Cut:** Lengthy capability mapping tables, verbose pipeline descriptions, obvious explanatory text ("it is important to note that..."), technical detail that doesn't differentiate the strategic argument

Target: ~400 lines for an executive-facing plan; ~600 lines for a detailed technical plan.

## Domain Correction Iteration (from user, not reviewer)

When the user provides highly specific domain knowledge corrections during iteration — org structure, metrics definitions, technical architectures, team dynamics — these are more valuable than any reviewer agent feedback. Key patterns:

- **Small corrections (1-2 sections):** Use targeted `patch()` calls
- **Medium corrections (3-5 sections):** Batch multiple patches, but verify the file didn't get corrupted (check `wc -c` after)
- **Large corrections (5+ sections or full restructure):** Do a single `write_file()` with the full rewritten content. Accumulating 10+ patches is error-prone and has corrupted files in practice — the string replacements in `execute_code` are not atomic and a single failed match silently drops content.

**After rewriting, always verify:** `wc -c <file>` to confirm the output is proportional to expected size. A 20K-word plan should be ~13-20KB. If the file is 156 bytes, it got corrupted and needs immediate recovery.

## Configuration

| Setting | Default | Notes |
|---------|---------|-------|
| Writer model | Current session model | Claude Opus recommended |
| Reviewer model | `zai/glm-5.1` | Change via reviewer_model below |
| Max rounds | 3 | Increase for critical pieces |
| Target score | 8.0 | Minimum for PUBLISH verdict |

To use a different reviewer model, adjust the `-m` flag in the hermes chat command.
