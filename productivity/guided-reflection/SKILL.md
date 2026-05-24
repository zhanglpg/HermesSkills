---
name: guided-reflection
description: "Multi-day structured questioning/reflection programs — state tracking, cron delivery, phase progression."
version: 1.0.0
category: productivity
metadata:
  hermes:
    tags: [journaling, reflection, coaching, cron, self-inquiry]
---

# Guided Reflection Programs

Run multi-day structured questioning programs (self-inquiry, journaling prompts, coaching frameworks) via cron-driven daily delivery with state tracking.

## When to Use

- User asks for a "N-day" questioning/reflection/journaling program
- User wants daily prompts delivered on a schedule
- Any structured multi-session interaction where progress must persist across cron runs

## Pattern

Three components working together:

```
state.json          →  tracks day, phase, history
state-reader script →  reads state, outputs context for agent
cron job            →  fires daily, agent reads context + generates + updates state
```

## Setup

### 1. State File

Create a JSON state file tracking progress. Minimal schema:

```json
{
  "program": "Program Name",
  "current_day": 0,
  "total_days": 20,
  "schedule": { "days_1_5": "Phase 1", "days_6_10": "Phase 2", ... },
  "history": [
    { "day": 1, "phase": "Phase 1", "questions": [...], "answers_summary": "..." }
  ]
}
```

### 2. Context Script

A Python script at `~/.hermes/scripts/<name>-state.py` that reads state.json and outputs context (CURRENT_DAY, CURRENT_PHASE, HISTORY). The cron job uses this as its `script` parameter — output is injected into the agent's prompt.

### 3. Cron Job

```bash
cronjob action=create \
  name="Program Name" \
  schedule="0 21 * * *" \
  script="<name>-state.py" \
  prompt="[instructions for the agent: generate content, update state]"
```

Key: the agent's prompt must include instructions to **update state.json via write_file** after each run — increment day, append history entry.

## Pitfalls

- **Script path must be relative** to `~/.hermes/scripts/`. Absolute paths are rejected.
- **Cron runs are stateless** — the agent has no memory of previous runs. All context must come from the script output.
- **State updates are the agent's responsibility.** If the prompt doesn't explicitly tell it to write state, progress will stall.
- **Phase transitions** — the script should compute the current phase from the day number, not rely on the agent to figure it out.

## Program References

- `references/self-inquiry-20day.md` — 20-day existential self-inquiry program (daily → patterns → values → fears)
