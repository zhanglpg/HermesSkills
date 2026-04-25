---
name: breaking-news-research-essay
description: Research a breaking tech announcement from multiple sources (official, HN, Reddit, Twitter, news) and synthesize into a polished essay. Handles the common failure mode where web search indices haven't caught up with same-day announcements.
tags:
  - research
  - essay
  - breaking-news
  - hacker-news
  - community-analysis
---

# Breaking News Research → Essay Pipeline

## When to Use
- User asks to research a very recent (same-day or within 48 hours) tech announcement
- Need to gather official sources, community reactions, and media coverage
- Output is a synthesized essay or analysis piece

## Key Pitfall: Search Index Lag
Standard web search (subagent or direct) often returns **zero results** for same-day announcements. Search indices (Google, Brave, etc.) can take hours to days to crawl new content. Reddit blocks automated access entirely.

## Step 1: Find the Announcement URLs via HN Algolia

**This is the critical discovery step.** HN Algolia indexes in near-real-time and is the fastest way to find URLs for breaking tech news.

### Method A: Algolia API (PREFERRED — more reliable than browser navigation)

The browser interface can intercept clicks and the date filter is sometimes unreliable. Use `execute_code` to query the API directly:

```python
import urllib.request, json

query = urllib.parse.quote("KEYWORDS")
url = f'https://hn.algolia.com/api/v1/search?query={query}&tags=story&hitsPerPage=10'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read())

for hit in data.get('hits', []):
    print(f"ID: {hit['objectID']} | Points: {hit['points']} | Comments: {hit.get('num_comments', 0)}")
    print(f"  Title: {hit['title']}")
    print(f"  URL: {hit.get('url')}")
    print(f"  HN: https://news.ycombinator.com/item?id={hit['objectID']}")
```

- Filter by points to find the main discussion: `numericFilters=points>100`
- Skip the `dateRange` filter entirely — the Algolia API sometimes returns 0 results for "past week" even when hits exist. Use `execute_code` with no date filter instead.
- Extract the `objectID` for constructing HN discussion URLs (`news.ycombinator.com/item?id=XXXXX`)

### Method B: Browser (fallback)

```
https://hn.algolia.com/?dateRange=all&page=0&prefix=true&query=KEYWORDS&sort=byDate&type=story
```

- Use `"all time"` instead of `"past week"` — the past week filter has known reliability issues
- If clicking result links doesn't navigate, fall back to Method A (API direct access)
- The HN submissions contain links to **official blog posts, docs, media articles, and tweets**

## Step 2: Parallel Content Fetching via Subagents

Once you have URLs from Step 1, delegate 3 parallel subagents:

1. **Official sources** — blog post, engineering blog, API docs (use browser_navigate + browser_console, or terminal with curl)
2. **HN discussion threads** — fetch the actual comment threads (browser_navigate on `news.ycombinator.com/item?id=XXXXX` then extract via browser_console)
3. **Media + social** — Wired/TechCrunch articles, Twitter links found in HN (browser_navigate for paywalled sites)

**Important:** Subagent web search tools may still fail. Give subagents the exact URLs to fetch, don't rely on them to search.

## Step 3: Reading Large Delegate Outputs

Delegate task results are cached at `~/.hermes/cache/tool_responses/delegate_task_*.txt`. These can be 100KB+.

- `read_file` may hit caching issues ("file unchanged since last read")
- `execute_code` may fail on JSON parsing (control characters in content)
- **Best approach:** Use `terminal` with `head -c N` and `tail -c N` to read chunks:
  ```bash
  head -c 15000 /path/to/cached_response.txt
  tail -c 50000 /path/to/cached_response.txt | head -c 25000
  ```

## Step 4: Essay Writing

Two approaches depending on whether a draft exists:

**A. No existing draft (write → critic → improve):**
1. Write a complete draft-1.md using all subagent data
2. Save to `~/.hermes/workspace/essays/<topic>/draft-1.md`
3. Delegate a **critic subagent** to read, review, and produce an improved draft-2.md
4. The critic should receive explicit instructions covering:
   - Which named commenters to add (with their actual quotes)
   - Missing sections to create (limitations, multimodal gap, competitive landscape)
   - New data points to integrate (pricing comparisons, technical details)
   - What to preserve (diagrams, frontmatter, structure, existing voices)
   - Output path: `~/.hermes/workspace/essays/<topic>/draft-2.md`
5. Use toolsets: `["terminal", "file"]` for the critic (it only needs to read/write)
6. Review draft-2 and iterate if needed, otherwise use it as the final essay

**B. Existing draft:** Delegate a critic/enrichment subagent with the current essay text and specific improvements needed. Same toolsets and format as above.

The critic subagent should have explicit instructions about:
- Which named commenters to quote (with their actual quotes)
- New factual details to integrate (pricing, exec quotes, demo details)
- What to preserve (diagrams, frontmatter, structure)

## Step 5: Save to Obsidian and Wiki Ingestion

### Save Essay

```bash
VAULT="${OBSIDIAN_VAULT_PATH:-$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents/notes}"
cp /path/to/final_essay.md "$VAULT/gen-notes/essays/Title.md"
```

Always backup existing file first if overwriting.

### Wiki Ingestion for Essays

**Important:** The wiki-manager's `ingest` command only handles files in `gen-notes/digests/`. Essays saved to `gen-notes/essays/` require manual concept page creation:

1. Identify concepts from the essay's frontmatter `concepts:` field
2. Check which concept pages already exist in `gen-notes/concepts/`
3. For each missing concept: create a new page using the format from existing concept pages (YAML frontmatter with `title`, `type`, `aliases`, `date-created`, `source-digests`/`source-essays`, `tags`, `domain`, followed by markdown body)
4. For each existing concept: update the page with new information from the essay
5. Run `cd ~/.hermes/skills/openclaw-imports/wiki-manager && python3 scripts/wiki_manager.py index` to rebuild

Concept pages should use `type: entity` for organizations/labs (e.g., DeepSeek) and `type: concept` for abstract topics (e.g., Long-Context).

## Essay Quality Checklist
- [ ] YAML frontmatter with tags and `[[concept]]` links
- [ ] Mermaid diagrams (not Excalidraw) for architecture and strategic frameworks
- [ ] Named community voices with specific attributed quotes
- [ ] Competitive landscape with all major players
- [ ] "What this means for builders" actionable section
- [ ] Source links at the bottom
- [ ] Punchy conclusion with specific things to watch

## Pitfalls
- **Don't waste time on parallel web search subagents for same-day news** — go straight to HN Algolia
- **Algolia "past week" filter is unreliable** — use the API directly with `execute_code` and no date filter; filter by sorting and points instead
- **Algolia browser clicks don't reliably navigate** — the JS page intercepts clicks. Use the API approach (Method A) for story IDs
- **Reddit blocks all automated access** — don't bother with browser or fetch
- **Google search triggers CAPTCHA** from automated browsers — use HN Algolia instead
- **Large delegate outputs need terminal reads**, not read_file or execute_code
- **Always extract URLs from HN first**, then fetch directly — don't search blindly
- **Wiki ingestion for essays is different from digests** — the `wiki_manager.py ingest` command only handles `digests/`; for essays, create/update concept pages manually, then rebuild index
