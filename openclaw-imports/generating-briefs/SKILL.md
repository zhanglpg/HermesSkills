---
name: generating-briefs
description: "Generates daily briefs (AI tech or investment/portfolio) from curated sources. Reads a config JSON for source lists, fetches content via web tools, and produces a structured markdown brief. Use when asked for a daily brief, AI news brief, portfolio brief, market brief, or morning briefing."
---

# Daily Brief Generator

Generate a daily brief by fetching content from curated sources and summarizing it into a structured markdown report.

## Instructions

### Step 1: Determine Brief Type

Ask the user which brief to generate if not specified:
- **AI Tech Brief** — `references/config.ai-tech.json`
- **Portfolio Brief** — `references/config.portfolio.json`

### Step 2: Read Configuration

Read the chosen config JSON file. The config contains:
- `twitter_accounts` — handles to search for recent tweets
- `rss_sources` — sources with RSS feed URLs (fetch and parse these)
- `web_only_sources` — sources to search the web for (no RSS)
- `arxiv_categories` — arXiv categories to query (AI tech only)
- `portfolio_holdings` — held positions grouped by sector (portfolio only)
- `watchlist` — tickers and themes to monitor (portfolio only)
- `extra_data_path` — path to pre-exported quantitative JSON (portfolio only)
- `brief_title` — display title for the brief

### Step 2.5: Fetch Real-Time Prices (Portfolio brief only)

**CRITICAL: Do this BEFORE gathering any other content.** This ensures the Market Snapshot has accurate, current prices.

Run the price fetcher script:
```bash
python3 ~/.hermes/skills/openclaw-imports/generating-briefs/scripts/fetch_prices.py
```

Parse the JSON output and use these exact prices and change percentages in the Market Snapshot table. Do NOT estimate or use stale data from web searches. The script output is authoritative for price data.

### Step 3: Gather Content

Fetch content from ALL configured sources. **Use browser tools directly** — they are far more reliable than delegating to subagents for web fetching (subagents often lack web tools or hallucinate data).

#### Pitfalls Learned
- **Parallel delegate_task WITH browser toolsets IS safe and fast** — using `delegate_task(tasks=[...])` with `toolsets: ["browser"]` on each task works reliably. Subagents CAN use browser_navigate + browser_console successfully when explicitly given browser toolsets. Use this pattern to fetch 3 sources concurrently and save significant time (e.g., GitHub Trending + The Verge + Ars Technica in one batch, then Anthropic + Meta AI in another).
- **DO NOT delegate web fetching to subagents WITHOUT browser toolsets** — if a subagent inherits default toolsets but lacks browser access, it will burn through its iteration budget and produce nothing. Always pass `toolsets: ["browser"]` explicitly.
- **arXiv listing pages work reliably via browser** — navigate to `https://arxiv.org/list/cs.AI/new` (or cs.LG/new, cs.SE/new) via browser_navigate. The page heading shows the listing date (e.g., "Showing new listings for Friday, 10 April 2026"). Extract with browser_console using: `document.querySelectorAll('a[href^="/abs/"]')` for IDs, `.list-title` divs for titles, `.list-authors` divs for authors. Note: `.mathjax` abstracts from the listing page often misalign with papers due to DOM structure — use them for rough keyword filtering only.
- **For detailed arXiv paper abstracts, fetch individual pages via Python temp file** — after identifying candidate papers from the listing, write a Python script to `/tmp/fetch_papers.py` using `write_file()`, then run with `terminal("python3 /tmp/fetch_papers.py")`. The script uses `urllib.request` to fetch each paper's `/abs/` page and parses `<meta name="citation_title">`, `<meta name="citation_author">`, `<meta name="citation_date">`, and the `<blockquote class="abstract mathjax">` for full metadata. This is far more reliable than browser_console extraction for abstracts.
- **NEVER pass multi-line Python scripts inline to terminal()** — nested quotes (mixing `'` and `"`) in multi-line strings cause `SyntaxError: unterminated string literal`. Always write the script to a temp file via `write_file()` first, then execute it.
- **arXiv API (`export.arxiv.org`) is unreliable from sandboxed environments** — timeouts are common. Prefer the listing pages approach above.
- **GitHub Trending extraction**: use `document.querySelectorAll('article')` (not `article.Box-row`). Each article has an `h2 > a` for the repo name, a `p` for description, `[itemprop="programmingLanguage"]` for language, and `.float-sm-right` for today's stars.
- **RSS feeds are lower-value than direct site visits** — most newsletter RSS feeds (TLDR, Ben's Bites, etc.) often fail or return stale content. Prioritize direct browser visits to key blogs (Simon Willison, AI lab blogs).
- **OpenAI's news page (`openai.com/news/`) is blocked by Cloudflare bot detection** — returns "Just a moment..." page. Skip it and rely on web search or other sources for OpenAI news instead.
- **Google DeepMind blog only shows month/year timestamps** (e.g., "April 2026"), not exact dates — makes freshness filtering unreliable. Cross-reference with other sources to confirm recency.
- **For cs.LG (92+ papers), use keyword filtering** — extract all papers via JS, then filter client-side with a regex for AI/LLM-relevant terms (LLM, language model, transformer, reasoning, agent, reinforcement, diffusion, attention, fine-tun, alignment, benchmark, scaling, multimodal, safety, hallucin, generation, vision, neural). This reduces noise dramatically.
- **HN front page extraction works well** — navigate to `https://news.ycombinator.com/front?day=YYYY-MM-DD`, then use browser_console with `document.querySelectorAll('.athing')` for rows and `row.nextElementSibling` for subtext (score + comments). Filter results client-side with AI keyword regex.
- **Today's HN front page may be nearly empty** — if running early in the UTC day, the current day's page may have only 2-4 stories. Always check yesterday's page too (use both dates) and merge results.
- **Google Search is blocked by bot detection** from browser — returns "unusual traffic" CAPTCHA page. Do NOT rely on Google Search for finding AI news. Instead, navigate directly to news sites: The Verge (`/ai-artificial-intelligence`), Ars Technica (`/ai/`), TechCrunch, etc.
- **Twitter/X is completely inaccessible** — no x-cli available, nitter.net is dead (empty page), xcancel.com has bot detection. Skip the Twitter/X section entirely rather than wasting time on workarounds.
- **browser_console JS must use IIFE wrapper** — `return` at top level causes `SyntaxError: Illegal return statement`. Always wrap JS in `(() => { ... })()`.
- **arXiv doesn't update on weekends** — if running on Saturday/Sunday/Monday, the listings will be from the previous Friday. The page heading shows the exact listing date; always check it for freshness filtering.

#### Hacker News (most reliable source)
Navigate to `https://news.ycombinator.com/front?day=YYYY-MM-DD` (yesterday's date UTC) for scored/ranked stories. Use JS console extraction:
```javascript
const rows = document.querySelectorAll('.athing');
// Extract title, url, score, comments, hnUrl from each row + its nextElementSibling .subtext
```
Filter results for AI/ML/LLM keywords. This gives accurate points and comment counts.

#### arXiv Papers
Navigate to `https://arxiv.org/list/{category}/new` via browser. Extract with JS:
```javascript
const dts = document.querySelectorAll('dt');
const dds = document.querySelectorAll('dd');
// Extract id, url, title, authors, abstract from dt/dd pairs
```
The page heading shows the listing date (e.g., "Wednesday, 8 April 2026"). Fetch cs.AI and cs.LG separately.

#### GitHub Trending
Navigate to `https://github.com/trending?since=daily`. Extract with JS:
```javascript
const articles = document.querySelectorAll('article.Box-row');
// Extract name, url, description, language, stars, todayStars from each article
```

#### RSS Feeds
For each source in `rss_sources`, fetch the RSS URL and extract recent article titles, URLs, dates, and summaries. If a feed fails, note it and move on.

#### Twitter/X
For each handle in `twitter_accounts`, search for their recent tweets (past 24-48 hours).

#### Web-Only Sources
For key blogs (Simon Willison, AI lab blogs), navigate directly to their homepage via browser and extract recent post titles/links. For general AI news discovery, navigate directly to major news sites instead of relying on search engines:
- **The Verge AI** (`https://www.theverge.com/ai-artificial-intelligence`) — excellent coverage, recent articles with timestamps, scrollable
- **Ars Technica AI** (`https://arstechnica.com/ai/`) — strong technical AI coverage, includes syndicated FT/WIRED content
- **TechCrunch AI** — good for startup/funding news
These sites are far more reliable than Google Search (blocked by bot detection) or RSS feeds (often stale).

#### Extra Quantitative Data (Portfolio only)
If `extra_data_path` is set and the file exists, read and incorporate it. Warn if the data is more than 2 days old.

### Step 4: Write the Brief

Compose the brief following the editorial guidelines below. Choose the correct set based on the config used.

**Key rules:**
1. Every URL, title, and data point must come from your actual fetched content. Never fabricate.
2. Lead with the most impactful stories.
3. Merge duplicate coverage into single entries with multiple source links.
4. Skip sections that have no content rather than writing filler.
5. Prefer depth over breadth — meaningful commentary beats a long list.
6. It is better to have a shorter brief with all real content than a longer brief with fabricated entries.

---

## AI Tech Brief — Output Format

```markdown
# {brief_title} - {date}

## Top Stories
### [Headline]
- **Summary:** 1-2 sentences
- **Why it matters:** Impact/significance
- **Source:** [Original Article Title](url)

## Twitter/X Updates
- **@[handle]:** [Tweet summary] — [Link](url)

## Newsletter & Blog Highlights
- **[Source Name]:** [Article title] — [Link](url) — 1-2 sentence summary

## AI Lab Updates
- **[Lab Name]:** [Announcement] — [Link](url) — 1-2 sentence summary

## Research Papers
| Paper | Key Finding | Link |
|-------|-------------|------|

## Hacker News AI Highlights
- **[Title]** (score pts, N comments) — [Link](url) | [Discussion](hn_url)

## GitHub Trending
- **[repo/name]** (language, stars) — [Link](url) — description

## Quick Links
- [Title](url) — 1 sentence description
```

---

## Portfolio Brief — Output Format

```markdown
# {brief_title} - {date}

## Market Snapshot
| Symbol | Price | Change | Sector |
|--------|-------|--------|--------|

**Market Sentiment:** [1-2 sentence assessment]

## Top Stories
### [Headline]
- **Summary:** 1-2 sentences
- **Market Impact:** How this affects markets/portfolios
- **Source:** [Original Article Title](url)

## Portfolio Impact
### [Sector/Theme]
- **[TICKER]:** [How this affects this position] — [Source](url)
  - **Action consideration:** [Hold/Monitor/Review — brief rationale]

## Watchlist Alerts
- **[TICKER or Theme]:** [What happened] — [Source](url)

## Twitter/X Market Commentary
- **@[handle]:** [Tweet summary] — [Link](url)

## Technical & Risk Dashboard
- **Bullish/Bearish/Most Volatile/Alerts**

## Macro & Economic Data
- **[Indicator/Event]:** [Reading/Outcome] — Impact assessment

## Sector Movers / Earnings & Corporate News / Newsletter Highlights / Quick Links
```
