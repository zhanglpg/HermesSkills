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

Fetch content from ALL configured sources. Use your web tools freely — you are both the fetcher and summarizer. Gather as much relevant content as possible.

#### RSS Feeds
For each source in `rss_sources`, fetch the RSS URL and extract recent article titles, URLs, dates, and summaries. If a feed fails, note it and move on.

#### arXiv Papers
If `arxiv_categories` is non-empty, search arXiv for recent papers in those categories.

#### Hacker News
Search for top AI-related stories on Hacker News.

#### GitHub Trending
Search for trending AI/ML repositories on GitHub from the past week.

#### Twitter/X
For each handle in `twitter_accounts`, search for their recent tweets (past 24-48 hours).

#### Web-Only Sources
For each source in `web_only_sources`, search the web for their latest content.

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
