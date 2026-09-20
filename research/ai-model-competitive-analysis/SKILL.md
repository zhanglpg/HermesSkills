---
name: ai-model-competitive-analysis
description: "Compare AI model specs, pricing, benchmarks for strategy."
tags:
  - research
  - competitive-analysis
  - ai-models
  - pricing
  - market-strategy
---

# AI Model Competitive Analysis

Compare frontier AI models across architecture specs, pricing tiers, and benchmark scores to derive strategic positioning recommendations. Use when the user asks to compare models across competitors, analyze pricing bands, or advise on a lab's next flagship model.

## When to Use
- User asks to compare models across specs/pricing/benchmarks
- "从市场模型价格带，看模型的规格、尺寸、定价选择" type requests
- Strategic positioning questions: "what should Lab X do with their next model?"
- Any request combining architecture choices, pricing tiers, and benchmark data across 3+ models

## Workflow

### Phase 1: Parallel competitor research (delegate_task)

Dispatch 2–3 subagents, each covering 1–2 competitors. Each subagent should:
- Check **Artificial Analysis model page** via browser (AA Intelligence Index score, speed, price ranking, cost-per-task)
- Check **official pricing page** (DashScope, api-docs.deepseek.com, platform.moonshot.cn, bigmodel.cn, z.ai/pricing)
- Check **HuggingFace model card** (`huggingface.co/{org}/{repo}/raw/main/README.md`) for architecture specs, benchmark tables, license
- Check **official blog/tech report** for architecture details (attention mechanism, MoE config, expert count)
- Return structured findings: total params, active params, activation ratio, architecture type, context window, modalities, pricing (input/output/cache), AA score, key benchmark numbers

**Subagent context must include:** the specific models to compare, that this is for pricing strategy analysis, and which data points matter most (activation ratio, cost-per-task, cache discount depth).

### Phase 2: Direct data collection (while subagents run)

Do these yourself in parallel — they're fast and don't need subagent overhead:

0. **HuggingFace config.json** — for architecture specs, this is the gold standard:
   - URL: `huggingface.co/{org}/{model}/raw/main/config.json`
   - **Multimodal models nest under `text_config`** — always check for nesting
   - **Hybrid attention**: `layer_types` array shows the pattern (e.g., 3×linear + 1×full)
   - Key fields: `num_experts`, `num_experts_per_tok`, `moe_intermediate_size`, `shared_expert_intermediate_size`, `head_dim`, `linear_num_key_heads`, `linear_num_value_heads`, `mtp_num_hidden_layers`, `full_attention_interval`, `partial_rotary_factor`, `attn_output_gate`
   - **Gated models** (Llama 4, Gemma 3): return auth error HTML, not JSON. Check response starts with `{`.
   - Model discovery: `huggingface.co/api/models?search=<name>&author=<org>&limit=10` (JSON, fast)
   - README.md often has richer architecture prose (hidden layout patterns, benchmark tables)

1. **AA leaderboard table** — `browser_navigate` to `artificialanalysis.ai/leaderboards/models`, then `browser_console` with JS to extract structured rows:
```javascript
(() => {
  const rows = document.querySelectorAll('table tbody tr');
  const results = [];
  rows.forEach(r => {
    const cells = r.querySelectorAll('td');
    if (cells.length > 3) {
      results.push({
        model: cells[0]?.textContent?.trim(),
        intelligence: cells[1]?.textContent?.trim(),
        speed: cells[2]?.textContent?.trim(),
        costPerTask: cells[3]?.textContent?.trim(),
        context: cells[4]?.textContent?.trim()
      });
    }
  });
  return results;
})()
```

2. **DashScope pricing** — `curl -sL "https://help.aliyun.com/zh/model-studio/billing-for-model-studio"` → strip tags → grep for model names + 元 prices. Prices are in ¥/百万Token. Convert: ¥12/M ≈ $1.65/M at ~7.25 CNY/USD.

3. **AA article pages** (blog posts, NOT model pages) — these ARE server-rendered and scrapable:
```bash
curl -sL "https://artificialanalysis.ai/articles/<slug>" -H "User-Agent: Mozilla/5.0" | python3 -c "
import sys, re, html
t = sys.stdin.read()
t = re.sub(r'<script.*?</script>', '', t, flags=re.S)
t = re.sub(r'<style.*?</style>', '', t, flags=re.S)
t = re.sub(r'<[^>]+>', ' ', t)
t = html.unescape(t)
t = re.sub(r'\s+', ' ', t)
print(t[:8000])
"
```

4. **HN sentiment** (optional) — if there's a recent HN thread on one of the models, use `hacker-news-research` skill for community sentiment.

### Phase 3: Synthesis structure

The report that landed well (user is a tech exec who wants actionable strategy, not just data):

1. **竞品全景** — master comparison table (specs × pricing × benchmarks, all models side by side)
2. **关键发现** — 3-5 bullet insights from the data (e.g., "DS Flash redefined the price band", "Qwen3.7 Max has lost competitiveness")
3. **架构选择的战略含义** — what the architecture choices (MoE activation ratio, attention mechanism, parameter scale) mean competitively
4. **策略建议** — numbered, specific recommendations:
   - Intelligence target (must be X+ score, here's why)
   - Pricing strategy (tiered: flagship/mainline/flash, with specific $/M numbers and cache discount depth)
   - Feature gaps to close (multimodal, agentic harness)
   - Open-source strategy (license choice, inference recipes)
   - Release cadence warnings
5. **定位图** — ASCII scatter plot: intelligence (Y) vs cost-per-task (X), with target zone marked
6. **风险** — competitive threats with timeline urgency

### Key metrics to always collect

| Metric | Why it matters |
|--------|---------------|
| AA Intelligence Index (max) | Single comparable intelligence number |
| Cost per Intelligence Index Task | Real-world economics, not just $/token |
| Cache hit discount % | Determines effective cost in agentic/RAG workloads (90% vs 98% is 5x difference) |
| Activation ratio (active/total) | Inference cost driver; 3.5-4% is current sweet spot |
| Output tokens/s | Latency-sensitive use cases |
| Modalities | Multimodal is increasingly table-stakes for flagship |
| License | MIT/Apache enables local deployment market |

## Pitfalls

- **AA model pages are JS-rendered** — don't try to scrape them with curl. Use browser_navigate + browser_console for structured extraction, or check the leaderboard table.
- **AA article pages ARE scrapable** — don't confuse them with model pages. Articles have full prose content in static HTML.
- **DashScope pricing is in CNY** — always convert and note the exchange rate used.
- **Chinese provider pricing pages** (bigmodel.cn, platform.moonshot.cn) are often JS-heavy — browser tools work better than curl. Moonshot pricing is at `platform.moonshot.cn/pricing/chat-k3` (per-model subpages).
- **Qwen preview models** may not appear on AA or DashScope public pricing — check the models page for "仅Token Plan可用" notes.
- **Don't present $/token pricing alone** — always include cost-per-task (from AA) because reasoning models with high token usage can be misleadingly cheap per-token but expensive per-task.
- **Cache discount depth is the hidden competitive lever** — DeepSeek's 98% vs industry 90% is the single biggest pricing differentiator. Always surface this.
- **Security scanner blocks curl|python3 pipes** — download HTML/JSON to files first, then parse with a separate python3 command. Also blocks shell `&` backgrounding — use sequential loops.
- **arXiv IDs can be wrong** — always verify the returned title matches the expected paper. Recent papers (2025+) sometimes have non-obvious IDs.

## Data source reliability ranking

1. **HuggingFace model card** (raw README.md) — official specs, benchmarks, license. Most reliable.
2. **Artificial Analysis** — independent benchmarks, cost-per-task, speed. Gold standard for comparison.
3. **Official API docs** (api-docs.deepseek.com, DashScope billing page) — authoritative pricing.
4. **Official blog/tech report** — architecture details, but may omit unflattering numbers.
5. **HN/tech press** — sentiment and real-world experience, not specs.

## Reference data
- `references/landscape-2026-08.md` — Aug 2026 snapshot: AA rankings, architecture/pricing tables, market dynamics. Use as a baseline; verify current numbers before citing (this market moves weekly).
- `references/competitor-architecture-2026-08.md` — Architecture-level details for DeepSeek/Kimi/Llama/Gemma/Mistral/MiniMax + convergence trends (verified from config.json + arXiv, Aug 2026).

## Related
- `hacker-news-research`: community sentiment on model releases
- `literature-survey`: academic paper research (different class — papers, not products)
- `breaking-news-research-essay`: single-event deep dive with essay output
