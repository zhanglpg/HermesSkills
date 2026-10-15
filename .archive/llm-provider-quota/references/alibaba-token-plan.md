# Alibaba Token Plan (百炼) — quota knowledge bank

Source: official help docs (help.aliyun.com/zh/model-studio/token-plan-*), verified 2026-08.

## Balance lookup (the key fact)
**No billing/credit API exists.** The token-plan gateway
(`https://token-plan.cn-beijing.maas.aliyuncs.com`) returns a generic 400
"Required parameter model missing" catch-all on every non-inference path
(`/compatible-mode/v1/subscription`, `/billing/*`, `/credits`, `/quota`, …) and
404 elsewhere. No balance info in response headers (OpenAI or Anthropic protocol).
Docs confirm: usage is visible only at **百炼控制台 → Token Plan → 我的订阅**:
`https://bailian.console.aliyun.com/cn-beijing?tab=plan#/efm/subscription/overview`

Valid liveness probe instead: `POST /compatible-mode/v1/chat/completions` with
`max_tokens:1` → HTTP 200 proves key valid AND neither window currently capped.
Anthropic-compatible base URL: `https://token-plan.cn-beijing.maas.aliyuncs.com/apps/anthropic`.

## Key facts
- API keys start with `sk-sp-` (distinct from general DashScope keys).
- Two protocol base URLs (see above). Region: 华北2（北京）only.
- Hermes credential pool name: `alibaba-coding-plan` (2 env keys; older one may show stale `exhausted`/401 status — trust live probe).

## Personal edition (个人版) limits
Rolling windows, Credits unit, start counting at **first API call**, no rollover:
| Tier | Price | 5-hour cap | 7-day cap |
|------|-------|-----------|-----------|
| Lite | ~39元/月 promo | 700 | 2,500 |
| Standard | 139元/月 (orig 180) | 3,000 | 10,000 |
| Pro | 499元/月 (orig 600) | 12,000 | 40,000 |
| 用量包 Extra bundle | 100元/个/月, 20,000 Credits/个, max 5, 1-month validity, NOT window-bound |

- Either window hitting its cap pauses service; wait out the window, buy a 用量包, or use the 额度重置 feature (consumes reset credits).
- Credits per call are dynamic (model, tokens, thinking mode, tool calls); no published per-token coefficient — only the console 用量详情 is authoritative.
- qwen3.8-max: night discount 22:00–08:00 = 5折. `qwen3.8-max-preview` is retired but still routes to qwen3.8-max for billing.
- Supported models include: qwen3.8-max, qwen3.7-max, glm-5.2, deepseek-v4-pro/flash, wan2.7 image, audio/realtime.

## Team edition (团队版)
Monthly per-seat total (25k/100k/250k Credits/seat by tier), no 5h/7d windows; billing cycle = subscription anniversary month, one-time grant, no rollover.

## Recovery when capped
1. Wait for window reset (5h or 7d from first call in that window).
2. Buy 用量包 (extra bundle) — needs active subscription first.
3. 额度重置 feature (resets current window consumption to zero; limited uses).
4. Upgrade tier (up only; no downgrade).

## 429 classes on this endpoint
- `code 1305` "temporarily overloaded" → transient throttle, retry with backoff.
- Explicit insufficient-balance message → real exhaustion (console only).
