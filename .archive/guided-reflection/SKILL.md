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
- **Cron delivery may be missed.** If the user directly asks about the program ("问题是什么？", "今晚的提问呢"), assume the cron delivery failed or was overlooked. Don't search for the cron output — go straight to reading `state.json`, generate the current day's questions manually, and continue the conversation live.

## Manual Recovery

When the user prompts for questions outside the cron run (e.g., in chat):

1. **Read state.json** to get current day, phase, and full history.
2. **Generate 3 questions** contextualized to the phase and the user's previous answers — each question should reference specifics from past responses to show continuity.
3. **Deliver in-chat** using the same format as the cron job:
   ```
   📅 Day N · 阶段：XXX

   Q1. ...
   Q2. ...
   Q3. ...
   ```
4. **After user answers, save immediately** — add entry to history array with answers_summary, then increment current_day.
5. **If user asks for another round** ("再继续问一组"), advance the day, generate the next set, and save again after answers.

## Program References

- `references/self-inquiry-20day.md` — 20-day existential self-inquiry program (daily → patterns → values → fears)
