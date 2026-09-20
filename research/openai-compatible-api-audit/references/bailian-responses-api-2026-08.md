# Bailian (百炼) Responses API vs OpenAI — verified snapshot, Aug 2026

Fact-checked against official Aliyun docs. Re-verify before reusing — this API moves fast.

**Sources:**
- Guide: https://help.aliyun.com/zh/model-studio/compatibility-with-openai-responses-api
- Reference: https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-responses
- Content selector: `.icms-help-docs-content` (not `article`)

## Compatibility principle (quoted from docs)
"请求将仅处理本文档明确列出的参数，任何未提及的 OpenAI 参数都会被忽略" — whitelist semantics.

## Endpoint family (all four exist)
创建响应 POST /responses · 获取响应 GET /responses/{id} · 删除响应 DELETE /responses/{id} · 获取输入项列表 GET /responses/{id}/input_items

## Request param whitelist (Bailian)
`model, input (string | Chat-style array), instructions, previous_response_id, conversation, stream, store (default true), tools, tool_choice (auto/none/required), temperature [0,2), top_p, reasoning, max_output_tokens`

## OpenAI params NOT supported (silently ignored)
`background` (explicitly named in docs: 仅支持同步调用), `include`, `metadata`, `user`, `service_tier`, `max_tool_calls`, `parallel_tool_calls` (response echoes fixed `false`), `text` (no structured-output JSON Schema), `top_logprobs`, `truncation`, `prompt_cache_key`, `prompt_cache_retention`, `reasoning.summary/generate` (Bailian returns plaintext `summary_text` instead).

## Behavior differences
- `reasoning.effort`: none/minimal/low/medium(default)/high — has `none`, unlike OpenAI
- No `thinking_budget`; vendor-only `enable_thinking` bool (via extra_body), being deprecated in favor of reasoning.effort
- `max_output_tokens` = reply + thinking tokens for Qwen3.8 series; reply-only for others; overrun → status `incomplete`
- `previous_response_id`: response id is UUID, TTL **7 days**; previous turn's `instructions` NOT carried forward; mutually exclusive with `conversation` (Conversations API)
- Response IDs: UUID vs OpenAI `resp_` prefix

## Built-in tools
Bailian: `web_search`, `web_extractor` (网页抓取 — no OpenAI equivalent as standalone), `code_interpreter`, `web_search_image` (文搜图), `image_search` (图搜图), `file_search` (知识库搜索, backed by Bailian KB), `mcp`, custom function. Missing vs OpenAI: computer_use, image_generation, hosted_shell. web_extractor & code_interpreter 限时免费.

## Streaming events
Same SSE protocol names + `sequence_number`. Dedicated events for web_search/code_interpreter/file_search/mcp; **no dedicated events for web_extractor/web_search_image/image_search** (identify via output_item.added/done + item.type). Documented OpenAI events not guaranteed: function_call_arguments.delta/done, refusal.*, error, rate_limits.updated.

## Caching
OpenAI prompt_cache_key/retention unsupported. Bailian uses request header `x-dashscope-session-cache: enable` (default disable): server-side auto session cache, min 1024 tokens, TTL 5 min; hits reported via `usage.input_tokens_details.cached_tokens`.

## Response extras
`usage.x_details` (billing detail, `x_billing_type: response_api`), `usage.x_tools` (per-tool call counts). Unsupported OpenAI fields echoed as null (FAQ explicitly says so).

## Models (Aug 2026)
qwen3-max/3.8-max/3.7-max + dated snapshots, 3.7/3.6/3.5 plus & flash, qwen-plus, qwen-flash, qwen3-coder plus/flash/next, open sizes (35b-a3b, 397b-a17b, 122b-a10b, 27b), deepseek-v4-flash (Beijing/Singapore only).

## URLs
- Old path `/api/v2/apps/protocols/compatible-mode/v1/responses` being deprecated → `/compatible-mode/v1/responses`
- Recommended workspace domains: `https://{WorkspaceId}.cn-beijing.maas.aliyuncs.com` (Beijing), `https://{WorkspaceId}.ap-southeast-1.maas.aliyuncs.com` (Singapore); regions also: US Virginia, Frankfurt, Tokyo
- SDK gotcha: OpenAI Python SDK 1.99.x dropped `output_text` property — upgrade

## OpenAI side (from public spec knowledge, not re-fetched this session)
platform.openai.com is Cloudflare-walled to headless browsers; use https://raw.githubusercontent.com/openai/openai-openapi/master/openapi.yaml for machine-readable upstream facts.
