# Qwen Architecture Evolution — Verified from HuggingFace config.json + arXiv

Data collected 2026-08-02 from HuggingFace config.json files and arXiv abstracts.

## Qwen1 (Sep 2023) — arXiv:2309.16609
- Dense Transformer, MHA (no GQA)
- 7B: hidden=4096, 32 layers, 32 heads, intermediate=22016
- Vocab: 151,936 (BPE)
- Context: 8K training, 32K max_position_embeddings
- RoPE base: 10,000

## Qwen2 (Jun 2024) — arXiv:2407.10671
- Dense + first MoE variant (hosted)
- 72B: hidden=8192, 80 layers, 64 Q heads, 8 KV heads (GQA 8:1), intermediate=29568
- Vocab: 152,064
- Context: 128K (max_position_embeddings=131,072)
- RoPE base: 1,000,000 (100x increase from Qwen1)
- Key changes: GQA introduced, SwiGLU, dual-chunk attention, 0.5B–72B range, ~30 languages

## Qwen2.5 (Sep 2024) — arXiv:2412.15115
- **Architecture IDENTICAL to Qwen2** (confirmed via config.json diff)
- Key change: data scale 7T → 18T tokens
- Post-training: 1M+ SFT samples, multi-stage RL
- First proprietary MoE: Qwen2.5-Turbo, Qwen2.5-Plus (hosted only)

## Qwen3 (May 2025) — arXiv:2505.09388
- Dense + MoE (open-weight)
- 235B-A22B: hidden=4096, 94 layers, 64 Q heads, 4 KV heads (GQA 16:1)
- MoE: 128 experts, 8 active, expert_intermediate=1536, head_dim=128
- Vocab: 151,936
- Context: 40,960 native (extendable)
- RoPE theta: 1,000,000
- Key innovations: unified thinking/non-thinking mode, thinking budget, distillation flagship→small, 119 languages, 0.6B–235B

## Qwen3.5 (2026) — CURRENT GENERATION, no arXiv paper yet
**Major architecture revolution: hybrid linear attention + native multimodal**

### 397B-A17B (flagship MoE)
- Architecture: Qwen3_5MoeForConditionalGeneration (native multimodal)
- Hidden: 4096, 60 layers
- Layer pattern: 15×(3×GDN→MoE + 1×FullAttn→MoE) — full_attention_interval=4
- Full attention: 32 Q heads, 2 KV heads, head_dim=256
- GDN (linear): 64 V heads, 16 QK heads, head_dim=128, conv_kernel=4
- MoE: 512 experts, 10 routed + 1 shared, expert_intermediate=1024
- MTP: mtp_num_hidden_layers=1
- Vocab: 248,320 (63% expansion from 151,936)
- Context: 262,144 native, extensible to 1,010,000
- RoPE: theta=10,000,000, partial_rotary_factor=0.25 (64 of 256 dims), mRoPE interleaved [11,11,10]
- attn_output_gate: true
- Vision: native early-fusion encoder (hidden=1152)
- Languages: 201
- License: Apache 2.0

### 9B (dense)
- Hidden: 4096, 32 layers
- Layer pattern: 8×(3×GDN + 1×FullAttn)
- Full attention: 16 Q, 4 KV, head_dim=256
- GDN: 32 V, 16 QK, head_dim=128
- Dense intermediate: 12288
- Same vocab/context/RoPE as flagship

### 35B-A3B (small MoE)
- Hidden: 2048, 40 layers
- MoE: 256 experts, 8 active, expert_intermediate=512
- Full attention: 16 Q, 2 KV, head_dim=256
- GDN: 32 V, 16 QK, head_dim=128

### Qwen3.5 key innovations summary
1. Gated DeltaNet for 75% of layers (KV cache savings)
2. Multi-token prediction (MTP) — first Qwen with MTP
3. Shared expert in MoE (1 shared + N routed)
4. Native multimodal (early fusion, not separate VL model)
5. Vocab 151K → 248K (201 languages)
6. head_dim 256 for full attention (was 128)
7. partial_rotary_factor 0.25
8. mRoPE (multimodal rotary) with interleaved sections
9. attn_output_gate
10. RoPE theta 10M (10x from Qwen3)

### Model lineup on HuggingFace (Aug 2026)
- Qwen3.5-0.8B, 2B, 4B, 9B, 27B (dense)
- Qwen3.5-35B-A3B, 122B-A10B, 397B-A17B (MoE)
- Qwen3.5-Plus = hosted 397B-A17B with 1M context + built-in tools

## Qwen4 — NOT FOUND (Aug 2026)
Checked: HuggingFace API (0 results), arXiv search (0 results), qwen.ai blog (JS-rendered, no evidence)
