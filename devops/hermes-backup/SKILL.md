---
name: hermes-backup
description: "Backup Hermes agent config, sessions, memories, and skills. Excludes reinstallable components (venv, binaries). Creates timestamped tar.gz archives."
---

# Hermes Backup

Create a backup of all irreplaceable Hermes data — config, credentials, session history, memories, and skills.

## When to Use

- Before upgrading Hermes
- Periodic backup (weekly/monthly)
- Before major config changes
- When migrating to a new machine

## What Gets Backed Up

| Component | Path | Why |
|-----------|------|-----|
| Config | `config.yaml` | All settings, model, gateway config |
| Credentials | `.env`, `auth.json`, `mem0.json` | API keys, provider auth |
| Sessions | `state.db`, `state.db-wal`, `state.db-shm` | Full conversation history |
| Memories | `memories/` | Built-in MEMORY.md / USER.md |
| Skills | `skills/` | Installed skills |
| Gateway state | `gateway_state.json`, `channel_directory.json` | Platform bindings |
| Cron | `cron/` | Scheduled jobs and run history |

## What Gets Excluded

- `hermes-agent/` — code + venv (~900MB, reinstallable via `hermes update`)
- `bin/` — CLI binaries (reinstallable)
- `logs/` — runtime logs (ephemeral)
- `cache/`, `models_dev_cache.json` — regenerated automatically
- `migration/` — one-time migration scripts
- `images/` — cached images
- `*.pid` — process ID files

## Usage

```bash
bash ~/.hermes/skills/devops/hermes-backup/scripts/backup.sh [backup_dir]
```

- Default backup directory: `~/Documents/hermesbackup/`
- Creates: `hermes-backup-YYYYMMDD-HHMMSS.tar.gz`
- Prints backup size and contents summary
- Exits with 0 on success, 1 on failure

## Restore

```bash
# Full restore (overwrites current config)
tar xzf ~/hermes-backups/hermes-backup-XXXXXXXX-XXXXXX.tar.gz -C ~/.hermes

# Selective restore (e.g., just config)
tar xzf ~/hermes-backups/hermes-backup-XXXXXXXX-XXXXXX.tar.gz -C ~/.hermes config.yaml .env

# After restore, restart gateway
hermes gateway restart
```

## Pitfalls

- **state.db WAL files:** Always backup `state.db-wal` and `state.db-shm` together with `state.db` — they contain uncommitted data
- **Credentials:** Backup contains API keys in plaintext — store securely
- **.env may not exist:** Script handles this gracefully
- **Cron runs history:** Can be large if many jobs; included but optional
