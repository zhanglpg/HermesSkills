#!/usr/bin/env bash
set -euo pipefail

# Hermes Backup Script
# Creates a timestamped tar.gz of all irreplaceable Hermes data

HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
BACKUP_DIR="${1:-$HOME/Documents/hermesbackup}"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_NAME="hermes-backup-${TIMESTAMP}.tar.gz"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

# Verify hermes home exists
if [ ! -d "$HERMES_HOME" ]; then
    echo "ERROR: Hermes home not found at $HERMES_HOME"
    exit 1
fi

echo "=== Hermes Backup ==="
echo "Source:  $HERMES_HOME"
echo "Target:  $BACKUP_PATH"
echo ""

# Build list of files/dirs to include (only those that exist)
INCLUDE_FILES=()

# Critical config
for f in config.yaml .env auth.json mem0.json; do
    [ -f "$HERMES_HOME/$f" ] && INCLUDE_FILES+=("$f")
done

# Session database (include WAL files for consistency)
for f in state.db state.db-wal state.db-shm; do
    [ -f "$HERMES_HOME/$f" ] && INCLUDE_FILES+=("$f")
done

# Gateway state
for f in gateway_state.json channel_directory.json; do
    [ -f "$HERMES_HOME/$f" ] && INCLUDE_FILES+=("$f")
done

# Directories
for d in memories skills cron; do
    [ -d "$HERMES_HOME/$d" ] && INCLUDE_FILES+=("$d")
done

if [ ${#INCLUDE_FILES[@]} -eq 0 ]; then
    echo "ERROR: No files found to backup"
    exit 1
fi

echo "Including:"
for f in "${INCLUDE_FILES[@]}"; do
    if [ -d "$HERMES_HOME/$f" ]; then
        SIZE=$(du -sh "$HERMES_HOME/$f" 2>/dev/null | cut -f1)
        echo "  📁 $f/ ($SIZE)"
    else
        SIZE=$(du -sh "$HERMES_HOME/$f" 2>/dev/null | cut -f1)
        echo "  📄 $f ($SIZE)"
    fi
done

echo ""

# Create backup
tar czf "$BACKUP_PATH" -C "$HERMES_HOME" "${INCLUDE_FILES[@]}" 2>/dev/null

# Verify
if [ -f "$BACKUP_PATH" ]; then
    BACKUP_SIZE=$(du -sh "$BACKUP_PATH" | cut -f1)
    FILE_COUNT=$(tar tzf "$BACKUP_PATH" | wc -l | tr -d ' ')
    echo "✅ Backup created successfully"
    echo "   File: $BACKUP_PATH"
    echo "   Size: $BACKUP_SIZE"
    echo "   Items: $FILE_COUNT files/dirs"
    echo ""
    echo "Contents summary:"
    tar tzf "$BACKUP_PATH" | head -30
    TOTAL=$(tar tzf "$BACKUP_PATH" | wc -l | tr -d ' ')
    if [ "$TOTAL" -gt 30 ]; then
        echo "   ... and $((TOTAL - 30)) more"
    fi
else
    echo "ERROR: Backup file was not created"
    exit 1
fi
