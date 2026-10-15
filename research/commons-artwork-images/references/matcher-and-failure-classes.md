# Commons matcher: filter stack and failure classes

## The filter stack (apply in this order)

`search(query) -> candidates -> allowed(candidate) -> score -> pick best`

A candidate is rejected at the first filter it fails; log the reason per key so
failures are diagnosable from the log alone rather than requiring a re-run.

| Order | Filter | Rejects | Why |
|---|---|---|---|
| 1 | `BANNED_MIME` | `image/vnd.djvu` | DjVu = digitized book scans from bulk projects. A page of a monograph about the work is never the work. |
| 2 | mime whitelist | anything not jpeg/png/tiff/pdf | SVG, audio, video, 3D |
| 3 | thumb availability | tiff/pdf with no `thumburl` | cannot be rendered at all |
| 4 | `HARD_BAD` | stamp, logo, icon, map, chart, diagram, signature, book cover, poster, screenshot, watermark, coat of arms, flag, banknote, label strip, script-evolution figures | non-artwork graphics that score well on keywords |
| 5 | `SITE_BAD` | scenic, museum interior/exterior, statue, portrait-of-person, gate, park, monument, panorama, peak, summit, "view of", tomb, grave, plus CJK equivalents (景区/风景/全景/山顶/寺前/寺内/塑像/雕像/纪念碑/墓/陵/国保碑) | the place where the work lives, not the work. Dominant failure for steles and cliff inscriptions: searching an inscription name returns the mountain. |
| 6 | `DOC_BAD` | 奏折/奏摺, 信函/致X函/信札, 日记, 文话/笔记/诗话/词话, 尺牍, 文集/全集/选集/丛刊, 史料, 研究/考证/释文/图录 | a document that merely contains the queried title. A row-count in a title (十三行) matches unrelated memorials; a two-character work name matches book titles. |
| 7 | `LATER_AUTHORS` minus the key's `allow` | named later masters appearing in the title | a later copyist's version standing in for the original — the single most common substitution error |
| 8 | `must` token present | no core name token | the catch-all; a work whose name never appears in the title is not that work |
| 9 | `ban` tokens | confusable siblings | near-homonym steles (石门颂 vs 石门铭), or an institutional survey series |
| 10 | PDF-only extra gate | `BOOK_BAD` unless `ART_GOOD` matches | PDFs are legitimate for 帖/碑/拓 scans but overwhelmingly books |

`ART_GOOD` (帖|卷|册|碑|铭|拓|书|轴|赋|颂|经|记|序|稿|诗|文|Tie|Scroll|rubbing|inscription)
is a positive signal used to admit PDFs, not as a gate on rasters.

## Scoring

Score rather than taking the first passing match. Working signals:

- exact full-name token present: large bonus
- institution prefix in filename (NPM-, SSID-, 故宫, 臺北故宮, 辽宁省博物馆, WUL,
  MET, British Museum): bonus — these are catalogued scans, not user uploads
- 拓/rubbing/墨拓本/宋拓/明拓: bonus for stele works
- 摹/臨/临/copy/after: penalty, but keep when it is the only extant version —
  handle those via `allow`, never via a blanket copy ban
- very long titles: mild penalty (compound and derivative files)
- prefer jpeg/png over pdf/tiff at equal score

## Failure classes

1. **Copyist substitution** — a later master's 临/摹 version wins because the
   original is not on Commons. Mitigate with `LATER_AUTHORS` plus per-key `ban`.
   When no original exists, prefer a clearly-labelled copy and say so in the
   caption and provenance text; never caption a copy as the original.
2. **Place-for-object** — steles and cliff carvings return the mountain, temple,
   or heritage-marker stele. `SITE_BAD` handles it; expect genuinely zero matches
   for some inscriptions and ship a text card instead.
3. **Homonym documents** — the title string appears in an unrelated document type.
   `DOC_BAD` handles it.
4. **Charts and comparison plates** — script-evolution and character-origin
   figures match on the script name. Add to `HARD_BAD`.
5. **Self-inflicted ban** — the work's own author sitting in its `ban` list,
   rejecting every legitimate match. Diff `ban` against `author` when generating rules.
6. **Research monographs as djvu/pdf** — bulk digitization projects. Filters 1 and 10.

Some keys will legitimately resolve to nothing. That is the correct outcome, not
a bug to work around; do not relax filters until a real match appears.

## Cache re-validation recipe (tighten filters without re-spending quota)

After editing filters, do NOT delete the cache. Replay it:

```python
import json, sys; sys.path.insert(0, PROJ)
import strict as S          # module exposing allowed()
rules = {it['k']: it for it in json.load(open(f'{PROJ}/strict.json'))}
cache = json.load(open(f'{PROJ}/links.json'))
for k, v in list(cache.items()):
    it = rules.get(k)
    if not v.get('ok') or not it:
        del cache[k]; continue
    fake = {'title': v['title'], 'mime': v.get('mime') or 'image/jpeg',
            'thumb': v.get('img'), 'url': v.get('full'),
            'w': v.get('w') or 1000, 'h': v.get('h') or 1000,
            'license': v.get('license'), 'desc': v.get('desc')}
    ok, why = S.allowed(fake, it['must'], it.get('ban') or [], it.get('allow') or ())
    if not ok:
        del cache[k]
json.dump(cache, open(f'{PROJ}/links.json', 'w'), ensure_ascii=False, indent=1)
```

The reconstructed dict must carry every field `allowed()` reads, or the replay
silently passes everything. Store `mime`, `title`, thumb URL, full URL, `license`,
and `desc` in each cache entry so replay is possible at all.

Print the cleared/kept counts and the list of cleared keys — an unexpected
cleared key usually means the new filter is over-broad.

## API shape

```
https://commons.wikimedia.org/w/api.php
  ?action=query&list=search&srnamespace=6&srlimit=20&srsearch=<q>&format=json&formatversion=2
```

Namespace 6 = File. Then `action=query&titles=File:...&prop=imageinfo` with
`iiprop=url|mime|size|extmetadata&iiurlwidth=1000` for `thumburl`, `mime`, and
license/artist out of `extmetadata`. `formatversion=2` returns plain strings
instead of `*`-keyed dicts. Every request needs a descriptive `User-Agent`; the
bare default agent gets 403.

`extmetadata` values are HTML fragments — strip tags before rendering.
