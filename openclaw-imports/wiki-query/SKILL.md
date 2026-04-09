---
name: wiki-query
description: "Answers research questions by searching the knowledge wiki (gen-notes/index.md), synthesizing answers from digest, concept, and name pages, and optionally filing valuable answers as synthesis or comparison pages. Use for research questions, cross-paper analysis, or wiki searches."
---

# Wiki Query

Answer research questions by searching the knowledge wiki, synthesizing answers from existing pages, and filing valuable analyses back into the wiki.

## Workflow

1. **Read the index** — Start by reading `gen-notes/index.md` to understand what pages exist and find relevant ones
2. **Read relevant pages** — Open the digest, concept, and name pages most relevant to the question
3. **Synthesize an answer** — Draw from multiple sources, cite pages with `[[wikilinks]]`
4. **File back if valuable** — If the answer is substantive (not a trivial lookup), save it as a synthesis page

## Filing Synthesis Pages

When an answer merits permanent storage:

1. Save to `gen-notes/syntheses/<Descriptive Title>.md`
2. Use this format:

```markdown
---
title: "Descriptive Title Based on the Question"
type: synthesis
date-created: YYYY-MM-DD
sources:
  - "[[Source Page 1]]"
  - "[[Source Page 2]]"
tags:
  - relevant-tag
status: 📥
---

# Descriptive Title

> **Query:** The original question asked
> **Date:** YYYY-MM-DD

## Answer

<Synthesized answer drawing from wiki pages. Use [[wikilinks]] for all references.>

## Sources Used

- [[Page 1]] — what was relevant from this page
- [[Page 2]] — what was relevant from this page
```

3. After saving, run `wiki_manager.py index` to update the index
4. Run `wiki_manager.py` log to record the query event (or append manually)

## When to File vs Not File

**File as comparison** (to `gen-notes/comparisons/`):
- Side-by-side comparisons of papers, methods, or approaches
- Multi-paper evolutionary narratives (e.g., how a technique developed across 3+ papers)

**File as synthesis** (to `gen-notes/syntheses/`):
- Answers that required reading 3+ wiki pages
- Insights that connect concepts in non-obvious ways
- Answers the user is likely to want again

**Don't file:**
- Simple factual lookups ("when was X published?")
- Answers from a single page
- Trivial questions

## Multi-Paper Synthesis Essay Workflow

When the user asks for a deep synthesis across a series of related digests (e.g., "trace the evolution of X" or "compare these papers"), use this workflow:

### Step 1: Draft
Write the full essay drawing from the digest pages. Include:
- Mermaid diagrams (`graph TD`, `flowchart LR`, `sequenceDiagram`, `gantt`) — 4-6 per essay for architecture/evolution
- Key equations (LaTeX `$$...$$`) where the method is mathematical
- A concrete worked example with real numbers (model sizes, GPU counts, latencies) — this is the highest-impact quality signal
- Explicit connections between papers (what each built on, what it added)
- Open questions and future directions section

### Step 2: Critic Pass
Run a single `delegate_task` critic with specific review dimensions:
```
delegate_task(goal="Critically review this essay...",
  context="Essay at /tmp/draft.md. Check: (1) technical accuracy,
  (2) structure/flow, (3) Mermaid correctness, (4) equation accuracy,
  (5) writing quality, (6) missing perspectives",
  toolsets=["file"], max_iterations=15)
```

### Step 3: Polish
Apply the critic's fixes. Common high-value fixes from experience:
- **Taxonomy consistency** — if you define a generational framework, ensure every "generation" meets the stated criteria (e.g., if "each generation adds a disaggregation boundary," don't include an optimization that isn't a boundary)
- **Equation precision** — critics catch unit errors, wrong variable definitions, and formulas that invite scrutiny without clear approximation conditions
- **Concrete numbers** — add a worked example with specific model/hardware configs; abstract cost models are forgettable
- **Missing failure modes** — fault tolerance, scheduling complexity, and operational overhead are commonly absent from systems synthesis

### Step 4: Save
Save to `gen-notes/comparisons/` (not syntheses/) with proper frontmatter including `domain:` tag, `type: comparison`, and `sources:` linking to all referenced digests.

## Notes

- Always check `gen-notes/index.md` first — it has one-line summaries of every page
- Prefer existing concept/name pages over raw digests when available
- If the wiki doesn't cover the topic, say so — don't hallucinate from outside the wiki
- Cross-reference with concept and name pages to provide broader context
