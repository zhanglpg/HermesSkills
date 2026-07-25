---
name: technical-survey-review
description: "Review and improve an existing technical survey or comparison essay — diagnose structural/coverage gaps, verify citations and mechanism descriptions, apply an editorial pass, and republish. Use when the user asks to 'review', 'comment on', 'suggest improvements for', or 'tighten' a finished long-form technical survey, comparison, or lineage essay (as opposed to writing one from scratch, which is the essay-writing skill)."
---

# Technical Survey Review

Review and improve an *existing* technical survey, comparison, or lineage essay. This is the complement to `essay-writing` (which drafts new essays via a multi-agent write/review loop): this skill governs critiquing a finished piece and making it better with an editorial pass. The user maintains a large library of these (Obsidian `gen-notes/surveys/`, each published to a GitHub Gist) and reviews them iteratively.

## When to use

- "Review the X survey and suggest improvements"
- "Comment on whether the new version is better"
- "Do the editorial pass and publish"
- "Add a section covering X and update the survey"

## The review: what to diagnose

Read the full survey first, then assess on these axes. Full checklist with examples in `references/review-checklist.md`. The high-value diagnoses, roughly in priority order:

1. **Does it deliver on its own title?** A survey titled "Comparison" with no master comparison table is the classic failure — the comparing is scattered through prose and the reader can't scan the design space. A "lineage" essay needs the lineage arc stated and defended.
2. **Structural overload in the intro.** Premature citations (naming systems/papers the reader hasn't met yet) and meta-references ("developed in Section 8, drives the conclusion in Section 9") front-load the argument before the reader has earned it. State the framework; defer the evidence.
3. **Wall paragraphs.** A single block that makes 3+ distinct points (a distinction, an example, a counterexample, a lesson) needs to be broken up. The sharpest counterexample usually deserves its own paragraph.
4. **Coverage gaps the vault already exposes.** Search the user's Obsidian vault for notes on the survey's topic — a thematically-central method that's in the vault but missing from the survey is the strongest, easiest coverage fix.
5. **Repetitive conclusions** that re-argue the thesis instead of pointing forward.
6. **Draft artifacts in a published piece:** `TBD` placeholders, broken YAML frontmatter (inline arrays — Obsidian won't parse them), Mermaid `graph LR` with subgraphs (overflows on vertical screens — prefer `flowchart TD` with stacked subgraphs).
7. **Citation and mechanism accuracy** — see below. This is where confident-sounding errors hide.

## Verify before you publish — citations AND mechanisms

When you add or check technical content, verify against sources, not memory:

- **arXiv IDs:** Confirm each ID resolves (`https://arxiv.org/abs/<id>` in the browser, or `http://export.arxiv.org/api/query?id_list=<id>` if not blocked). **Verify any ID you recalled from memory before publishing** — do not trust recalled IDs.
- **Mechanism descriptions (the most-skipped check):** When you describe *what a paper's technique actually does* — its named components, objective, innovations — check the abstract/body, not your memory. Recalled mechanism names are a frequent source of confident errors. *Cautionary example:* describing VAPO from memory as "value clipping + token-level advantage normalization" was wrong on both counts; the paper's real innovations are Length-adaptive GAE and Decoupled-GAE (arXiv:2504.05118). This applies *doubly* when you are adding technical detail to explain a method more deeply — that is exactly when you are most tempted to elaborate from memory.
- **Numbers:** Recompute any KV-cache/latency/throughput/FLOP claim you touch (see `essay-writing` Phase 1.5 for the verification-script pattern).

## The editorial pass

After the review is accepted, apply fixes with targeted `patch` calls (not full rewrites — these files are large, 40-70KB). Typical moves:

- Break wall paragraphs; give the sharpest counterexample its own paragraph with real technical detail (verified).
- Add a master comparison table near the top for comparison-titled surveys — every method on common dimensions (complexity, memory, quality impact, retrofittable?, train/infer asymmetry, production status). Follow it with 2-3 observations the table surfaces.
- Add a missing subsection for a vault coverage gap; wire it into the overview diagram and references.
- Fix YAML, placeholders, and Mermaid orientation.
- Update the byline to credit the editorial pass: `*Liping Zhang, assisted by Hermes Agent ([model]); ... ; editorial pass by Hermes Agent ([model]) | Date*`.
- Bump `date-updated` in frontmatter.

## Republish (mandatory)

Every survey has a `published:` Gist URL. After any edit, republish:

```bash
gh gist edit <gist_id> "<full path to the .md file>"
```

This replaces the Gist content cleanly (no `-f` flag, no stdin — those hit TERM errors). Verify with `gh gist view <id> --raw | grep <something new>`. The Gist ID is the last path segment of the `published:` URL.

## Pitfalls

- **Don't rewrite the whole file.** Use `patch` for surgical edits. A 60KB file rewritten via `write_file` risks silent corruption; accumulated string replacements in `execute_code` are non-atomic and can drop content.
- **Don't elaborate technical detail from memory.** Verify the paper first (see above). This is the single most common way to introduce a confident error during an editorial pass.
- **Don't leave redundant Mermaid headers.** When converting a diagram, watch for a subgraph title AND an internal node carrying the same label — remove the internal one.
- **The Obsidian vault path** is `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/notes/gen-notes/surveys/` (iCloud-synced), NOT `~/notes/gen-notes/`.
- **Cross-check the user's stated standards:** Mermaid over Excalidraw (self-contained in markdown), full reference list, byline format, republish on every edit.
