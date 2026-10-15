#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Strict Wikimedia Commons image resolver for illustrated documents.

Usage: python3 resolve_commons.py rules.json cache.json
rules.json: [{"k": key, "q": [queries], "must": [tokens], "ban": [confusable-work
            tokens only], "allow": [author names], "st": is_stele_bool}]
cache.json: {key: {ok, title, img, full, page, w, h, mime, license, artist, desc, ver}}
            Re-runnable: entries with ok=true are skipped. When rules change, delete
            only the entries that now fail (re-validate with allowed()) to save quota.
"""
import json, os, re, sys, time, urllib.parse, urllib.request

UA = {'User-Agent': 'HermesAgent/1.0 (illustrated document research; educational)'}
THUMB_W = 1000
RASTER_OK = ('image/jpeg', 'image/png')
THUMBABLE = ('image/tiff', 'application/pdf')
BANNED_MIME = ('image/vnd.djvu',)          # CADAL digitized books, never the artwork
HARD_BAD = re.compile(r'(stamp|logo|icon|map\b|chart|diagram|signature|\.svg$|book cover|'
                      r'poster|screenshot|watermark|template|coin|banknote|evolution of|'
                      r'印章|钤印|seal\b)', re.I)
SITE_BAD = re.compile(r'(scenic|museum interior|building exterior|statue|portrait of|'
                      r'park|monument|summit|mountain top|view of|tomb|grave|风景|全景)', re.I)
BOOK_BAD = re.compile(r'(叢書|丛书|論|论|研究|考證|释文|釋文|字典|目錄|WZLib)', re.I)
DOC_BAD = re.compile(r'(奏折|信函|日记|詩話|诗话|筆記|文集|全集|選集|史料)', re.I)
ART_GOOD = re.compile(r'(帖|卷|册|冊|碑|铭|銘|拓|書|书|軸|轴|赋|颂|经|记|序|稿|诗|文|'
                      r'Tie|Scroll|rubbing|inscription)', re.I)
COPY_TANG = re.compile(r'(唐摹|響拓|响拓|馮承素|冯承素|虞摹|褚摹|神龍本|神龙本)')
COPY_SONG = re.compile(r'(宋拓|宋摹|淳化|大觀|大观|叢帖|刻帖|法帖)')
COPY_LATE = re.compile(r'(摹本|臨本|临本|臨|临|仿|copy of|after )')
RUBBING = re.compile(r'(拓本|拓片|墨拓|舊拓|旧拓|rubbing)')
INST = re.compile(r'(NPM-|NDL\d|SSID-|WUL-|CADAL|NLC\d)')


def clean_url(u):
    sp = urllib.parse.urlsplit(u or '')
    return urllib.parse.urlunsplit((sp.scheme, sp.netloc, sp.path, '', ''))


def api(params, retries=4):
    params = dict(params, format='json')
    url = 'https://commons.wikimedia.org/w/api.php?' + urllib.parse.urlencode(params)
    for a in range(retries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=50) as r:
                return json.load(r)
        except Exception as ex:
            if a == retries - 1:
                return {'_error': str(ex)}
            time.sleep(12 + a * 8 if getattr(ex, 'code', None) == 429 else 3 + a * 3)


def search(q, limit=12):
    d = api({'action': 'query', 'generator': 'search', 'gsrsearch': q, 'gsrlimit': limit,
             'gsrnamespace': 6, 'prop': 'imageinfo', 'iiprop': 'url|size|mime|extmetadata',
             'iiurlwidth': THUMB_W})
    out = []
    for p in (d.get('query', {}).get('pages', {}) or {}).values():
        ii = (p.get('imageinfo') or [{}])[0]
        if not ii or not ii.get('url'):
            continue
        em = ii.get('extmetadata', {}) or {}
        def strip(v):
            return re.sub(r'<[^>]+>', '', (em.get(v, {}) or {}).get('value', '')).strip()
        out.append({'title': p.get('title', ''), 'url': clean_url(ii.get('url')),
                    'thumb': clean_url(ii.get('thumburl')), 'w': ii.get('width') or 0,
                    'h': ii.get('height') or 0, 'mime': ii.get('mime', ''),
                    'license': strip('LicenseShortName'), 'artist': strip('Artist')[:180],
                    'desc': strip('ImageDescription')[:400],
                    'page': 'https://commons.wikimedia.org/wiki/' +
                            urllib.parse.quote(p.get('title', '').replace(' ', '_'))})
    return out


def allowed(f, must, ban, allow):
    t = f['title']
    if f['mime'] in BANNED_MIME:
        return False, 'djvu-book'
    if f['mime'] not in RASTER_OK and f['mime'] not in THUMBABLE:
        return False, 'mime'
    if f['mime'] in THUMBABLE and not f['thumb']:
        return False, 'no-thumb'
    if f['mime'] == 'application/pdf' and (BOOK_BAD.search(t) or not ART_GOOD.search(t)):
        return False, 'pdf-book'
    if HARD_BAD.search(t) or SITE_BAD.search(t):
        return False, 'not-artwork'
    if f['w'] * f['h'] < 120_000:
        return False, 'too-small'
    if not any(m.lower() in t.lower() for m in must):
        return False, 'no-must'
    if DOC_BAD.search(t):
        return False, 'doc-not-artwork'
    for b in ban:                      # confusable works ONLY — never artist names
        if b.lower() in t.lower() and b not in allow:
            return False, f'ban:{b}'
    return True, 'ok'


def quality(f, must, is_stele):
    t, s = f['title'], 0.0
    s += 10 * sum(1 for m in must if m.lower() in t.lower())
    ar = f['w'] / f['h'] if f['h'] else 0
    if 2.0 <= ar <= 60:
        s += 5
    s += min(f['w'] * f['h'] / 3_000_000, 8)
    s += 3 if f['license'] else 0
    s += 5 if f['mime'] == 'image/tiff' else 0
    s -= 3 if f['mime'] == 'application/pdf' else 0
    if RUBBING.search(t):
        s += 7 if is_stele else 1
    # copies are the norm: rank by authority, never reject
    if COPY_TANG.search(t):
        s += 12
    elif COPY_SONG.search(t):
        s += 8
    elif COPY_LATE.search(t):
        s -= 6
    if INST.search(t):
        s += 3
    return s


def version_tag(title, desc=''):
    text = f'{title} {desc}'
    if COPY_TANG.search(text):
        return '唐摹本'
    if re.search(r'宋摹', text):
        return '宋摹本'
    if re.search(r'宋拓', text):
        return '宋拓本'
    if re.search(r'(明拓|成化|萬曆|万历)', text):
        return '明拓本'
    if re.search(r'清拓', text):
        return '清拓本'
    if COPY_SONG.search(text):
        return '刻帖／拓本'
    if RUBBING.search(text):
        return '拓本'
    if re.search(r'(墨跡|墨迹|真跡|真迹)', text):
        return '墨迹本'
    if COPY_LATE.search(text):
        return '后世临摹本'
    if INST.search(text):
        return '馆藏扫描件'
    return ''


def resolve(item):
    must = item.get('must') or []
    ban = [b for b in (item.get('ban') or []) if b not in (item.get('allow') or [])]
    allow = item.get('allow') or []
    cands, seen = [], set()
    for q in item['q']:
        for c in search(q, 12):
            if c['title'] not in seen:
                seen.add(c['title'])
                cands.append(c)
        time.sleep(0.7)
    ok = sorted(((quality(c, must, item.get('st')), c) for c in cands
                 if allowed(c, must, ban, allow)[0]), key=lambda x: -x[0])
    return ok, cands


def main(rules_p, cache_p):
    cache = json.load(open(cache_p)) if os.path.exists(cache_p) else {}
    for item in json.load(open(rules_p)):
        k = item['k']
        if cache.get(k, {}).get('ok'):
            continue
        ok, cands = resolve(item)
        if ok:
            sc, f = ok[0]
            img = f['thumb'] if (f['mime'] in THUMBABLE or f['w'] > 2600) else f['url']
            cache[k] = {'ok': True, 'score': round(sc, 1), 'title': f['title'], 'img': img,
                        'full': f['url'], 'page': f['page'], 'w': f['w'], 'h': f['h'],
                        'mime': f['mime'], 'license': f['license'], 'artist': f['artist'],
                        'desc': f['desc'], 'ver': version_tag(f['title'], f['desc'])}
            print(f'[{k}] OK {f["title"][:60]}', flush=True)
        else:
            cache[k] = {'ok': False,
                        'cands': [{'title': c['title'], 'mime': c['mime']} for c in cands[:10]]}
            print(f'[{k}] NONE ({len(cands)} cands)', flush=True)
        json.dump(cache, open(cache_p, 'w'), ensure_ascii=False, indent=1)
    print(f'DONE ok={sum(1 for v in cache.values() if v.get("ok"))}/{len(cache)}', flush=True)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
