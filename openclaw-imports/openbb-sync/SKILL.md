---
name: openbb-sync
description: "Syncs the OpenBB repo from GitHub, reruns the data pipeline on changes, and restarts and verifies the dashboard. Silent by default -- reporting is the caller's responsibility. Use when the dashboard needs a data refresh or repo synchronization."
---

# OpenBB Sync Skill

Pull the OpenBB repo, rerun the data pipeline when changes are detected, and restart the dashboard. **Silent by default** — no Discord messages sent by this skill.

## Quick Start

```bash
# Run manually
bash ~/.hermes/skills/openclaw-imports/openbb-sync/scripts/sync.sh

# Check exit code
echo $?  # 0=success, 1=pipeline failed, 2=dashboard failed
```

## How It Works

1. **Safety Check:** Skips if uncommitted changes are detected (detects active development)
2. **Sync:** Pulls latest from GitHub
3. **Pipeline:** Runs full data refresh if repo changed
4. **Restart:** Restarts dashboard via launchctl
5. **Verify:** Confirms HTTP 200

**Note:** This skill does NOT send Discord messages. Reporting is the caller's responsibility.

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success (or skipped due to no changes/uncommitted work) |
| `1` | Pipeline execution failed |
| `2` | Dashboard verification failed |

## Safety Features

| Check | Action |
|-------|--------|
| Uncommitted git changes | Skip silently (active development detected) |
| No remote changes | Skip silently (nothing new) |
| Pipeline fails | Exit with code 1 |
| Dashboard fails health check | Exit with code 2 |

## Configuration

Variables at the top of `scripts/sync.sh`:

| Variable | Default | Purpose |
|----------|---------|---------|
| `OPENBB_DIR` | `$HOME/.openbb_platform` | OpenBB platform directory |
| `LOG_FILE` | `/tmp/logs/skills/openbb-sync/sync.log` | Log file location |
| `DASHBOARD_URL` | `http://localhost:8501` | Dashboard health check URL |

## Dependencies

| Tool | Purpose |
|------|---------|
| bash | Script runtime |
| git | Repo sync |
| python 3 | Pipeline execution (via venv at `$OPENBB_DIR/.venv`) |
| curl | Health check |
| launchctl | Dashboard restart (macOS-specific) |
