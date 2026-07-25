---
name: paper-queue
description: "Manages a reading queue of academic papers with priority scoring, progress tracking, and suggestions. Adds papers from arXiv IDs, URLs, or Twitter/X links. Tracks reading status (to-read, reading, digested) and auto-scores by citations, recency, and topic affinity. Integrates with the paper-summarizer skill for processing queued papers. Use when managing a paper queue, reading list, or paper backlog."
---

# Paper Queue Manager

Manage a prioritized reading queue of academic papers with automatic scoring and integration with the paper-summarizer skill.

## Quick Start

```bash
SKILL_DIR=~/.hermes/skills/openclaw-imports/paper-queue

# Initialize the database (first time only)
python3 $SKILL_DIR/scripts/paper_queue.py --init

# Add a paper by arXiv ID
python3 $SKILL_DIR/scripts/paper_queue.py add 2401.12345

# Add from a URL
python3 $SKILL_DIR/scripts/paper_queue.py add https://arxiv.org/abs/2401.12345

# Add from a tweet
python3 $SKILL_DIR/scripts/paper_queue.py add https://x.com/karpathy/status/123456

# Add manually
python3 $SKILL_DIR/scripts/paper_queue.py add --manual --title "Paper Title" --url "https://..."

# View the queue
python3 $SKILL_DIR/scripts/paper_queue.py list --top 10

# Mark as reading
python3 $SKILL_DIR/scripts/paper_queue.py status 1 reading

# Mark as digested
python3 $SKILL_DIR/scripts/paper_queue.py status 1 digested

# Get suggestions for new papers
python3 $SKILL_DIR/scripts/paper_queue.py suggest

# Queue stats
python3 $SKILL_DIR/scripts/paper_queue.py stats
```

## How It Works

1. **Add** — Papers enter the queue from arXiv (ID or URL), Twitter/X links (extracts embedded paper URLs), or manual entry
2. **Score** — Each paper is automatically scored on three dimensions:
   - **Citations** (30%) — From Semantic Scholar API (log scale)
   - **Recency** (30%) — How recently published (decay over time)
   - **Queue affinity** (40%) — Topic overlap with papers already in the queue
3. **Track** — Papers move through statuses: `to-read` → `reading` → `digested`
4. **Digest** — Use the paper-summarizer skill to process papers, then mark as digested
5. **Suggest** — Get recommendations for new papers based on the queue's topic profile

## Storage

Papers are stored in a SQLite database. The path is controlled by `db_path` in `references/config.json`.  
**Current path:** `~/.hermes/skills/openclaw-imports/paper-queue/.paper_queue/queue.db`

> **Note:** The DB lives in a `.paper_queue/` hidden directory within this skill folder. This directory is git-ignored to keep the repo clean. If you see "Queue database not found", check `references/config.json` → `db_path`.

## Dependencies

| Tool | Purpose |
|------|---------|
| Python 3.10+ | Runtime |
| sqlite3 | Storage (built-in) |

No additional pip packages required. Optional: `httpx` for better HTTP handling.

External APIs (no auth needed):
- **arXiv API** — Paper metadata
- **Semantic Scholar API** — Citation counts

## Configuration

See `references/config.json` for scoring weights and paths.

## Pitfalls

### arXiv ID resolution can return wrong papers
The arXiv API sometimes resolves an ID to an unexpected paper (e.g., `2210.06413` should be Orca but resolves to EleutherAI; `2404.01869` should be Helix but resolves to a survey). **Always verify the resolved title** in the `add` output. If wrong:
1. Mark the bad entry as `digested` to get it out of the active queue
2. Re-add the correct paper via `add --manual --title "Correct Title" --url "https://correct-url"`

### Batch additions
When adding many papers at once (e.g., a recommended reading list), use `execute_code` with a loop over `subprocess.run()` calls. Check each result's stdout for the resolved title to catch mismatches early.

### Conference papers not on arXiv
Some important systems papers (Orca/OSDI, vLLM/SOSP) have arXiv preprints but the IDs may not match. For conference papers, prefer `--manual` with the USENIX/ACM URL rather than guessing arXiv IDs.

### `list` truncates titles and omits URLs
The `list` command output truncates long titles and does not show `url` or `arxiv_id`. When you need full details (e.g., to recommend a paper to the user), query SQLite directly:

```python
import sqlite3, os
db = os.path.expanduser("~/.hermes/skills/openclaw-imports/paper-queue/.paper_queue/queue.db")
conn = sqlite3.connect(db)
row = conn.execute("SELECT id, title, url, arxiv_id, authors, priority_score, abstract FROM papers WHERE id=?", (111,)).fetchone()
```

**Column name is `priority_score`, NOT `score`.** The CLI displays it as "Score" but the DB column is `priority_score`.

### `suggest` command can fail with URL encoding error
The `suggest` subcommand may crash with `URL can't contain control characters` due to unencoded spaces in the arXiv API query string. If this happens, suggestions can be obtained by querying arXiv API manually with proper URL encoding, or by using the `list --topic` filter instead.

### Manual entries with wrong metadata
Manual entries (`source: manual`) often have approximate or misremembered titles, wrong years, and missing URLs. When you discover the real paper:

1. **Search by system/acronym name, not title.** The queue title may say "SystemName: A Tetromino-Inspired Scheduling for Heterogeneous MoE (2025)" when the real paper is "Inference without Interference: Disaggregate LLM Inference (2024)" — but both share the system name "SystemName." Search `all:SystemName` on arXiv, not `ti:` with the full queue title.
2. **Use direct SQLite to fix metadata.** The `paper_queue.py` CLI has no update-metadata command. Connect to the DB directly:
   ```python
   import sqlite3
   conn = sqlite3.connect("~/.hermes/skills/openclaw-imports/paper-queue/.paper_queue/queue.db")
   conn.execute("UPDATE papers SET url=?, arxiv_id=?, authors=?, title=?, source='arxiv', status='digested' WHERE id=?", ...)
   conn.commit()
   ```
3. **Update all fields**: url, arxiv_id (set to the correct ID), authors, title (use the actual paper title, optionally appending the system name in parens), source (change from `manual` to `arxiv`).

## Commands Reference

| Command | Description |
|---------|-------------|
| `add <paper>` | Add paper (arXiv ID, URL, or tweet link) |
| `add --manual --title "..."` | Add paper manually |
| `list [--status S] [--top N] [--topic T]` | List queue |
| `status <id> <status>` | Update status (to-read, reading, digested) |
| `score [<id>]` | Re-score papers |
| `suggest [<id>]` | Get related paper suggestions |
| `stats` | Queue statistics |
