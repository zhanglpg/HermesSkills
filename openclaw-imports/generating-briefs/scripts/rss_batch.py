#!/usr/bin/env python3
"""Batch RSS fetcher for brief generation. Reference skeleton — copy feed URLs from config JSON.
Usage: python3 rss_batch.py
Output: Per-feed summary + JSON to stdout.
"""
import json
import ssl
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

# === CONFIGURE: Copy feeds from config JSON ===
FEEDS = [
    # {"name": "CNBC Top News", "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114"},
    # {"name": "MarketWatch", "url": "http://feeds.marketwatch.com/marketwatch/topstories/"},
    # ... add more from config
]

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

cutoff = datetime.now(timezone.utc) - timedelta(hours=36)
NS_ATOM = "http://www.w3.org/2005/Atom"


def parse_date(text):
    """Try multiple date formats, return timezone-aware datetime or None."""
    if not text:
        return None
    text = text.strip()
    formats = [
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S %Z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S+00:00",
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(text, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    return None


results = []

for feed in FEEDS:
    try:
        req = urllib.request.Request(
            feed["url"], headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            raw = resp.read()

        root = ET.fromstring(raw)

        items = []
        is_atom = root.tag == f"{{{NS_ATOM}}}feed"

        if is_atom:
            for entry in root.findall(f".//{{{NS_ATOM}}}entry"):
                title_el = entry.find(f"{{{NS_ATOM}}}title")
                link_el = entry.find(f"{{{NS_ATOM}}}link")
                updated_el = entry.find(f"{{{NS_ATOM}}}updated")
                summary_el = entry.find(f"{{{NS_ATOM}}}summary")

                title = title_el.text if title_el is not None else ""
                link = link_el.get("href") if link_el is not None else ""
                updated = updated_el.text if updated_el is not None else ""
                summary = summary_el.text if summary_el is not None else ""

                dt = parse_date(updated)

                items.append({
                    "title": title,
                    "link": link,
                    "date": updated,
                    "summary": (summary[:200] if summary else ""),
                    "fresh": dt is not None and dt > cutoff,
                })
        else:
            for item in root.findall(".//item"):
                title_el = item.find("title")
                link_el = item.find("link")
                date_el = item.find("pubDate")
                desc_el = item.find("description")

                title = title_el.text if title_el is not None else ""
                link = link_el.text if link_el is not None else ""
                date_str = date_el.text if date_el is not None else ""
                desc = desc_el.text if desc_el is not None else ""

                dt = parse_date(date_str)

                items.append({
                    "title": title,
                    "link": link,
                    "date": date_str,
                    "summary": (desc[:200] if desc else ""),
                    "fresh": dt is not None and dt > cutoff,
                })

        fresh = [i for i in items if i["fresh"]]
        results.append({
            "name": feed["name"],
            "status": "ok",
            "total": len(items),
            "fresh": len(fresh),
            "items": fresh,
        })
    except Exception as e:
        results.append({
            "name": feed["name"],
            "status": "error",
            "error": str(e)[:150],
        })

# Print final summary
for r in results:
    if r["status"] == "ok":
        print(f"\n{'=' * 60}")
        print(f"SOURCE: {r['name']} — {r['fresh']}/{r['total']} fresh items")
        print(f"{'=' * 60}")
        for item in r["items"][:8]:
            print(f"  [{item.get('date', '?')[:25]}] {item['title']}")
            print(f"    {item['link']}")
            if item.get("summary"):
                s = item["summary"].replace("\n", " ").strip()[:150]
                print(f"    {s}")
    else:
        print(f"\nSOURCE: {r['name']} — ERROR: {r.get('error', 'unknown')[:120]}")

print("\n\n--- JSON OUTPUT ---")
print(json.dumps(results, ensure_ascii=False, default=str))
