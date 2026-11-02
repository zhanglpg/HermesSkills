---
name: hermes-cron-operations
version: 1
author: Hermes Agent
license: MIT
description: Diagnose failing Hermes cron jobs and harden their runs.
metadata:
  hermes:
    tags: [cron, scheduler, debugging, automation]
    related_skills: [himalaya-gmail, hermes-config-hygiene]
---

# Hermes cron jobs: diagnose failures, harden runs

## When to Use

- A scheduled job reports failure, stops delivering, or delivers an empty message.
- Writing or editing a cron prompt that shells out to scripts, network calls, or a TUI.
- Any job that must stay silent when there is nothing new.

## Diagnose in this order

1. **List the jobs** — `cronjob_manage(action='list')`. Record `job_id`, `schedule`,
   `deliver`, `last_status`, `last_error`, `last_run_at`, `last_delivery_error`.
   `last_delivery_error` (e.g. a 404) means the run worked but the channel is gone —
   a different bug from a failed run.
2. **Read the execution record** — this separates `failed` from `completed` and shows
   how long the run actually took:
   ```bash
   sqlite3 ~/.hermes/cron/executions.db \
     "SELECT claimed_at, finished_at, status, error FROM executions \
      WHERE job_id='<id>' ORDER BY claimed_at DESC LIMIT 5;"
   ```
3. **Read the rendered run** — `ls -lt ~/.hermes/cron/output/<job_id>/ | head`, then
   read the newest `.md`. It carries the full prompt, the pre-run script output, and
   the terminal exception. A file titled `(FAILED)` is the scheduler's own record.
4. **Find the slow or dead tool call** — grep `~/.hermes/logs/agent.log` for the
   session id from that window for `tool ... completed (<secs>s)` and `Turn ended:`.
   `interrupted_by_system(session_turn_lease_lost)` means the turn outlived its
   lease and was killed mid-call.
5. **Reproduce by hand** — run each command in the prompt with `time` and a timeout.
   Do not guess which step hung; the log gives you the duration, the shell gives you
   the current behaviour.

## What actually breaks jobs

- **`RuntimeError: agent reported failure` with no message is not a model error.**
  It means the turn died without producing a final response. Chase the slow tool
  call, not the prompt's logic.
- **One unbounded command can consume the whole lease.** A single terminal call
  running for many minutes is enough for the scheduler to kill the turn and record a
  generic failure. Every command in a cron prompt gets `timeout <seconds>`.
- **Inline code in prompts is re-derived on every run.** Placeholders go
  unsubstituted and formats drift (e.g. an IMAP `SEARCH` built with an ISO date —
  IMAP wants `dd-Mon-yyyy` and returns `BAD [Could not parse command]`). Move logic
  into a committed script under `~/.hermes/scripts/` and call that with a timeout.
- **TUIs hang forever with no TTY.** Bare `himalaya`, editors, pagers. Always pass a
  subcommand and non-interactive flags.
- **Hand-rolled protocol code loses to the configured client.** Prefer the CLI that
already owns the credentials (`himalaya envelope list --json`) over an inline snippet
that re-implements IMAP and re-reads the password out of Keychain. Measured on the
same mailbox: 3.3 s vs 50 s, and only the CLI version was correct. A second hardcoded
lookup keychain key is a second thing that can disappear.
- **Silent jobs hide their own failure.** A job designed to send nothing when idle
  will also send nothing when it breaks; check `last_status` and the output dir rather
  than assuming quiet means healthy.
- **A checkpoint that only advances on a successful report makes the next run
  re-read the same window.** Update the checkpoint unconditionally at the end.

## Hardening rules for a cron prompt

1. Self-contained: the job runs in a fresh session with no chat context. State the
   goal, the exact commands, and the output shape.
2. One bounded command per step; on timeout, report the step and continue instead of
   abandoning the run.
3. Silence contract: an exact token for nothing-to-report, with nothing else in the
   message.
4. Delivery target explicit — chat-created jobs often carry no origin. Verify with a
   test fire and read `last_delivery_error`.
5. Keep the final checkpoint-update step unconditional.

## Verify a fix

- `cronjob_manage(action='run', job_id=...)` fires in the background; the outcome
  re-enters the conversation. Do not poll for it.
- Confirm the new execution row is `completed` and the delivered text matches the
  expected shape; then let the next scheduled fire confirm it independently.

## Pitfalls

- Job IDs are opaque — always list before acting, never guess one.
- A pre-run script's stdout is injected into the prompt. If the prompt also fetches
  the same data itself, two divergent copies reach the model; keep one source.
- Cron sessions are not normal chat sessions: they cannot ask questions, and their
  final response is the only thing delivered. Put the answer in the final response,
  never in a side effect.
