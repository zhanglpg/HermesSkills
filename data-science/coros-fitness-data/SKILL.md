---
name: coros-fitness-data
description: COROS MCP data pipeline for fitness dashboards.
---

# COROS fitness data pipeline

Fetch, process, and visualize COROS training data. Covers the MCP tools,
FIT file parsing, geographic segment mining, and the data pipeline that
feeds the coros-dashboard on zhanglpg.github.io.

## COROS MCP tools

Configured in `~/.hermes/config.yaml` under `mcp_servers.coros` (OAuth,
`https://mcp.coros.com/mcp`). Requires `sampling.enabled: false` AND
`elicitation.enabled: false` in the config or the Java SDK rejects the
handshake. Token auto-refreshes (30-day access + refresh token).

Key tools:
- `querySportRecords` — activity list (text format, paginated at 100)
- `queryActivityLapData` — per-run 1K splits (JSON, ~3-4 KB each)
- `downloadActivityFitFiles` — full GPS track as FIT binary (single-activity)
- `queryActivityFitFileDownloadUrls` — URL-based FIT download (date-range
  version sometimes returns garbage errors; prefer single-activity)
- `queryFitnessAssessmentOverview` — VO2max, threshold pace, race predictions

## Bulk fetching without context bloat

Call the MCP HTTP endpoint directly and stream results to disk:

```python
import json, urllib.request, os
tok = json.load(open(os.path.expanduser("~/.hermes/mcp-tokens/coros.json")))["access_token"]
payload = {"jsonrpc":"2.0","id":1,"method":"tools/call",
           "params":{"name":"queryActivityLapData","arguments":{"labelId":lid,"sportType":st}}}
req = urllib.request.Request("https://mcp.coros.com/mcp", data=json.dumps(payload).encode(),
    headers={"Authorization":f"Bearer {tok}","Content-Type":"application/json",
             "Accept":"application/json, text/event-stream"})
text = json.loads(urllib.request.urlopen(req,timeout=60).read())["result"]["content"][0]["text"]
```

See `coros-dashboard/fetch_laps.py` for the auto-detect-missing version.
NEVER trust subagent self-reports for file writes — always verify with
`ls | wc -l`. A delegate_task once claimed 46 files written but wrote zero.

**Cron-mode pitfall:** `execute_code` is BLOCKED when running as a cron job
(approvals). Instead use `coros-dashboard/cron_sync.py START END` — it fetches
records via direct MCP HTTP, writes `sync_latest.txt` verbatim, and prints
MISSING_LAPS / MISSING_FITS / NEW_LABEL_IDS as JSON for the next step.
NEW_LABEL_IDS includes non-run sport types (e.g. 402 = strength, no lap
data needed); cross-check SportType before treating them as missing laps.
When `git diff data.js` shows ONLY the `generated` timestamp changed, skip
the commit/push — no meaningful data update.

## FIT file parsing

Use **fitdecode** (not fitparse — fitparse throws "Invalid field size" on
COROS files). Coordinates are in semicircles: `deg = semicircle * 180 / 2^31`.

```python
import fitdecode
with fitdecode.FitReader(path) as fit:
    for frame in fit:
        if isinstance(frame, fitdecode.FitDataMessage) and frame.name == "record":
            lat = frame.get_value("position_lat")  # semicircles
            lon = frame.get_value("position_long")
            # convert: deg = val * 180 / 2**31
```

COROS has a daily FIT download limit. Cache FITs in `raw/fits/` so re-runs
are free. Prioritize the runs you care about.

## Geographic route-segment mining

See `references/geo-segments.md` for the full algorithm and pitfalls.

The user explicitly rejected per-km distance-from-start segments — they want
**geographic** segments: the same physical stretch of trail compared across
efforts. Algorithm: cluster by trailhead → build corridor centerline →
project GPS points → detect natural segments (outbound, return, extension) →
time traversals via s-crossing detection → render on Leaflet maps.

## Data pipeline (coros-dashboard)

```
raw/records/*.txt  ─┐
raw/laps/*.json    ─┼─→ update.py ─→ data.js ─→ index.html (React)
raw/geo_segments.json ─┘     ↑
raw/fits/*.fit ─→ segments.py ─┘
```

- `update.py`: idempotent, dedupes by labelId, generates data.js
- `segments.py`: FIT → geo_segments.json (geographic segment mining)
- `fetch_laps.py`: direct HTTP fetcher for missing lap data
- Cron job `coros-dashboard-sync` (daily 21:00 GMT+8): fetches new records,
  laps, and FITs; runs update.py + segments.py; commits and pushes

## Privacy

`zhanglpg.github.io` is PUBLIC. `coros-dashboard/raw/` (heart rate, GPS
coords, per-run laps, FIT files) is gitignored. Only processed `data.js`
and app code are published.
