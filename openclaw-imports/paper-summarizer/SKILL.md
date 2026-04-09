---
name: paper-summarizer
description: "Summarizes academic papers, articles, blog posts, and essays, then saves structured notes to the Obsidian vault (gen-notes/ folder). Use when an arXiv link, paper URL, blog post URL, or paper title is shared and needs summarizing. Also handles processing the reading backlog from the Obsidian AI.md note."
---

# Paper Summarizer

Fetch, read, and summarize a paper or article, then save a structured note to Obsidian.

## Workflow

1. **Fetch the content**
   - arXiv link: navigate to the HTML version (`arxiv.org/html/<id>`) via browser, then use `browser_console` with JS to bulk-extract all section text at once (see technique below). This is far more efficient than scrolling/snapshotting. If HTML is unavailable, fetch the `/pdf` URL using the `pdf` tool.
   - Blog post / web article: use `web_fetch`
   - PDF URL: use the `pdf` tool directly
   - GitHub repo (library/framework): navigate to the repo's README and any linked docs/papers. Some important work (e.g., DeepEP) is released as open-source code with a detailed README rather than a traditional paper — treat the README + any technical blog post as the primary source.
   - Title only: search for it first with `web_search`, then fetch the best result

   **arXiv HTML extraction technique (preferred):**
   ```javascript
   // Run via browser_console after navigating to arxiv.org/html/<id>
   const sections = {};
   document.querySelectorAll('h2, h3, h6').forEach(h => {
     let text = '', el = h.nextElementSibling, count = 0;
     while (el && !['H2','H3','H6'].includes(el.tagName) && count < 40) {
       text += el.textContent + '\n'; el = el.nextElementSibling; count++;
     }
     sections[h.textContent.trim().substring(0, 80)] = text.substring(0, 3000);
   });
   JSON.stringify({ keys: Object.keys(sections), abstract: sections["Abstract"], ...});
   ```
   First call with just `keys` to see all sections, then a second call selecting the sections you need (intro, method, results, discussion, conclusion). Two JS calls typically captures an entire paper.

2. **Generate the note** using the template in `references/note-template.md`
   - Be substantive — the reader reads deeply, so the summary should too
   - Optional: Only when there is clear correlation, add a "Personal take" section: apply the perspective of engineering culture, complexity, long-termism, AI systems focus, resource constraints, and skepticism of hype to anticipate what would resonate or what he'd push back on
   - Keep it honest — note limitations and open questions, don't just celebrate the paper

3. **Save to Obsidian**
   - Default path: `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/notes/gen-notes/digests/<Title>.md`
   - Sanitize the title for use as a filename (remove special chars, keep it readable)
   - If the note already exists, ask before overwriting

4. **Confirm** — tell the user the note was saved and give a one-line headline of the paper's key contribution

5. **After digest — wiki integration:**
   - **Minimum:** Run `python3 scripts/wiki_manager.py index` to rebuild the index so the new digest appears in the wiki index and domain sections.
   - **Full ingest:** Run `wiki_manager.py ingest <path> --extract-only` then create/update concept and name pages (see wiki-manager skill). Only needed if you want concept/name pages updated — skip for quick digests.
   - The index rebuild is fast (<5s) and always safe. Full ingest involves LLM calls and may timeout.

## ⚠️ Concept Limits

**Max 3 concepts in frontmatter.** Concepts should be "worthy of a Wikipedia page, a survey paper, or mentioned in a book" — not paper-specific jargon or implementation details. If the paper introduces 10 terms, pick the 3 most fundamental. Same rule applies to `names:` — only include people who are notable beyond this one paper.

## ⚠️ Frontmatter Format (CRITICAL for wiki-manager ingest)

The digest MUST have proper YAML frontmatter **at the top** of the file with `---` delimiters. The wiki-manager parses this to find concepts and names — without it, ingest falls back to slow LLM extraction that often times out.

```yaml
---
date: YYYY-MM-DD
domain: ai
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
source: https://...
---
```

**Domain field:** Required. One of: `ai`, `systems`, `history`, `science`, `wisdom`. See wiki-manager schema for assignment rules. When in doubt: "which section of a university library would this belong in?"

**Pitfalls:**
- Do NOT put metadata at the bottom of the file (Obsidian inline format like `status:: 📥`) — wiki-manager won't find it
- Do NOT use `[[wikilinks]]` in frontmatter values — use plain strings in YAML lists
- Do NOT use `#tags` in frontmatter — use plain strings in YAML lists
- Concepts and names MUST be YAML lists (one per line with `- `), not comma-separated

## Obsidian linking & tags

- **Wikilinks:** Always add `[[Note Name]]` links when referencing concepts, papers, or notes that exist in the vault. Use exact filenames where possible (check `notes/` folder). When uncertain, use the title as-is — Obsidian will resolve it.
- **Connections section:** Every note should have a "Connections" section that explicitly links to related vault notes
- **Tags:** Use both inline `#tags` in frontmatter AND `[[Category]]` wikilinks for categories
- **Cross-link into existing notes:** If a paper directly extends or contradicts an existing vault note, mention it in the Connections section

## Mermaid Diagrams

Include 1-2 Mermaid diagrams in each digest to visually illustrate the paper's core architecture, data flow, or key mechanism. Place them after the "Method / How It Works" section. Use `graph TD`, `flowchart LR`, or `sequenceDiagram` as appropriate. Keep diagrams readable — max ~15 nodes. Obsidian renders Mermaid natively.

**Mermaid pitfalls:**
- **No trailing spaces after subgraph declarations.** `subgraph Foo["Label"]    ` (with trailing spaces) causes a parse error: `Expecting 'SEMI', 'NEWLINE', 'EOF', got 'SPACE'`. Always ensure subgraph lines have no trailing whitespace.
- **No blank lines inside subgraph blocks** — some Mermaid renderers treat them as block terminators.

## Key Equations

For papers with mathematical core, include 1-2 key equations (LaTeX, Obsidian-compatible `$$...$$` blocks) that capture the essential formalism. Place after the Method section, near the diagrams. Skip for purely empirical/systems papers where there's no central equation.

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
