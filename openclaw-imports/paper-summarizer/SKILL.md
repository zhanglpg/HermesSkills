---
name: paper-summarizer
description: "Summarizes academic papers, articles, blog posts, and essays, then saves structured notes to the Obsidian vault (gen-notes/ folder). Use when an arXiv link, paper URL, blog post URL, or paper title is shared and needs summarizing. Also handles processing the reading backlog from the Obsidian AI.md note."
---

# Paper Summarizer

Fetch, read, and summarize a paper or article, then save a structured note to Obsidian.

## Workflow

1. **Fetch the content**
   - arXiv link: try fetching the HTML page first; if content is thin, fetch the `/pdf` URL using the `pdf` tool
   - Blog post / web article: use `web_fetch`
   - PDF URL: use the `pdf` tool directly
   - Title only: search for it first with `web_search`, then fetch the best result

2. **Generate the note** using the template in `references/note-template.md`
   - Be substantive — the reader reads deeply, so the summary should too
   - Optional: Only when there is clear correlation, add a "Personal take" section: apply the perspective of engineering culture, complexity, long-termism, AI systems focus, resource constraints, and skepticism of hype to anticipate what would resonate or what he'd push back on
   - Keep it honest — note limitations and open questions, don't just celebrate the paper

3. **Save to Obsidian**
   - Default path: `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/notes/gen-notes/digests/<Title>.md`
   - Sanitize the title for use as a filename (remove special chars, keep it readable)
   - If the note already exists, ask before overwriting
   - **IMPORTANT:** Frontmatter MUST use `---` YAML delimiters at the TOP of the file, not Obsidian inline properties at the bottom. `concepts:` and `names:` must be YAML lists (`- item`), not `[[wikilink]]` format. The wiki-manager ingest pipeline depends on this exact format.

## ⚠️ Frontmatter Format (CRITICAL for wiki-manager ingest)

The note **MUST** have proper YAML frontmatter at the **TOP** of the file with `---` delimiters. The metadata block in the template (`date:`, `status::`, `tags:`, `concepts:`, `names:`) must be converted to YAML frontmatter format:

```yaml
---
date: 2026-04-08
status: 📥
tags:
  - AI
  - LLM
concepts:
  - Concept One
  - Concept Two
names:
  - Name One
  - Name Two
categories:
  - AI
  - LLM
source: https://arxiv.org/abs/XXXX.XXXXX
---
```

**Rules:**
- Do NOT use Obsidian inline format (`status::`, `categories::`) — use plain YAML
- Do NOT use `[[wikilinks]]` in frontmatter values — use plain strings (wikilinks go in the body)
- `concepts` and `names` MUST be YAML lists (one item per line with `- `), not comma-separated or wikilink format
- Do NOT duplicate metadata at the bottom of the file — frontmatter only

4. **Confirm** — tell the user the note was saved and give a one-line headline of the paper's key contribution

## Obsidian linking & tags

- **Wikilinks:** Always add `[[Note Name]]` links when referencing concepts, papers, or notes that exist in the vault. Use exact filenames where possible (check `notes/` folder). When uncertain, use the title as-is — Obsidian will resolve it.
- **Connections section:** Every note should have a "Connections" section that explicitly links to related vault notes
- **Tags:** Use both inline `#tags` in frontmatter AND `[[Category]]` wikilinks for categories
- **Cross-link into existing notes:** If a paper directly extends or contradicts an existing vault note, mention it in the Connections section

## Notes on content quality

- TL;DR should be 1-2 sentences max — if you can't summarize it that crisply, you haven't understood it yet
- "What's novel" should be specific, not generic ("introduces a new method" is not useful)
- Tags should reflect the vault's existing categories: `AI`, `LLM`, `systems`, `hardware`, `inference`, `scaling`, `training`, `data`, `management`, `leadership`, `engineering`, `physics`, `history`, `philosophy`, etc.

## Reading backlog mode

When asked to work through the reading backlog:
1. Read `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/notes/AI.md`
2. Find unchecked items `- [ ]` that have a URL or title
3. Process them one by one (or a batch if specified), saving each note to `gen-notes/`
4. Do NOT mark items as done in AI.md — let the user decide when he's satisfied with a note
