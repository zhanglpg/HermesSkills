---
name: jekyll-research-publishing
description: "Use when publishing research reports to GitHub Pages."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [GitHub Pages, Jekyll, Publishing, Research]
    related_skills: [single-file-react-gh-pages, breaking-news-research-essay]
---

# Jekyll Research Report Publishing (zhanglpg.github.io)

Markdown research reports / deep-dive essays published to Liping's GitHub Pages site. Not for interactive dashboards — those are single-file React apps (see the user-owned `single-file-react-gh-pages` skill).

## When to Use
- "Do deep research on X and publish the report to my GitHub Pages"
- Any text deliverable (business analysis, tech deep-dive, research report) for `~/claudews/zhanglpg.github.io`.

## Site structure
Jekyll site with a `_research/` collection: permalink `/research/:slug/`, layout `project` (set via `defaults` in `_config.yml`), auto-indexed at `/research/` sorted by date desc. Filename slug = URL slug, so name the file descriptively: `_research/<topic-slug>.md`. Kramdown renders GFM tables — use markdown tables freely.

## Procedure

1. **Research first** (web_search/web_extract/HN Algolia/GitHub API), then write the whole report with one `write_file` to `_research/<slug>.md`.
2. **Frontmatter** (all fields used by the index):
   ```yaml
   ---
   title: "<Report Title>"
   date: YYYY-MM-DD
   summary: "<one-sentence hook shown on the index>"
   tags: [topic, company, ...]
   status: published
   ---
   ```
3. **Byline immediately after frontmatter** (standing convention for published pieces):
   `*Liping Zhang, assisted by Hermes Agent (<model-name>) | <Month D, YYYY>*`
   Run `date` for the real current date — never trust conversation metadata dates.
4. **Deploy**:
   ```
   cd ~/claudews/zhanglpg.github.io
   git status --porcelain        # check what will be staged — repo has auto-commit jobs touching portfolio/
   git add _research/<slug>.md
   git commit -m "Research: <topic>" && git push
   ```
5. **Verify**: sleep ~60s (Jekyll build), then `curl -s -o /dev/null -w '%{http_code}' https://zhanglpg.github.io/research/<slug>/` must be 200 AND `grep -o '<title>[^<]*</title>'` must show the report title. A 200 alone doesn't prove the right page rendered.
6. Reply in chat with the URL + a tight summary of key findings (the chat message is the executive brief; the page is the artifact).

## Report structure that landed well (business/tech deep-dives)
1. Executive summary (bolded key numbers, thesis up front)
2. Status callout if covering a pending event (e.g. unclosed acquisition) — date-stamp what is fact vs prediction
3. Company/timeline history table
4. How it operates — product stack, free vs paid layers, revenue flywheel
5. Financials table (with sources and "estimate" flags — private companies' ARR is always third-party estimated)
6. Market & competitive landscape table
7. Event analysis (terms from primary filings — SEC 8-K beats press coverage; note what filings OMIT)
8. Prediction section: near/medium/long term, explicit scenario-probability table (subjective, labeled), and a concrete "what to watch" checklist
9. Bottom line
10. Grouped sources list; footnote distinguishing company disclosures from estimates

## Pitfalls
- Stage ONLY the new report file — never `git add -A`: auto-commit jobs (portfolio dashboard) leave unrelated dirty state in this repo.
- web_extract can hit WAF 403s and direct curl can hang on small blog hosts; use the Wayback availability API (`http://archive.org/wayback/available?url=<URL>`) for blocked/deleted primary sources.
- Don't present predictions as facts: label scenario probabilities subjective, date-stamp pending deals, and separate filings-verified terms from press speculation.

## Related
- `single-file-react-gh-pages` (user-owned): interactive dashboards on the same repo.
- `breaking-news-research-essay`: multi-source breaking-news research pipeline (Obsidian essay output rather than Pages).
