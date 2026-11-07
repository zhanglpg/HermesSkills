# Lightbox + swipe gallery for single-file atlas pages

The viewer that this user expects on an illustrated atlas page (single-file HTML under
`~/claudews/zhanglpg.github.io/<slug>/`). Cards stay compact; the viewer is where a 20:1
handscroll or a 3:1 hanging scroll is actually read.

## Behaviour contract
- Clicking ANY card image opens a full-screen overlay; no new tab, no `window.open`.
- Toolbar: 适应 (fit) / 1:1 (native pixels) / 2× zoom, image counter, close. Keys 0/1/2
  map to the zooms, Esc closes.
- The image stage scrolls (both axes). Default zoom is `fit`, EXCEPT when `w/h > 4`, where
  the viewer opens at 1:1 so a handscroll is immediately readable and horizontally
  scrollable — fitting a 15:1 scroll to the viewport is what makes it look blank.
- Multi-image works: ‹ › buttons, ←/→ keys, and a horizontal touch swipe cycle images;
  counter reads `n / N`; arrows hide when `N == 1`.
- Caption bar shows the version chip, the credit line, and a 查看原图 link to the remote
  original when one exists.
- Drag-to-pan while zoomed (mousedown + scrollLeft/Top), cursor grab/grabbing.

## Data model
Each image is `{src, full, ver, credit, name, w, h, hi}`; `hi` is an optional higher-res
local file used only by the viewer (`src` stays the 2200 px card file). A work carries
`imgs: [...]` — the first entry is the card image — and falls back to its single
`src/full/ver/credit` when absent. The build emits one JSON blob:

```html
<script type="application/json" id="gal">{"<key>":[{...}]}</script>
```

with `</` escaped as `<\/` so a credit string containing `</a>` cannot close the tag.
Zero-parse fallback in JS: `try { JSON.parse(...) } catch { {} }`.

## Card side
- Badge `1 / N` on multi-image cards.
- `object-fit: cover` only when `ar > 5`, for handscroll strips; cropping is wrong for tall
  couplets and hanging scrolls (it eats characters), so never apply it below that ratio.
- Counting check: the viewer's own `<img id="lb-img">` is src-less until opened — exclude
  it when asserting `broken == 0`.

## Build-side gotchas
- Do not name a top-level const `top` (see SKILL.md pitfalls); `topBtn` is safe.
- Emit `w`/`h` from the real file (`sips -g pixelWidth -g pixelHeight`) so the viewer can
  choose the opening zoom without waiting for `naturalWidth`.
- When a work has BOTH `imgs` and a work-level `hi`, the builder must fall back to that `hi` for
  image 0; a `work_images()` that reads only `img.get('hi')` silently drops the high-res file
  for every multi-image work, which then opens at the card copy. Assert the emitted JSON:
  `sum(1 for v in GAL.values() if v[0].get('hi'))` must equal the number of `img/hi/` files made,
  then in the browser check `#lb-img` `naturalWidth` is the hi width (e.g. 3840), not 1280.
- Preload only the immediate neighbours of the current index.
- Verify in a real browser: click a card, assert `.lb.on`, assert the counter, step with
  the arrow key, press Esc, and for a handscroll assert `scrollWidth > clientWidth`.
