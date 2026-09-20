---
name: openai-compatible-api-audit
description: "Audit vendor OpenAI-compatible APIs vs upstream OpenAI."
tags:
  - research
  - api-compatibility
  - openai
  - providers
---

# OpenAI-Compatible API Audit

Compare a provider's OpenAI-compatible endpoint (Bailian/DashScope, DeepSeek, Moonshot, Zhipu, etc.) against the real OpenAI API — supported formats, parameters, tools, and behavior — fact-checked against official docs. Use when the user asks "how does provider X's <endpoint> differ from OpenAI" or wants a compatibility/migration assessment.

## Workflow

### 1. Locate the vendor's official docs (never guess URLs)

Vendor help centers 404 on guessed paths. Use the site's own search:

- **help.aliyun.com (百炼/Model Studio):** search via `https://www.aliyun.com/search/?k=<keyword>&scene=all` (help.aliyun.com/search redirects there). Click through to the doc page.
- Find the endpoint family from the doc sidebar — e.g. the Responses API family is 创建响应 / 获取响应 / 删除响应 / 获取输入项列表, which tells you which CRUD operations exist before reading a word.

**Aliyun doc content extraction (verified):** the page is React-rendered; `article`/`document.body.innerText` return near-nothing. The content lives in:

```javascript
document.querySelector('.icms-help-docs-content').innerText      // full text
document.querySelectorAll('.icms-help-docs-content table')       // parameter tables
```

Parameter sub-tables hide behind collapsed sections marked with class `expandable-title` — the top-level parameter list is in the first table, but per-param attribute tables (input item types, tools attributes, reasoning sub-fields) may need expanding/clicking or appear as separate tables further down.

### 2. Find the vendor's compatibility statement

Most vendors state an organizing principle up front — Bailian's is: **"请求将仅处理本文档明确列出的参数，任何未提及的 OpenAI 参数都会被忽略"** (whitelist semantics; undocumented OpenAI params are silently ignored). Quote it; it frames the whole comparison. Then enumerate the whitelist of supported request params from the reference table.

### 3. Get the upstream OpenAI facts

`platform.openai.com/docs` is Cloudflare-walled against headless browsers. Machine-readable alternative: the official OpenAPI spec at `https://raw.githubusercontent.com/openai/openai-openapi/master/openapi.yaml` (public repo, curl-able). For well-known parameter sets, curated knowledge is fine — but in the deliverable, separate "per vendor docs" claims from "per OpenAI spec" claims so the user knows which side was actually verified this session.

### 4. Structure the comparison

The shape that landed well (tables + short verdict, in the user's language):

1. **总原则** — the vendor's compatibility principle, quoted
2. **端点与操作** — which CRUD/list operations exist on each side (table)
3. **不支持的参数** — OpenAI params the vendor silently ignores (group: async/background, structured output, logprobs, caching keys, metadata/user/service_tier, etc.)
4. **行为差异** — params that exist on both sides but differ (enum values, defaults, semantics, ranges). Watch for semantic traps, e.g. Bailian's `max_output_tokens` counts thinking tokens for Qwen3.8 series only
5. **厂商扩展** — vendor-only params/tools (Bailian: `enable_thinking`, `ocr_options`, `x-dashscope-session-cache` header, web_extractor/文搜图/图搜图 tools, Conversations API)
6. **多轮/缓存/流式差异** — response-id format & TTL, instructions carry-over rules, caching mechanism design, streaming event coverage gaps (which tools have dedicated SSE events vs generic output_item events)
7. **其他** — model scope, URL/path deprecations, SDK gotchas
8. **一句话结论** + doc source URLs

### 5. Pitfalls

- **Guessing help-center URLs → 404.** Always go through the site search.
- **`article` selector on Aliyun docs is empty** — use `.icms-help-docs-content`.
- **Distinguish "not documented" from "documented as unsupported".** A param absent from the whitelist is silently ignored; a param the docs explicitly discuss (e.g. Bailian's `background`: 仅支持同步调用) is a confirmed gap — the latter are the headline differences, quote them.
- **Collapsed attribute tables** (`expandable-title`) hide the details that make the comparison precise — check for them before declaring a param has no sub-options.
- **Vendor response bodies echo OpenAI fields as null** for unsupported features (Bailian FAQ says so explicitly) — don't read nulled echo fields as support.
- **Docs move fast** — date-stamp any saved fact snapshot and re-verify before reusing.

## References

- `references/bailian-responses-api-2026-08.md` — verified snapshot of Bailian Responses API surface vs OpenAI (Aug 2026), with doc URLs. Re-verify before citing.

## Related

- `ai-model-competitive-analysis` — model/pricing strategy comparisons (different axis: this skill audits API surface, not model quality)
- `grounded-citations` — citation ledger when the deliverable is a formal written report
