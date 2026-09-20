# China flight schedule research — FlightConnections recipe + dead ends

Verified 2026-08-28 on the HET→HGH (呼和浩特→杭州) and UCB→HGH (乌兰察布→杭州) routes.

## Why not the obvious sources
- **ctrip schedule pages** (`flights.ctrip.com/schedule/<dep>.<arr>.html`): return HTTP 200 but zero flight data in static HTML — the schedule loads via JS. `searchConditionVO` JSON is embedded but empty of flights.
- **UMETRIP** (`umetrip.com/mskyweb/fs/fc.do?dep=...&arr=...&flightDate=...`): 403 even with browser UA + Referer.
- **Trip.com REST APIs** (`/restapi/soa2/...`, guessed schedule endpoints): 403/404.
- **Qunar mobile flightlist**: 200 with ~600KB HTML but no parseable flight JSON without a JS session.
- **Airport/本地宝 season-timetable articles** (e.g. tencent news "XX机场夏航季时刻表"): the actual tables are IMAGES (`inews.gtimg.com/om_bt/...`). Vision analysis of those images is possible but can time out; treat as last resort.
Don't spend many calls probing these — go straight to FlightConnections.

## FlightConnections: what you get
Route page: `https://www.flightconnections.com/cn/%E4%BB%8E-<dep>-飞往-<arr>-的航班` (URL-encode; verified working with curl, plain UA, 200, ~170KB). English form: `/flights-from-het-to-hgh`.

Server-rendered facts in the visible text:
- Existence: "目前,从X到Y的 **没有直达航班**" + a connections table (transfer airport, layover duration, carrier per leg) — this is how a missing route is proven.
- Operating airlines (with Chinese/English names), weekly frequency ("每周运营21次，平均每天3架次"), earliest/latest departure, flight duration, cabin classes, aircraft types.
- `last-updated-on` timestamp (`<time itemprop="dateModified" datetime="...">`) — cite this date in advice.
- schema.org JSON-LD with week-by-week event ranges (e.g. 2026-09-04 to 2026-09-11).

## Extracting the schedule grid
The grid rows are in the raw HTML. Parse WITHOUT stripping `<script>`/structure:

```python
import re
t = open('page.html', encoding='utf-8', errors='ignore').read()
rows = re.findall(
    r'data-dates="([^"]+)"\s+data-airline="([^"]+)"[^>]*>'
    r'.*?<p>(\d\d:\d\d)</p>\s*</li>\s*<li[^>]*>\s*<p>(\d\d:\d\d)</p>',
    t, re.S)
# rows: (day-of-month list, airline IATA, dep HH:MM, arr HH:MM)
names = {'MF':'厦航','CA':'国航','SC':'山航','CZ':'南航','MU':'东航',
         'HU':'海航','GS':'天津航','NS':'河北航','9C':'春秋','G5':'华夏'}
```

- `data-dates` = comma-separated days of month the flight runs in the displayed month; a full 1–31 list means daily.
- Airline codes: `data-airline="CA|MF|SC|..."`; carrier names appear in nearby `<img ... title="Xiamen Airlines">`.
- Splitting on `<ul class="schedule-table-row` and scanning each block's first ~1200 chars also works.

## Critical caveats
1. **Grid = displayed month only.** `?month=2026-09` / `?date=...` query params are IGNORED server-side (same 183KB page returned, verified). Month switching is client-side JS. So for a trip date in a future month, you're extrapolating: report flights "as of the current schedule" and tell the user to confirm in a booking app before purchase.
2. **Never present grid data as a bookable seat.** It's a schedule snapshot; Chinese regional routes change weekly and some rows only run on listed days-of-month.
3. OTA "direct flight" cards can be stale placeholders — require two independent sources (FlightConnections + one more) before asserting a route exists.

## UCB (乌兰察布集宁) facts captured 2026-08-28
- No route to Hangzhou (confirmed on FlightConnections; old 2022 "开通杭州航线" news is stale — route suspended).
- ~2 routes / 4 cities total (typical connections to HGH: via 石家庄/郑州/武汉/西安/赤峰, one stop).
- Nearest major airport: 呼和浩特白塔 (HET), ~110km from 集宁; 呼和浩特↔乌兰察布 high-speed rail ~40 min as a fallback connector.
