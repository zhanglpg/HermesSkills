---
name: commons-artwork-images
version: 1
author: Hermes Agent
license: MIT
description: Use when a page needs real artwork images from Commons.
metadata:
  hermes:
    tags: [commons, images, artwork, provenance, research]
    related_skills: [blocked-page-recovery, single-file-react-gh-pages, baoyu-article-illustrator, curated-digest]
---

# Sourcing authentic artwork images from Wikimedia Commons

## When to Use

Load this when a deliverable must be illustrated with photographs or scans of
REAL artworks and artifacts — calligraphy and painting surveys, art-history
timelines, museum or corpus catalogues, bronze/ceramics/coin references,
manuscript studies, or any "配真实资料图片" request. Also load when auditing an
existing illustrated page for wrong images.

Do NOT use for generated/AI illustration (`baoyu-article-illustrator`), for
diagrams and charts (`excalidraw`, `mermaid-debug`), or for generic blocked
fetches unrelated to artwork authenticity (`blocked-page-recovery`).

## Scope

For illustrated reference pages, art-history surveys, catalogues, museum/corpus
documents — anything where the user asks for 真实资料图片 of actual artworks
(calligraphy, painting, sculpture, manuscripts, bronzes, coins). Wikimedia Commons
is the only realistic free source with museum-grade scans AND usable license
metadata, but its search index mixes originals with later copies, scenery photos,
signage, and digitized books. Naive search produces ~30% wrong matches, and a
wrong image on a reference page is far worse than no image.

## Always-on rules

1. **Authenticity over coverage.** Ship fewer images than keys. A later dynasty's
copy, a competitor's work, or a photo of the mountain instead of the inscription
is a factual error the reader will trust because it sits next to authoritative text.
2. **Use pre-rendered thumbnails, then self-host them compressed.** Request a standard
   width (500/800/1000/1200) and use the returned `thumburl`; full-resolution
   originals hit HTTP 429 within ~20 files, and non-standard widths force on-demand
   rendering, which is what gets throttled. For a published page, download the
   thumbnails into the repo with probe-first + backoff (~1.5 s spacing) and compress
   before committing (macOS `sips --resampleHeightWidthMax 2200 -s format jpeg
   -s formatOptions 80`; ~150 raw scans are 150MB+, ~60MB after) — self-hosting
   immunizes the page against upstream throttling. Never pip-install Pillow inside
   the Hermes venv for this: browser-harness pins pillow==12.3.0 and a mismatched
   reinstall corrupts `_imaging`, breaking the browser tools.
3. **Every image carries attribution.** File page URL + license + artist, rendered
   under the image. Commons requires it and the user's pages are public.
4. **Verify every load-bearing number with a search before publishing.**
   Dimensions, row and character counts, dates, acquisition and donation years,
   and the current holding institution are exactly where model memory fails
   confidently, and they are the claims a knowledgeable reader checks first. One
   web_search per such figure is cheaper than one published error.
5. **Never state a contested attribution as settled.** When a work's authenticity
   is disputed (真迹 vs 摹本 vs 伪), say so in the provenance text and name the
   mainstream position; do not launder a fringe private-collector claim into fact.

## Procedure

1. **Author content first, in era-partitioned Python modules**
   (`content1.py`, `content2.py`, …) exporting lists of era dicts, each with a
   `works` list. Per-work dict: `name, author, date, script/medium, material,
   size, loc (current holder), feat (form/style), eval (later reception), img
   (stable key), star (bool), prov (HTML provenance for starred works)`.
   Splitting by era keeps each file editable and lets a later 补遗 module append
   to existing eras by index without touching the originals.
2. **Give each work a unique `img` key and assert uniqueness** before resolving —
   two works sharing a key silently get the same picture.
3. **Generate matcher rules from the content, not by hand**
   (`gen_strict.py`): derive `must` tokens from the work's own name(s) and
   `allow` from its true author. Hand-writing 170 rule sets is how you miss keys.
   Then review the generated rules for the failure classes in
   `references/matcher-and-failure-classes.md`.
4. **Resolve with `scripts/commons_strict_resolve.py`** (adapt paths/inputs).
   Run it in the background and poll; 170 keys take ~15-25 min at polite rates.
5. **Audit the resolved set before building.** Print `key -> matched title` for
   every key and read it. Mismatches are obvious in a list and invisible in a
   rendered page. Re-audit after any filter change.
6. **Build HTML from the content modules + resolved images**, then verify by DOM
   counts in the browser (`document.querySelectorAll('article.work').length`,
   `.imgbox img` count, `details.prov` count) — not by eyeballing a screenshot.
   Works with no resolved image must render as a clean text card, never a broken
   `<img>`.
7. **Publish** to `~/claudews/zhanglpg.github.io/<project>/` and git push
   (same flow as any static page there).

## Quota, caching, and iteration

- **Cache to a JSON file keyed by `img` key and make the resolver resumable.**
  A run of 170 keys will be interrupted; re-running from zero wastes the quota.
- **When you tighten a filter, re-validate the cache instead of deleting it:**
  replay each cached hit through the new `allowed()` and drop only the ones that
  now fail. Clearing the whole cache to fix ten bad matches costs hundreds of API
  calls. Recipe in `references/matcher-and-failure-classes.md`.
- **Send a real User-Agent** on every Commons request — the API returns 403 to
  the default urllib/python-requests agent.
- **Do not issue probe searches from `execute_code` while the resolver runs.**
  Concurrent requests trip the rate limiter and you will read the resulting empty
  results as "no candidates exist".

## Pitfalls

- **Never put the work's own author in its `ban` list.** Auto-derived rules easily
  ban a name that appears in the legitimate match (`张旭` banned, then every real
  张旭 scroll rejected). `allow` exists for exactly this; check it before adding a ban.
- **A `must` token that is too generic matches the wrong century.** `刻石` alone
  pulls in any stele. Use the full compound name (`泰山刻石`, `秦泰山`) and put the
  confusable siblings in `ban`.
- **Maintain the later-author blocklist as data, not as per-key bans.** Any name
  who could plausibly have copied the work belongs in one global list; a per-key
  ban list always misses the copyist you did not think of.
- **Content edits need real quoting.** Chinese full-width quotes inside
  triple-quoted Python strings terminate the string early; and `patch` on files
  containing `[[wikilinks]]` or heavy nesting fails — write a small `fix.py` that
  does an exact `str.replace` with an `assert s.count(old) == 1` guard.
- **Strip HTML from Commons `Artist` metadata** before rendering it; it arrives as
  `<a href=...>` markup.
- **Report coverage honestly.** Tell the user the resolved/total ratio and that
  unmatched works render as text cards. Do not imply full illustration.
