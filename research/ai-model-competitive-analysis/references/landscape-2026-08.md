# Frontier Model Competitive Landscape — August 2026 Snapshot

Data collected 2026-08-01 from Artificial Analysis, official pricing pages, HuggingFace model cards.

## AA Intelligence Index Rankings (max reasoning)

| Rank | Model | Score | Cost/Task | Speed (tok/s) |
|------|-------|-------|-----------|---------------|
| #1 | Kimi K3 (max) | 57 | ~$0.86 | 35 |
| #2 | GLM-5.2 (max) | 51 | ~$0.69 | 106 |
| #3 | DS V4 Flash 0731 (max) | 50 | ~$0.03 | N/A (new) |
| #6 | DS V4 Pro (max) | 44 | ~$0.05 | 62 |
| ~#10 | Qwen3.7 Max | 46 | ~$1.28 | 199 |

## Architecture Comparison

| Model | Total Params | Active | Ratio | Architecture | Context | Multimodal | License |
|-------|-------------|--------|-------|-------------|---------|------------|---------|
| Kimi K3 | 2,800B | 104B | 3.7% | MoE + KDA/Gated MLA (896 experts, 16+2 selected) | 1M | ✅ Vision | MIT |
| GLM-5.2 | 753B | 40B | 5.3% | MoE + DSA | 1M | Partial | Open |
| DS V4 Flash 0731 | 284B | 13B | 4.6% | MoE + DSpark speculative decoding | 1M | ❌ | MIT |
| DS V4 Pro | ~1,600B | ? | ? | MoE | 1M | ❌ | Open |
| Qwen3.7 Max | undisclosed | undisclosed | ? | MoE | 1M | ❌ (VL separate) | Partial |
| Qwen3.8 Max (preview) | 2,400B | 90B | 3.75% | MoE + GDN | 1M (expected) | Unknown | Expected open |

## Pricing (per 1M tokens, USD, first-party API)

| Model | Input | Output | Cache Hit | Cache Discount |
|-------|-------|--------|-----------|---------------|
| DS V4 Flash 0731 | $0.14 | $0.28 | $0.0028 | **98%** |
| DS V4 Pro | $0.435 | $0.87 | $0.004 | ~99% |
| GLM-5.2 | $1.40 | $4.40 | — | — |
| Kimi K3 | $3.00 | $15.00 | $0.30 | 90% |
| Qwen3.7 Max | ~$1.65 (¥12) | ~$4.97 (¥36) | 10% of input price | 90% |

## Key Market Dynamics (Aug 2026)

- **DeepSeek's 98% cache discount** is the single biggest pricing differentiator. In agentic workflows with high system-prompt reuse, effective cost drops 5-10x below list price.
- **DS V4 Flash 0731's 10-point jump** (40→50) came entirely from post-training — no architecture change. Proves post-training headroom is massive.
- **Kimi K3 is the intelligence ceiling** (57) but also the most expensive open model. Its moat: native multimodal + SWE-Marathon 42.0 (vs GLM-5.2's 13.0).
- **Qwen3.7 Max at $1.28/task is uncompetitive** — 85% more expensive than GLM-5.2 for 5 fewer points, 42x more than DS Flash for 4 fewer points.
- **MoE activation ratio sweet spot: 3.5-4%** — Kimi K3 (3.7%) and Qwen3.8 Max (3.75%) converged independently.
- **GDN (Gated Delta Network)** in Qwen3.8 Max is the same linear-attention family as Kimi's KDA — should enable efficient 1M context inference.
- **OpenAI cut GPT-5.6 Luna pricing 80%** on Jul 31 — even after that, DS Flash 0731 is still ~60% cheaper per task at comparable intelligence (50 vs 51).

## Sources
- Artificial Analysis Intelligence Index v4.1 (artificialanalysis.ai)
- DashScope billing page (help.aliyun.com/zh/model-studio/billing-for-model-studio)
- DeepSeek API Docs (api-docs.deepseek.com/quick_start/pricing)
- HuggingFace: deepseek-ai/DeepSeek-V4-Flash-0731, moonshotai/Kimi-K3
- Kimi Platform (platform.moonshot.cn/pricing/chat-k3)
- Z.ai pricing (z.ai/pricing, bigmodel.cn/pricing)
- HN #49120299 (530pts, 289 comments)
