---
name: github-popularity-forensics
description: "Diagnose repo star spikes: time the burst, find the driver."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [GitHub, Research, Forensics, Trending]
    related_skills: [hacker-news-research, github-repo-management]
---

# GitHub Popularity Forensics

## When to Use
- "Why did repo X gain stars yesterday / is it trending?"
- Attributing a star burst to a launch, HN thread, tweet, or trending listing
- Quantifying a repo's growth rate over recent hours/days

## Step 1: Time the burst (public events API, no auth)

```bash
curl -s "https://api.github.com/repos/OWNER/REPO/events?per_page=100&page=1" | python3 -c "
import sys, json, collections
d = json.load(sys.stdin)
if isinstance(d, dict): print(d.get('message')); sys.exit()
hours = collections.Counter(e['created_at'][:13] for e in d)
types = collections.Counter(e['type'] for e in d)
print('types:', dict(types))
for h in sorted(hours): print(h, hours[h])
print('oldest event in page:', d[-1]['created_at'] if d else None)"
```

- `WatchEvent` = star, `ForkEvent` = fork, `PushEvent` = commit activity — all with `created_at` timestamps. Unauthenticated is fine for repo events.
- **Pagination is hard-capped at 300 events** (pages 4+ return "In order to keep the API fast for everyone, pagination is limited"). On a busy repo 300 events may span only a few hours — the oldest event in your last good page is your horizon, not "no earlier activity".
- The stargazers endpoint with `starred_at` timestamps (`Accept: application/vnd.github.star+json`) **requires authentication** — anonymous calls 401. Don't burn turns on it without a token.
- Cross-check current totals: `GET /repos/OWNER/REPO` → `stargazers_count`, `forks_count`.

## Step 2: Rule out the usual amplifiers, in order

1. **GitHub trending** — parse `https://github.com/trending?since=daily` and `?since=weekly`: regex `<article class="Box-row">` blocks; repo name from `<h2 ... href="/owner/repo"`, `([\d,]+) stars today` / `stars this week` per block. Note sponsor slots pollute the list. Absence from trending rules out the biggest organic driver.
2. **HN mentions** — Algolia `search_by_date`:
   - `https://hn.algolia.com/api/v1/search_by_date?query=REPONAME&tags=story` and `&tags=comment`
   - URL-encode query; use `numericFilters=created_at_i>EPOCH` to bound the window (epoch for N days ago).
3. **X/Twitter** — xcancel search (`xcancel.com/search?f=tweets&q=...`) is usually bot-walled (returns 0 timeline items); fxtwitter API works for *known* tweet ids (`api.fxtwitter.com/USER/status/ID`) but has no search. Often unverifiable — move on.
4. **Repo-side triggers** — recent releases (`/releases`), tags (`/tags`), commits in the window (`/commits?since=...&until=...`), README news section, new sibling repos in the org (`/orgs/ORG/repos?sort=created`).

## Step 3: Attribution

- Correlate the burst start time with ecosystem events (same-org launches, adjacent model releases, conference announcements). Minute-level correlation between a launch and burst onset is strong evidence even without a direct link.
- If a candidate source exists (HN thread, tweet), fetch it and search the full text for the repo name before claiming causation.
- **No public footprint + tight timing correlation**: amplification almost certainly came via private/community channels (WeChat articles, DingTalk groups, internal org promotion — common for Chinese-ecosystem repos). Report the timing correlation and state the channel hypothesis honestly; do NOT fabricate a causal link.

## Pitfalls

- Events API horizon: 300 events ≈ hours, not days, on viral repos — never conclude "no stars before X" from it.
- `api.star-history.com/svg` can return empty (0 bytes) — don't rely on it.
- GitHub search API (`/search/repositories`) sometimes returns `null` entries in `items` — guard with `if r is None` before indexing.
- Trending page regexes break periodically; the article-block pattern above worked Aug 2026.

## Verification

- Burst onset time established from WatchEvent histogram.
- Each candidate amplifier explicitly checked and ruled in/out.
- Final claim distinguishes "correlated with X" from "linked from X".

## Related
- `hacker-news-research` — the HN-side extraction when a thread IS found; also covers fxtwitter and Algolia patterns in depth.
