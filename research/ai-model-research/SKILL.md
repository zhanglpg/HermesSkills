---
name: ai-model-research
title: "AI Model Research & Comparison"
description: "Use when researching AI model specs, pricing, benchmarks."
triggers:
  - User asks to research or compare AI/LLM models
  - User wants benchmark scores, pricing, or specs for specific models
  - User asks about model positioning or competitive landscape
  - User mentions artificialanalysis.ai, model leaderboards, or API pricing
---

# AI Model Research & Comparison

Multi-source workflow for gathering authoritative AI model data: specs, benchmarks, pricing, and competitive positioning.

## Source Priority Order

1. **artificialanalysis.ai** — AA Intelligence Index scores, speed, pricing, parameter counts, context windows. Most structured data.
2. **Official API docs** (api-docs.deepseek.com, help.aliyun.com, etc.) — Canonical pricing, model IDs, feature matrices.
3. **Vendor sites** (qwen.ai, deepseek.com, openai.com) — Announcements, architecture details, blog posts.
4. **HuggingFace** (huggingface.co/models) — Open-weight model cards, parameter counts, config.json for architecture details.

## Workflow

### Step 1: AA Model Pages
- URL pattern: `artificialanalysis.ai/models/<slug>` (e.g., `deepseek-v4-flash`, `qwen3-7-max`)
- Slugs use lowercase, hyphens, dots become hyphens (qwen3.7-max → qwen3-7-max)
- Returns: Intelligence Index score, pricing, speed, context window, total/active parameters, license
- If 404: model not yet benchmarked or slug is wrong — try variants

### Step 2: AA Leaderboard (for competitive context)
- URL: `artificialanalysis.ai/leaderboards/models`
- **Use browser_console JS extraction** — the table is huge and snapshots truncate:
```javascript
(() => {
  const rows = document.querySelectorAll('table tbody tr');
  const results = [];
  rows.forEach(r => {
    const cells = r.querySelectorAll('td');
    if (cells.length > 3) {
      const name = cells[0]?.textContent?.trim();
      if (name && name.toLowerCase().includes('TARGET')) {
        results.push({
          model: name,
          context: cells[1]?.textContent?.trim(),
          intelligence: cells[3]?.textContent?.trim(),
          costPerTask: cells[4]?.textContent?.trim(),
          speed: cells[5]?.textContent?.trim()
        });
      }
    }
  });
  return results;
})()
```
- Column indices: 0=model, 1=context, 2=creator, 3=intelligence, 4=cost/task, 5=speed, 6=latency, 7=total response

### Step 3: Official Pricing Pages
- DeepSeek: `api-docs.deepseek.com/quick_start/pricing` — clean table, all models
- Alibaba DashScope: `help.aliyun.com/zh/model-studio/models` → click "模型调用计费"
  - Use `browser_console` with `document.body.innerText.indexOf('model-name')` to check existence
  - Prices in CNY (元) per 1M tokens; convert at ~7.2 CNY/USD for international comparison
  - Watch for tiered pricing (阶梯计费) by input token count
- Qwen international: pricing shown on AA is the international USD price

### Step 4: Vendor Blogs/Announcements
- qwen.ai is heavily JS-rendered — navigate to specific subpages (/blog, flagship models page)
- Check "Our Flagship Models" section for current model lineup
- Research Index page shows latest releases chronologically

### Step 5: HuggingFace (open weights only)
- Search: `huggingface.co/models?search=<model-name>`
- 0 results = proprietary or not yet released
- Model cards have config.json with architecture details (num_experts, hidden_size, etc.)
- **Model discovery API** (fast, JSON): `huggingface.co/api/models?search=<name>&author=<org>&limit=10` — returns model IDs + download counts. Use this to check what's been released before scraping pages.

### Step 5b: Architecture extraction from config.json (PRIMARY for architecture specs)
- URL: `huggingface.co/{org}/{model}/raw/main/config.json`
- **Multimodal models have nested configs**: top-level keys are `text_config` + `vision_config`. Always check for nesting — flat extraction will miss everything.
- **Hybrid attention models**: `layer_types` array reveals the pattern (e.g., `["linear_attention","linear_attention","linear_attention","full_attention",...]`). Also check `full_attention_interval`.
- Key fields to extract: `hidden_size`, `num_hidden_layers`, `num_attention_heads`, `num_key_value_heads`, `head_dim`, `num_experts`, `num_experts_per_tok`, `moe_intermediate_size`, `shared_expert_intermediate_size`, `vocab_size`, `max_position_embeddings`, `rope_theta`, `partial_rotary_factor`, `linear_conv_kernel_dim`, `linear_num_key_heads`, `linear_num_value_heads`, `linear_key_head_dim`, `linear_value_head_dim`, `mtp_num_hidden_layers`, `attn_output_gate`, `layer_types`
- **GATED MODELS PITFALL**: Llama 4, Gemma 3 return "Access restricted" HTML instead of JSON. Must use browser with HF auth or find community mirrors. Always check if response starts with `{` before JSON-parsing.
- README.md (`/raw/main/README.md`) often has richer architecture prose than config.json (e.g., Qwen3.5 model card documents the full hidden layout pattern).

### Step 6: arXiv abstract scraping (for architecture papers)
- **Download-then-parse** (curl|python3 pipe is blocked by security scanner):
```bash
# Download phase — sequential loop, no shell backgrounding
mkdir -p /tmp/arxiv && cd /tmp/arxiv
for id in 2309.16609 2407.10671; do
  curl -sL --max-time 20 "https://arxiv.org/abs/$id" \
    -H "User-Agent: Mozilla/5.0" -o "$id.html"
done
# Parse phase (write script to file first, then run)
python3 /tmp/arxiv/parse.py
```
- Parse script extracts `citation_title` meta tag + `blockquote.abstract` content
- arXiv search: `arxiv.org/search/?query=<terms>&searchtype=all` — results have `arxiv.org/abs/ID` links + `p.title.is-5.mathjax` elements
- **Pitfall**: arXiv IDs can be wrong for recent papers — always verify title matches expected paper before citing

## Pitfalls

- **AA scores are effort-dependent**: Models show different scores for (max), (high), (medium), (low) reasoning effort. Always note which effort level. The default page shows "max" for reasoning models.
- **AA class comparisons**: Open-weight models are compared within size classes; proprietary models within price bands. A score of 50 means different things in different classes.
- **Non-reasoning vs reasoning variants**: Same model can have very different AA scores (e.g., V4 Flash 0731: 50 reasoning vs 29 non-reasoning). Check which variant the page shows.
- **qwen.ai JS rendering**: The blog/research pages render content client-side. Full snapshots may show only navigation chrome. Navigate to specific subpages or use the Research Index.
- **DashScope pricing is CNY**: International pricing (shown on AA) differs from Chinese domestic pricing. Note both when available.
- **Model naming confusion**: Vendors use similar names (qwen3.7-max vs qwen3.7-max-preview vs qwen3.7-max-2026-05-20). Always note the exact model ID.
- **Peak/off-peak pricing**: DeepSeek announced upcoming 2x peak pricing (9:00–12:00, 14:00–18:00 Beijing time). Check for temporal pricing changes.

## Output Format

Present findings as:
1. Per-model spec tables (parameters, context, pricing, AA score, speed)
2. Competitive comparison table (ranked by intelligence or price-performance)
3. Strategic positioning summary (price per intelligence point, open vs proprietary)
4. Explicit "NOT FOUND" section for models that don't exist yet, with all sources checked listed

Always cite sources per data point. Flag unverified/rumored specs explicitly.

## Reference data
- `references/model-data-2026-08.md` — Aug 2026 snapshot: AA scores, pricing, leaderboard
- `references/qwen-architecture-evolution.md` — Qwen1→3.5 architecture specs from config.json + arXiv (verified Aug 2026)
