---
name: github-activity-attribution
description: "Diagnose GitHub star spikes via events API + rule-outs."
version: 1.0.0
author: Hermes Agent (curator)
license: MIT
tags:
  - research
  - github
  - community-analysis
metadata:
  hermes:
    tags: [github, stars, trending, attribution, community-analysis]
    related_skills: [hacker-news-research]
---

# GitHub Activity Attribution

## When to Use
- User asks "why did repo X get stars / trend yesterday" or notices a star/fork spike
- Need to attribute (or honestly fail to attribute) a popularity anomaly to a cause

## Step 1: Confirm and timestamp the spike (events API)

The public events API is the unauthenticated star proxy — `WatchEvent` = star, timestamped:

```bash
curl -s "https://api.github.com/repos/<owner>/<repo>/events?per_page=100&page=1"
```

Count by day/type in Python: `collections.Counter` over `e['created_at'][:10]` and `e['type']`.

- **HARD CAP: 300 events.** Pages ≥ 4 return `{"message": "In order to keep the API fast for everyone, pagination is limited for this resource."}` — you can only see the ~300 most recent events. Spikes older than that are invisible here; say so.
- **Do NOT chase stargazers timestamps unauthenticated**: `Accept: application/vnd.github.star+json` paging returns 401 `Requires authentication` past the first pages. Only viable with a GH token (`gh api` if configured).
- The oldest event timestamp in your fetched pages bounds how far back you can see — check it before claiming "no spike before date X".
- WatchEvent count ≈ stars but is not unique-user-verified; fine as a proxy, don't overclaim.

## Step 2: Establish spike onset
The first dense cluster of WatchEvents (e.g. ~300 watches in a 5-hour window vs a quiet baseline) gives onset time in UTC. This is your correlation anchor.

## Step 3: Rule out candidate causes (run in parallel)

| Candidate | How to check |
|---|---|
| Release/tag | `api.github.com/repos/<o>/<r>/releases`, `/tags` |
| Hacker News | Algolia `search` + `search_by_date` for repo name (stories AND comments), `numericFilters=created_at_i%3E<epoch>` |
| GitHub Trending | Scrape `github.com/trending?since=daily` and `since=weekly` — `<article class="Box-row">` blocks contain "N stars today" / "N stars this week" |
| Launch tweet / org announcement | `https://api.fxtwitter.com/<user>/status/<id>` (clean JSON, no wall); check the org's other same-day announcements |
| Sibling-repo halo | `api.github.com/orgs/<org>/repos?sort=created` — a same-org launch the same day can spill stars onto related repos |
| README/self-promo | README news section, badges (e.g. a Trendshift badge indicates prior trending history) |

## Step 4: Timing correlation
Compare spike onset (UTC) with candidate event times. A tight lag (e.g. stars starting ~30 min after a same-org product launch at a known timestamp) is strong circumstantial evidence of halo effect.

## Step 5: Honest conclusion
If every public footprint is negative (no HN, no trending, no tweet trail) but timing correlates with an org event, the amplification likely ran through **off-platform channels** (WeChat articles, DingTalk groups, ModelScope/community forums — common for Chinese-org repos like Alibaba/Qwen). Report: the confirmed spike shape, what was ruled out, the correlation, and the honest limit of attribution. Never fabricate a specific cause.

## Pitfalls
- Events API window is the ~300 most recent events only — for older spikes use a GH token + stargazers timestamps; star-history services may be down.
- GitHub Trending HTML parsing: repo names come from `<h2 ...><a href="/owner/repo">`; the "stars today/week" text is per-article. Other numeric regexes on that page (e.g. total-star counts) pick up nav constants like "16" — don't trust them.
- Algolia comment search needs URL-encoded queries; `numericFilters` `>` must be encoded as `%3E`.

## Related
- `hacker-news-research`: the HN rule-out queries and fxtwitter tweet reading live there.
