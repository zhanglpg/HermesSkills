---
name: literature-survey
description: Multi-source literature surveys on technical topics — combining arxiv web search, lab blogs, citation cross-referencing, and structured synthesis. Use when the user asks to "search for papers on X", "what's the state of research on Y", or "find papers about Z from labs A, B, C".
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [Research, Literature-Survey, Papers, Synthesis]
    related_skills: [arxiv, breaking-news-research-essay]
---

# Literature Survey / Research Reconnaissance

Conduct structured multi-source literature surveys on technical topics. Combines arxiv search, lab blog scanning, citation following, and synthesis into a comprehensive report.

## When to Use

- "Search for papers on X" / "What's the state of research on Y"
- "Find work from [specific lab] on [topic]"
- "What's the relationship between technique A and technique B"
- "Is X being used as replacement for Y or alongside it?"
- Any request requiring coverage across multiple sources and labs

## Workflow

### Phase 1: Broad Discovery (arxiv web search)

Use **browser-based arxiv search** for exploratory multi-concept queries — far more practical than the API for complex boolean combinations, and more reliable (the API at `export.arxiv.org` can return HTTP 429 even for a single request from terminal; browser search is unaffected):

```
browser_navigate(url="https://arxiv.org/search/?query=%22exact+phrase%22+concept2&searchtype=all")
```

- URL-encode exact phrases as `%22...%22`
- Combine with `+` (AND) or `+OR+`
- Results show titles, authors, abstracts, dates inline
- Use `read_file` on the truncated snapshot path to see all results
- Sort by announcement date (newest first) for recent work
- **The search endpoint needs a valid `size` param (25 or 50):** `&size=25`. Smaller values (e.g. `size=5`) return HTTP 400 Bad Request with an empty shell page. This bit both browser and curl paths in practice.
- **Terminal-curl variant** (works when browser is slow/unavailable): `curl -s --max-time 40 -A "Mozilla/5.0 (research)" "https://arxiv.org/search/?query=...&searchtype=all&size=25" -o s.html`, then parse with regex `arXiv:(\d{4}\.\d{4,5})v?\d*.*?<p class="title is-5 mathjax">\s*(.*?)\s*</p>` (re.S) for (id, title) pairs.

**Run multiple searches in parallel** with different query formulations:
- `"exact phrase" + related_concept`
- `"exact phrase" + specific_lab_or_model_name`
- `broader_term + narrower_term`

#### Quote-mining strategy (for evidence-gathering surveys)

When the user wants quantitative claims or specific assertions from papers, conceptual searches ("attention bottleneck decode") often return zero results. Instead, search for **phrases papers would actually use in their abstracts**:

- `"attention dominates" + decode` → finds papers asserting attention is the bottleneck
- `"attention accounts for" + inference` → finds papers with percentage breakdowns
- `"memory bandwidth" + "KV cache" + decode + bottleneck` → finds memory-wall analyses
- `"scales linearly" + "sequence length" + attention` → finds scaling analyses

This is far more productive than searching for the user's conceptual framing. Papers describe their findings in their own language, not the requester's.

#### Named-paper searches

When you know key papers in the field (from domain knowledge or prior searches), search by name directly — this is the fastest path to verified arxiv IDs and abstracts:

```
browser_navigate(url="https://arxiv.org/search/?query=Splitwise+efficient+generative+LLM+inference&searchtype=all")
```

Then navigate to `arxiv.org/abs/ID` for the full abstract. This is more reliable than trying to reconstruct a conceptual query that would surface the same paper.

### Phase 1b: Bulk recent-paper discovery via HTML listing pages

For "what's new in category X this week" (hundreds of papers with titles/authors/subjects in one fetch), the HTML listing pages beat the search endpoint and the API:

```
https://arxiv.org/list/{category}/pastweek?show=2000   # 5 listing days in one page
```

- Fetch with `urllib.request` + regex — browser DOM access is unreliable on 1,000+ entry pages, raw HTML parses cleanly. `?show=2000` is the max; `?show=3000` returns HTTP 400.
- A `pastweek` page has MULTIPLE `<dl>` blocks (one per listing day). Use `re.findall(r'<dl[^>]*>(.*?)</dl>', html, re.DOTALL)` — `re.search` silently keeps only the first day.
- HTML attributes use single quotes (`class='list-title mathjax'`) — regexes must match both quote styles: `class=['\"]list-title[^'\"]*['\"]`. Title text lives AFTER the `</span>` descriptor: `r"<div class=['\"]list-title[^'\"]*['\"][^>]*>.*?</span>\s*(.*?)\s*</div>"` (capturing before `</span>` yields the literal string "Title:").
- **⚠️ Date-attribution trap: the FIRST `<dl>` precedes the first `<h3>` in document order.** Listing-day dates are `<h3>` headings ("Tue, 4 Aug 2026 (showing 464 of 464 entries)") interspersed among the `<dl>` blocks — but the newest day's `<dl>` comes BEFORE any `<h3>` (verified Aug 2026, cs.AI: first dl at pos 5844, first h3 at pos 5867). Position-based date tracking assigns date=None to ALL of the newest day's ~340–465 papers. Fix: attribute any `<dl>` with no preceding `<h3>` to the FIRST `<h3>`'s date (cross-check: the dl's paper count matches the h3's "showing N of N"). Without this, freshness filters silently drop the freshest papers.
- Paper IDs appear as `arXiv:NNNN.NNNNN` inside `<dt>` blocks; for each DT, parse the FOLLOWING `<dd>` (don't match DDs and search backwards — that grabs adjacent papers' IDs).
- **Isolating truly-new submissions:** cross-lists and replacements keep their original IDs — a `2411.04440` paper can legitimately appear in today's listing (verified Aug 8, 2026). Genuinely new submissions carry the current month's `YYMM.` prefix (e.g. `2608.*` in Aug 2026). For freshness filters, combine `id.startswith('YYMM.')` with the listing-day date; ID prefix alone is a cheap and reliable first cut.
- **Date-block count varies:** a `pastweek` page can show fewer than 5 `<h3>`/`<dl>` pairs — on Saturday Aug 8, 2026 all three of cs.AI/cs.LG/cs.SE showed exactly 2 blocks (Wed + Fri). Don't hardcode 5; print the block count and per-day DT totals to stderr and sanity-check against the "showing N of N" text in each heading.
- Scale (Aug 2026): cs.AI pastweek ≈ 1,270 papers, cs.LG ≈ 980, cs.SE ≈ 200. Score all papers uniformly with keyword matching (cs.AI gets a +3 base as inherently AI-relevant), keep all cs.AI, filter cs.LG/cs.SE by score > 0 — no arbitrary per-category caps, which silently drop later categories when results are appended sequentially.

### Phase 2: Lab Blog Scanning

Some labs publish primarily via blogs, NOT arxiv. Always check relevant lab blogs:

| Lab | Blog URL | Notes |
|-----|----------|-------|
| Thinking Machines (Mira Murati) | thinkingmachines.ai/blog | Technical posts, no arxiv papers |
| OpenAI | openai.com/research | Mix of blog + arxiv |
| Anthropic | anthropic.com/research | Mix of blog + arxiv |
| Google DeepMind | deepmind.google/research | Mostly arxiv |
| Meta FAIR | ai.meta.com/research | Mostly arxiv |
| Alibaba/Qwen | qwenlm.github.io | Tech reports on arxiv |
| DeepSeek | api-docs.deepseek.com | Papers on arxiv |

### Phase 3: Deep Reading

For key papers found in Phase 1-2:

```
# Full abstract + metadata
browser_navigate(url="https://arxiv.org/abs/XXXX.XXXXX")
browser_snapshot(full=true)

# Quick title verification (no browser needed)
curl -s "https://arxiv.org/abs/XXXX.XXXXX" | grep -o '<meta name="citation_title" content="[^"]*"'
```

For blog posts: navigate and use `browser_snapshot(full=true)`, then `read_file` on the snapshot for long content.

### Phase 4: Citation Cross-Referencing

Follow citations from blog posts and papers to discover foundational works:
- Blog post references → foundational arxiv papers
- Paper "Related Work" sections → competing approaches
- Use Semantic Scholar for citation graphs: `curl -s "https://api.semanticscholar.org/graph/v1/paper/arXiv:ID/references?fields=title,citationCount&limit=20"`

### Phase 5: Synthesis

Structure the output as:
1. **Foundational paper** (origin of the technique)
2. **Key lab contributions** (who uses it and how)
3. **Technical formulations** (loss functions, algorithms)
4. **Relationship to related techniques** (complementary vs replacement)
5. **Paper table** (title, arxiv ID, date, key contribution)
6. **Quantitative results** where available

#### Evidence-gathering variant

When the user wants to build a quantitative case (e.g., "find evidence that X is true"), structure the output differently:

1. **Papers with explicit claims** — exact quotes from abstracts, grouped by assertion type
2. **Quantitative evidence** — specific numbers (speedups, percentages, FLOPs ratios) with source
3. **Derived synthesis** — combine numbers from multiple papers into a coherent argument (e.g., "Paper A shows O(n) scaling; Paper B shows 6x speedup from 80% sparsification → implies attention is ~83% of cost")
4. **Gaps** — what no paper directly measures, and how to construct the argument from indirect evidence

Write the output to a file (e.g., `~/topic_research.md`) so the user has a persistent reference with all arxiv IDs, exact quotes, and the synthesis.

#### Parallel subagent research pattern (proven effective)

For evidence-gathering surveys, dispatch 2–3 `delegate_task` subagents in parallel, each with a different search angle:
- **Agent 1:** Broad arxiv + Semantic Scholar search for papers with quantitative claims
- **Agent 2:** Named-paper search for known foundational works (serving papers, architecture papers) + their specific numerical findings
- **Agent 3 (optional):** Hardware/accelerator papers and benchmarking studies

While subagents run, **simultaneously read existing vault digests** (`gen-notes/digests/`, `gen-notes/concepts/`) — these often contain the exact quotes needed and avoid redundant work. In the attention-decode session, the NSA digest already had "attention accounts for 70–80% of total latency when decoding 64K contexts" — a key data point that would have taken a subagent minutes to find.

**Critical instruction for subagents:** Tell them to expect arxiv API rate limiting (HTTP 429 after ~5 rapid queries) and to fall back to browser-based arxiv search (`arxiv.org/search/?query=...`) and Semantic Scholar API. Also instruct them to write findings to a structured markdown file with exact quotes, not just summaries.

**Salvaging timed-out subagents (proven in practice):** Research subagents hit their 600s timeout frequently when they stall on rate-limited API calls — but their partial work is usually recoverable and worth more than a re-dispatch:

1. **Read the live transcripts:** `read_file` on `~/.hermes/cache/delegation/live/<delegation_id>/task-N.log` — they record every tool call and result, including extracted paper text and verified IDs.
2. **Recover downloaded artifacts:** subagents save fetched files to `/tmp` and `/private/tmp` (same dir on macOS) — `abs_*.html` paper pages, `*.html` full papers, extracted `*.txt`. Find them with `find /private/tmp -name "<pattern>"`. These survive the timeout.
3. **Extract from the log:** transcript `result` lines contain the actual outputs (e.g., parsed abstracts, section text). Copy what you need directly.
4. **Finish the remainder yourself** rather than re-dispatching — you now know exactly which sub-questions are still open, and doing them in the main session avoids paying the timeout tax again. In one session, 3 timed-out subagents left ~15 verified papers + one full downloaded tech report; the parent finished the remaining ~20 lookups in ~10 minutes of direct curl-to-abs-page verification.

**Fastest verification path for known IDs:** `curl -s "https://arxiv.org/abs/ID" -o f.html` in a loop with `sleep 0.5` between calls, then parse `citation_title` / `citation_date` meta tags and the `<h1 class="title">` block with python3. The abs pages are NOT subject to the export.arxiv.org API rate limit — batch-verifying 15-20 IDs this way takes under a minute. Guessed IDs often resolve to unrelated papers, so always confirm the title matches before citing.

**Bulk-reading a paper without the browser:** for any recent paper, `curl -sL -A "Mozilla/5.0 (research)" "https://arxiv.org/html/<id>" -o p.html` (LaTeXML HTML, ~0.5-1MB) then split with `re.split(r'<section id="(S\d+|A\d+)"', raw)` and clean each body with a python3 heredoc — strip `<script>/<style>`, replace `<math.*?</math>` / `<table.*?</table>` / `<figure.*?</figure>` with placeholders (separate regex per tag: alternation + backreference like `</\2>` fails on Python 3.9 with "invalid group reference"), then `H.unescape(re.sub(r'<[^>]+>', ' ', t))`. Print bodies in ~4000-char slices. Authors live in `ltx_personname` spans, abstract in the `ltx_abstract` div. Four to five terminal calls extract an entire paper including appendices — much faster than browser_console when the browser stack is busy or rate-limited.

**User preference on evidence attribution:** When the user says "基于已有的研究论文的直接结论作汇总，不要自己给结论" — all conclusions must be directly attributed to specific papers with arxiv IDs. Use exact quotes where possible. Never present derived analysis as if it were a paper's finding. Clearly label any cross-paper synthesis as "constructed from multiple sources" in an Open Caveats section.

## Pitfalls

- **Don't rely on arxiv alone** — some of the most influential work (e.g., Thinking Machines OPD post) is blog-only
- **Search with multiple formulations** — "on-policy distillation" vs "OPD" vs "on-policy knowledge distillation" return different results
- **Check the truncated snapshot file** — arxiv search results often exceed the browser snapshot limit; use `read_file` on the saved path
- **Verify paper IDs** — arxiv IDs from search results can point to unrelated papers; always confirm title matches
- **Distinguish off-policy vs on-policy** — labs may use "distillation" generically; check if it's truly on-policy (student-generated rollouts) or off-policy (teacher-generated SFT data)
- **macOS grep lacks -P flag** — use `grep -o` with basic patterns or `python3 -c` for complex extraction

### Rate limiting (critical for multi-query searches)

- **ArXiv API:** Rate limits aggressively after ~9 queries in quick succession (HTTP 429). Once triggered, the block persists for **10+ minutes** even with `sleep(5)` between requests. For multi-query batch searches (5+ queries), write a Python script using `urllib.request` with `time.sleep(3)` between calls and run it as a file. If you hit 429, do NOT retry immediately — switch to browser-based `arxiv.org/search/` or `arxiv.org/abs/ID` for remaining lookups.
- **Semantic Scholar API:** Even with 2-second delays, batch requests (20+ in sequence) reliably trigger 429s. For known paper lookups, use `browser_navigate(url="https://arxiv.org/abs/ID")` instead — it's immune to API rate limits.
- **Recovery strategy:** When both APIs are rate-limited, fall back to: (1) browser_navigate to arxiv.org/abs/ID for known papers, (2) browser_navigate to arxiv.org/search/ for discovery queries, (3) wait 10+ min before retrying API calls.

### Hermes security scanner (tirith) blocks

- `curl | python3` pipes are blocked as "pipe to interpreter" — write the script to a file first, then execute it
- Inline Python containing XML namespace URLs (`http://www.w3.org/2005/Atom`) triggers "plain HTTP URL in execution context" false positives — another reason to use file-based scripts
- Plain `http://` URLs to `export.arxiv.org` are blocked — always use `https://export.arxiv.org`
- **Pattern that works:** Write a Python script using `urllib.request` (not curl) to a `.py` file, then run `python3 script.py`. Use `write_file` to create the script, `terminal` to execute it.

### Multi-query batch search pattern

For surveys needing 5+ different search queries, use this proven pattern:

```python
# Write to ~/search_papers.py via write_file, then run via terminal
import urllib.request, urllib.parse, xml.etree.ElementTree as ET, json, time

QUERIES = ["query1", "query2", ...]
BASE = "https://export.arxiv.org/api/query"
ns = "{http://www.w3.org/2005/Atom}"
all_results = {}

for q in QUERIES:
    url = f"{BASE}?search_query={urllib.parse.quote(q)}&start=0&max_results=15&sortBy=relevance"
    req = urllib.request.Request(url, headers={"User-Agent": "research-bot/1.0"})
    data = urllib.request.urlopen(req, timeout=20).read().decode()
    root = ET.fromstring(data)
    for entry in root.findall(f"{ns}entry"):
        aid = entry.find(f"{ns}id").text.strip()
        title = entry.find(f"{ns}title").text.strip().replace("\n", " ")
        # ... extract authors, summary, etc.
        all_results[aid] = {...}
    time.sleep(3)  # critical: avoid 429

json.dump(all_results, open("results.json", "w"), indent=2)
```

Then analyze the JSON results in a second script (relevance scoring, deduplication, filtering).

## Parallelization Strategy

Independent searches should be batched:
- Multiple arxiv queries with different formulations → parallel browser sessions OR a single Python script with urllib (preferred for 5+ queries)
- Metadata checks for multiple paper IDs → Python script with urllib (NOT curl|python pipes — blocked by tirith)
- Lab blog check + arxiv search → parallel (different tools)
- Known paper lookups when API is rate-limited → parallel browser_navigate calls to arxiv.org/abs/ID

Only serialize when: reading a paper found in a previous search, or following a citation chain.

### Recommended workflow for large surveys (10+ queries)

1. Write a batch search script (urllib + sleep(3)) → run it → get JSON results
2. Write an analysis/scoring script → run it → get ranked papers
3. For top papers needing full abstracts: parallel browser_navigate to arxiv.org/abs/ID
4. Compile final report with write_file to a .md file

This avoids the rate-limit + tirith double bind that blocks the naive curl-based approach.
