---
name: interactive-svg-charts
description: Use when SVG charts need hover tooltips or crosshairs.
---

# Interactive SVG Charts (hover tooltips + crosshair)

Class-level recipe for hand-rolled SVG charts (no chart lib) in no-build React
dashboards. The user expects EVERY chart in a report to support hover once any
one of them does — build all charts with this pattern from the start, and when
asked to "add hover to the remaining charts", reuse this recipe verbatim.

## Per-chart recipe

1. Wrap the `<svg>` in `<div style={{position:'relative'}}>` — the tooltip is a
   sibling div positioned against this wrapper.
2. State: `const [hover,setHover]=useState(null)` holding `{i, mxPct}` (data
   index + mouse x as % of svg width, for tooltip flip).
3. `onMove(e)` on the svg:
   ```js
   const rect = svgRef.current.getBoundingClientRect();
   const px = (e.clientX-rect.left)/rect.width*W;      // W = viewBox width
   let i = Math.round((px-P.l)/(W-P.l-P.r)*(n-1));     // invert x-scale
   i = Math.max(0, Math.min(n-1, i));                  // clamp
   setHover({i, mxPct:(e.clientX-rect.left)/rect.width*100});
   ```
   For continuous-x charts (payoff curves) invert to the x VALUE instead of an
   index; for point charts (term structure) snap to nearest point index.
4. Bind `onMouseMove={onMove} onMouseLeave={()=>setHover(null)}` plus
   `onTouchStart/onTouchMove={onMove}` and `onTouchEnd` clearing, for mobile.
   `cursor:'crosshair'`, `touchAction:'pan-y'` on the svg.
5. Crosshair + markers inside `<g pointerEvents="none">`: one vertical
   `<line>` at x(i) (stroke `#e8ebf0`, opacity .3-.35) and one `<circle>` per
   series at its y-value (fill bg color, stroke series color). Markers must
   never capture pointer events or the hover flickers.
6. Tooltip div (rendered only when hover != null):
   `position:'absolute', top:8, pointerEvents:'none', zIndex:5`,
   bg `rgba(22,26,34,.96)`, border `1px solid #303848`, radius 10,
   `backdropFilter:'blur(6px)'`, minWidth ~180. Content: x-label line (date /
   expiry+DTE / scenario price) then one row per series: colored dot + name +
   right-aligned tabular-nums value, green/red by sign; optional divider row
   for a derived quantity (delta vs baseline, ±1σ band).
7. Edge flip: `left:(mxPct+2)+'%'` while mxPct<=62, else
   `right:(102-mxPct)+'%'` — otherwise the card covers the data near the
   right edge.

## Verifying hover from browser_exec

- Trigger: `svg.dispatchEvent(new MouseEvent('mousemove',{clientX,cy,bubbles:true}))`
  with clientX computed from `getBoundingClientRect()`; then read the tooltip
  div's textContent after ~250ms.
- DISMISSAL test must use `mouseout`, NOT `mouseleave`: React implements
  onMouseLeave via a delegated mouseout listener at the root, so a synthetic
  `mouseleave` never clears the tooltip and looks like a bug that isn't.
- Assert tooltip text contains the expected series values, and that markers
  (`svg circle` with the series stroke) appear/disappear with hover state.

## Pitfalls

- Computing the index from `e.clientX` without dividing by `rect.width` (i.e.
  mixing client px with viewBox px) mis-snaps on any non-1:1 scaled svg —
  always convert through the rect first.
- Putting the tooltip INSIDE the svg (foreignObject/text) breaks styling and
  clipping; keep it an HTML sibling of the svg inside the relative wrapper.
- Forgetting `pointerEvents:'none'` on crosshair/markers/tooltip: the tooltip
  under the cursor re-triggers mousemove and flickers.
