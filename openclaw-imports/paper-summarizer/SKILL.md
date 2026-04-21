---
name: paper-summarizer
description: "Summarizes academic papers, articles, blog posts, and essays, then saves structured notes to the Obsidian vault (gen-notes/ folder). Use when an arXiv link, paper URL, blog post URL, or paper title is shared and needs summarizing. Also handles processing the reading backlog from the Obsidian AI.md note."
---

# Paper Summarizer

Fetch, read, and summarize a paper or article, then save a structured note to Obsidian.

## Workflow

1. **Fetch the content**
   - arXiv link: navigate to the HTML version (`arxiv.org/html/<id>`) via browser, then use `browser_console` with JS to bulk-extract all section text at once (see technique below). This is far more efficient than scrolling/snapshotting. If HTML is unavailable (common for older papers, e.g. pre-2021), use the **pdftotext fallback**:
     ```bash
     cd /tmp && curl -sL -o paper.pdf "https://arxiv.org/pdf/ID"
     pdftotext -layout paper.pdf -  # outputs to stdout
     ```
     Papers are typically 100K–150K chars; read in ~15K-char chunks via `execute_code` with `subprocess.run(['pdftotext', '-layout', 'paper.pdf', '-'], capture_output=True, text=True)` then slice `text[0:15000]`, `text[15000:30000]`, etc. Five to six chunks covers most papers. This reliably extracts full content including equations, tables, and algorithm boxes.
   - Blog post / web article: use `web_fetch`
   - PDF URL: use the `pdf` tool directly
   - GitHub repo (library/framework): navigate to the repo's README and any linked docs/papers. Some important work (e.g., DeepEP) is released as open-source code with a detailed README rather than a traditional paper — treat the README + any technical blog post as the primary source.
   - Title only: search for it first with `web_search`, then fetch the best result
   - **Ambiguous/misremembered titles:** If the user gives an acronym + descriptor that doesn't match (e.g., "LACE latent attention" when the paper is actually "LACE: Lattice Attention"), search arXiv by title acronym only (`ti:LACE`) with `sortBy=submittedDate&sortOrder=descending` — this reliably surfaces recent papers by acronym. The user's descriptor word (e.g., "latent") may be a misremembering of a similar-sounding word (e.g., "lattice"). Don't get stuck searching for the exact phrase the user provided.
   - **Blog post + HN/community discussion:** When the user provides both an article and its discussion thread, treat them as a combined source. Fetch the article normally (delegate_task or web_fetch). For HN discussions, use the Algolia API via `mcp_terminal` heredoc — do NOT delegate HN scraping to subagents (they hallucinate wrong threads). The digest should synthesize both the author argument AND the community debate (camps, counterarguments, representative quotes). See HN extraction technique below.

   **HN discussion extraction (via terminal heredoc):**
   Use `mcp_terminal` with `python3 << PYEOF` to fetch `https://hn.algolia.com/api/v1/items/<ID>`. Parse with `urllib.request` + `json.loads(resp.read().decode())`. Sort top-level comments by total descendant count (recursive `count_all` helper) to surface the hottest threads. Print top 15 threads with 3 replies each. **Why heredoc not execute_code:** Algolia returns large JSON (>50KB for 300+ comment threads); `execute_code` terminal() helper truncates stdout causing JSON parse failures mid-JSON.

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

5. **After digest — wiki integration (MANDATORY):**
   - **ALWAYS run full wiki ingestion** after every digest. This is not optional. The user expects concept and name pages to be created/updated every time.
   - **Workflow:** Run `wiki_manager.py ingest <path> --extract-only` to get concepts/names, then create/update concept and name pages (see wiki-manager skill), then run `python3 scripts/wiki_manager.py index` to rebuild the index. (Note: command is `index`, not `rebuild-index`.)
   - **Agent-primary method (preferred):** Parse frontmatter yourself for concepts/names, check which pages exist, create new / update existing pages via `delegate_task` or directly, then rebuild index. This avoids the script's Gemini CLI timeout issues.
   - Skip wiki ingestion ONLY if the user explicitly says to skip it.

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

## Parallel digest mode (via delegate_task)

When digesting 2-3 papers at once (e.g., as preparation for expanding an essay), use `delegate_task` with batch mode. Each subagent gets:
- The paper's source URL and any alternate sources (USENIX, ACM if arXiv fails)
- The full note template and frontmatter format requirements
- The exact output file path in the vault
- Connections to link to (other papers in the same reading group)
- A reminder about Mermaid diagrams and max 3 concepts

After all subagents complete:
1. Verify both digests exist and have proper frontmatter
2. Update paper-queue status to `digested` for each paper
3. **Run FULL wiki ingestion for each digest** — create/update concept and name pages. Can parallelize: batch the ingestions into 2 `delegate_task` subagents (e.g., 2 digests per subagent). Each subagent checks for existing pages, creates new ones, updates existing ones, then runs `wiki_manager.py index`.
4. Proceed with any downstream task (essay expansion, etc.)

**Pitfall from experience:** Index rebuild alone is NOT sufficient — user expects full concept/name page creation. Forgetting this step caused a correction. Also, when running wiki ingestion in parallel subagents, they may concurrently modify the same concept page (e.g., both digests reference "KV Cache"). The subagents handle this via read-then-patch, but watch for duplicate YAML keys in frontmatter after concurrent edits.

This pattern was validated for 2 parallel digests (Orca + PagedAttention) completing in ~160s total vs ~300s sequential.

## Digest-to-Expand-Essay Workflow

When an existing essay references papers shallowly (e.g., "Orca introduced continuous batching"), digest those foundational papers, then weave the depth back into the essay. This is a common pattern for comparison essays and tutorials.

### Steps:
1. **Identify gaps**: Read the essay, find papers mentioned but not substantively covered
2. **Batch-digest**: Digest 2-3 papers in parallel via `delegate_task` (each subagent fetches + writes to vault)
3. **Mark as digested** in paper queue: `paper_queue.py status <id> digested`
4. **Run wiki ingestion** for each new digest (MANDATORY — see step 5 in main workflow)
5. **Read digests + essay**: Load both to understand what depth is available
6. **Expand the essay**: Patch the shallow section with substantive content from digests — concrete mechanisms, equations, diagrams, numbers. Don't just add a paragraph; restructure the section with subsections if the added depth warrants it.
7. **Update essay frontmatter**: Add new digest wikilinks to the `sources:` list

### Key lesson from experience:
When expanding Gen 0 of the Disaggregation Thesis essay with Orca + vLLM digests, the expansion went from 3 bullet points to 4 subsections (2.1 Orca, 2.2 PagedAttention, 2.3 Complementary Foundation, 2.4 MoE Utilization Problem). The subsection structure made it possible to thread the "parameter-free attention" insight across the entire essay — connecting it to why selective batching works, why P/D disaggregation is clean, and why attention-FFN disaggregation is possible. The essay grew from 395 to 538 lines but became structurally stronger because each generation's section could reference the Gen 0 depth.

## Publishing workflow

When essays or digests are published to GitHub Gist:

1. **After publishing**: Add `published: <gist_url>` to YAML frontmatter
2. **On any update**: If a file has a `published:` field, republish it: `gh gist edit <gist_id> <file_path>`
3. **Mermaid for vertical screens**: Prefer `flowchart TD` over `flowchart LR` for Gist/mobile readability. Keep sequence diagrams to ≤3 participants. Shorten node labels.

## Essay fact-checking workflow

Before finalizing a tutorial/comparison essay, run a parallel review via `delegate_task` with 3 subagents:
1. **Architecture fact-check**: Verify model dimensions against HuggingFace config (`https://huggingface.co/api/models/<org>/<model>` returns config JSON) and source papers
2. **Systems claims check**: Verify throughput/latency numbers against source paper digests in the vault
3. **Writing review**: Check narrative flow, logical gaps, diagram correctness, detail consistency, redundancy, conclusion quality

Key finding: HuggingFace API (`/api/models/`) returns the full `config.json` without auth — more reliable than trying to `curl` the raw file. Use `python3 -c "import urllib.request, json; ..."` to fetch and parse.

**Pitfall — nested configs for multimodal models:** Models like `Qwen3_5MoeForConditionalGeneration` store architecture details in `config["text_config"]` and `config["vision_config"]` sub-dicts, not at the top level. Always check for nested config structures.

**Pitfall — don't assume layer counts from model names or secondary sources.** Always verify `first_k_dense_replace` (or equivalent) in the actual HF config. In this session, "first 3 layers dense" was assumed for DeepSeek-V3 but the actual config showed `first_k_dense_replace=1` (only layer 0 is dense). This cascaded to wrong MoE layer counts (58 vs 60) and wrong all-to-all operation counts (116 vs 120) throughout an essay.

## CRITICAL Pitfalls: File Editing in Obsidian Vault

### execute_code read_file caching can destroy files
When execute_code calls read_file() on a file already read in the conversation, it may return a cached message like "File unchanged since last read..." instead of actual content. If you then call write_file() with the parsed result, you overwrite the real file with the cache message. This destroyed the Disaggregation Thesis essay in session 2025-04-11 — recovered only because it was published to a GitHub Gist.

**Prevention:** Never use execute_code's write_file on vault files that were read earlier in the conversation. Use mcp_terminal with Python heredoc for read-modify-write operations on already-read files.

### mcp_patch tool fails on wikilinks
The patch tool's find-and-replace breaks with "too many values to unpack" when old_string or new_string contains double-bracket wikilink syntax. This affects ALL Obsidian vault files. The skill_manage patch action has the same bug.

**Workaround:** Use mcp_terminal with python3 heredoc for any file edits involving wikilink-containing text. Read the file, do string replacement in Python, write it back.

### Published essays: always republish after editing
If the essay frontmatter has a published: URL, run `gh gist edit <gist_id> <file_path>` after ANY edit. Check for this in frontmatter before finishing.

### HN discussion extraction belongs in terminal, not delegate_task
Subagents tasked with fetching HN threads via Algolia API hallucinated wrong thread content (returned a completely different HN discussion). Always fetch HN threads yourself using mcp_terminal with python3 heredoc and the Algolia items API. Sort comments by descendant count to surface hottest threads.

## Reading backlog mode

When asked to work through the reading backlog:
1. Read `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/notes/AI.md`
2. Find unchecked items `- [ ]` that have a URL or title
3. Process them one by one (or a batch if specified), saving each note to `gen-notes/`
4. Do NOT mark items as done in AI.md — let the user decide when he's satisfied with a note
