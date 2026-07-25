#!/usr/bin/env python3
"""Batch fetch all RSS/Atom feeds in parallel. Reads feed list from stdin or config.
Run: python3 scripts/rss_batch.py                              (uses default feeds)
Or:   echo '[{"name":"X","url":"..."}]' | python3 scripts/rss_batch.py  (custom feeds)
Or:   cat config.json | jq '.rss_sources | map({name:.name, url:.rss})' | python3 scripts/rss_batch.py

IMPORTANT: In background/cron mode, stdin may not be a tty but also may have no valid JSON.
The script handles this gracefully — if stdin JSON parsing fails, it falls back to defaults.
"""
import urllib.request
import ssl
import json
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed


# Default AI tech brief feeds (kept current as of Jun 2026)
DEFAULT_FEEDS = [
    {"name": "Import AI",      "url": "https://jack-clark.net/feed/"},
    {"name": "TLDR AI",        "url": "https://tldr.tech/feed/ai"},
    {"name": "Latent Space",   "url": "https://latentspace.blog/rss"},
    {"name": "The Neuron",     "url": "https://theneuron.beehiiv.com/rss"},
    {"name": "Anthropic",      "url": "https://www.anthropic.com/news?format=rss"},
    {"name": "OpenAI",         "url": "https://openai.com/news/rss"},
    {"name": "Hugging Face",   "url": "https://huggingface.co/blog/feed.xml"},
    {"name": "Simon Willison", "url": "https://simonwillison.net/atom/everything/"},
    # NOTE: Ben's Bites (bensbites.beehiiv.com/rss) and Interconnects (interconnects.ai/rss)
    # both return 404 as of Jun 2026 — removed from defaults. Re-add when URLs are confirmed.
]


def parse_date(date_str):
    """Parse various date formats to timezone-aware datetime."""
    if not date_str:
        return None
    date_str = date_str.strip()
    formats = [
        '%a, %d %b %Y %H:%M:%S %z',     # RFC 2822
        '%Y-%m-%dT%H:%M:%S%z',           # ISO 8601 with tz
        '%Y-%m-%dT%H:%M:%S.%f%z',
        '%Y-%m-%dT%H:%M:%SZ',            # ISO 8601 UTC
        '%Y-%m-%dT%H:%M:%S.%fZ',
        '%Y-%m-%d %H:%M:%S',
        '%a, %d %b %Y %H:%M:%S %Z',
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    return None


def fetch_feed(name, url, cutoff_days=2):
    """Fetch and parse a single RSS/Atom feed.
    
    IMPORTANT: Uses urlopen() directly with context= kwarg, NOT opener.open().
    The build_opener() pattern is incompatible with SSL context passing.
    """
    try:
        gcontext = ssl.SSLContext()
        gcontext.check_hostname = False
        gcontext.verify_mode = ssl.CERT_NONE

        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=15, context=gcontext)
        content = resp.read()

        root = ET.fromstring(content)
        is_atom = root.tag.endswith('}feed') or root.tag == 'feed'
        items = []
        cutoff = datetime.now(timezone.utc) - timedelta(days=cutoff_days)

        if is_atom:
            entries = root.findall('{http://www.w3.org/2005/Atom}entry')
            for entry in entries[:10]:
                title_el = entry.find('{http://www.w3.org/2005/Atom}title')
                link_el = entry.find('{http://www.w3.org/2005/Atom}link')
                updated_el = entry.find('{http://www.w3.org/2005/Atom}updated')
                summary_el = entry.find('{http://www.w3.org/2005/Atom}summary')

                title = title_el.text.strip() if title_el is not None and title_el.text else ""
                link = link_el.get('href', '') if link_el is not None else ""
                updated = parse_date(updated_el.text) if updated_el is not None and updated_el.text else None
                summary = summary_el.text.strip()[:300] if summary_el is not None and summary_el.text else ""

                if updated and updated < cutoff:
                    continue
                items.append({
                    "title": title,
                    "link": link,
                    "date": str(updated),
                    "summary": summary
                })
        else:
            for item in root.findall('.//item')[:10]:
                title = item.findtext('title', '').strip()
                link = item.findtext('link', '').strip()
                pubdate = item.findtext('pubDate', '')
                desc = item.findtext('description', '').strip()[:300]

                dt = parse_date(pubdate) if pubdate else None
                if dt and dt < cutoff:
                    continue
                items.append({
                    "title": title,
                    "link": link,
                    "date": str(dt),
                    "summary": desc
                })

        return {"name": name, "status": "ok", "items": items}
    except Exception as e:
        err = str(e)[:200]
        return {"name": name, "status": "error", "error": err, "items": []}


def load_feeds():
    """Load feeds from stdin JSON, falling back to defaults on any parse error.
    
    Handles both 'url' and 'rss' keys in feed dicts (config.ai-tech.json uses 'rss').
    """
    if not sys.stdin.isatty():
        try:
            raw = sys.stdin.read()
            if raw.strip():
                feeds = json.loads(raw)
                # Normalize key: config uses 'rss', script uses 'url'
                for f in feeds:
                    if 'url' not in f and 'rss' in f:
                        f['url'] = f['rss']
                return feeds
        except (json.JSONDecodeError, ValueError, TypeError):
            pass  # Fall through to defaults
    return DEFAULT_FEEDS


if __name__ == '__main__':
    feeds = load_feeds()
    results = {}
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(fetch_feed, f["name"], f["url"]): f["name"] for f in feeds}
        for future in as_completed(futures):
            result = future.result()
            results[result["name"]] = result

    print(json.dumps(results, indent=2))
