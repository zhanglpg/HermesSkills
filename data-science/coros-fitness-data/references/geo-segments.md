# Geographic route-segment mining from COROS GPS tracks

The user wants **geographic** segments (same physical stretch of trail compared
across efforts), NOT per-km distance-from-start splits. This requires GPS tracks.

## Data source

COROS FIT files contain full GPS tracks. Get them via the
`mcp__coros__downloadActivityFitFiles` tool (single-activity; the date-range
URL query tool sometimes returns garbage errors). Files are saved to a cache
path — copy to `raw/fits/<labelId>.fit`.

Parse with **fitdecode** (not fitparse — fitparse throws "Invalid field size"
on COROS files). Coordinates are in semicircles: `deg = semicircle * 180 / 2^31`.

## Algorithm (coros-dashboard/segments.py)

1. **Cluster by trailhead** — group runs whose start coordinates are within
   ~200 m (haversine).
2. **Build corridor centerline** — take the outbound leg (start → farthest
   point) of the run that reached farthest from the start. Resample to even
   ~30 m spacing. This covers the FULL corridor including any "go forward"
   extension.
3. **Project every run onto the centerline** — for each GPS point, find the
   nearest point on the centerline; record arc-length position `s` and
   perpendicular distance `d`. Use a spatial hash grid for speed (O(n·m) is
   too slow for 10k points). Keep points with `d <= 70 m` (corridor width).
4. **Determine turnaround L** — median of `max_s` across out-and-back runs
   (start ≈ end, gap < 100 m).
5. **Detect segments:**
   - core outbound: [0 → L], direction forward
   - core return: [L → 0], direction return (out-and-back runs only)
   - extension: [L → max_s], runs where max_s > L + 150 m
6. **Time traversals** — detect when projected `s` crosses segment endpoints
   in the relevant direction; interpolate between points.
7. **Render** — Leaflet map per segment with the geographic path as a polyline,
   start/end markers, and an effort leaderboard beside it.

## Critical pitfalls (learned the hard way)

- **Exact-cell edge matching fails on GPS.** Snapping to ~20 m directed grid
  cells and matching edge sequences gives only ~680 m contiguous matches on a
  4 km trail (GPS jitter breaks exact matches). Corridor projection tolerates
  tens of metres of noise. Do NOT use the cell-edge approach.
- **crossing_time falling direction:** must detect an actual transition
  (`s_prev >= target AND s_cur < target`), not just the first point where
  `s <= target` (that's the start, where s=0).
- **Return timing:** find the peak `s` (turnaround), then time from the peak to
  when `s` drops to ≤ 50 m (not exactly 0 — GPS rarely returns to exactly 0;
  runs end at s=1–12 m). Require peak_s >= L*0.8.
- **Second crossing in time_segment:** search only after the first crossing
  time, or it re-matches the start point.
- **Extension path decimation:** the raw beyond-L points can be 7000+;
  decimate to ~30 m spacing for the map polyline.
- **Core forward target:** use `min(L, run_max_s)` and require the run to reach
  >= 95% of L, or runs peaking a few metres short of L get no effort recorded.
- **COROS daily FIT download limit** — prioritize the runs you care about;
  cache FITs in `raw/fits/` so re-runs are free.
- **Leaflet in React:** use `useRef` + `useEffect` with cleanup (`map.remove()`
  on unmount/re-render), `scrollWheelZoom:false`, CARTO dark tiles
  (`https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png`). The map
  container needs an explicit CSS height or it renders at 0 px.

## Real example (user's mountain trail)

10 trail runs from one trailhead (30.274, 120.115): 5 one-way (~4.3 km),
5 out-and-back (~9 km), 1 long run continuing forward (13.5 km). Discovered:
- Outbound start→turnaround: 4.3 km, 10 efforts, best 44:29
- Return turnaround→start: 4.3 km, 5 efforts, best 38:27
- Extension beyond turnaround: 8.8 km, 1 effort

This matches the user's description exactly: a favorite ~4.3 km segment where
they sometimes turn around and sometimes go forward.
