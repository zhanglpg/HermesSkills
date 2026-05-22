---
name: discord-rendering
description: "Definitive guide to Discord markdown rendering: what works, what doesn't, and workarounds for diagrams, charts, code, and formatted content. Load when composing complex messages for Discord delivery."
---

# Discord Rendering Guide

Definitive reference for what Discord's markdown renderer supports and workarounds for unsupported formats. Use this whenever composing complex messages (diagrams, charts, code, structured data) for Discord delivery.

## Quick Reference

| Format | Status | Workaround |
|--------|--------|------------|
| Tables | ✅ Native | Use standard `\| a \| b \|` syntax |
| Headers | ✅ Native | `# ## ###` |
| Bold/Italic/Underline/Strike | ✅ Native | `**bold**`, `_italic_`, `__underline__`, `~~strike~~` |
| Lists (ordered/unordered) | ✅ Native | `- *` or `1. 2.` |
| Code blocks | ✅ Native | `` `inline` `` or ` ```lang ``` ` (~20 langs) |
| Block quotes | ✅ Native | `>` single-line, `>>>` multi-line |
| Links (masked) | ✅ Native | `[text](url)` — bare URLs auto-embed |
| Spoiler tags | ✅ Native | `\|\|hidden\|\|` |
| Subtext | ✅ Native | `-# small text` |
| Mermaid diagrams | ❌ No renderer | ASCII box-drawing or PNG attachment |
| SVG | ❌ Not inline | Export to PNG, attach |
| LaTeX / Math | ❌ No KaTeX/MathJax | Plaintext or image |
| HTML | ❌ Stripped | Markdown only |
| Footnotes / TOC | ❌ No extended MD | Manual linking |

## Workarounds by Use Case

### Flowcharts / Causal Chains → ASCII Box-Drawing in Code Blocks

Use Unicode box-drawing characters for simple diagrams:

```
Characters: ─ │ ┌ ┐ └ ┘ ├ ┤ ┬ ┴ ┼ ╭ ╮ ╰ ╯
Arrows:     → ← ↑ ↓ ↔ ⇒ ⇐
```

Example pattern:

```
IRAN CONFLICT ──► OIL SURGE ──► HOT CPI ──► FED HIKE
       │                                        │
       └──► TRUMP-XI SUMMIT                      │
              │                                  │
              ├──► Wed: BABA +8.2%               │
              └──► Fri: BABA -6.0% ←─────────────┘
```

For multi-level hierarchies, use indented tree patterns:

```
IRAN-US CONFLICT (Hormuz Standoff)
    │
    ├──► OIL: Brent $95 → $109 (+10% WoW)
    │       │
    │       └──► CPI hot (+2.1 pts MoM) → Fed hike priced
    │              │
    │              └──► 10Y 4.47% → Multiples compress
    │
    └──► TRUMP-XI SUMMIT (Binary Event)
           │
           ├──► Wed: Tariff hopes → BABA +8.2%
           └──► Fri: Taiwan exposed → BABA -6.0%
```

### Data Presentation → Tables

Discord tables render fully. Keep columns narrow for mobile readability (3-4 columns max per table, 5 if values are short).

**Good:**
```
| Symbol | Price | Change | vs SMA-20 |
|--------|-------|--------|-----------|
| GOOG | $393.32 | -0.97% | Above 🟢 |
| BABA | $132.59 | -6.04% | Below 🔴 |
```

**Bad:** Too many columns breaks on mobile. Split into multiple tables if needed.

### Price Charts / Trends → Text-Based Sparklines

Use Unicode block characters for mini trend visualization:

```
BABA week: $140 ──╮ +8.2% ╭── -6.0% ──► $133
GOOG week: $397 ─────────────── -0.94% ──► $393
```

Or with emoji indicators:
```
BABA: 📉 -5.3% WoW (below SMA-20, -32.4% max DD)
GOOG: 📊 -0.94% WoW (above SMA-20, relative strength)
```

### Warnings / Callouts → Block Quotes + Emoji

```
> ⚠️ **BABA Risk:** Below SMA-20, no near-term catalyst post-summit
> 🟢 **GOOG Strength:** Above SMA-20, AI moat intact, Apple fracture = opportunity
> 📊 **Macro:** Oil $109, 10Y 4.47%, Fed hike Dec 2026 priced in
```

### Complex Diagrams → PNG Attachment

If ASCII can't capture it, generate an image:
1. Use `architecture-diagram` skill for system/architecture diagrams
2. Use Python `matplotlib` for charts
3. Use `image_generate` for conceptual illustrations
4. Attach via `MEDIA:/path/to/file.png`

Discord renders PNG, JPG, WebP, GIF inline. Max file size: 25MB (Nitro/Boost servers), 8MB (free).

## Pitfalls

- **Code fences in messages break markdown rendering** — the `chunk_brief.py` script in `generating-briefs` avoids this by design. If a message contains code fences and is multipart, subsequent parts may lose formatting.
- **Mermaid/PlantUML won't render** — there is no renderer in any Discord client. Must convert to ASCII or image.
- **Mobile truncation** — Discord mobile shows ~2000 chars before "Show more." Tables with many columns overflow horizontally.
- **Syntax highlighting languages** — only ~20 langs supported: `asciidoc, autohotkey, bash, coffeescript, cpp, cs, css, diff, fix, glsl, ini, json, md, ml, prolog, ps, py, tex, xl, xml, yaml`. No `mermaid`, `plantuml`, `latex`, `html`.
- **Bare URLs auto-embed** — suppresses if you don't want a link preview. Wrap in `<>` to prevent: `<https://example.com>`.

## Integration with generating-briefs

When composing the daily investment brief for Discord:
1. Use tables for price snapshots (already done)
2. Use text-based causal chains instead of Mermaid
3. Use block quotes + emoji for portfolio impact callouts
4. Keep ASCII diagrams simple — avoid > 60 chars wide (Discord wraps at ~72 chars on desktop, much less on mobile)

The `chunk_brief.py` script already handles message splitting. Ensure any ASCII art or structured diagrams survive chunking — put them in their own paragraph to avoid being split mid-diagram.
