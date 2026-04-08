---
name: wiki-manager
description: "Maintains a living knowledge wiki in the Obsidian vault. After any paper is digested, extracts concepts and names, creates/updates concept and name pages, rebuilds the index, and appends to the log. Also supports periodic lint checks, LLM-powered compile analysis, index rebuilding, and broken wikilink repair. Use for wiki updates, ingestion, lint checks, compile analysis, or knowledge graph maintenance."
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

## Vault Structure

```
gen-notes/
  index.md          — auto-generated catalog of all pages
  log.md            — append-only chronological record
  digests/          — paper digest notes
  concepts/         — concept pages
  names/            — name pages
  syntheses/        — filed query answers
  comparisons/      — side-by-side comparisons
```

## Configuration

See `references/config.json` for vault paths. All paths are relative to `vault_root`.

## Pitfalls

- **Frontmatter format:** Digest files MUST have YAML frontmatter with `---` delimiters at the TOP of the file. Obsidian inline properties at the bottom (`key:: value`) will NOT be parsed. The `concepts:` and `names:` fields must be YAML lists (`- item`), not `[[wikilink]]` format.
- **Script path:** Always run from `~/.openclaw/skills/custom/wiki-manager/` — the hermes-imported copy at `~/.hermes/skills/openclaw-imports/wiki-manager/` fails with `ModuleNotFoundError: No module named 'logging_utils'`.
- **`--extract-only` hangs:** If frontmatter concepts/names aren't found, the script falls back to LLM extraction (Gemini CLI) which can take 5-10 minutes and often times out. Fix the frontmatter first.
- **Agent-primary workflow is more reliable than full ingest:** Use `--extract-only` to get metadata → check which pages exist → create/update pages via delegate_task or directly → run `index` to rebuild. This avoids the sequential Gemini CLI calls that cause SIGTERM/timeout issues.
- **Timeout:** If using full ingest (not agent-primary), set `timeout=600+`. Multiple polls can interfere — use a single long wait.

## Dependencies

| Tool | Purpose |
|------|---------
| Python 3.10+ | Runtime |

Gemini CLI is only needed for the ingest fallback pipeline (`ingest` without `--extract-only`).

## Pitfalls

- **Script path:** The copy at `~/.hermes/skills/openclaw-imports/wiki-manager/scripts/wiki_manager.py` has a missing `logging_utils` dependency. Use the openclaw version at `~/.openclaw/skills/custom/wiki-manager/scripts/wiki_manager.py` instead (it has the full dependency tree).
- **Frontmatter format is critical:** Concepts and names MUST be in YAML frontmatter at the **top** of the digest file with `---` delimiters. If missing, the script falls back to LLM extraction via Gemini CLI which takes 5-10 min and often times out. Always verify frontmatter before running ingest.
- **Frontmatter values must be plain strings:** Use `- Multi-Agent Systems` not `- [[Multi-Agent Systems]]`. Wikilink syntax in YAML values breaks parsing.
- **Agent-primary workflow is more reliable:** Instead of letting `ingest` run end-to-end (which makes sequential Gemini calls), prefer: (1) `ingest <path> --extract-only` to get metadata, (2) create/update concept and name pages yourself or via subagent delegation, (3) run `index` to rebuild. This avoids timeouts and gives you control over page quality.
- **Timeout budget:** If using the full ingest pipeline, set `timeout=600+`. With 3 concepts + 5 names, expect 5-10 minutes of sequential Gemini CLI calls. Multiple polls can interfere — use a single long wait.

## Pitfalls

### Script location
The `wiki_manager.py` under `~/.hermes/skills/` fails with `ModuleNotFoundError: No module named 'logging_utils'`. **Always use the openclaw version:**
```bash
cd ~/.openclaw/skills/custom/wiki-manager && python3 scripts/wiki_manager.py ...
```

### `ingest --extract-only` hangs
Even with correct frontmatter, the extract-only command may hang (likely during page existence checks or LLM fallback). If it times out after 30-60s:

**Use the agent-primary workflow instead:**
1. Verify frontmatter parses correctly (check that "Concepts from frontmatter" appears in output before timeout)
2. Check which concept/name pages already exist by listing files in `gen-notes/concepts/` and `gen-notes/names/`
3. Create new pages manually or via `delegate_task` subagent (use concept-page-prompt.md and name-page-prompt.md templates)
4. Update existing pages to incorporate the new digest
5. Run `python3 scripts/wiki_manager.py index` to rebuild the index (this always works quickly)

### Frontmatter format
Digest notes MUST have YAML frontmatter at the TOP with `---` delimiters. Concepts and names must be YAML lists:
```yaml
---
concepts:
  - Multi-Agent Systems
  - Deep Research
names:
  - GEPA
  - TextGrad
---
```
NOT `concepts: [[Multi-Agent Systems]], [[Deep Research]]` — wikilink format is not parsed.
