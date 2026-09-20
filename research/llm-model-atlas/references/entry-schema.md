# models.js entry schema

Each entry is one object in `window.MODELS`. Insert at the **top** of the array (newest first). All fields shown; use `null` for unknown/absent.

## Field reference

| Field | Type | Notes |
|---|---|---|
| `id` | string | kebab-case, unique (e.g. `kimi-k3`) |
| `name` | string | Display name (e.g. `Kimi K3`) |
| `org` | string | `Moonshot`, `DeepSeek`, `Alibaba`, … (must match existing org names for the filter dropdown) |
| `family` | string | Model family (`Kimi`, `Qwen`, …) |
| `released` | string | `YYYY-MM` |
| `license` | string | Exact license name from README (`Kimi K3 License`, `Apache-2.0`, `Modified MIT`) |
| `modality` | string | `text` \| `multimodal` \| `image-gen` (drives filter chips) |
| `decoder_type` | string | `Dense` \| `MoE` (also `DiT` for image-gen) |
| `params_total_B` | number | Billions — official README number (2.8T → `2800`) |
| `params_active_B` | number | Activated params, billions |
| `n_layers` | int | `num_hidden_layers` |
| `d_model` | int | `hidden_size` |
| `d_ff` | int\|null | Dense-layer FFN dim (`intermediate_size`); null if all-MoE |
| `d_ff_moe` | int\|null | Per-expert FFN dim (`moe_intermediate_size`) |
| `n_heads` / `n_kv_heads` | int | `num_attention_heads` / `num_key_value_heads` |
| `head_dim` | int | Usually 128; for MLA models use the README's attention head dim |
| `attention` | string | `GQA` \| `MHA` \| `MLA` \| `linear` \| `hybrid` (hybrid = mixed full+linear layers) |
| `attention_detail` | string | One dense sentence: layer split, head counts, conv kernels, gates, LoRA ranks, position-encoding specifics |
| `attention_split` | object\|null | Optional; renders a dedicated two-type split diagram for hybrid models — `{parts:[{name,n,type,sub},…], pattern:"kkkm…", pattern_map:{k:"linear",m:"MLA"}}`. See "Split diagrams" below. |
| `n_experts` / `active_experts` / `shared_experts` | int | MoE routing |
| `vocab_size` | int | config value (README may round — "160K" → `163840`) |
| `context_length` | int | `max_position_embeddings` |
| `norm` / `norm_placement` | string | `RMSNorm` / `pre` typical |
| `pos_encoding` | string | `RoPE` \| `NoPE` \| `relative` \| `learned` — for hybrid models use the full-attention layers' scheme |
| `activation` | string | `SwiGLU` \| `SiTU-GLU` \| `GeGLU` \| … (README display name; `hidden_act: "situ"` → SiTU-GLU) |
| `tie_embeddings` | bool | `tie_word_embeddings` |
| `vision` | object\|null | `{encoder, encoder_params_B, fusion, notes}` — fusion: `adapter` \| `early-fusion` |
| `notes` | string | 2–4 sentences: architecture story, routing scheme, quantization caveats, lineage |
| `sources` | string[] | Tech report/blog first, then HF repo, then raw config.json URL |
| `confidence` | string | `verified` \| `partial` \| `estimated` |
| `dense_first_layers` | int | Optional; from `first_k_dense_replace` |

## Worked example — Kimi K3 (added 2026-07-28, verified)

```json
{
"id": "kimi-k3",
"name": "Kimi K3",
"org": "Moonshot",
"family": "Kimi",
"released": "2026-07",
"license": "Kimi K3 License",
"modality": "multimodal",
"decoder_type": "MoE",
"params_total_B": 2800,
"params_active_B": 104,
"n_layers": 93,
"d_model": 7168,
"d_ff": 33792,
"d_ff_moe": 3072,
"n_heads": 96,
"n_kv_heads": 96,
"head_dim": 128,
"attention": "hybrid",
"attention_split": {
"parts": [
{"name": "KDA", "n": 69, "type": "linear", "sub": "delta rule · conv k4 · gated"},
{"name": "Gated MLA", "n": 24, "type": "MLA", "sub": "latent KV · NoPE"}
],
"pattern": "kkkmkkkmkkkmkkkmkkkmkkkmkkkmkkkmkkkmkkkmkkkmkkkmkkkmkkkmkkkmkkkmkkkmkkkmkkkmkkkmkkkmkkkmkkkmm",
"pattern_map": {"k": "linear", "m": "MLA"}
},
"attention_detail": "69 KDA (Kimi Delta Attention) linear-attention layers interleaved with 24 gated-MLA full-attention layers (full_attn_layers every 4th, 4/8/.../92 plus final layer 93). KDA: 96 heads, head_dim 128, short-conv kernel 4, full-rank output gate (lower bound -5). Gated MLA: q_lora 1536, kv_lora 512, qk_nope 128 + qk_rope 64, v 128, NoPE + output gate; attn_res_block_size 12 (Attention Residuals).",
"n_experts": 896,
"active_experts": 16,
"shared_experts": 2,
"vocab_size": 163840,
"context_length": 1048576,
"norm": "RMSNorm",
"norm_placement": "pre",
"pos_encoding": "RoPE",
"activation": "SiTU-GLU",
"tie_embeddings": false,
"vision": {
"encoder": "MoonViT (27L/1024d)",
"encoder_params_B": 0.4,
"fusion": "adapter",
"notes": "27-layer, 1024-dim (12-head) vision tower, patch 14, divided-fixed positional embeddings, sd2_tpool patch merger (2x2) projecting into the 7168-dim decoder; native text/image/video input."
},
"notes": "World's first open 3T-class model: 2.8T/104B Stable LatentMoE on a Kimi Delta Attention backbone — 896 experts top-16 + 2 shared (latent dim 3584, expert d_ff 3072), first layer dense (d_ff 33792). 93 layers split 69 KDA linear + 24 gated-MLA full attention with Attention Residuals (AttnRes); SiTU-GLU activation (situ beta 4.0); noaux_tc routing. ~2.5x scaling-efficiency gain over Kimi K2. Native multimodal, 1M context. HF release is MXFP4-quantized (compressed-tensors; attention, shared experts, and vision tower kept at full precision).",
"sources": [
"https://github.com/MoonshotAI/Kimi-K3/blob/main/k3_tech_report.pdf",
"https://www.kimi.com/blog/kimi-k3",
"https://huggingface.co/moonshotai/Kimi-K3",
"https://huggingface.co/moonshotai/Kimi-K3/raw/main/config.json"
],
"confidence": "verified",
"dense_first_layers": 1
}
```

Derivation notes for this entry: 24 full-attention layers = `len(linear_attn_config.full_attn_layers)`; 69 KDA = 93 − 24. README's "69 KDA + 24 Gated MLA" row confirmed the split. `d_ff: 33792` is the dense first layer (`first_k_dense_replace: 1`); all other layers use `moe_intermediate_size: 3072`.

## Split diagrams (`attention_split`) — for any heterogeneous-layer model

By default a model gets one generic attention box (e.g. "Hybrid Attention"). For any model whose layers are NOT all one attention type, add `attention_split` to render a dedicated diagram: N side-by-side colored boxes (one per attention type, widths proportional to layer counts) plus a **layer-order strip** — one colored tick per layer in the true interleave order. The renderer lives in `archSVG()` in `app.js` (search `m.attention_split`); it is data-driven and reusable, not hardcoded to any model. It handles 2-way AND 3-way splits.

This is the mechanism to reach for when the user asks to "highlight architecture differences" (稀疏/稀释注意力, MLA, interleaved layer patterns, etc.). Homogeneous models (e.g. pure-MLA DeepSeek-V3) correctly keep a single box — don't force a split.

**Note — mHC is NOT an attention type:** if the user cites mHC (Manifold-Constrained Hyper-Connections, DeepSeek-V4's residual-connection upgrade) as a difference to highlight, it's a residual-stream change, not per-layer attention heterogeneity — it does not map to `attention_split`. Handle it as a note/callout, not a split box.

```json
"attention_split": {
  "parts": [
    {"name": "KDA", "n": 69, "type": "linear", "sub": "delta rule · conv k4 · gated"},
    {"name": "Gated MLA", "n": 24, "type": "MLA", "sub": "latent KV · NoPE"}
  ],
  "pattern": "kkkmkkkm…kkkmm",
  "pattern_map": {"k": "linear", "m": "MLA"}
}
```

- `parts[].type` must be a key of `A_COL` in `app.js` — it picks the box/tick color. Current palette: `MHA/GQA/MQA/global` green, `MLA/HCA/MMDiT` purple/pink, `linear` cyan, `sliding/CSA/SW/sparse` orange, `hybrid` blue. If you add a new type, add it to BOTH `A_COL` and `A_NAME`, and add a light-mode mapping in `LIGHT_SVG_MAP` (exact-string substitution).
- Keep `sub` short (~16 chars): the smaller part's box is narrow and long subtext gets cramped.
- `pattern` is one char per layer, in order (bottom = first layer). `pattern_map` maps each char to an `A_COL` type for tick coloring.
- **Widths:** proportional to layer counts, with a per-part minimum (118px for ≤2 parts, 60px for 3+) so labels stay legible; space taken by minimums is redistributed across the larger parts so relative order stays honest (wider box = more layers). You normally don't tune this — just set `n` correctly.

### Deriving the per-layer pattern — read the config, vendors differ
Never guess the interleave; read the actual per-layer field from config.json:
- **explicit list:** `layer_types` (Qwen3.5 `["linear_attention","full_attention",…]`; gpt-oss `["sliding_attention","full_attention",…]`; Laguna `["full_attention","sliding_attention",…]`)
- **0/1 list:** `attn_type_list` (MiniMax Text-01: 0=linear/Lightning, 1=full)
- **interval:** `full_attention_interval` (Qwen3-Next: full every Nth), `sliding_window_pattern` (Gemma 3: global every 6th), or "every Nth layer" prose (Llama 4: global every 4th)
- **index array:** `linear_attn_config.full_attn_layers` (Kimi K3) — length = full count, rest are linear
- **compressed:** `compress_ratios` (DeepSeek-V4: **4=CSA, 128=HCA, 0=sliding warmup**). ⚠️ array length = `num_hidden_layers`+1 — ignore the trailing extra entry. Pro = 30 CSA + 31 HCA; Flash = 21 CSA + 20 HCA + 2 SW warmup (leading zeros).
- **sparse warmup:** `sparse_disable_index_value` (MiniMax-M3: 0=dense/full, 1=sparse MSA; first 3 are 0)

Then VALIDATE programmatically — never by eye:
```python
assert len(pat) == n_layers
for part in parts:
    chars = [c for c,t in pattern_map.items() if t == part["type"]]
    assert sum(pat.count(c) for c in chars) == part["n"]
```
- **PITFALL — never hand-type `pattern`.** A 93-char string typed by hand came out 4 chars short (89) and silently rendered a wrong interleave. Always generate from the config and assert.
- After adding, verify in the drawer: the SVG should contain every part label (`N× Name`), the tick count (`rect[opacity="0.9"]`) should equal `n_layers`, and the "N + M = total layers" caption should be present.

## changelog.js entry shape

```js
{
  "date": "2026-07-28",
  "added": ["kimi-k3"],        // ids added this run
  "upgraded": [],              // ids whose confidence/specs were upgraded
  "note": "One paragraph: what changed and why it matters."
}
```

Insert at top of `entries`; bump `last_run` to `"YYYY-MM-DD HH:MM"` on every run.
