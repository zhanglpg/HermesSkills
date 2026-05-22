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

### Step 2.6: Pre-run Script Failure Recovery (Portfolio only)

If the pre-run data-collection script (e.g., `investment-brief-data.py`) times out or fails, **do not abandon the brief**. Proceed with manual recovery:

1. **Run `fetch_prices.py` directly** to get the latest prices:
   ```bash
   python3 ~/.hermes/skills/openclaw-imports/generating-briefs/scripts/fetch_prices.py
   ```
2. **Read `brief_data.json`** as fallback for both technical data and prices:
   ```bash
   ~/.openbb_platform/data/brief_data.json
   ```
   This file contains SMA signals, volatility, drawdowns, correlations, valuation metrics, macro indicators, and SEC filing activity. It may also contain cached prices if the fetch script failed.
3. **Proceed to Step 3** (content gathering). The brief can still be generated with full quantitative data even when the automated pipeline breaks.

### Step 3: Gather Content

Fetch content from ALL configured sources. **Use browser tools directly** — they are far more reliable than delegating to subagents for web fetching (subagents often lack web tools or hallucinate data).

**Recommended parallel fetch strategy for AI Tech Brief (revised May 2026):**
1. **Terminal (background):** RSS batch script (all feeds in one Python call, ~15 sec) + arXiv extraction if using Python approach. Use `background=true` with `notify_on_complete=true`.
2. **Main agent (browser):** arXiv cs.AI pastweek extraction via `browser_navigate` + `browser_console` IIFE with `dl.children` DOM traversal. Browser_console works reliably on pastweek pages up to 1,600+ entries (verified May 2026). Do cs.AI first, then cs.LG with keyword filtering, then cs.SE if time permits. For cs.LG and cs.SE, apply client-side keyword scoring to filter AI/LLM-relevant papers. If DOM is genuinely inaccessible (`document.querySelector('dl')` returns null), fall back to Python urllib (see pitfalls).
3. **Main agent (browser):** TechCrunch AI (`techcrunch.com/category/artificial-intelligence/`) — snapshot parsing is reliable; retry once if first navigation times out. Ars Technica AI (`arstechnica.com/ai/`) — snapshot parsing is reliable. Both are MORE reliable from the main agent than via subagents.
4. **Subagent (browser toolsets):** GitHub Trending daily + weekly — single subagent task with browser tools, ~9 min. Extract both pages in one subagent with JS filtering.
5. **Main agent (browser):** HN front page (`news.ycombinator.com`) — use `document.querySelector('table')?.innerText` for all stories at once; parse text for AI-relevant items. Do NOT scroll — HN scrolling breaks the page.
6. **Skip or deprioritize:** The Verge (times out in subagents, JS extraction fragile), DeepMind/LMSYS blogs (often stale), Meta AI blog (weeks-old content), Twitter/X (inaccessible).

This reliable strategy avoids the biggest failure modes. HN coverage comes from the main HN page (`https://news.ycombinator.com/`) — parse the accessibility tree snapshot for AI-relevant stories.

**Recommended parallel fetch strategy for Portfolio Brief:**
1. **Terminal:** Run `fetch_prices.py`, then read `brief_data.json`.
2. **Main agent (browser):** Navigate to `finance.yahoo.com/` first — capture futures/VIX/gold/oil/BTC from sidebar, then extract news headlines via `browser_console`: `JSON.stringify(Array.from(document.querySelectorAll('main h3, main h2')).filter(el => el.closest('a')).map(el => ({text: el.textContent?.trim().substring(0,200), href: el.closest('a')?.href})), null, 2)` — returns 30-60 linked headlines with relative timestamps ("2h ago", "39m ago").
3. **Main agent (browser):** Navigate to `cnbc.com/markets/` — the accessibility tree snapshot gives trending stories, market movers, and sector roundups with no JS needed.
4. **Terminal (background):** Run the RSS batch script for all configured feeds as a single Python script — this replaces ~10 individual fetches and completes in ~30s. Use `background=true` with `notify_on_complete=true` so it runs while you browse.
5. **Deprioritize/skip:** Bloomberg, FT, WSJ (paywalled/blocked), Twitter/X (inaccessible), The Reformed Broker (RSS parse errors), Calculated Risk (often stale).

Use `scripts/rss_batch.py` as a reference skeleton for the RSS batch script — the pattern (parallel urllib fetches, RSS+Atom parsing, datetime-aware filtering, SSL context) is reusable. Copy the feed URLs from the current config JSON.

#### Pitfalls Learned

- **Portfolio/Investment Brief content gathering order:** Do NOT delegate web fetching to subagents for portfolio sources — browser tools in the main agent are far more reliable. Priority order: (1) `fetch_prices.py` + `brief_data.json`, (2) Yahoo Finance homepage (futures + news headlines via browser_console), (3) CNBC Markets (snapshot), (4) RSS batch (background terminal). This produces a complete brief in ~2-3 minutes.
- **Yahoo Finance news headlines via browser_console** — the Yahoo homepage sidebar gives futures data, but the page is also a rich news source. After capturing futures, use `browser_console` with the querySelectorAll pattern above to extract 30-60 linked article headlines. Timestamps are relative ("2h ago", "39m ago") making freshness filtering straightforward. Scroll and re-snapshot if you need more stories. This is more reliable than the Yahoo Finance RSS feed which returns items without useful summaries.
- **CNBC Markets snapshot is reliable for headlines** — `cnbc.com/markets/` loads cleanly and provides trending stories, market movers, and sector roundups in the accessibility tree snapshot. No JS extraction needed — just scan the snapshot for headings and links. The Trending Now section is particularly valuable.
- **brief_data.json is large (~1500 lines, ~38KB)** — use `read_file` with `offset` to paginate through it. The file contains: `portfolio_snapshot` (prices from last trading day), `technical_signals` (SMA, volatility, drawdowns, volume), `risk_dashboard` (Sharpe proxies, correlations), `macro_snapshot` (GDP, unemployment, CPI, Fed funds, VIX, 10Y), `valuation_check` (PE, PB, ROE, earnings yield), `sec_activity` (filings per symbol, recent 8-Ks), and `alerts`. Note that `portfolio_snapshot` prices can be 1-3 trading days stale — prefer `fetch_prices.py` output.
- **Don't batch 3+ complex news sites into a single subagent task** — even with browser toolsets, fetching The Verge + Ars Technica + TechCrunch in one subagent will hit the 600s timeout (45+ API calls). Fetch news sites directly from the main agent (one `browser_navigate` per site), or split across 2 subagent tasks max. arXiv+HN+GitHub in parallel subagents is safe because each is a single-page extraction.
- **DO NOT delegate web fetching to subagents WITHOUT browser toolsets** — if a subagent inherits default toolsets but lacks browser access, it will burn through its iteration budget and produce nothing. Always pass `toolsets: ["browser"]` explicitly.
- **arXiv listing pages work reliably via browser** — navigate to `https://arxiv.org/list/cs.AI/new` (or cs.LG/new, cs.SE/new) via browser_navigate. The page heading shows the listing date (e.g., "Showing new listings for Friday, 10 April 2026"). Extract with browser_console using: `document.querySelectorAll('a[href^="/abs/"]')` for IDs, `.list-title` divs for titles, `.list-authors` divs for authors. Note: `.mathjax` abstracts from the listing page often misalign with papers due to DOM structure — use them for rough keyword filtering only.
- **⚠️ browser_console DOM queries can fail ENTIRELY on large pastweek pages** — the accessibility tree snapshot shows content but `document.querySelector` returns nothing (not even `document.body.children`). This was observed on the cs.AI pastweek page (997 papers, 1.6MB HTML). When `document.querySelectorAll('dt')` returns 0 despite the snapshot showing 117 dt/dd pairs, the DOM is inaccessible via JS. **Workaround:** use Python `urllib.request` to fetch the raw HTML and parse with regex. The Python approach successfully extracts all papers from the raw HTML when browser_console fails. This approach works for any arXiv category. **HTML quote-style gotcha:** arXiv uses single quotes (`class='list-title mathjax'`), so regex patterns must match both quote styles: `class=['\"]list-title[^'\"]*['\"]`.
- **For detailed arXiv paper abstracts, fetch individual pages via Python temp file** — after identifying candidate papers from the listing, write a Python script to `/tmp/fetch_papers.py` using `write_file()`, then run with `terminal("python3 /tmp/fetch_papers.py")`. The script uses `urllib.request` to fetch each paper's `/abs/` page and parses `<meta name="citation_title">`, `<meta name="citation_author">`, `<meta name="citation_date">`, and the `<blockquote class="abstract mathjax">` for full metadata. This is far more reliable than browser_console extraction for abstracts.
- **NEVER pass multi-line Python scripts inline to terminal()** — nested quotes (mixing `'` and `"`) in multi-line strings cause `SyntaxError: unterminated string literal`. Always write the script to a temp file via `write_file()` first, then execute it.
- **arXiv API (`export.arxiv.org`) is unreliable from sandboxed environments** — timeouts are common. Prefer the listing pages approach above.
- **GitHub Trending extraction**: use `document.querySelectorAll('article')` (not `article.Box-row`). Each article has an `h2 > a` for the repo name, a `p` for description, `[itemprop="programmingLanguage"]` for language, and `.float-sm-right` for today's stars.
- **RSS feeds are lower-value than direct site visits** — most newsletter RSS feeds (TLDR, Ben's Bites, etc.) often fail or return stale content. Prioritize direct browser visits to key blogs (Simon Willison, AI lab blogs).
- **OpenAI's news page (`openai.com/news/`) is blocked by Cloudflare bot detection** — returns "Just a moment..." page. Skip it and rely on web search or other sources for OpenAI news instead.
- **Google DeepMind blog only shows month/year timestamps** (e.g., "April 2026"), not exact dates — makes freshness filtering unreliable. Cross-reference with other sources to confirm recency.
- **For cs.LG (92+ papers), use keyword filtering** — extract all papers via JS, then filter client-side with a regex for AI/LLM-relevant terms (LLM, language model, transformer, reasoning, agent, reinforcement, diffusion, attention, fine-tun, alignment, benchmark, scaling, multimodal, safety, hallucin, generation, vision, neural). This reduces noise dramatically.
- **HN extraction: `document.querySelectorAll('.athing')` returns EMPTY in headless browser** — same issue as arXiv large pages. `document.querySelectorAll('tr.athing')`, `.athing`, and any className-based selectors return 0 results on HN in headless environments. **Workaround:** use `document.querySelector('table')?.innerText` to get the full plaintext of all stories with scores, comment counts, and timestamps in a single string. Parse the text to extract rank, title, points, comments, and "X hours ago" timestamps. This is faster and more reliable than DOM traversal for HN specifically.
- **Today's HN front page may be nearly empty** — if running early in the UTC day, the current day's page may have only 2-4 stories. Always check yesterday's page too (use both dates) and merge results.
- **Google Search is blocked by bot detection** from browser — returns "unusual traffic" CAPTCHA page. Do NOT rely on Google Search for finding AI news. Instead, navigate directly to news sites: The Verge (`/ai-artificial-intelligence`), Ars Technica (`/ai/`), TechCrunch, etc.
- **Twitter/X is completely inaccessible** — no x-cli available, nitter.net is dead (empty page), xcancel.com has bot detection. Skip the Twitter/X section entirely rather than wasting time on workarounds.
- **Do NOT call `browser_navigate` for multiple URLs in a single tool-call block** — the browser has a single active page. If you call two `browser_navigate` in parallel, they race and only the last one's page is active for subsequent `browser_console` calls. Navigate one at a time, extract with `browser_console`, then navigate the next. Or use separate subagent tasks for different sites.
- **The Verge URL structure uses category/numeric-id/slug** `/{category}/{numeric-id}/{slug}` (e.g., `/ai-artificial-intelligence/918035/deepseek-preview-v4-ai-model`). A date-based regex like `/20\d{2}/\d{1,2}/\d+/` will return zero results. **JS extraction is fragile on The Verge:** The two-pass strategy (extract links via `document.querySelectorAll('main a[href]')` + filter by URL regex) frequently returns 0 results — Verge's React-rendered pages may not expose links in the expected DOM structure. The most reliable approach is **manual snapshot parsing**: scan the accessibility tree from `browser_navigate` for story titles (in link text under `<article>` or `<generic>` elements), timestamps ("MAY 1", "TWO HOURS AGO", times like "5:36 AM GMT+8"), and author bylines. Titles are visible as link text; timestamps are in `<time>` elements. This is slower but avoids the JS extraction fragility. If the snapshot is truncated, try `browser_scroll` and `browser_snapshot` again rather than fighting with JS selectors.
- **arXiv cs.AI has 300+ papers per listing** — all inherently AI-relevant (no keyword filtering needed). Extract the listing date from the page heading, note the total count, and use the listing page titles/authors for rough curation. Don't attempt to fetch individual paper pages for 300+ papers — pick 3-5 notable titles from the listing. Save detailed extraction for cs.LG where keyword filtering narrows to ~90 papers.
- **Discord output requires ~1800 char chunking** — Discord has a ~2000 character limit per message. After writing the full brief to disk, use the permanent chunk script at `~/.hermes/skills/openclaw-imports/generating-briefs/scripts/chunk_brief.py`. Do NOT use send_message — the cron auto-delivers the final response.
- **Chunking workflow (markdown-aware, no code fences):** (1) Write the full brief to disk. (2) Run the permanent chunker: `terminal("python3 ~/.hermes/skills/openclaw-imports/generating-briefs/scripts/chunk_brief.py /path/to/brief.md")`. (3) Copy each `=== CHUNK N/T ===` section from the script output verbatim into your final response — each chunk already has the `**(Chunk N/T)**` label and is self-contained markdown under 1850 chars. **CRITICAL: Do NOT wrap chunks in ``` fences** — wrapping markdown in code blocks prevents Discord from rendering headings, tables, links, and formatting. The chunker outputs raw markdown that Discord renders natively. (4) The chunker automatically handles: table splitting with header prepending to continuation chunks, orphan chunk merging (<80 chars), HN table deduplication, and greedy paragraph-based combining. **Always use this script — do not write ad-hoc chunking code.**
- **HN section descriptions should be terse** — HN highlights lists are the most common source of chunk overflow. Keep each item's description to one short sentence. If the section still overflows, trim the lowest-scoring items rather than splitting mid-list.
- **browser_console JS must use IIFE wrapper** — `return` at top level causes `SyntaxError: Illegal return statement`. Always wrap JS in `(() => { ... })()`.
- **Ars Technica AI section (`arstechnica.com/ai/`) is a reliable and rich source** — loads cleanly in headless browser, provides unique coverage of AI legal/policy, security (drone strikes on data centers), and developer tools (Copilot pricing). Often catches stories missed by TechCrunch and The Verge. Articles have comment counts that proxy for importance. **Extraction recipe:** Use `Array.from(document.querySelectorAll('main article'))` (NodeList doesn't support `.slice()`, must convert first), then for each article: title from `article.querySelector('h2 a')`, URL from `h2 a.href`, date from `article.querySelector('time').getAttribute('datetime')` (returns ISO 8601), comment count from `article.querySelector('a[href*=\"comments\"]')`, description from `article.querySelector('p')`. Wrap in IIFE for multi-step extraction. Ars dates are reliable ISO format, making freshness filtering trivial.
- **HN in a subagent can time out if given 2+ complex page navigations** — fetching both April 30 AND May 1 HN pages in a single subagent task (2 navigations + 2 console extractions + client-side keyword filtering) can hit the 600s timeout. Either: (a) split into 2 separate subagent tasks (one per date), or (b) do HN directly from the main agent. A single subagent fetching just HN usually succeeds; it's the combination of 2 navigations + filtering logic that risks timeout.
- **GitHub Trending daily page shows only ~9 repos** — GitHub reduced the daily trending display count. Supplement with `?since=weekly` to reach a useful count. Weekly trending is a separate navigation. Filter both daily and weekly for AI/ML repos. Mark weekly repos with "⭐/wk" instead of "⭐" to distinguish.
- **Meta AI blog is low-value for daily briefs** — latest posts are often weeks old (latest was April 8 on May 2). Skip it unless there's a major announcement. Check TechCrunch for Meta AI news instead.
- **TechCrunch snapshot extraction from browser_navigate is highly reliable** — the accessibility tree snapshot alone gives article titles, timestamps ("X hours ago", "X days ago"), categories, and author names without needing JS. Use JS extraction as a supplement only if the snapshot is truncated. This is faster and more reliable than The Verge's React-rendered pages.
- **arXiv cs.AI pastweek now has ~1,000 papers** (1,020 observed May 2026) and cs.LG has ~1,000 papers (1,009 observed). Combined cs.AI+cs.LG+cs.SE = ~2,200 papers per week. cs.SE contributes ~160 papers. For AI tech briefs, extract all three categories via browser_console. cs.AI papers are inherently AI-relevant (no keyword filter needed). cs.LG and cs.SE need keyword filtering to isolate AI/ML/LLM papers.
- **arXiv date extraction from `pastweek` pages uses `<h3>` headings** — dates are in `<h3>` elements like "Fri, 1 May 2026 (showing 217 of 217 entries)". **h3 elements are direct children of `<dl>`, NOT inside `<dt>` elements** (confirmed: `h3.closest('dt')` returns null). The reliable extraction pattern: (1) get `dl.children`, (2) iterate children, tracking `currentDate` when hitting an `H3` child, (3) for each `DT` child, consume the next sibling as the `DD` (increment index by 1 extra to skip it). Do NOT use parallel `querySelectorAll('dt')`/`querySelectorAll('dd')` arrays — they don't account for h3 siblings interspersed among dt/dd pairs. Verify h3 count matches the expected number of listing days (5 for pastweek).
- **Hugging Face Blog RSS omits dates** — the `/blog/feed.xml` RSS returns items without pubDate. Navigate directly to `https://huggingface.co/blog` to get post dates and like counts.
- **DeepMind + LMSYS in a single subagent task times out at 600s** — even 2 complex blog sites can exceed the budget. Fetch each in separate subagent tasks, or navigate directly from the main agent.
- **cs.AI subagent data is overwhelming at 80+ papers** — the subagent extracts fine, but the main agent should curate to ~12 notable papers based on title interest, author reputation, and alignment with news themes. Don't try to include every paper; brevity is a feature.
- **arXiv doesn't update on weekends** — if running on Saturday/Sunday/Monday, the listings will be from the previous Friday. The page heading shows the exact listing date; always check it for freshness filtering.
- **arXiv `pastweek?show=2000` is the best endpoint for multi-day coverage** — navigate to `https://arxiv.org/list/{category}/pastweek?show=2000` to get ALL papers from the past 5 listing days in a single page. The page groups entries by date with `<h3>Mon, 27 Apr 2026 (showing N of M entries)</h3>` headings. This is much more efficient than fetching individual `/new` pages when covering a full week. Available for all categories (cs.AI, cs.LG, cs.CL, cs.DC, cs.AR, etc.).
- **JavaScript client-side filtering for 900+ paper listings** — when dealing with a pastweek page containing hundreds of papers, use `browser_console` with an IIFE that: (1) iterates `dl.children` to correlate h3 date headings with dt/dd paper pairs (h3s are direct children of dl, interspersed among dts), (2) reads title from `.list-title`, authors from `.list-authors`, subjects from `.list-subjects`, (3) filters with a comprehensive keyword array (llm, reasoning, agent, scaling law, attention, inference, quantization, etc.) scoring each paper by match count, (4) sorts by score, (5) returns `JSON.stringify({total, filtered, papers})`. This eliminates the need to fetch individual abstracts for thousands of papers.
- **arXiv extraction: browser_console is the PRIMARY approach, Python urllib is fallback** — contrary to earlier observations where `document.querySelector('dl')` returned null on large pages, browser_console DOM traversal now works reliably on pastweek pages with 1,600+ entries (verified May 2026: cs.AI 1,629 entries, cs.LG 1,571 entries). **Use browser_console with `dl.children` iteration as the primary method** — it's faster and avoids regex fragility. **Python urllib fallback** (for when DOM is genuinely inaccessible): **CRITICAL DT-DD pair fix:** Don't match DDs then search backwards for IDs — backwards regex matches IDs from *adjacent* papers. **Correct method:** (1) match DT blocks first: `<dt>.*?arXiv:(\\d+\\.\\d+).*?</dt>` to extract paper ID — do NOT include `[arxiv]` literal text in the regex (arXiv HTML uses `[1] arXiv:ID` not `[arxiv] arXiv:ID`); (2) for each DT match, find the *following* `<dd>(.*?)</dd>` in the HTML after the DT end position, (3) from each dd block, extract title: match text after the `</span>` closing the descriptor, authors: within `<div class='list-authors'>`, subjects: within `<div class='list-subjects'>`, comments: within `<div class='list-comments'>` (if present), (4) strip all HTML tags from extracted fields. **KEY INSIGHT: don't try to match dt/dd pairs in a single regex** — match dds first, then find IDs by position. arXiv HTML uses single quotes (`class='list-title mathjax'`). Scale observed May 2026: cs.AI 1,629 papers, cs.LG 1,571, cs.CL 569, cs.DC 107, cs.AR 54 (3,930 total across 5 categories).
- **⚠️ arXiv JSON output exceeds process log buffer (~200K char cap)** — 3 categories with ~1,500 papers produce 215K+ chars of JSON that gets truncated in process log. The truncated output starts mid-paper (missing the opening bracket) and cannot be parsed. **Fix:** redirect arXiv script stdout to a file: `python3 /tmp/fetch_arxiv.py > /tmp/arxiv_full.json`. Then parse the file directly. When reading the persisted process-log output file, the output field contains escaped JSON: do `json.loads(raw)['output']` then `json.loads(output_str)` (two-step parse).
- **⚠️ TITLE EXTRACTION GOTCHA:** The regex `r'<div class=['\"]list-title[^'\"]*['\"][^>]*>.*?<span[^>]*>(.*?)</span>'` captures the **descriptor text** ("Title:"), NOT the actual paper title. The actual title text is on the next line after the `</span>` closing tag. Correct pattern: match the list-title div, skip past `</span>`, then capture the following text up to `</div>` — `r"<div class=['\"]list-title[^'\"]*['\"][^>]*>.*?</span>\s*(.*?)\s*</div>"`. Always verify by debugging the first 3 DD blocks before processing thousands of papers. Same approach applies to authors/subjects/comments extraction — capture the full div content then strip HTML tags.
- **HN `front?day=YYYY-MM-DD` pages return EMPTY in headless browser** — navigating to `https://news.ycombinator.com/front?day=2026-05-06` returned an empty page (0 elements, no snapshot). The main HN page `https://news.ycombinator.com/` works fine and shows the current day's front page stories. Parse the accessibility tree snapshot for AI-relevant stories instead of relying on the dated front pages.
- **HN scrolling breaks the page** — scrolling down on `news.ycombinator.com` causes the page snapshot to become completely empty. Extract all content from the initial page load without scrolling. Use `document.querySelector('table')?.innerText` to get all stories at once.
- **HN Firebase API (`hacker-news.firebaseio.com`) times out from sandboxed environments** — the official HN API is unreliable. Stick to the `innerText` extraction from the main HN page.
- **Individual abstract fetching via Python urllib** — for the top N candidate papers after filtering, write a Python script to `/tmp/fetch_abstracts.py` that fetches each `https://arxiv.org/abs/{id}` and parses: title from `<h1 class="title[^"]*">`, authors from `<div class="authors">`, abstract from `<blockquote class="abstract[^"]*">`, submitted date from `Submitted on (\d+ \w+ \d+)`, subjects from `<span class="primary-subject">`, and comments (pages/figures) from `<td class="tablecell comments">`. Regexes must handle both single and double quote HTML attributes.
- **Weekly paper brief is a distinct format from daily news brief** — when asked for a "weekly paper brief" or "AI paper roundup," use the Top 5 + Honorable Mentions + Trends format (see Weekly Paper Brief Output Format below) rather than the daily news brief template. The focus is on arXiv papers exclusively, not general AI news.
- **CNBC Markets (`cnbc.com/markets/`) is a reliable fallback for index data** — when Bloomberg, FT, and other premium sources are blocked by bot detection, CNBC's markets page loads reliably and provides S&P 500, NASDAQ, DJIA, VIX, and top movers.
- **Yahoo Finance (`finance.yahoo.com/news/`) provides reliable futures data** — even when its news stories fail to load ("We're unable to load stories right now"), the sidebar reliably shows S&P/Dow/Nasdaq futures, VIX, gold, crude oil, and Bitcoin prices.
- **MarketWatch and Reuters often return empty pages via browser** — `marketwatch.com/investing` and `reuters.com/markets/` frequently load as empty snapshots in headless environments. Do not rely on them as primary sources; use RSS or direct article URLs instead.
- **Seeking Alpha has aggressive bot detection** — `seekingalpha.com` blocks headless browsers with "Access to this page has been denied." Use RSS feeds or cached data instead.
- **RSS batch script datetime comparison bug** — feeds like CNBC, MarketWatch, and FT Alphaville fail with `"can't compare offset-naive and offset-aware datetimes"`. Root cause: `parse_date()` can return naive `datetime` objects (from formats without timezone) while the cutoff is timezone-aware (`datetime.now(timezone.utc)`). **Fix:** make all parsed dates timezone-aware — after parsing, if `dt.tzinfo is None`, set `dt = dt.replace(tzinfo=timezone.utc)`. This prevents silent failure on otherwise-valid feeds.
- **Portfolio Brief: CNBC Markets + Yahoo Finance homepage are the most reliable web sources** — `cnbc.com/markets/` loads cleanly and provides market headlines, trending stories, and sector roundups in the accessibility tree snapshot (no JS needed). `finance.yahoo.com/` gives real-time futures (S&P, Dow, Nasdaq, Russell 2000), VIX, gold, crude oil, and Bitcoin prices in its sidebar. Navigate to both as the first web sources for Portfolio Brief. **Yahoo Finance is also a rich news source:** after capturing futures data, use `browser_console` with `JSON.stringify(Array.from(document.querySelectorAll('main h3, main h2')).filter(el => el.closest('a')).map(el => ({text: el.textContent?.trim().substring(0,200), href: el.closest('a')?.href})), null, 2)` — this returns all linked article headlines in one shot, typically 30-60 items with timestamps in the snapshot. Scroll and re-snapshot to get older stories. Yahoo Finance timestamps are relative ("2h ago", "39m ago") making freshness filtering easy.
- **Portfolio Brief: brief_data.json prices can be stale** — the file is generated weekdays but the `portfolio_snapshot` prices are from the most recent trading day's close. On a Tuesday, prices may be from Friday (3 days stale). The `fetch_prices.py` output is always preferred for current prices; use `brief_data.json` prices only as fallback if the fetch script failed. Brief_data.json's technical signals (SMA, volatility, drawdown) also lag by one trading day — note this in the brief.
- **NEVER wrap brief chunks in ``` code fences for Discord** — wrapping markdown in code blocks prevents Discord from rendering headings, tables, links, and bold/italic formatting. Always use the permanent chunker script which outputs raw markdown chunks with plain `**(Chunk N/T)**` labels. Code fences are the #1 cause of broken brief rendering.

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

#### RSS Feeds (Batch via Terminal)

Do NOT fetch RSS feeds one by one. Write a single Python script that fetches ALL feeds in parallel via `urllib.request`, parses both RSS (`<item>`) and Atom (`<entry>`) formats, and returns JSON with per-feed results (status, items with title/link/date/summary, and error messages for failed feeds). Run it once via `terminal()`.

**Key implementation details:**
- Use `ssl.create_default_context()` with `check_hostname=False` and `verify_mode=ssl.CERT_NONE` to handle feeds with SSL issues
- Set a `User-Agent: Mozilla/5.0` header
- Use `timeout=15` per feed to avoid hanging on dead sources
- Detect Atom vs RSS by checking if root tag is `{http://www.w3.org/2005/Atom}feed` — Atom uses `{http://www.w3.org/2005/Atom}entry` with `title`/`link[@href]`/`updated`/`summary`; RSS uses `.//item` with `title`/`link`/`pubDate`/`description`
- **CRITICAL — datetime comparison fix:** After parsing a date, if `dt.tzinfo is None`, set `dt = dt.replace(tzinfo=timezone.utc)`. The cutoff must also be timezone-aware (`datetime.now(timezone.utc)`). Without this, feeds like CNBC and MarketWatch fail silently with `"can't compare offset-naive and offset-aware datetimes"`.
- Include feed name + status ('ok' or 'error') even for failed feeds, with truncated error messages
- This single terminal call replaces ~10 individual fetches and completes in ~15-30 seconds

Most newsletter RSS feeds (TLDR, Ben's Bites, The Neuron, Latent Space, Interconnects) will fail or return stale content. **Anthropic RSS** and **OpenAI RSS** may fail with XML parse errors. **Hugging Face** and **Simon Willison** feeds are consistently reliable. If a feed fails, note it and move on — do not retry.

#### Twitter/X
For each handle in `twitter_accounts`, search for their recent tweets (past 24-48 hours).

#### Web-Only Sources
For key blogs (Simon Willison, AI lab blogs), navigate directly to their homepage via browser and extract recent post titles/links. For general AI news discovery, navigate directly to major news sites instead of relying on search engines:
- **The Verge AI** (`https://www.theverge.com/ai-artificial-intelligence`) — excellent coverage, recent articles with timestamps, scrollable
- **Ars Technica AI** (`https://arstechnica.com/ai/`) — strong technical AI coverage, includes syndicated FT/WIRED content
- **TechCrunch AI page (`techcrunch.com/category/artificial-intelligence/`) is reliable** — loads cleanly in headless browser. The accessibility tree snapshot from `browser_navigate` is often clean enough to extract article titles, timestamps ("X hours ago"), categories, and links directly without JS — scan the snapshot for headings and times. If JS extraction is needed: `document.querySelectorAll('main li h3 a, main li h2 a')` inside an IIFE. For each link, get: title (`a.textContent`), URL (`a.href`), time (`li.querySelector('time').textContent`), category (`li.querySelector('a[href*=\"category\"]').textContent`). Deduplicate by URL. Articles include "X hours ago" and "X days ago" timestamps — include only ≤1 day old for daily briefs. Unlike The Verge, TechCrunch's simpler DOM structure means single-pass extraction usually works.
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

### Discord Delivery

After writing the brief, load the `discord-rendering` skill for Discord-specific formatting rules:
- Use `chunk_brief.py` for message splitting (~1800 char chunks)
- Never wrap chunks in code fences
- Tables/headers render natively
- Mermaid/PlantUML don't render — use ASCII box-drawing or PNG attachments
- Unicode box-drawing characters (─ │ ┌ ┐ └ ┘ ├ ┤) work in code blocks

---

## Weekly Paper Brief — Output Format

Use this format when asked for a weekly paper brief, AI paper roundup, or top papers of the week. This is distinct from the daily AI Tech Brief — it focuses exclusively on arXiv papers, not general AI news.

```markdown
# Weekly AI Paper Brief — {date}

**Week of {start_date}–{end_date}** · Curated from arXiv cs.AI, cs.LG, cs.CL, cs.DC, cs.AR and community discussion (HN, social media).

{One-paragraph intro: 1-2 sentences capturing the theme of this week's selection.}

---

## Top 5 Papers

### 1. {Paper Title}
**arXiv:{id}** · https://arxiv.org/abs/{id}
**Authors:** {First few authors}, et al. ({total} authors) — or list all if ≤8
**Submitted:** {date} · {pages/figures} · {optional: HN points if applicable}

{3-4 sentence summary of what the paper does and why it matters.}

> **Takeaway:** {One-line memorable takeaway.}

### 2. {Paper Title}
... (repeat for all 5)

---

## Honorable Mentions

| Paper | Why Notable | Link |
|-------|------------|------|
| **{Title}** ({Authors}, {id}) | {1 sentence why it's worth knowing} | [arXiv](https://arxiv.org/abs/{id}) |

---

## Trends & Commentary

{2-4 thematic observations connecting multiple papers, identifying emerging patterns in the week's research. Each observation should be a short paragraph with a bold lead-in.}

---

*Brief compiled autonomously from arXiv listings, Hacker News discussions, and community sources. Papers selected for impact, novelty, and practical relevance across AI/ML and AI Infrastructure categories.*
```

**Paper discovery (preferred method):** Use the Hugging Face Daily Papers API for initial discovery — `https://huggingface.co/api/daily_papers?date=YYYY-MM-DD` returns community-submitted papers with upvotes and summaries in compact JSON. Fetch 5-7 dates to cover a full week. Advantages over arXiv listing pages: curated with upvote counts, summaries included, ~50KB JSON vs. 1.6MB HTML. Use `execute_code` with subprocess (not curl|python3 pipes — blocked by security scanner). After gathering via HF API, fetch full abstracts by navigating browser to `https://arxiv.org/abs/{id}` (arXiv API timeouts make this the most reliable method).

**Relevance scoring:** When processing 100+ papers, score by keyword match count — AI/ML terms (LLM, reasoning, agent, training, MoE, multimodal, RL, alignment, distillation, GRPO, reward, policy) and Infrastructure terms (inference, serving, GPU, distributed, compiler, quantization, KV cache, speculative decoding, LoRA, adapter).

**Selection criteria for Top 5:**
- Aim for a mix of AI/ML (LLMs, reasoning, agents, training, multimodal, RL, safety) and AI Infrastructure (systems, inference, serving, hardware, compilers)
- Prioritize papers with: community discussion (HN points), well-known co-authors, practical deployment impact, novel theoretical insights, comprehensive surveys/taxonomies
- Each paper must have a clear, memorable one-line takeaway
- Honorable Mentions table should include 5-8 additional notable papers
- Trends section should identify 2-4 thematic connections across papers

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