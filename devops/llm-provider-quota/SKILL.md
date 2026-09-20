---
name: llm-provider-quota
description: Check remaining credits/quota on LLM subscription plans...
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [quota, credits, billing, token-plan, provider]
---

# LLM Provider Quota & Credits

Verify remaining credits/balance/quota on model subscription plans (Alibaba Token Plan, coding plans, etc.) and estimate consumption locally when the provider exposes no billing API.

## When to use
- "How many credits/quota do I have left on plan X?"
- Calls blocked by limit/balance errors — need to distinguish exhaustion from transient throttling.

## Workflow

1. **Identify the active provider and credential.**
   - `~/.hermes/config.yaml` → `model.provider` + `model.base_url`.
   - `~/.hermes/auth.json` → `credential_pool.<provider>` is a **list** of dicts (label, source, base_url, last_status, last_error_*). API key values are NOT stored there — keys come from env vars named by the entry's `source` (e.g. `env:DASHSCOPE_API_KEY` in `~/.hermes/.env`).
   - Pool status can be stale (e.g. `exhausted` recorded against a deprecated key while a sibling key works). Trust a live probe over pool status; `hermes auth list` shows all pools.

2. **Check provider references first** (`references/`) — most subscription gateways expose no billing API and blind probing wastes turns. Known: `references/alibaba-token-plan.md`.

3. **Unknown provider: probe billing endpoints exactly once.** Try OpenAI-style `/v1/dashboard/billing/subscription`, `/v1/dashboard/billing/credit_grants`, `/v1/dashboard/billing/usage`. Interpretation: 404 or the same generic 400 catch-all on every path (e.g. "Required parameter model missing") means the route doesn't exist → no billing API; fall back to console + local estimation. Do not loop over more paths.

4. **Live probe: is the key valid and under cap?** Minimal completion — `POST {base_url}/chat/completions` with `{"model": ..., "messages":[{"role":"user","content":"hi"}], "max_tokens":1}`. HTTP 200 ⇒ key valid AND not currently capped. Costs ~1 output token.

5. **Distinguish 429 classes:**
   - Body code `1305` / "temporarily overloaded" ⇒ transient throttle; back off and retry. NOT exhaustion.
   - Explicit "insufficient balance/credits" wording ⇒ real exhaustion.

6. **Estimate consumption locally** with `scripts/estimate_usage.py` (read-only against `~/.hermes/state.db`, table `session_model_usage`, filtered by `billing_base_url`): window totals, daily breakdown, and activity gaps — a gap >26h before continuous daily use suggests the start of a rolling window.

7. **Report**: what is confirmed (key valid / not capped right now), local consumption estimate, the exact console URL for the authoritative balance, and the estimated window reset time. Offer a cron reminder before the reset.

## Pitfalls
- Do not present failed billing-endpoint probes as "the endpoint is broken" — the 400 catch-all just means the route doesn't exist; the same key can work fine for chat.
- Rolling-window plans (e.g. Token Plan personal) start counting from the **first API call**, not the purchase date; unused quota does not roll over.
- Credits-per-call are dynamic (model, token count, thinking mode, tool calls) — local token counts only approximate credits; the provider console is authoritative.

## Support files
- `references/alibaba-token-plan.md` — tiers, window rules, console URL, key format, recovery options.
- `scripts/estimate_usage.py` — local usage/window estimator against state.db.
