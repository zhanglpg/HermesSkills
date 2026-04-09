---
name: memory-pruning
description: >
  Prune built-in memory (memory + user profile) and migrate overflow entries
  to mem0 local. Use when either store exceeds ~80% capacity or when the user
  asks to clean up / reorganize memory.
tags: [memory, mem0, pruning, migration, maintenance]
triggers:
  - built-in memory or user profile exceeds 80% capacity
  - user asks to clean up, prune, or reorganize memory
  - need to free space for new high-priority entries
---

# Memory Pruning & Migration

## Triage: What to Keep in Built-in vs Migrate to mem0

Built-in memory is injected every turn — expensive real estate. Keep only what's
needed nearly every session. Everything else goes to mem0 (searchable on demand).

### KEEP in built-in (high-frequency, every-session facts):
- Model config and provider quirks (used on most tasks)
- Git rules (used on every commit)
- Active project repos (the ones being worked on now)
- CLI tool quirks that cause errors if forgotten
- Skills repo location (needed for skill sync)

### MIGRATE to mem0 (searchable when needed):
- Security/trust model rules (rarely referenced)
- GitHub repo URLs not actively being worked on
- Workspace organization paths (discoverable via filesystem)
- Detailed personality/intellectual character notes
- Historical config info (e.g. "was X, now Y")
- Tool config details (mem0 setup, embedder config)

## Procedure

### 1. Audit current state
Check both stores' usage percentages (shown in context header).

### 2. Write to mem0 FIRST (no data loss)
Use `mem0_conclude` to store each migrated fact. Batch independent calls.
- Combine related small entries into single conclusions
- Be explicit and self-contained — mem0 entries have no surrounding context

### 3. Confirm mem0 storage
Run `mem0_profile` to verify entries landed. Note: mem0 may auto-expand
your 8 explicit facts into 20+ inferred sub-facts — this is normal.

### 4. Remove from built-in memory
Use `memory(action='remove', old_text=...)` for each migrated entry.

### 5. Clean up separators and markers
After removing entries, orphaned `---` separators and section headers
remain. Remove these too — they waste chars.

## Pitfalls

### old_text matching is literal
- The `old_text` parameter must match the ACTUAL stored text
- HTML entities in the tool response (`&amp;`) are NOT what's stored — use
  the literal character (`&`) in your old_text parameter
- If a remove fails, check the raw entries list in the response for the
  exact text to match against

### Separator cleanup ordering
- Remove content entries first, THEN their `---` separators
- If multiple entries share the same separator text `---`, each remove call
  only deletes one instance

### mem0 lock conflicts
- If mem0 returns a Qdrant "already accessed" error, another process has the
  lock. Wait a moment or check for background hermes sessions.
- The `mem0_conclude` calls should all be batched together before any
  `mem0_search` or `mem0_profile` calls to minimize lock contention

### Capacity math
- Memory notes: 2,200 char limit
- User profile: 1,375 char limit
- Target after pruning: ~40-50% usage (leaves room for growth)
- Each separator `---` + section marker wastes ~20-40 chars

## Verification
After pruning, report before/after percentages for both stores plus
mem0 entry count. Format as a clear status table.
