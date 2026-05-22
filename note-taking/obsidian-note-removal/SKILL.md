---
name: obsidian-note-removal
description: Safely remove Obsidian notes and clean up all backlinks across the wiki — concepts, names, index, log, cross-references, and lint report.
---

# Obsidian Note Removal with Link Cleanup

## Pitfall
`obsidian-cli delete` only removes the file. It does **NOT** clean up backlinks (unlike `move`, which does). You must handle backlink cleanup manually.

## Workflow

### Step 1: Delete files
```bash
obsidian-cli delete "gen-notes/digests/Note Name"
```
Use the path relative to vault root, without `.md` extension.

### Step 2: Find all backlinks
Search the entire `gen-notes/` tree for the deleted note's full name:
```bash
VAULT="$OBSIDIAN_VAULT_PATH"
grep -rl "Full Note Name" "$VAULT/gen-notes/" --include="*.md"
```

Affected files typically span:
- `gen-notes/concepts/*.md` — frontmatter lists + inline refs + "New paper ingested" lines
- `gen-notes/names/*.md` — frontmatter lists + inline refs
- `gen-notes/index.md` — bullet list entries
- `gen-notes/log.md` — historical ingestion entries
- `gen-notes/digests/*.md` — cross-references in other digests
- `gen-notes/essays/*.md` — minor references
- `gen-notes/_lint-report.md` — generated diagnostic file

### Step 3: Bulk clean with Python regex
Use `execute_code` to process all files. Required regex patterns (in order):

```python
import re

full_name = "Exact Note Name - Author Year"
short_name = "Short Display Name"

# 1. Standalone bullet: "- [[Full Name]]" or "- [[Full Name]] (digest)"
content = re.sub(
    rf'^- \[\[{re.escape(full_name)}\]\]\s*(?:\(digest\))?\s*$',
    '', content, flags=re.MULTILINE
)

# 2. Inline wikilink in sentence → plain text
content = re.sub(
    rf'\[\[{re.escape(full_name)}\]\]',
    short_name, content
)

# 3. Piped wikilink: [[Full Name|alias]] → alias
content = re.sub(
    rf'\[\[{re.escape(full_name)}\|([^\]]+)\]\]',
    r'\1', content
)

# 4. Frontmatter double-quoted: '  - "[[Full Name]]"'
content = re.sub(
    rf'^\s*- "\[\[{re.escape(full_name)}\]\]"\s*$',
    '', content, flags=re.MULTILINE
)

# 5. Frontmatter single-quoted: "  - '[[Full Name]]'"
content = re.sub(
    rf"^\s*- '\[\[{re.escape(full_name)}\]\]'\s*$",
    '', content, flags=re.MULTILINE
)

# 6. Inline double-quoted wikilink: '"[[Full Name]]"'
content = re.sub(
    rf'"\[\[{re.escape(full_name)}\]\]"',
    f'"{short_name}"', content
)

# 7. Inline single-quoted wikilink: "'[[Full Name]]'"
content = re.sub(
    rf"'\[\[{re.escape(full_name)}\]\]'",
    f"'{short_name}'", content
)

# 8. "New paper ingested: [[Full Name]]" — remove entire line
content = re.sub(
    rf'^New paper ingested: \[\[{re.escape(full_name)}\]\].*$',
    '', content, flags=re.MULTILINE
)

# 9. Log entry: 'ingest: "Title" → [[Full Name]]' → keep text, drop wikilink
content = re.sub(
    rf'(\" → )\[\[{re.escape(full_name)}\]\]',
    r'\1' + short_name, content
)

# Cleanup whitespace
content = re.sub(r'\n{3,}', '\n\n', content)
content = re.sub(r'[ \t]+$', '', content, flags=re.MULTILINE)
```

### Step 4: Clean `_lint-report.md` separately
Remove stale entries referencing the deleted files (broken wikilink + missing frontmatter lines). Use `patch` with targeted `old_string`/`new_string` replacements — one per stale line.

### Step 5: Verify
```bash
grep -rl "Deleted Note Full Name" "$VAULT/gen-notes/" --include="*.md"
# Should return exit code 1 (no matches)
```

## Edge cases
- **Piped wikilinks** (`[[Full Name|alias]]`) — Pattern 3 handles these. They often appear in comparison tables within other digests.
- **Multiple deletions** — Process all deleted names in a single pass over `gen-notes/` to avoid re-reading files.
- **Patch tool** — When cleaning `_lint-report.md`, be precise with `old_string` to avoid accidentally removing unrelated adjacent lines. Check the diff output.
