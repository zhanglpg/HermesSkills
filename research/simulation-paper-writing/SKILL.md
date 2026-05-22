---
name: simulation-paper-writing
title: Simulation and Analytical Paper Writing
description: Companion to research-paper-writing for simulation, modeling, and analytical framework papers (not empirical ML). Covers dual-format Obsidian+LaTeX writing, hardware spec research, per-layer precision modeling, and cache-aware roofline extensions.
version: 1.0.0
dependencies: [research-paper-writing]
platforms: [linux, macos]
metadata:
  hermes:
    tags: [Research, Paper Writing, Simulation, Roofline, Hardware, Performance Modeling, FP4, KV Cache]
    category: research
    related_skills: [research-paper-writing, arxiv, subagent-driven-development]
    requires_toolsets: [terminal, files, browser]
---

# Simulation/Analytical Paper Writing (Companion Skill)

Companion to `research-paper-writing`. Use when writing simulation, modeling, or analytical framework papers (not empirical ML with training runs).

## When To Use

- Simulation study (roofline, performance model, analytical framework)
- Cross-architecture comparison paper (GPU vs TPU, etc.)
- Model of hardware-model-parallelism interactions
- Any paper where the contribution is a framework, not empirical results

## Dual-Format Writing: Obsidian Markdown + LaTeX

When the project has both an internal Obsidian wiki and a formal LaTeX submission, write the comprehensive markdown version first (serving as thought organization and experiment log), then adapt to LaTeX. The markdown version uses Mermaid diagrams; the LaTeX version uses TikZ. Keep both consistent.

| Element | Obsidian Markdown | NeurIPS/ICML LaTeX |
|---------|------------------|-------------------|
| Figures | Mermaid (in-text) | TikZ or PDF (vector) |
| Tables | Markdown pipes | `booktabs` + `siunitx` S-columns |
| Equations | `$$...$$` display math | `\begin{equation}...\end{equation}` |
| Citations | Inline links | `\cite{}` + `.bib` |
| Speculative data | `† Projected` footnotes | `\textasciitilde` notation |
| Length | Unlimited | Strict page limits |

**Obsidian vault path**: `/Users/lipingzhang/Library/Mobile Documents/iCloud~md~obsidian/Documents/notes/`. Surveys go under `gen-notes/surveys/`.

## Simulation Paper Structure

Key differences from empirical ML papers:
- **No Phase 2-3 (Experiment Design/Execution)**: Replace with simulation design and parameter space definition
- **Results = simulation outputs**: Tables of optimal configurations, roofline maps, sensitivity sweeps
- **Validation**: Compare simulation predictions against published benchmarks, report accuracy (±X%)
- **"Experiments" renamed to "Results and Analysis"** or "Simulation Results"
- **The contribution is the framework itself**, not an empirical finding

## Hardware Specification Research

When a paper requires hardware specs (GPU FLOPS, TPU bandwidth, etc.):

**Reliable sources:**
- **Wikipedia**: Most reliable for TPU specs (generations comparison table on "Tensor Processing Unit" page)
- **Tom's Hardware**: NVIDIA GPU specs from manufacturer announcements (search: "NVIDIA announces [chip name]")
- **Google Cloud Blog**: Latest TPU announcements and Next keynote recaps
- **ServeTheHome**: Server/GPU specs, sometimes paywalled

**Unreliable sources:**
- **SemiAnalysis**: Paywalled, don't waste time
- **Google Search**: Rate-limits bot traffic quickly; fall back to direct navigation

**Protocol:**
1. Search Wikipedia first for generational spec tables
2. Search Tom's Hardware for manufacturer announcements
3. For unreleased hardware: use generational scaling (~2× per generation) and mark as projected with `†`
4. Always footnote projected/estimated specs
5. Validate: cross-check specs across 2+ sources when possible

## FP4 Precision-Adaptive Modeling

When modeling hardware with multiple precision modes (FP4, FP8, BF16):

**Per-layer precision assignment** (from DeepSeek V4 QAT):
| Layer | Precision | Rationale |
|-------|-----------|-----------|
| Embedding | BF16 | Small, precision-critical |
| Attention QKV/Output | FP8 | Moderate precision needed |
| MoE FFN (experts) | **FP4** | Bulk computation, FP4-tolerant with QAT |
| Shared FFN | FP4 | FP4-tolerant |
| Router/Gate | FP8 | Top-k selection needs precision |
| Layer Norm | BF16 | Small, precision-critical |

**Precision-weighted effective FLOPS formula:**
$$F_{\text{eff}} = \left(\sum_i \frac{p_i}{F_i}\right)^{-1}$$

where $p_i$ is the fraction of FLOPs at precision $i$ and $F_i$ is the hardware's throughput at that precision.

**Key insight**: With ~75% of FLOPs at FP4, effective FLOPS is ~3.1× BF16-only. This shifts the roofline knee dramatically and changes optimal parallelism (toward more expert parallelism since communication, not compute, becomes the bottleneck).

## KV Cache Hit Rate Integration

When modeling KV cache hit rate $H$ in disaggregated serving:

**Cache-aware effective compute**: $F_{\text{eff}} = (1-H) \cdot F_{\text{prefill}}$

**MoE-specific cache coherence**: $H_{\text{MoE}} = H_{\text{prefix}} \cdot P(\text{same routing} \mid \text{same prefix})$

**Cache-aware break-even hit rate $H^*$**: Minimum $H$ at which disaggregation beats monolithic. Lower $H^*$ = disaggregation viable at lower cache hit rates.

For cache architecture references: Mooncake (arXiv:2407.00079), ShadowRadix (DeepSeek V4), BanaServe (arXiv:2510.13223), PrefillShare (arXiv:2602.12029).

## Pre-Submission Verification (No TeX Required)

When `pdflatex` is not installed, verify correctness with:
```python
# 1. Check all \cite{} entries exist in .bib
# 2. Check all \label{} are unique
# 3. Count \begin{} and \end{} for balance
# 4. Verify $ signs are even (balanced math mode)
```
These catch 90% of compilation errors without needing a TeX installation.
