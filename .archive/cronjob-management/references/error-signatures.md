# Cron Job Error Signatures

Exact strings seen in `last_error` / `last_delivery_error`, with diagnosis and fix.

## Delivery: deleted Discord channel

```
live adapter send failed: 404 Not Found (error code: 10003): Unknown Channel;
live adapter delivery to discord:<channel_id> failed: 404 Not Found (error code: 10003): Unknown Channel;
delivery error: Discord API error (404): {"message": "Unknown Channel", "code": 10003}
```

- **Diagnosis:** target channel deleted (or bot lost access). If job has `deliver: "all"`, the 404 names the dead channel in the error text.
- **Fix:** verify a live home channel (`DISCORD_HOME_CHANNEL` in config.yaml; probe with `discord` tool `fetch_messages`), then `cronjob action=update deliver=discord:<live_id>`.
- Observed 2026-08: `coros-dashboard-sync` with `deliver: "all"` broke on deleted channel `1491210397100019752`; live replacement was `1491211614265802832` from config.yaml `DISCORD_HOME_CHANNEL`.

## Run skip: provider/model config drift

```
RuntimeError: Skipped to prevent unintended spend: global inference config drifted since
this job was created (provider '<old>' -> '<new>'; model '<old>' -> '<new>'), and this
job is unpinned. No inference call was made. To run on the new config, pin it explicitly:
`cronjob action=update job_id=<id> provider=<provider> model=<model>`
(or pin the original values to keep them). See #44585.
```

- **Diagnosis:** global inference config changed; unpinned job refuses to spend on new config.
- **Fix:** pin via CLI — `hermes cron edit <job_id> --provider <provider> --model <model>`. The MCP `cronjob` tool has NO provider/model params; an update call without supported fields returns `"No updates provided."` The CLI error-message suggestion (`cronjob action=update ... provider=...`) is misleading for tool use; the CLI verb `hermes cron edit` is what works.
- Observed 2026-08: drift `alibaba-coding-plan` → `alibaba`, `qwen3.8-max-preview` → `qwen3.8-max`; pinned with `hermes cron edit 844e0dcf1dbf --provider alibaba --model qwen3.8-max`, verified by re-reading `~/.hermes/cron/jobs.json`.

## Notes on co-occurrence

Both failures can hit the same job on the same tick (drift skip = run error; then the error notification itself fails delivery). Fix both before retrying:
1. pin provider/model (CLI), 2. fix delivery target (tool), 3. verify in jobs.json, 4. `cronjob action=run`.
