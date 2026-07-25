---
name: single-file-react-gh-pages
description: Build no-build React dashboards for GitHub Pages.
---

# Single-file React dashboards for GitHub Pages

The user (Liping) repeatedly deploys no-build-step single-file React apps to
`~/claudews/zhanglpg.github.io/<project>/` (model-atlas, hotcrp-tracker,
schoology-tracker, coros-dashboard). Pattern: CDN React 18 + Babel standalone,
one `index.html`, a generated `data.js`, published via git push (Jekyll site).

## CRITICAL PITFALL — Babel automatic JSX runtime breaks UMD React

With `<script type="text/babel" data-presets="env,react">`, modern Babel
standalone uses the **automatic JSX runtime**, emitting
`import { jsx } from "react/jsx-runtime"` at the top of the transformed code.
In a classic (non-module) script with the UMD React build this throws
`Cannot use import statement outside a module` and the app renders NOTHING
(blank page, background CSS still shows). Very easy to misdiagnose.

**Fix:** transform with the **classic** runtime and execute manually:

```html
<script type="text/plain" id="app-code">
  /* your JSX here; use React/ReactDOM globals, no imports */
  ReactDOM.createRoot(document.getElementById("root")).render(<App/>);
</script>
<script>
  (function () {
    var src = document.getElementById("app-code").textContent;
    try {
      var out = Babel.transform(src, { presets: [["react", { runtime: "classic" }]] });
      new Function("React", "ReactDOM", out.code)(React, ReactDOM);
    } catch (e) {
      document.getElementById("root").innerHTML =
        '<div style="color:#ff5d5d;font-family:monospace;padding:40px">Failed: ' + e.message + '</div>';
      console.error(e);
    }
  })();
</script>
```

Drop the `env` preset entirely — all ES syntax used (const, arrow, template,
destructuring, spread) is natively supported by every modern browser. Only JSX
needs transforming. The try/catch surfaces real errors on-page instead of a
silent blank screen.

CDN tags (order matters):
```html
<script src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
<script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
<script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
<script src="data.js"></script>  <!-- defines global const DATA = {...}; -->
```

## Verifying rendering (vision tool often times out)

Don't rely on screenshots alone. Inspect the DOM via browser_console:
```js
(() => ({
  statValues: [...document.querySelectorAll('.card .big')].map(e=>e.textContent.trim()),
  svgPaths: document.querySelectorAll('svg path').length,
  bars: document.querySelectorAll('svg rect.bar').length,
  feedItems: document.querySelectorAll('.feed-item').length,
}))()
```
Empty result + empty `#root` but libs loaded (`typeof React/ReactDOM/Babel/DATA`)
=> the JSX-runtime import bug above.

## Context-free bulk data fetching (COROS MCP over raw HTTP)

When you need many MCP results (e.g. 46 lap files) and don't want the payloads
in your context, call the MCP HTTP endpoint directly and stream to disk. The
COROS server is stateless and returns plain JSON:

```python
import json, urllib.request
tok = json.load(open(os.path.expanduser("~/.hermes/mcp-tokens/coros.json")))["access_token"]
payload = {"jsonrpc":"2.0","id":1,"method":"tools/call",
           "params":{"name":"queryActivityLapData","arguments":{"labelId":lid,"sportType":st}}}
req = urllib.request.Request("https://mcp.coros.com/mcp", data=json.dumps(payload).encode(),
    headers={"Authorization":f"Bearer {tok}","Content-Type":"application/json",
             "Accept":"application/json, text/event-stream"})
text = json.loads(urllib.request.urlopen(req,timeout=60).read())["result"]["content"][0]["text"]
```
See `coros-dashboard/fetch_laps.py` for the full auto-detect-missing version.
This avoids both context bloat and subagent self-report fabrication (a
delegate_task once claimed 46 files written but wrote zero — always verify
with `ls | wc -l`, never trust the summary).

## Privacy on a public repo

`zhanglpg.github.io` is PUBLIC. Gitignore raw personal fitness data
(`coros-dashboard/raw/` — heart rate, GPS coords, per-run laps); commit only the
processed `data.js` + app + pipeline scripts.

## Deploy

```
cd ~/claudews/zhanglpg.github.io
git add <project>/ .gitignore && git commit -m "..." && git push
```
Jekyll build takes ~30-60s; a fresh subdir 404s briefly then returns 200.
Verify with `curl -s -o /dev/null -w '%{http_code}' https://zhanglpg.github.io/<project>/`.

## Design system (dark, Strava-style)

- Fonts: Bebas Neue (display numerals/headers) + Space Grotesk (body).
- Palette: bg #0e1014, card #161a22, line #242b38; accents run #ff6b35,
  strength #3ddc84, segment #4cc9f0, hike #ffc857.
- Layered ambient bg: 2-3 radial-gradient glows + a faint grid via body::before/::after.
- Motion: count-up stats, IntersectionObserver scroll reveals, SVG line-draw
  (stroke-dashoffset) and bar-grow animations, hover lift on cards.

## Route-based segments (Strava-style, from lap data only)

COROS lap data has no GPS track, only 1K splits. To get "same route" segment
bests without a map: cluster outdoor runs by START coordinate (haversine,
~200m radius). Runs sharing a start follow the same route, so their 1K splits
are aligned from the start — segment k = best time for the k-th km across all
efforts on that route. Honest and simple. See `build_route_segments` in
`coros-dashboard/update.py`. Fetch trail-run laps too (not just flat runs) or
the most-repeated mountain route is missing.

## Detail modal + mobile patterns

- Detail view: build a labelId->activity index, set a module-level
  `_openDetail` callback from App via useEffect, and call `openDetail(id)`
  from any row/card onClick. Modal: Escape-to-close, overlay-click-to-close,
  lock body scroll while open (restore on unmount).
- Mobile: bottom-sheet modal on <=640px (`align-items:flex-end`,
  `border-radius:18px 18px 0 0`), `.table-scroll{overflow-x:auto}` for tables,
  scrollable tab bar, fluid `clamp()` type, collapse grids at 960/640/400px.
- Note: `element.click()` from browser_console does NOT reliably fire React
  synthetic handlers (and module-scoped functions aren't on window). Use the
  real `browser_click` tool to test interactions; use DOM queries to assert.
