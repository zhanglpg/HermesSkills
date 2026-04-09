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

```
https://hn.algolia.com/?dateRange=pastWeek&page=0&prefix=true&query=KEYWORDS&sort=byDate&type=story
```

- Use `browser_navigate` to this URL
- The HN submissions contain links to the **official blog posts, docs, media articles, and tweets**
- Extract all source URLs from the HN results before doing any fetching

## Step 2: Parallel Content Fetching via Subagents

Once you have URLs from Step 1, delegate 3 parallel subagents:

1. **Official sources** — blog post, engineering blog, API docs (use WebFetch)
2. **HN discussion threads** — fetch the actual comment threads (WebFetch on `news.ycombinator.com/item?id=XXXXX`)
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

**A. No existing draft:** Write the essay directly, then delegate a critic subagent to review and improve.

**B. Existing draft:** Delegate a critic/enrichment subagent with:
- The current essay text
- Specific improvements needed (named community voices, new data points, source details)
- Instructions to return the COMPLETE improved essay
- `toolsets: ["terminal", "file"]` so it can write the result to a file

The critic subagent should have explicit instructions about:
- Which named commenters to quote (with their actual quotes)
- New factual details to integrate (pricing, exec quotes, demo details)
- What to preserve (diagrams, frontmatter, structure)

## Step 5: Save to Obsidian

```bash
VAULT="${OBSIDIAN_VAULT_PATH:-$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents/notes}"
cp /path/to/final_essay.md "$VAULT/gen-notes/essays/Title.md"
```

Always backup existing file first if overwriting.

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
- **Reddit blocks all automated access** — don't bother with browser or fetch
- **Google search triggers CAPTCHA** from automated browsers — use HN Algolia instead
- **Large delegate outputs need terminal reads**, not read_file or execute_code
- **Always extract URLs from HN first**, then fetch directly — don't search blindly
