---
name: wiki-manager
description: "Maintains a living knowledge wiki in the Obsidian vault. After any paper is digested, extracts concepts and names, creates/updates concept and name pages, rebuilds the index, and appends to the log. Supports domain-based organization (ai, systems, history, science, wisdom) with domain-filtered index views. Also supports periodic lint checks, LLM-powered compile analysis, index rebuilding, and broken wikilink repair. Use for wiki updates, ingestion, lint checks, compile analysis, or knowledge graph maintenance."
---

# Wiki Manager

Maintain a living knowledge wiki in the Obsidian vault. This skill transforms isolated paper digests into an interconnected knowledge graph by managing concept pages, name pages, a content index, and a chronological log.

## When to Use

- **After digesting a paper** — run ingest to create concept and name pages, update the index, and log the event
- **To rebuild the index** — run `index` to regenerate `index.md` from all vault pages
- **To check vault health** — run `lint` to find orphan pages, broken wikilinks, stale concepts
- **To fix broken wikilinks** — run the `fix-links` workflow (see below)
- **To run AI compile** — analyze the wiki for contradictions, stale claims, gaps, and missing cross-references
- **To view the log** — read `gen-notes/log.md` for a chronological record of all wiki activity

---

## Ingest (Agent-Primary) — PREFERRED METHOD

After a paper digest is created, ingest it into the wiki to extract concepts and names and create their pages.

**⚠️ The script-based `ingest` command frequently times out** (it makes sequential Gemini CLI calls, ~2 min per concept/name). The agent-primary workflow below is more reliable — use `--extract-only` to validate frontmatter parsing, then create/update pages yourself and run `index` at the end.

### Step 1: Extract metadata

```bash
python3 scripts/wiki_manager.py ingest <digest_path> --extract-only
```

This outputs JSON with:
- `digest_title`, `digest_content` — the parsed digest
- `concepts` — list of concepts from frontmatter (each with `name`, `exists`, `path`)
- `names` — list of names from frontmatter (each with `name`, `exists`, `path`)
- `existing_pages` — dict of existing page titles by type (`concepts`, `names`, `digests`)
- `concept_dir`, `names_dir` — directories for writing new pages
- `vault_root`, `gen_notes_dir`, `log_path` — vault paths

### Step 2: Create/update concept pages

For each concept in the extract output:

- **If new** (`exists: false`): Create a concept page following `references/concept-page-prompt.md`. Write to `<concept_dir>/<Concept Name>.md`.
- **If existing** (`exists: true`): Read the existing page at `path`, then update it to incorporate the new digest.

### Step 3: Create/update name pages

For each name in the extract output:

- **If new** (`exists: false`): Create a name page following `references/name-page-prompt.md`. Write to `<names_dir>/<Name>.md`.
- **If existing** (`exists: true`): Read the existing page at `path`, then update it similarly.

### Step 4: Update index and log

```bash
python3 scripts/wiki_manager.py index
```

---

## Compile (Agent-Primary)

Analyze the wiki for semantic issues: contradictions between pages, stale claims, missing cross-references, concept gaps, and research questions.

### Step 1: Extract data and lint issues

```bash
python3 scripts/wiki_manager.py compile extract
```

### Step 2: Cross-page analysis

For each batch, analyze using `references/compile-cross-page-prompt.md`.

### Step 3: Gap analysis

Using the `wiki_summary`, analyze using `references/compile-gap-analysis-prompt.md`.

### Step 4: Save report

```bash
python3 scripts/wiki_manager.py compile save-report '<json_array>'
```

---

## Non-LLM Commands (Script-Only)

```bash
# Rebuild index.md from all vault pages
python3 scripts/wiki_manager.py index

# Run vault health checks (deterministic, no LLM)
python3 scripts/wiki_manager.py lint

# List all concept pages
python3 scripts/wiki_manager.py concepts

# List all name pages
python3 scripts/wiki_manager.py names
```

## Fixing Broken Wikilinks

```bash
# Step 1: Scan
python3 scripts/wiki_manager.py fix-links scan

# Step 2: Decide resolutions (agent reviews output)

# Step 3: Apply
python3 scripts/wiki_manager.py fix-links apply '{"Transformer Architecture": "Transformer"}'
```

## Domain Support

Every page has a `domain` frontmatter field. Valid domains:

| Domain | Scope |
|--------|-------|
| `ai` | AI & Machine Learning |
| `systems` | Computing Systems & Infrastructure |
| `history` | History & Civilization |
| `science` | Physics, Mathematics & Complexity |
| `wisdom` | Philosophy, Leadership & Classical Thought |

- Digests: set `domain:` in frontmatter before ingesting. Defaults to `ai` if missing.
- Concepts/Names: inherit domain from the digest during ingest.
- Index: auto-generates a "By Domain" section with emoji-labeled subsections and domain counts in Stats.
- Config: `valid_domains` and `default_domain` in `references/config.json`.
- Cross-domain connections are expressed through wikilinks, not multiple domains per page.

## Vault Structure

```
gen-notes/
  index.md          — auto-generated catalog of all pages (includes By Domain section)
  log.md            — append-only chronological record
  digests/          — paper digest notes
  concepts/         — concept pages
  names/            — name pages
  syntheses/        — filed query answers
  comparisons/      — side-by-side comparisons
```

## Backfilling Domains on Existing Pages

When adding `domain:` to pages that predate domain support, use `execute_code` with **native Python file I/O** (not `hermes_tools` wrappers) to avoid the 50 tool-call limit:

```python
import os, re
digests_dir = os.path.expanduser("~/path/to/gen-notes/digests")
# Map non-default domains explicitly; everything else defaults to "ai"
domain_map = {
    "Some Science Paper.md": "science",
    "Some Systems Paper.md": "systems",
}
for filename in os.listdir(digests_dir):
    if not filename.endswith(".md"): continue
    filepath = os.path.join(digests_dir, filename)
    domain = domain_map.get(filename, "ai")
    with open(filepath, 'r') as f: raw = f.read()
    fm_match = re.match(r'^---\s*\n(.*?)\n---', raw, re.DOTALL)
    if not fm_match or re.search(r'^domain:', fm_match.group(1), re.MULTILINE):
        continue  # skip if no frontmatter or domain already set
    # Insert before tags:/categories:/concepts: line
    fm = fm_match.group(1)
    for marker in ["\ntags:", "\ncategories:", "\nconcepts:"]:
        if marker in fm:
            raw = raw.replace(marker, f"\ndomain: {domain}{marker}", 1)
            break
    with open(filepath, 'w') as f: f.write(raw)
```

After backfill, run `python3 scripts/wiki_manager.py index` to rebuild the index with domain sections.

**Key lesson:** `hermes_tools.read_file`/`patch` each count as tool calls — processing 50+ files exhausts the 50-call budget. Native `open()`/`re.sub()` uses zero tool calls.

## Configuration

See `references/config.json` for vault paths. All paths are relative to `vault_root`.

## Dependencies

| Tool | Purpose |
|------|---------
| Python 3.10+ | Runtime |

Gemini CLI is only needed for the ingest fallback pipeline (`ingest` without `--extract-only`).

## Pitfalls

### Script location
Run wiki_manager.py from the hermes skills directory (logging_utils.py is bundled):
```bash
cd ~/.hermes/skills/openclaw-imports/wiki-manager && python3 scripts/wiki_manager.py ...
```

### Frontmatter format
Digest notes MUST have YAML frontmatter at the TOP with `---` delimiters. Concepts, names, and domain must be YAML values:
```yaml
---
domain: ai
concepts:
  - Multi-Agent Systems
  - Deep Research
names:
  - GEPA
  - TextGrad
---
```
- Use `- Multi-Agent Systems` not `- [[Multi-Agent Systems]]` — wikilink syntax in YAML breaks parsing.
- Obsidian inline properties at the bottom (`key:: value`) will NOT be parsed.
- If `domain:` is missing or invalid, defaults to `ai`.

### `ingest --extract-only` hangs
Even with correct frontmatter, the extract-only command may hang (likely during page existence checks or LLM fallback). If it times out after 30-60s:

**Use the agent-primary workflow instead:**
1. Verify frontmatter parses correctly (check that "Concepts from frontmatter" appears in output before timeout)
2. Check which concept/name pages already exist by listing files in `gen-notes/concepts/` and `gen-notes/names/`
3. Create new pages manually or via `delegate_task` subagent (use concept-page-prompt.md and name-page-prompt.md templates — pass `{domain}` placeholder)
4. Update existing pages to incorporate the new digest
5. Run `python3 scripts/wiki_manager.py index` to rebuild the index (this always works quickly)

### Agent-primary workflow is more reliable
Instead of letting `ingest` run end-to-end (which makes sequential Gemini calls), prefer: (1) `ingest <path> --extract-only` to get metadata, (2) create/update concept and name pages yourself or via subagent delegation, (3) run `index` to rebuild. This avoids timeouts and gives you control over page quality.

### Subagent wikilink hallucination

When delegating concept/name page creation or updates to subagents, they frequently invent wikilink names that don't match actual digest filenames (e.g., `[[MiniMax-M2 Technical Report]]` instead of `[[MiniMax-M2]]`). This creates broken wikilinks.

**Prevention:** In the subagent's `context`, always include the **exact digest filename** (without `.md` extension) for use in wikilinks, e.g.:

```
The source digest filename is 'MiniMax-M2' — use [[MiniMax-M2]] (NOT [[MiniMax-M2 Technical Report]]) for all wikilinks to this digest.
```

After all subagents complete, verify the critical wikilinks by reading the updated files. Run `python3 scripts/wiki_manager.py fix-links scan` to catch any broken links.

### Timeout budget
If using the full ingest pipeline, set `timeout=600+`. With 3 concepts + 5 names, expect 5-10 minutes of sequential Gemini CLI calls.
