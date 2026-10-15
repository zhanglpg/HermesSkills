---
name: curated-digest
description: Use when distilling a large source into a personal digest.
---

# Curated Digest from a Large Source

## When to Use
- User shares or points at a large structured source (open-source book repo, evidence-graded guide with hundreds of numbered entries) and asks for the parts relevant to them, a personal selection, or a standalone document.
- Do NOT use for academic papers/arxiv (use `paper-summarizer`) or wiki ingestion (use `wiki-manager`).

Turn a big structured source (e.g. a GitHub repo book with 500–700 numbered entries, a long evidence-graded guide) into a personal selection document for THIS user: regrouped by their life situations, pruned to incremental value, delivered as a vault note plus a searchable single-file HTML. Not for academic papers — use `paper-summarizer`.

## Procedure

1. **Clone shallow, never read wholesale.** `git clone --depth 1 <repo> /tmp/<name>`; list the content dir once (search_files target='files' scoped to the clone) to learn the chapter/entry layout. A 7 MB book must never enter context chapter-by-chapter.
2. **Parse to a JSON index first.** Regex-split entries into records: `{ch, num, title, cost_tags, evidence_grade, plain_summary}` (fields follow the source's own skeleton — most evidence-graded books have cost/benefit/evidence per entry). Dump to `/tmp/<name>_entries.json`; print only aggregate counts (entries, chapters, evidence distribution) to verify the parse.
3. **Triage from compact title lists.** Print `num [evidence] title | cost_tags` per chapter in batches (stdout truncates ~50KB — page the spill file or print chapter-by-chapter). Titles are conclusions; they are enough to judge relevance. Select in three passes: (a) chapters relevant to the user profile, (b) entries within them, (c) prune to **incremental value only** — counter-intuitive claims, concrete numeric thresholds, identity-specific rules (the user's profession, hobbies, family stage, assets). First passes over-include (~40% of a book); the third pass is what makes it a digest.
4. **Regroup by the user's situations, not the source's chapters.** 10–15 groups max. Each group gets: a one-paragraph *why this group matters to you* (tie to known facts about the user), a ★must-read line (the 5–10 entries to act on now), then the full table `| # | advice | key number | evidence | cost | benefit |`.
5. **State what you excluded.** A short list of dropped categories (life stages/topics that don't apply) with a pointer back to the source, so the user knows the digest's boundaries.
6. **Add a "my added judgments" section**: where the source conflicts with the user's current state (e.g. advice contradicting holdings they already have), where one chapter is the best value in the book, and which group needs memorization vs understanding. Flag "consult a professional, don't copy verbatim" on legal/tax items that touch the user's actual position.
7. **Dual output.** (a) Markdown to the vault digests folder — paper digests live under `gen-notes/digests/` (paper-summarizer's convention); other digests go to `notes/digests/`. (b) A searchable single-file HTML companion (cards + client-side filter + dark-mode media query; skeleton in `templates/searchable-digest.html`) saved to `~/Desktop/` and attached with `MEDIA:`.
8. **Verify before delivering:** parsed-entry count == table-row count == card count; every table row has the same column count; open the HTML in the browser, assert card/section counts and run one search query.

## Pitfalls

- Write to the vault by direct path (`test -d`, `mkdir -p`, `cp`) — never recursively list or search an iCloud-synced vault to locate folders; listing materializes evicted files and hangs for minutes.
- Keep source entry IDs (`ch.num`) in every row so each line is checkable against the original; quote the source's evidence-grade distribution in the header so the digest inherits the source's credibility framing.
- Do not let the digest become a copy: if a group is >40 entries it is a chapter dump, not a selection — split or prune it.
- Chinese sources: preserve original wording in the plain-summary field (it is the author's own plain-language line); only truncate, never paraphrase numbers.
- The HTML companion must be zero-dependency and offline-capable; verify the JS filter actually hides non-matching cards before attaching.

## Related

- `paper-summarizer` — academic papers/arxiv into the same vault digests folder.
- `obsidian` — vault paths and write conventions.
