---
name: import-openclaw-skills
description: "Import skills from Openclaw (~/.openclaw/skills/custom/) into Hermes (~/.hermes/skills/). Handles structure translation, shared dependency inlining, config path updates, and data file discovery. Use when migrating openclaw skills to Hermes."
---

# Importing Openclaw Skills to Hermes

Migrate skills from Openclaw's custom skill repo to Hermes skill format.

## Key Differences Between Formats

| Aspect | Openclaw | Hermes |
|--------|----------|--------|
| Skill root | `~/.openclaw/skills/custom/<name>/` | `~/.hermes/skills/<category>/<name>/` |
| Config files | `config.json` at skill root | `references/config.json` |
| Prompts | `prompts/` directory | `references/` directory |
| Shared utils | `shared/` at repo root (sibling to skills) | None — must inline |
| Data files | May live OUTSIDE the skill dir (e.g. `~/.openclaw/paper-queue/`) | Colocated in skill dir |

## Workflow

### Step 1: Inventory the source

```bash
find ~/.openclaw/skills/custom -name "SKILL.md" -type f
```

List all skills, their scripts, configs, prompts, and references.

### Step 2: Find data files stored separately

**PITFALL:** Openclaw stores runtime data (DBs, state files) outside the skill code directory. Common locations:
- `~/.openclaw/<skill-name>/` (e.g. `~/.openclaw/paper-queue/queue.db`)
- `$AGENT_DATA_DIR/<skill-name>/`
- Paths referenced in `config.json` via `$AGENT_DATA_DIR` variable

**Always check:** `config.json` for `db_path`, `state_file`, `output_dir` fields. Search `~/.openclaw/` for `.db` files.

### Step 3: Check for shared dependencies

```bash
grep -rn "from shared\|import shared" ~/.openclaw/skills/custom/<name>/scripts/
```

Common shared imports:
- `shared.logging_utils.get_agent_data_dir` — returns `$AGENT_DATA_DIR` or `/tmp`
- `shared.logging_utils.setup_logger` — configures console + file logging
- `shared.llm_utils.run_gemini` — Gemini CLI wrapper with retry

**These must be inlined** into the importing script since Hermes skills don't share a repo root.

### Step 4: Create the Hermes skill

1. `skill_manage(action='create')` with the SKILL.md content (adapt paths)
2. Copy scripts with `skill_manage(action='write_file')` or `cp`
3. Copy prompts → `references/` directory
4. Copy configs → `references/` directory
5. Copy data files (DBs) into the skill directory

### Step 5: Fix import paths

After copying, patch each script:
- Remove `sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))` lines
- Replace `from shared.logging_utils import ...` with inlined functions
- Update `_DEFAULT_CONFIG_PATH` from `config.json` → `references/config.json`
- Update any `$AGENT_DATA_DIR` references in config files to concrete paths

### Step 6: Verify

- Test scripts can import and run: `python3 scripts/<main>.py --help`
- For DB-backed skills, verify schema: `sqlite3 <db> ".schema"`
- Confirm `skills_list(category='openclaw-imports')` shows the new skill

## Pitfalls

1. **Empty decoy DBs** — The skill code directory may contain empty `.db` files (created by git or init). The real data DB lives elsewhere (e.g. `~/.openclaw/<name>/`). Always check file size and table contents.
2. **Shared utility imports** — Will break at runtime if not inlined. `grep` for them before considering the import done.
3. **Config path drift** — Openclaw `config.json` uses `$AGENT_DATA_DIR` variable expansion. Hermes doesn't set this env var by default. Fix: change the `get_agent_data_dir()` fallback from `/tmp` to `os.path.expanduser('~/.openclaw')` so scripts find existing data. Also copy `config.json` to the skill root if the script uses `_SKILL_DIR / "config.json"` (Hermes imports put it under `references/`).
   4. **Missing shared dependencies** — Openclaw skills import from `shared/logging_utils.py`. Bundle a copy of `logging_utils.py` directly into the skill's `scripts/` directory so it works standalone.
4. **launchctl references** — Some scripts (openbb-sync) use macOS-specific `launchctl`. Note these for cross-platform awareness.
