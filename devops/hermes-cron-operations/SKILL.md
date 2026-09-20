---
name: hermes-cron-operations
description: "Use when inspecting/auditing Hermes cron jobs."
tags: [cron, hermes, ops, debugging]
---

# Hermes Cron Operations

Inspect and debug scheduled jobs beyond what `cronjob action='list'` shows.

## When to use
- "What cron jobs are configured?" / "Is there a recently added job for X?"
- A job appears to run but nothing arrives (silent runs).
- You need run history or exact creation timestamps.

## Inspecting jobs

1. Start with `cronjob action='list'` — gives name, schedule, deliver, last_status, next_run, script/monitor_script. **Note: this output has NO `created_at` field** — it cannot answer "recently added" questions.
2. For creation dates, read `~/.hermes/cron/jobs.json` directly. It is a JSON list of job dicts; useful fields: `id`, `name`, `created_at` (ISO with tz), `deliver`, `schedule_display`, `monitor_script`, `workdir`, `enabled_toolsets`, `paused_at`, `last_delivery_error`. Use the helper to list newest-first:
   ```bash
   python3 ~/.hermes/skills/devops/hermes-cron-operations/scripts/recent_jobs.py [N]
   ```
   Prints jobs sorted by `created_at` descending (all by default, or the N most recent).
3. **Do not infer job age from file timestamps.** `jobs.json` is rewritten by the scheduler on ticks, so its mtime ≈ last tick, not last edit. State files beside it (e.g. `github-state.json`, `email-state.json`) belong to job scripts, not job definitions. The per-job `created_at` field is the only reliable age signal.

## Run history and debugging silent jobs

- `~/.hermes/cron/output/` — per-run output artifacts.
- `~/.hermes/cron/executions.db` — SQLite run log.
- `~/.hermes/cron/usage_audit.jsonl` — per-run audit lines.

Silent-job checklist:
1. Check `last_delivery_error` (in jobs.json or list output) — a 404 usually means a deleted channel; prefer explicit channel IDs over channel names.
2. Jobs created from chat can have `origin: null` — with no explicit `deliver`, output is saved locally only and nobody is notified.
3. Monitor-mode jobs (`monitor_script`/`monitor_url` set) suppress the agent run AND delivery when the output hash is unchanged — silent `no_change` ticks are by design, not failures. The first tick always runs the agent (baseline).
4. `deliver: 'local'` means deliberately no notification (watchdog pattern) — confirm intent before "fixing" it.

## Pitfalls
- From a CLI session, jobs with default/`origin` delivery will NOT message the terminal — there is no live channel; target a gateway platform (e.g. `deliver='telegram'` or `'all'`) if the user expects notification.
- When asked "what jobs exist", re-run the list fresh — jobs may have been added by other sessions since any earlier list in the conversation.
