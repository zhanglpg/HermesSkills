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
