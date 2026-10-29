---
name: cronjob-management
description: Use when Hermes cron jobs fail, skip, or go silent.
---

# Cronjob Management

Triage, repair, and re-run Hermes scheduled jobs.

## When to Use

- A cron job has `last_status: error`, silently skips, or its output never arrives.
- The user asks to retry / re-run / fix a scheduled job.
- You're creating a job and want durable delivery and pinning settings up front.

## 1. Triage first

`cronjob action=list` — read these fields per job:

- `last_status`: `ok` / `error`
- `last_error`: the *agent-run* failure (e.g. model drift skip, script crash)
- `last_delivery_error`: the *delivery* failure (job may have succeeded but the message never landed)

These are independent failure channels — a job can have BOTH (seen in the wild: run skipped for drift AND delivery 404 on the same tick). Check both before declaring a fix.

For deeper fields (`deliver`, `origin`, pinned `provider`/`model`, `workdir`), read `~/.hermes/cron/jobs.json` directly.

## 2. Retry a failed job

`cronjob action=run job_id=<id>` — fires in the background immediately; outcome re-enters the conversation when done. Don't poll. Optionally pass `prompt=` for transient per-run context.

If the job has a known broken config, **fix the config first, then retry** — otherwise you just reproduce the failure.

## 3. Delivery failures (404 Unknown Channel)

Symptom: `last_delivery_error` contains `404 ... Unknown Channel` (Discord code 10003).

Cause: the delivery target channel was deleted. Watch out for `deliver: "all"` — it fans out to every home channel at fire time, so one dead home channel breaks delivery for the whole job.

Repair recipe:
1. Find the live channel: check `DISCORD_HOME_CHANNEL` in `~/.hermes/config.yaml`, and/or the "Home Channels" block in session context.
2. Verify the candidate channel is alive: `discord` tool `fetch_messages` with a small limit. 404 = dead, messages = live. Also confirm the dead ID actually 404s so you're sure of the diagnosis.
3. `cronjob action=update job_id=<id> deliver=discord:<live_channel_id>` — prefer an explicit channel ID over `origin` or `all` for durability (chat-created jobs often have `origin: null` anyway).
4. Grep `~/.hermes/cron/jobs.json` and `~/.hermes/config.yaml` for the dead channel ID to catch other jobs/configs referencing it.

## 4. Model/provider config drift skip

Symptom: `last_error` says *"Skipped to prevent unintended spend: global inference config drifted since this job was created ... and this job is unpinned. No inference call was made."*

Cause: global provider/model changed since the job was created; unpinned jobs refuse to spend on the new config.

Fix: pin the job to explicit values. **The `cronjob` MCP tool does NOT expose `provider`/`model` parameters** — an update call with only unsupported fields returns "No updates provided." Use the CLI:

```bash
hermes cron edit <job_id> --provider <provider> --model <model>
```

Pin the CURRENT global values (check `~/.hermes/config.yaml`) unless the user wants the legacy ones. The error message itself names the exact provider/model transition — use those strings.

Note: `hermes cron update` does not exist; the CLI verb is `edit`. `hermes cron edit --help` lists all flags (`--deliver`, `--schedule`, `--prompt`, `--workdir`, `--model`, `--provider`, etc.).

## 5. Verify

After repairs, confirm final state before reporting success: re-read the job via `cronjob action=list` or parse `~/.hermes/cron/jobs.json` for the specific fields you changed.

## 6. Script-gated jobs (script + agent, create-time)

- The `script` field accepts ONLY a filename relative to `~/.hermes/scripts/`;
  absolute or `~/...` paths are rejected at create. To run a pipeline that
  lives in a repo, add a thin wrapper in `~/.hermes/scripts/` that
  `subprocess.run`s the repo script (cwd=repo dir) and forwards stdout/exit
  code — keeps the real logic version-controlled next to its output.
- Have the script print sentinel lines (`NO_CHANGE`, `ERROR=...`, `FLAGS=...`,
  plus KEY=VALUE data lines) and write the job prompt to BRANCH on them:
  NO_CHANGE → one-line reply (or `[SILENT]`); ERROR → verify the live artifact
  is intact, then report; specific FLAGS → named repair steps. All report
  numbers must come from script stdout only — the agent formats, never
  recomputes, so figures can't hallucinate.
- Make the script idempotent (skip + print NO_CHANGE when upstream data is
  unchanged, e.g. same quote date) so weekends/holidays cost a one-liner
  instead of a full report run.

## Pitfalls

- **Manual `cronjob run` before the next scheduled fire silently swallows that fire**: the manual execution's DB row gets `scheduled_instant` = the UPCOMING occurrence (e.g. run at 12:15 → instant = next day 08:25). At that occurrence the scheduler's dedupe index (`executions(job_id, scheduled_instant) WHERE status='completed'`) treats it as done and skips — no log line, no error, `next_run_at` just advances. Symptom: job `last_status: ok` but zero activity at its fire time (check `sqlite3 ~/.hermes/cron/executions.db "SELECT scheduled_instant,status FROM executions WHERE job_id='<id>'"`). One-off; the following day fires normally. If the skipped run did real work, backfill manually.
- `deliver: "all"` is fragile: resolves at fire time against every home channel; one deleted channel = delivery error. Prefer explicit `discord:<channel_id>`.
- `last_status: error` with `last_delivery_error: null` means the RUN failed, not delivery — read `last_error` (or jobs.json) for why.
- Jobs created from chat frequently have `origin: null`; never assume `deliver: origin` will work on them.
- When the user says "retry the latest failed job": list ALL jobs and pick the most recent `last_run_at` among those with `last_status == error` — don't assume it's the one you last touched.
- Report adjacent latent failures you notice while triaging (e.g. another job with the same dead channel) — but get user confirmation before changing jobs they didn't ask about.

See `references/error-signatures.md` for exact error strings to pattern-match against.
