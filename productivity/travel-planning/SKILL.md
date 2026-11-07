---
name: travel-planning
description: "Use when planning trips: flights, closures, itineraries."
version: 1.1.0
author: Hermes Agent
license: MIT
tags:
  - travel
  - itinerary
  - flights
  - hiking
---

# Travel Planning & Itinerary Feasibility

## When to Use
- User asks to plan a multi-day trip, recommend routes for a destination, or check whether an itinerary fits around a flight/train ("顺路吗？来得及吗？" style questions).
- Checking flight options from secondary/regional airports (esp. China).

## Step 0 — Operating window and legality gate (do this first)

Transport feasibility is worthless if the objective is shut. For any summit, national park, seasonal toll road, or ticketed scenic area, open the **operator's own site** before sequencing days and answer four questions:

- **Can the traveller enter the country at all?** Entry rules are passport-specific and outrank every other gate. Mainland Chinese residents cannot travel to Taiwan for tourism island-wide (individual travel suspended since 2019; since April 2026 only Fujian and Shanghai residents, and only to Kinmen–Matsu), while a US passport uses Taiwan's foreign-national channel. Confirm nationality before researching routes — a perfect route behind an impossible visa is worthless. Taiwan permit mechanics: `references/taiwan-hiking-permits.md`.

- **What are this year's opening and closing dates?** Not "usually" — the current year's published dates.
- **Is the closure advisory or statutory?** "Not recommended" and "prohibited by law, penalty X" are completely different products. Quote the rule and the penalty.
- **What closes with it?** Huts, rescue stations, toilets, water, trail maintenance, signage, cell coverage, and the access road usually close as a set. A still-open lower section does not make the summit reachable.

If the objective is closed on the requested dates, lead with that fact in the first paragraph, then offer exactly two constructive paths: **keep the dates and swap the objective** for something nearby of comparable difficulty (give route stats and a hard turn-around time), or **keep the objective and move the dates** into the legal window (give the booking lead time). Never hand over a "how to do it anyway" itinerary, and never bury a closure under logistics. Depth and a worked example: `references/seasonal-and-legal-gates.md`.

## Core workflow: anchor-first feasibility
1. **Anchor the hard constraint first — and check the RETURN leg's departure time, not just its existence.** The return flight/train dictates everything. Before any itinerary talk, verify the route exists from that airport/station (Step A / A2). Old "route opened" news is frequently stale — routes get suspended within a season or two.
   From a remote/small station there may be exactly ONE direct train back and it may be an early-morning departure, which silently destroys the last day of the trip. Enumerate transfer hubs (provincial capital, or the nearest major station on the trunk line) before committing, and price the last day in hours: "the only direct train leaves 08:22 → 6:00 wake-up, no Sunday activity" vs "transfer via hub, 15:00 out → free morning". Present both and let the user choose; never quietly pick the one that wastes a day.
2. **Map the geometry.** For each candidate stop, fix direction + distance + drive time from the base town. Stops on opposite sides of the base cannot share a day. Decide ordering: the **rigid/full-day** activity goes on the free day; the **elastic/shortenable** activity goes on the constrained (flight) day, in the morning.
3. **Back-calculate with hard deadlines.** From departure time subtract: airport buffer (domestic: arrive ~90 min early, check-in cutoff ~45 min), drive time to airport, car-return time if rented. Whatever remains is the on-site window — state it as a hard departure time ("11:00 硬性发车"), not a suggestion.
4. **Give a per-flight decision table** instead of prose: candidate departure times → ✅ safe / ⚠️ compressed (state the squeeze) / ❌ not viable. Recommend one flight, then ask the user to confirm the real bookable option.
5. **Overnight placement.** The night before a tight morning must be at the base nearest the morning stop — never on the far side of it. Quantify the penalty ("staying in X adds ~2h backtracking and kills the morning").
6. **Logistics sweep:** one-way car rental between airports (异地还车), fuel/water/supplies (remote areas have none — state it), signal coverage, and venue entry rules that changed recently (see Step B — for Chinese scenic areas the ticket gate, not the trail, is usually the binding constraint).

## This user's standing trip preferences
- **Do not pad hiking time.** The team is strong; use upper-bound pace assumptions and put the hard variant first, with the easier one as fallback. Conservative estimates read as distrust of their fitness.
- **Hotels: comfort and safety first.** For the night before a hard hike, prefer a branded chain (锦江/亚朵-class) over 民宿 — consistent service, secure access, and a dryer/laundry matters after a long day. Check breakfast, parking, and walking distance to dinner.
- **Fill spare time with local food and nearby sights.** Always include a food list (name the dishes, not just "try local cuisine") and 2–4 low-effort nearby spots slotted into the return-day morning — villages, ancient towns, hot springs, tea/theme towns — ranked by proximity to the route back.
- **End with an action list ordered by urgency,** with dated deadlines for anything time-sensitive (ticket release, train pre-sale window).
## Step A: Flight schedule research (regional airports)
Booking-site APIs (ctrip/umetrip/qunar/trip.com/variflight) are JS-rendered or anti-bot-walled from curl — don't burn many calls probing them. The reliable server-rendered source is **FlightConnections**:

- Route page URL pattern: prefer the **English slug** `https://www.flightconnections.com/flights-from-<dep>-to-<arr>` (e.g. `-hgh-to-kwe`). The Chinese `/cn/从-X-飞往-Y-的航班` form 404s for many city pairs — go straight to English. English slugs also work for the map page.
- The page states plainly whether the route exists ("目前...没有直达航班" + connection options), airlines serving it, weekly frequency, earliest/latest departure, flight duration, and a `last-updated-on` timestamp — quote that date when advising.
- The monthly schedule grid IS in the raw HTML even though it looks client-rendered. Parse with regex on the UNSTRIPPED page — see `references/china-flight-data.md` for the exact recipe.
- **Caveats:** the grid covers only the currently displayed month; `?month=`/`?date=` query params do NOT change the served HTML (month switching is client-side), so day-lists in `data-dates` apply to that month. For a specific future date, present the pattern with caveats and tell the user to confirm in a booking app before buying. Never present this data as a confirmed bookable seat.
- **Nonstop frequency is weekday-specific — query the actual travel date, not just the route page.** A route can run Fri/Mon but not Sunday; the grid's `data-dates` shows operating days, and a dated Google Flights query (`q=Nonstop flights from X to Y on YYYY-MM-DD`) confirms whether the return date really has a nonstop.
- **No nonstop on the return date? Enumerate alternate arrival airports** within ~2h ground transfer (NRT→NGB/PVG instead of HGH, then HSR) and put arrival-home time in the decision table — a cheap morning flight to a secondary airport often beats a 1-stop connection that lands at midnight.
- **Never state a flight number you have not seen in a source.** Route + airline + times is a complete, verifiable statement; an invented number reads authoritative and is wrong. The FlightConnections grid carries the numbers when you need them.
- Route absent? Rank fallbacks by effort: (a) drive/train to the provincial capital airport, (b) high-speed rail to a major hub, (c) one-stop connection from the regional airport (connection risk is the user's — flag it).

## Step A2: Rail schedule research (China)
For domestic trips, rail usually beats flying — and the binding question is how FEW direct trains exist, not how many. See `references/china-rail-data.md` for the source list and recipe.

Cheapest first move: `web_search "<from> <to> 高铁 时刻表 车次"` and read the **search-result snippets** — OTA pages are JS-walled in the browser, but their server-rendered snippet text carries exact 车次/发车/到达/历时/票价 plus transfer options. Then cross-check against a server-rendered timetable site before asserting a time.
Snippet text concatenates rows of ADJACENT trains, so a dep/arr pair can sit next to the wrong 车次 (an "evening-departure, dawn-arrival sleeper" fragment once belonged to a different train than the number printed beside it). Confirm train identity — number AND both endpoint times AND the via-stops shape — on a full stop-list timetable page before naming a train in the itinerary or building a morning around its arrival.

## Step B: Chinese scenic-area entry constraints (5A / 景区)
Pull these from the scenic area's OWN official site or 公众号 (购票须知 / 景区公告) — third-party guide articles and SEO pages routinely carry a different, wrong pre-sale window. When sources conflict, quote the official text verbatim and flag the conflict.

Must be resolved BEFORE sequencing days:
- **Pre-sale window + daily release time.** Official rule may be only a few days ahead with a fixed early-morning release, while guides say a week. Give the user the exact date-and-time to start refreshing, and the official customer-service number to confirm.
- **Hard cut-off times.** Last entry, plus separate bans on ascending vs descending after a given hour. These are red lines in the itinerary ("must be on the descent by 14:30"), never suggestions — they can invalidate an otherwise feasible route outright.
- **On-site queue-ticketed summits.** Narrow iconic peaks are often NOT bookable online: you scan a QR after entering and get a called number. Peak-season waits reach 1–2h, so make it the first thing done after entry, count it as rigid added time, and build a fallback (cable car down) for when the call slips past the descent cut-off.
- **Multiple gates with non-interchangeable tickets.** East/west gates can be tens of km apart and require separate tickets; a traverse ("up one side, down the other") may or may not be purchasable. Phone the service line to confirm — official 攻略 and the booking page can contradict each other.
- **Ticket ≠ all-in.** Gate ticket, shuttle bus, and cable car are usually three separate charges; total the real per-person cost rather than quoting the headline ticket price.

## Deliverable: standalone HTML itinerary
When the user asks for the plan as a document rather than chat text, build one self-contained `.html` (inline CSS, no external assets, `prefers-color-scheme`, `@media print`), save it to the Desktop, and send it as a file. Put the blocking fact in a coloured box in the first screen, not in a footnote.

Verify before delivering: tag-balance counts for `table/tr/td/div/ol/li`, a real browser render with a screenshot of the top and one mid-page section (tables and timelines break quietly), and a scan for traditional-character contamination when Chinese body text carries Japanese proper nouns — 稜/續/個/時 slip in from copied source names and read as sloppy.

## Pitfalls
- Don't build an itinerary around a flight or train you haven't verified exists — check route existence BEFORE sequencing days. A whole morning-hike plan collapsed because the assumed airport had no route to the destination city.
- Outbound and return availability are asymmetric on remote routes: verify BOTH directions separately. A comfortable afternoon departure out can pair with a 08:22-only return, and the return is what costs you a day.
- Secondary airports often have 2–4 routes total; a plausible-looking city pair may simply have no service. Same for small rail stations — one direct train a day is common.
- Flight day + activity on the same side as the airport is fine; opposite direction is a trap.
- "直飞" results on OTA aggregator pages are sometimes stale placeholder data — cross-check against at least two independent sources.
- Third-party travel-guide articles are unreliable on ticket pre-sale windows and opening hours — they are frequently AI-generated and self-contradictory (some even carry a "本文由AI生成" footer). Use them for route shape and local colour; use official sources for anything that gates entry.
- **Match rental-car counter hours to the actual arrival time, not the scheduled landing.** Wheels-down 19:00 + 40–50 min immigration puts you at the desk after a 20:00 close; pick the earlier flight or book after-hours pickup. Compute last buses, last trains, and rental desks from wheels-down, never from the timetable's arrival.

## Related skills
- `maps` — geocoding, distances, driving times (use it instead of guessing km).
- `find-nearby` — POI searches at the destination.
