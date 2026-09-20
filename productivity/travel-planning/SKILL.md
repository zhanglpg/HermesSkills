---
name: travel-planning
description: "Multi-stop trip feasibility + flight schedule research."
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

## Core workflow: anchor-first feasibility
1. **Anchor the hard constraint first.** The return flight/train dictates everything. Before any itinerary talk, verify the route actually exists from that airport (Step A). Old "route opened" news is frequently stale — routes get suspended within a season or two.
2. **Map the geometry.** For each candidate stop, fix direction + distance + drive time from the base town. Stops on opposite sides of the base cannot share a day. Decide ordering: the **rigid/full-day** activity goes on the free day; the **elastic/shortenable** activity goes on the constrained (flight) day, in the morning.
3. **Back-calculate with hard deadlines.** From departure time subtract: airport buffer (domestic: arrive ~90 min early, check-in cutoff ~45 min), drive time to airport, car-return time if rented. Whatever remains is the on-site window — state it as a hard departure time ("11:00 硬性发车"), not a suggestion.
4. **Give a per-flight decision table** instead of prose: candidate departure times → ✅ safe / ⚠️ compressed (state the squeeze) / ❌ not viable. Recommend one flight, then ask the user to confirm the real bookable option.
5. **Overnight placement.** The night before a tight morning must be at the base nearest the morning stop — never on the far side of it. Quantify the penalty ("staying in X adds ~2h backtracking and kills the morning").
6. **Logistics sweep:** one-way car rental between airports (异地还车), fuel/water/supplies (remote areas have none — state it), signal coverage, and venue entry rules that changed recently (scenic areas in China adjust gate/shuttle policies; tell the user to verify day-of).

## Step A: Flight schedule research (regional airports)
Booking-site APIs (ctrip/umetrip/qunar/trip.com/variflight) are JS-rendered or anti-bot-walled from curl — don't burn many calls probing them. The reliable server-rendered source is **FlightConnections**:

- Route page URL pattern: `https://www.flightconnections.com/cn/%E4%BB%8E-<dep>-飞往-<arr>-的航班` (URL-encode; e.g. het→hgh, ucb→hgh). English slugs also work: `/flights-from-het-to-hgh`.
- The page states plainly whether the route exists ("目前...没有直达航班" + connection options), airlines serving it, weekly frequency, earliest/latest departure, flight duration, and a `last-updated-on` timestamp — quote that date when advising.
- The monthly schedule grid IS in the raw HTML even though it looks client-rendered. Parse with regex on the UNSTRIPPED page — see `references/china-flight-data.md` for the exact recipe.
- **Caveats:** the grid covers only the currently displayed month; `?month=`/`?date=` query params do NOT change the served HTML (month switching is client-side), so day-lists in `data-dates` apply to that month. For a specific future date, present the pattern with caveats and tell the user to confirm in a booking app before buying. Never present this data as a confirmed bookable seat.
- Route absent? Rank fallbacks by effort: (a) drive/train to the provincial capital airport, (b) high-speed rail to a major hub, (c) one-stop connection from the regional airport (connection risk is the user's — flag it).

## Pitfalls
- Don't build an itinerary around a flight you haven't verified exists — check route existence BEFORE sequencing days. A whole morning-hike plan collapsed because the assumed airport had no route to the destination city.
- Secondary airports often have 2–4 routes total; a plausible-looking city pair may simply have no service.
- Flight day + activity on the same side as the airport is fine; opposite direction is a trap.
- "直飞" results on OTA aggregator pages are sometimes stale placeholder data — cross-check against at least two independent sources.

## Related skills
- `maps` — geocoding, distances, driving times (use it instead of guessing km).
- `find-nearby` — POI searches at the destination.
