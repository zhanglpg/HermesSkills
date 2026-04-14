---
name: mermaid-debug
description: Fix broken Mermaid diagrams in Obsidian and other Markdown renderers. Systematic audit and repair for syntax errors, unsupported features, and rendering failures.
version: 1.0.0
author: Hermes
---

# Mermaid Diagram Debugger

Fix broken Mermaid diagrams in Obsidian and other Markdown renderers. Use when a Mermaid diagram fails to render, shows a syntax error, or displays as raw code.

## Quick Audit Checklist

When a Mermaid block is broken, check these in order:

### 1. `flowchart` Keyword
**Use `graph` instead of `flowchart`.** Obsidian's bundled Mermaid version doesn't fully support `flowchart` — diagrams render as "Unsupported markdown". `graph LR`, `graph TD`, `graph TB` are the compatible equivalents.

### 2. Unsupported Diagram Types
- **`timeline`** — not supported in many renderers (Obsidian < 1.5, GitHub). Rewrite as `graph LR` with subgraphs.
- **`mindmap`** — limited support. Rewrite as `graph TB` with tree edges.
- **`sankey`** — not supported outside mermaid-live. Rewrite as `graph LR`.

### 3. Nested Subgraphs
**Most common cause of silent rendering failure.** Many renderers don't support subgraphs-inside-subgraphs. Fix: flatten to a single level.

```
%% BROKEN — nested subgraph
graph TB
    subgraph "Outer"
        subgraph "Inner"   ← fails silently
            A[B]
        end
    end

%% FIXED — flatten to one level
graph TB
    subgraph "Inner"
        A[B]
    end
```

### 4. Hard Syntax Errors
- **Dangling edge** — `A -->|"label"|` with no target node after the pipe. Must have a target.
- **Unmatched quotes** — `A["text"]` must close the bracket and quote.
- **Special chars in unquoted labels** — use quotes: `A["label with : special chars"]`.

### 5. HTML Tags in Nodes
`<i>`, `<b>`, `<em>`, `<strong>` work in mermaid-live but **fail in Obsidian and many embedded renderers**. Strip them:

```
%% BROKEN
A["<b>Title</b><br><i>subtitle</i>"]

%% FIXED
A["Title<br>subtitle"]
```

### 6. Emoji in Nodes
Emoji (📋, ⚡, ✅, etc.) cause rendering failures in some Mermaid versions. Strip them — the node content should be plain text. Use `style` directives for color instead.

### 7. Parentheses in Subgraph Names
`subgraph "Name (Detail)"` can fail. Replace parens with dashes or colons:
- `"Name - Detail"` works
- `"Name: Detail"` works

### 8. Line Breaks in Labels
- **Node labels:** Use `<br>` inside quoted labels for line breaks: `A["Line 1<br>Line 2"]`. Do NOT use `\n` — it renders as literal text in Obsidian. Always quote labels containing `<br>`.
- **Edge labels:** `<br>` in edge labels often breaks. Use single-line labels or split into separate edges.

## Systematic Audit Method

When reviewing a document with multiple Mermaid blocks, use `execute_code` with this script:

```python
import re
with open('FILEPATH') as f:
    content = f.read()
blocks = re.findall(r'```mermaid\n(.*?)```', content, re.DOTALL)
for i, b in enumerate(blocks):
    subgraphs = [l for l in b.split('\n') if 'subgraph' in l and not l.strip().startswith('#')]
    ends = [l for l in b.split('\n') if l.strip() == 'end']
    has_html = '<i>' in b or '<b>' in b or '<em>' in b
    has_emoji = any(ord(c) > 0x2600 for c in b)
    issues = []
    if len(subgraphs) != len(ends): issues.append('UNBALANCED subgraph/end')
    if has_html: issues.append('HTML tags')
    if has_emoji: issues.append('emoji')
    print(f'Block {i+1}: {len(subgraphs)} subgraphs, issues: {issues or "none"}')
```

## Fix Pattern Summary

| Issue | Detection | Fix |
|-------|-----------|-----|
| `flowchart` keyword | First line starts with `flowchart` | Replace with `graph` (e.g., `graph LR`, `graph TD`) |
| `timeline` type | First line of block | Rewrite as `graph LR` with subgraphs |
| Nested subgraphs | Subgraph count vs indentation | Flatten to single level |
| Dangling edge | Edge with label but no target | Add target node |
| HTML tags | `<i>`, `<b>` in block | Strip tags, keep text |
| Emoji | Unicode > U+2600 | Strip emoji, rely on style colors |
| Parens in subgraph | `subgraph "...(..."` | Replace with dash or colon |
| `\n` in node labels | Literal `\n` in node text | Replace with `<br>` in quoted label: `["A<br>B"]` |
| `<br>` in edges | `<br>` inside edge label | Flatten to single line |

## Pitfalls

- **Obsidian's Mermaid version lags** — features that work on mermaid.live may not work in Obsidian. Always test locally.
- **Style directives are safe** — `style X fill:#color,color:#fff` works everywhere. Prefer colors over emoji for visual distinction.
- **Quote all node labels with `<br>` or special chars** — `A["Label<br>detail"]` not `A[Label<br>detail]`.
- **Don't nest `direction` inside subgraphs in older versions** — `direction LR` inside a `graph TB` subgraph can cause layout bugs.
