# Competitor Architecture Bets — Verified Aug 2026

From HuggingFace config.json + arXiv abstracts. Architecture-level (not pricing — see landscape-2026-08.md).

## DeepSeek lineage
- **V2 (2405.04434)**: introduced MLA (Multi-head Latent Attention) — KV compressed to latent vector (kv_lora_rank=512, q_lora_rank=1536), 93% KV reduction. 236B/21B active, 128K.
- **V3 (2412.19437)**: 671B/37B. MLA + DeepSeekMoE + **auxiliary-loss-free load balancing** + **MTP training objective** + **native FP8**. 14.8T tokens, 2.788M H800-hours, zero rollbacks.
- **V3.2-Exp (config)**: MLA + **DSA** (DeepSeek Sparse Attention — index_n_heads=64, index_topk=2048, learned indexer), 256 experts/8 active + 1 shared, MTP layer, native FP8 (e4m3 block 128×128), YaRN factor=40.
- **V4 Flash (284B/13B, 4.6%)** / **V4 Pro (~1600B/49B)**: 1M context, MIT. Flash +10 AA points from post-training alone (no arch change).

## Kimi / Moonshot
- **K2 (2507.20534)**: 1T/32B. MLA-style. **MuonClip optimizer** (QK-clip for stability), 15.5T tokens zero loss spike. Agentic data synthesis + joint RL. MIT.
- **Kimi Linear (2510.26692)**: **KDA (Kimi Delta Attention)** — Gated DeltaNet + finer-grained gating. Hybrid KDA+MLA, 48B/3B. Claims to outperform full MLA, 75% KV reduction, 6x decode at 1M. Open KDA kernel + vLLM.
- **K3 (2026)**: 2800B/104B (3.7%), 896 experts/16+2 selected, KDA + Gated MLA, 1M, native vision, MIT. AA 57 (highest open).

## Meta Llama 4 (Apr 2025)
- First Meta MoE. Scout: 17B active/16 experts, **10M context**. Maverick: 17B active/128 experts, ~400B total.
- **iRoPE**: interleaved attention layers — some layers have NO positional embeddings, others use RoPE. Inference-time temperature scaling for length generalization.
- Native multimodal. Config.json is GATED (auth required).

## Google Gemma 3 (2503.19786)
- Dense 1B–27B. KV-cache reduction via increased local-to-global attention ratio + short local span. 128K+. Native vision. Trained with distillation (4B-IT ≈ 27B-IT prev gen). Config.json GATED.

## Mistral Magistral (2506.10910)
- First Mistral reasoning model. **Pure RL** — no distilled traces, no human CoT. RL on text alone maintains multimodal/instruction-following/function-calling. Small = Apache 2.0.

## MiniMax M1 (2506.13585)
- 456B/45.9B MoE + **Lightning Attention** (hybrid linear). 1M native (8x R1). **CISPO** RL algo (clips IS weights not token updates). Full RL on 512 H800s / 3 weeks / $534K.

## Key architecture papers
- **Gated DeltaNet (2412.06464)**: gating + delta rule for linear attention; hybrid w/ sliding window/Mamba2. Foundation for Qwen3.5 + Kimi Linear.
- **NSA (2502.11089)**: Natively-trainable Sparse Attention — hierarchical compression + fine-grained selection. Precursor to DeepSeek DSA.
- **MTP (2404.19737)**: multi-token prediction, n independent heads, up to 3x inference speedup. Adopted by DS V3, Qwen3.5.
- **DeepSeekMoE (2401.06066)**: fine-grained expert segmentation + shared experts.

## Convergence trends (2025-2026)
1. **Hybrid linear+full attention** — Qwen3.5 (GDN 3:1), Kimi (KDA), MiniMax (Lightning), Gemma3 (local/global) converged independently
2. **MoE activation ratio 3.5-4.5%** — Kimi K3 3.7%, Qwen3.5 4.3%, DS V4 Flash 4.6%
3. **MTP as standard** — DS pioneered, Qwen3.5 + DS V3.2 adopted
4. **Shared experts** — universal in new MoE (DS, Qwen3.5, Kimi)
5. **Native multimodal early fusion** — separate VL models dead (Qwen3.5, Llama4, Gemma3, Kimi K3)
6. **1M context table stakes**
7. **Post-training > architecture for intelligence** — DS V4 Flash +10 AA from post-training alone

## Open architectural bets
- **Sparse attention (DSA/NSA)** vs **linear attention (GDN/KDA)** — DeepSeek vs Qwen/Kimi. Kimi Linear claims linear wins under fair comparison.
- **Optimizer innovation** — Kimi MuonClip (QK-clip), zero loss spikes
- **RL-only post-training** — Mistral Magistral proves no-distillation works
- **Context ceiling** — Meta 10M vs everyone's 1M
