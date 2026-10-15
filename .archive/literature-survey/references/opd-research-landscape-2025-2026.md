# On-Policy Distillation (OPD) — Research Landscape (2025-2026)

Condensed from a July 2026 literature survey. Key papers, formulations, and relationships.

## Foundational Papers

| Paper | arXiv ID | Date | Lab |
|-------|----------|------|-----|
| GKD: On-Policy Distillation of Language Models | 2306.13649 | Jun 2023 (ICLR 2024) | Google DeepMind (Agarwal et al.) |
| Qwen3 Technical Report (Table 21: OPD results) | 2505.09388 | May 2025 | Alibaba/Qwen |
| Thinking Machines OPD blog post | N/A (blog) | Oct 2025 | Thinking Machines (Kevin Lu) |

## Core Technical Formulation

**Per-token reverse KL** (Thinking Machines / Qwen3):
```
KL(π_θ ∥ π_teacher) = E_{x∼π_θ}[log π_θ(x_{t+1}|x_{1..t}) − log π_teacher(x_{t+1}|x_{1..t})]
```
- Advantage = negative reverse KL
- Discount factor = 0 (immediate next token only)
- Trained with importance-sampling RL loss
- "Unhackable" — low KL always = high probability of desirable teacher behavior
- Mode-seeking (learns one specific behavior, not spread across suboptimal options)

## Key Quantitative Results (Qwen3 Table 21, replicated by Thinking Machines)

Starting from SFT-400K checkpoint (Qwen3-8B-Base, 60% AIME'24):
- RL (17,920 GPU hrs) → 67.6% AIME'24, 61.3% GPQA-Diamond
- **OPD (1,800 GPU hrs) → 74.4% AIME'24, 63.3% GPQA-Diamond**
- OPD achieves higher performance at ~1/10th the GPU cost

Thinking Machines replication: OPD reaches 70% AIME'24 at 9-30× less compute than SFT/RL.

## OPD ↔ RLVR Relationship

1. **Complementary (alongside RL)**: Qwen3 pipeline: SFT → RL → OPD. OPD adds +6.8% on top of RL.
2. **Replacement (compute-constrained)**: Thinking Machines shows OPD matches/exceeds RL at 9-30× less compute.
3. **Theoretical framing** (arXiv:2607.13399): OPD = "exploration catalyst" — steers toward correct reasoning via dense token-level guidance WITHOUT expanding capability ceiling. Ceiling set by teacher.
4. **Key insight**: OPD provides O(seq_len) bits/episode vs O(1) for RLVR terminal reward.

## Major 2026 Papers

| Paper | arXiv ID | Key Contribution |
|-------|----------|-----------------|
| Demystifying OPD: Roles, Pathologies, Regulations | 2607.13399 | Student-Teacher Mismatch + Length Exploitation pathologies; advantage clipping + log-scale compression fixes |
| Direct-OPD (Weak-to-Strong) | 2607.05394 | Transfers RL policy *shift* (log-ratio post/pre-RL) as implicit reward; Qwen3-1.7B 48.3%→58.3% AIME in 4hrs |
| Co-Evolving Policy Distillation | 2604.27083 | Unified RLVR+OPD analysis for multi-expert consolidation |
| Self-Supervised OPD | 2605.17497 | Extracts process signal from correct/incorrect completions in GRPO groups |
| AsyncOPD | 2606.24143 | Staleness tolerance in async OPD (github.com/furiosa-ai/async-opd) |
| Multi-Turn OPD with Prefix Replay | 2607.04763 | Multi-turn extension (Microsoft: Liao, Dong, Monz, Wei) |
| On-Policy Delta Distillation | 2607.15161 | NAVER (Heo et al.) |
| Many Faces of OPD | 2605.11182 | Systematic failure mode study |
| Geometry of OPD | 2606.07082 | Optimization landscape analysis |
| Dense Supervision, Sparse Updates | 2606.13657 | Sparsity analysis (github.com/SydCS/OPD-Param-Analysis) |
| Beyond SFT-to-RL: Black-Box OPD | 2604.28123 | OPD as pre-alignment before multimodal RL |
| Non-vacuous Bounds for RLVR | 2607.14506 | Theoretical generalization bounds (Zhu, Alur, Kang) |

## DeepSeek's Approach

DeepSeek uses **off-policy distillation** (large-scale SFT on teacher outputs), NOT on-policy distillation:
- DeepSeek-R1-0528-Qwen3-8B: 86% AIME'24 via off-policy distillation
- Qwen2.5-7B/14B: 55.5%/69.7% after 800k distillation prompts from DeepSeek-R1
- No DeepSeek paper uses the term "on-policy distillation"

## Thinking Machines (Mira Murati's Lab)

- Publishes via blog (thinkingmachines.ai/blog), NOT arxiv
- Key posts: "On-Policy Distillation" (Oct 2025), "LoRA Without Regret" (Sep 2025, John Schulman)
- Uses Tinker training API for experiments
- Replicated Qwen3 OPD results; extended to personalization/continual learning
- Draws from DAGGER (Ross 2010), process reward modeling, GKD (Agarwal 2023)
