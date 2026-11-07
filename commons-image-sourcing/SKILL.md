---
name: commons-image-sourcing
description: "Use when sourcing or auditing archival images for a page."
version: 1.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [images, wikimedia-commons, publishing, art-history]
    related_skills: []
---

# Archival imagery for illustrated documents

## When to Use
A document or web page must display REAL archival imagery (museum scans, rubbings,
manuscript photos, artefact photographs) — typically art/calligraphy history, catalogue
or exhibition pages — with correct licensing, version labelling and self-hosting.
This covers both sourcing a new set and auditing one that is already published.

## Standing policy (this user)
- The card image must BE the work: an inscription, a rubbing, a manuscript. A temple,
  a stele standing in a field, a memorial hall, a portrait of the calligrapher, a book
  cover or a product shot is a DEFECT even when the caption names the right work — those
  are the exact complaints that trigger a re-do. Test each image by asking "can I read
  the work in it?", not "does the file mention the work?".
- Key works (重点考据) may carry several images: the card shows the first, the viewer
  swipes through the rest (contract in references/atlas-page-lightbox.md).
- Copies are the norm for ancient works: most pre-Tang works survive only as later
  copies, rubbings or modelbook carvings; a Tang copy of a Jin work is often the best
  surviving version. NEVER reject a candidate merely for being a copy — require only
  that the image's RELATIONSHIP to the work is stated: render a version chip on every
  image (真迹墨迹 / 唐摹本 / 宋拓本 / 拓本·刻帖 / 后世临摹本(具临者名) / 原器影像 / 馆藏扫描).
- No suitable image → show "暂无影像" plus the holding location on the card. Never
  substitute an unrelated image to fill the slot.
- Every image keeps its license name and a link to the source page (hover credit).

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
   in-browser loaded-image count). Stamp every build with a version string rendered in the page
   and verify the LIVE html with a cache buster — Pages serves HTML at `max-age=600`, so a stale
   tab reads as "the site is unchanged" while the deploy is fine (recipe:
   single-file-react-gh-pages → Deploy).

Reusable resolver implementing steps 2–6: `scripts/resolve_commons.py`
(rules.json in, cache.json out, re-runnable).

## Audit pass — run this before publishing, every time
A name-based filter accepts anything whose TITLE contains the work name, so book covers,
study editions and site photos survive it. Audit the finished set visually, not just the
new picks:
1. Build contact sheets from the published `img/` files: PIL grid, 5 columns, ~20 cards per
   sheet, each cell labelled with its key + version chip, then read every sheet with vision.
2. Flag and replace: temple/field/ravine/stele-in-situ with no legible inscription, memorial
   halls, portraits of the calligrapher, book covers and boxed 字帖, an open book with a
   "始" arrow, porcelain/product shots, paintings standing in for calligraphy, rubbings so
   faint they read as blank, and near-blank slivers (see the strip pitfall below).
3. Expect these survivors specifically: an NLC/NDL catalogue cover passes a mime+title
   check because the title carries the work name; 丛书/釋文/圖錄 study editions do too;
   故居 and 纪念馆 photos and encyclopedia portraits arrive from artist-name queries.
4. Replace, rebuild, re-run the same contact-sheet pass. Do not declare done until a full
   pass shows no defect — one pass catches only what you look at.

## When Commons has nothing (Chinese/Japanese museum holdings)
Commons cannot cover works held in PRC/Taiwan/Japan museums — CADAL/NPM book scans flood
the results and no object image exists. Do not conclude "no image"; switch source:
1. Museum official image endpoints first: a TNM collection page
   (`tnm.jp/modules/r_collection/index.php?colid=TB1459&controller=dtl`) embeds
   `uploads/r_collection/LL_<no>.jpg` at 3000 px, clean and correctly identified — far better
   than any aggregator copy. ColBase (`colbase.nich.go.jp/collection_items/tnm/<id>`) and NPM's
   open data cover most Japan/Taiwan-held works.
2. Otherwise harvest Baidu Images: `image.baidu.com/search/index?tn=baiduimage&word=<query>`,
   scroll, then read `img[data-objurl]` (original URL) — not `src`, which is a 500 px proxy.
   Rank by alt-text match + domain, then vision-verify.
3. Reject modern practice sheets (临帖稿: grid paper, correction dots, student handwriting),
   sticker/emoji-decorated reproductions, and article screenshots with title cards; crop
   watermarks only when they sit in the margin.
4. When you must crop one work out of a long scroll (e.g. 黄庭坚's colophon inside 寒食帖),
   download the full Commons file, locate the segment on a downscaled strip, then crop at full
   resolution — that beats any web copy.

## Pitfalls
- A Commons thumbnail at `iiurlwidth=1400` collapses a 20:1 handscroll to 1280×53–210 px:
  blank on the card, unreadable at 1:1 in a viewer. Detect `ar > 6` and re-fetch — but
  Commons caps the SERVED thumb at 3840 px (`thumburl` ends `/3840px-…` while `thumbwidth`
  echoes the 6000/8000 you asked for), so 3840 is the practical ceiling without storing
  originals. Keep the 2200 px file for the card and a separate `img/hi/` copy for the
  viewer rather than shipping one oversized file to every card.
- A Commons file titled …卷/册 is often the WHOLE album — painting, letter, then colophons — so
  its thumbnail reads as a faint landscape and passes any name check. 王珣《伯远帖卷》 is mostly
  董邦达's painting with the 47-character letter as one small panel; open the middle of the file
  at full size before shipping, then crop to the letter or source a separate sheet.
- `const top = document.getElementById('top')` in a classic inline script throws
  `Identifier 'top' has already been declared` (window.top is a non-configurable global)
  and kills the ENTIRE script block — search, nav and lightbox all silently dead while the
  HTML still renders. Rename it (`topBtn`). Diagnose a dead inline script by hooking
  `window.onerror` via `Page.addScriptToEvaluateOnNewDocument` before navigating and reading
  `window.__errs`. `node --check` passes on the identical text — the rejection happens when the
  browser instantiates the script's global bindings, so a syntax check proves nothing.
- Write harvested candidate JSON to your own scratch directory, never `$BH_AGENT_WORKSPACE`:
  the browser workspace can rotate between browser_exec calls and the files vanish mid-task
  (a full re-harvest costs more than the write).
- When counting loaded images on a page, exclude the viewer's own `<img id="lb-img">` — it
  has no src until opened and registers as the one "broken" image.
- On macOS the system python3 (Command Line Tools) ships without a CA bundle, so urllib to
  https dies with CERTIFICATE_VERIFY_FAILED; fetch with `curl -sSL` or run the script under
  the Hermes venv python instead.
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
- The viewer (click-to-zoom, swipe gallery, aspect thresholds) has its own contract in
  references/atlas-page-lightbox.md — read it before touching the lightbox CSS/JS.
