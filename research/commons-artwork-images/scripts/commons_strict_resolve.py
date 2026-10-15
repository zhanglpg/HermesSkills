#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Resolve artwork keys to Wikimedia Commons images with strict authenticity filters.

Reads a rules file (list of {k, q[], must[], ban[], allow[], st}) and writes a
resumable JSON cache keyed by k. Successful entries carry ok/title/img(thumb)/
full/page/license/artist/desc/mime/w/h/score; failures carry ok:False, why, and
the top candidate list so the failure is auditable without a re-run.

Adapt PROJ/RULES/CACHE and the width ladder to the project, then run in the
background and poll the cache. Never bulk-download: use the pre-rendered thumburl.

Rules file format (one object per artwork key):
  {"k": "unique_key", "q": ["search phrase", ...], "must": ["name token", ...],
   "ban": ["confusable sibling", ...], "allow": ["author name if it would
   otherwise be caught by LATER_AUTHORS"], "st": true}

IMPORTANT: never put the work's own author in "ban"; auto-generated rules do this
easily and it silently rejects every legitimate match.
"""
import json, os, re, time, urllib.parse, urllib.request

API   = 'https://commons.wikimedia.org/w/api.php'
UA    = {'User-Agent': 'HermesAgent/1.0 (artwork image research)'}
PROJ  = os.environ.get('PROJ', '.')
RULES = os.path.join(PROJ, 'strict.json')
CACHE = os.path.join(PROJ, 'links.json')
WIDTHS = (1200, 1000, 800, 640, 500)   # standard widths only; others force re-render -> 429
SLEEP  = 1.2                            # be polite; raise on 429

RASTER_OK = ('image/jpeg', 'image/png')
THUMBABLE = ('image/tiff', 'application/pdf')
BANNED_MIME = ('image/vnd.djvu',)

HARD_BAD = re.compile(r'(stamp|logo|icon|map\b|chart|diagram|signature|\.svg$|book cover|'
                      r'poster|screenshot|watermark|template|coat of arms|flag|banner|'
                      r'banknote|label strip|label\b|evolution of|script chart|comparison|'
                      r'字体演变|字形演变|演變|字源)', re.I)
SITE_BAD = re.compile(r'(国保碑|景区|scenic|museum interior|building exterior|'
                      r'塑像|雕像|铜像|石像|人像|portrait of|牌坊|山门|gate\b|公园|park|'
                      r'纪念碑|monument|展览馆|山顶|山頂|寺前|寺内|寺外|风景|風景|全景|'
                      r'panoram|peak\b|summit|mountain top|view of|墓|陵|tomb|grave)', re.I)
DOC_BAD = re.compile(r'(奏折|奏摺|信函|致.*函|信札|日记|日記|文話|文话|筆記|笔记|詩話|诗话|'
                     r'詞話|词话|尺牘|書牘|文集|全集|選集|叢刊|史料|研究|考證|考证|釋文|'
                     r'图录|圖錄)', re.I)
BOOK_BAD = re.compile(r'(叢書|丛书|論|论|答問|答问|研究|考證|考证|釋文|释文|字典|词典|'
                      r'目錄|目录|年鑑|年鉴|WZLib|DB-\d)', re.I)
ART_GOOD = re.compile(r'(帖|卷|册|冊|碑|铭|銘|拓|書|书|軸|轴|赋|賦|颂|頌|经|經|记|記|'
                      r'序|稿|诗|詩|文|Tie|Scroll|rubbing|inscription)', re.I)
COPY_HINT = re.compile(r'(摹|臨|临|copy\b|after\b)', re.I)

# Later masters who must never stand in for an earlier work's original.
# Keep as data and extend it here; per-key ban lists always miss a copyist.
LATER_AUTHORS = ('揭傒斯', '莫友芝', '赵之谦', '趙之謙', '吴昌硕', '吳昌碩', '邓石如', '鄧石如',
                 '董其昌', '文徵明', '文征明', '祝允明', '王铎', '王鐸', '傅山', '何绍基', '何紹基',
                 '于右任', '沈尹默', '启功', '林散之', '沙孟海', '俞和', '赵孟頫', '趙孟頫', '鲜于枢',
                 '鮮于樞', '宋克', '杨维桢', '楊維楨', '金农', '金農', '郑板桥', '郑燮', '伊秉绶',
                 '伊秉綬', '刘墉', '劉墉', '康有为', '康有為', '翁同龢', '张瑞图', '張瑞圖', '徐渭',
                 '八大山人', '朱耷', '黄道周', '倪元璐', '陈淳', '陳淳', '秦树声')


def get(url, timeout=30):
    req = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(req, timeout=timeout).read()


def api(params):
    params = dict(params)
    params.setdefault('format', 'json')
    params.setdefault('formatversion', '2')
    for attempt in range(4):
        try:
            return json.loads(get(API + '?' + urllib.parse.urlencode(params)).decode('utf-8', 'ignore'))
        except Exception:
            if attempt == 3:
                return {}
            time.sleep(SLEEP * (3 ** attempt))
    return {}


def search(q, limit=20):
    d = api({'action': 'query', 'list': 'search', 'srnamespace': '6',
             'srlimit': str(limit), 'srsearch': q})
    return [r['title'] for r in d.get('query', {}).get('search', [])]


def imageinfo(titles):
    if not titles:
        return []
    d = api({'action': 'query', 'titles': '|'.join(titles[:20]), 'prop': 'imageinfo',
             'iiprop': 'url|mime|size|extmetadata', 'iiurlwidth': '1000'})
    out = []
    for p in d.get('query', {}).get('pages', []):
        ii = (p.get('imageinfo') or [{}])[0]
        em = ii.get('extmetadata') or {}

        def strip(k):
            v = (em.get(k) or {}).get('value') or ''
            return re.sub(r'<[^>]+>', '', str(v)).strip()

        out.append({'title': p.get('title', ''), 'mime': ii.get('mime', ''),
                    'thumb': ii.get('thumburl') or '', 'full': ii.get('url') or '',
                    'page': ii.get('descriptionurl') or '', 'w': ii.get('width') or 0,
                    'h': ii.get('height') or 0, 'license': strip('LicenseShortName'),
                    'artist': strip('Artist'), 'desc': strip('ImageDescription')[:300]})
    return out


def allowed(f, must, ban, allow_artists=()):
    """Return (ok, reason). Cheapest and most certain rejections first."""
    t = f['title']
    if f['mime'] in BANNED_MIME:
        return False, 'djvu-book'
    if f['mime'] not in RASTER_OK and f['mime'] not in THUMBABLE:
        return False, 'mime'
    if f['mime'] in THUMBABLE and not f.get('thumb'):
        return False, 'no-thumb'
    if f['mime'] == 'application/pdf':
        if BOOK_BAD.search(t):
            return False, 'pdf-book'
        if not ART_GOOD.search(t):
            return False, 'pdf-unknown'
    if HARD_BAD.search(t):
        return False, 'hard-bad'
    if SITE_BAD.search(t):
        return False, 'site-photo'
    if DOC_BAD.search(t):
        return False, 'doc-not-artwork'
    for la in LATER_AUTHORS:
        if la in t and la not in (allow_artists or ()):
            return False, 'later-author:' + la
    if not any(m.lower() in t.lower() for m in must):
        return False, 'no-must'
    for b in (ban or ()):
        if b and b.lower() in t.lower():
            return False, 'ban:' + b
    return True, 'ok'


def score(f, must):
    t, s = f['title'], 0
    tl = t.lower()
    for m in must:
        if m.lower() in tl:
            s += 20
    for pref in ('NPM-', 'SSID-', '故宫', '故宮', '辽宁省博物馆', '遼寧省博物館', 'WUL',
                 'MET ', 'British Museum', 'Boston Museum'):
        if pref in t:
            s += 8
    if re.search(r'(宋拓|明拓|墨拓本|拓本|rubbing)', t):
        s += 6
    if COPY_HINT.search(t):
        s -= 12
    if f['mime'] in RASTER_OK:
        s += 4
    if len(t) > 90:
        s -= 3
    return s


def resolve(rule, cache):
    k = rule['k']
    if k in cache:
        return cache[k]
    must, ban = rule['must'], rule.get('ban') or []
    allow = tuple(rule.get('allow') or ())
    cands, seen = [], set()
    for q in rule.get('q') or []:
        for t in search(q):
            if t not in seen:
                seen.add(t)
                cands.append(t)
        time.sleep(SLEEP)
        if len(cands) >= 40:
            break
    infos = imageinfo(sorted(cands)[:40])
    passed, rejects = [], []
    for f in infos:
        ok, why = allowed(f, must, ban, allow)
        if ok:
            passed.append((score(f, must), f))
        else:
            rejects.append(why)
    if passed:
        passed.sort(key=lambda x: -x[0])
        sc, f = passed[0]
        thumb = f['thumb']
        if not thumb:  # try smaller standard widths before giving up
            for w in WIDTHS:
                d = api({'action': 'query', 'titles': f['title'], 'prop': 'imageinfo',
                         'iiprop': 'url', 'iiurlwidth': str(w)})
                pg = (d.get('query', {}).get('pages') or [{}])[0]
                thumb = (pg.get('imageinfo') or [{}])[0].get('thumburl') or ''
                if thumb:
                    break
                time.sleep(SLEEP)
        rec = {'ok': bool(thumb), 'title': f['title'], 'img': thumb, 'full': f['full'],
               'page': f['page'], 'license': f['license'], 'artist': f['artist'],
               'desc': f['desc'], 'mime': f['mime'], 'w': f['w'], 'h': f['h'], 'score': sc}
        if not thumb:
            rec['why'] = 'no-thumb-at-any-width'
    else:
        rec = {'ok': False, 'why': ','.join(sorted(set(rejects))) or 'no-candidates',
               'cands': [{'title': i['title'], 'mime': i['mime'], 'thumb': i['thumb']}
                         for i in infos[:8]]}
    cache[k] = rec
    json.dump(cache, open(CACHE, 'w'), ensure_ascii=False, indent=1)
    tag = 'OK ' if rec.get('ok') else 'NONE'
    extra = rec.get('title') or rec.get('why', '')
    rej = (' rej=' + str(sorted(set(rejects))[:3])) if not rec.get('ok') else ''
    print(f"[{k}] {tag} {extra[:70]} sc={rec.get('score', '')}{rej}", flush=True)
    return rec


def main():
    rules = json.load(open(RULES))
    try:
        cache = json.load(open(CACHE))
    except FileNotFoundError:
        cache = {}
    todo = [r for r in rules if r['k'] not in cache]
    print(f'rules {len(rules)} cached {len(cache)} todo {len(todo)}', flush=True)
    for r in todo:
        resolve(r, cache)
        time.sleep(SLEEP)
    ok = sum(1 for v in cache.values() if v.get('ok'))
    print(f'DONE ok {ok} / {len(cache)}', flush=True)


if __name__ == '__main__':
    main()
