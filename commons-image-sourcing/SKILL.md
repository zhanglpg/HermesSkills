---
name: commons-image-sourcing
description: "Use when sourcing archival images from Wikimedia Commons."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [images, wikimedia-commons, publishing, art-history]
    related_skills: []
---

# Wikimedia Commons imagery for illustrated documents

## When to Use
A document or web page must display REAL archival imagery (museum scans, rubbings,
manuscript photos, artefact photographs) resolved from Wikimedia Commons — typically
art/calligraphy history, catalogue or exhibition pages — with correct licensing,
version labelling and self-hosting.

For pages/documents that must show REAL archival imagery (museum scans, rubbings,
manuscript photos) — art/calligraphy history, artefact catalogues, exhibition pages.

## Standing policy (this user)
- Copies are the norm for ancient works: most pre-Tang works survive only as later
  copies, rubbings or modelbook carvings; a Tang copy of a Jin work is often the best
  surviving version. NEVER reject a candidate merely for being a copy — require only
  that the image's RELATIONSHIP to the work is stated: render a version chip on every
  image (真迹墨迹 / 唐摹本 / 宋拓本 / 拓本·刻帖 / 后世临摹本(具临者名) / 原器影像 / 馆藏扫描).
- No suitable image → show "暂无影像" plus the holding location on the card. Never
  substitute an unrelated image to fill the slot.
- Every image keeps its Commons license name and a link to the file page (hover credit).

## Procedure
1. Build per-item rules: `must` = core work-name tokens in simplified AND traditional
   AND pinyin/romanized variants; `ban` = confusable-WORK tokens only (see pitfalls);
   `allow` = the true author's name; `st` = is-stele flag.
2. Query the Commons API (`action=query, generator=search, gsrnamespace=6,
   prop=imageinfo, iiprop=url|size|mime|extmetadata, iiurlwidth=1000`) with a
   descriptive User-Agent header — anonymous requests are refused.
3. Filter: reject mime `image/vnd.djvu` and book-like titles (叢書/論/研究/釋文/字典);
   reject site photos, scenery, statues, seals, charts; require a must-token hit;
   reject confusable ban tokens.
4. Score copy-status instead of rejecting it: Tang copy of an earlier work +12,
   Song rubbing/modelbook +8, Ming–Qing facsimile −6, later-hand name −10 (and surface
   the hand's name in the caption). Rubbing bonus for steles; institutional catalogue
   prefix (NPM-, NDL, SSID-, WUL-) +3.
5. Version-tag every accepted image (priority table in references/image-version-policy.md)
   and render it as a chip over the image; add a page-level note stating the copy norm.
6. Cache resolutions in JSON keyed by item; re-runs skip OK entries. When rules change,
   re-validate cached OK entries against the new filters and clear ONLY the ones that
   now fail — never wipe the cache and re-spend API quota.
7. Vision-verify (vision_analyze) every hand-picked file whose name is English or
   pinyin before publishing — the name alone does not prove content.
8. Self-host: download accepted thumbnails into the repo `img/` and rewrite to relative
   paths; probe one URL with backoff first (429 = IP throttle). Keep the remote Commons
   URL as the attribution link.
   - Compress BEFORE committing: museum scans arrive as 10-15MB PNGs and ~150 raw
     files exceed 150MB, bloating the git repo. On macOS use
     `sips --resampleHeightWidthMax 2200 -s format jpeg -s formatOptions 80 in --out out.jpg`
     per file (~150 images: 153MB → 58MB, visually sufficient), then normalize the
     cached img paths to the final extension (png→jpg) and rebuild the page.
   - Do not pip-install Pillow for this inside the Hermes venv: browser-harness pins
     `pillow==12.3.0`, and force-reinstalling a different version corrupts the
     `_imaging` extension and breaks the browser tools. Use sips, or a separate venv.
9. Hand the page to the publishing workflow (this user: single-file HTML under
   `~/claudews/zhanglpg.github.io/<slug>/`, homepage card, git push; verify curl 200 and
   in-browser loaded-image count).

Reusable resolver implementing steps 2–6: `scripts/resolve_commons.py`
(rules.json in, cache.json out, re-runnable).

## Pitfalls
- Never ban artist names globally: a global artist ban rejects a work's OWN author
  (a 張旭 piece was killed by ban token 張旭). Per-work ban lists hold confusable works
  only (石門頌 vs 石門銘; 散氏盤 vs 吳昌碩臨散氏盤). Later hands = score penalty plus a named
  caption, not rejection.
- Commons search AND-matches every query token: "前后赤壁赋" misses a file named
  "赤壁赋". Query author + core name; add pinyin must-tokens — many scans live under
  pinyin filenames (NongfangShitie.jpg = 秾芳诗帖).
- When book scans flood a result set, re-query with `filetype:bitmap` in gsrsearch to
  keep djvu/PDF out of the candidate pool.
- 429 from upload.wikimedia.org is IP throttling from your own dense API traffic, not a
  dead link — never mark a URL broken on 429. Space requests ~1.5 s, retry with backoff,
  probe one URL before any bulk download. Do not audit links with a loop of HEAD
  requests either — HEAD is throttled the same way, and a batch audit turns every valid
  URL into a 429; verify on the published page in a browser instead.
- Nested triple-quoted strings inside execute_code cells are syntax errors; write patch
  scripts to a file and run them instead.
- Lazy-loaded images: count `naturalWidth>0` only after scrolling the whole page; a
  subset failing means throttling, all failing means broken src.
