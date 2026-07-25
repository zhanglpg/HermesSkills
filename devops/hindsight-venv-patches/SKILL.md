---
name: hindsight-venv-patches
description: Historical record of three venv source patches that used to keep the hindsight API alive across pip upgrades. Now obsolete — the durable fix lives in hermes-agent's pyproject.toml. Use this doc only if you ever see the original symptoms recur.
category: devops
---

# Hindsight Venv Patches — Historical / Fallback

> **As of 2026-05-24 this skill is no longer the primary fix.** The three
> patches it documented were workarounds for a dependency-version drift
> between `hindsight-api-slim 0.5.3` and the venv's installed `torch`,
> `sentence-transformers`, and `numpy`. The root cause is fixed by the
> pins in `~/.hermes/hermes-agent/pyproject.toml` (`hindsight` and `voice`
> extras). Keep this file for the symptom→cause map; the fix recipes
> below are emergency-only fallbacks if upstream regresses.

## TL;DR — what *should* happen now

```bash
# Install only the deps that satisfy the platform constraints in pyproject.
~/.hermes/hermes-agent/venv/bin/pip3 install -e ~/.hermes/hermes-agent[hindsight,voice]
# On Intel Mac that pins torch==2.2.2, numpy<2, sentence-transformers>=5.0.
bash ~/.hermes/scripts/hindsight-daemon.sh restart
bash ~/.hermes/scripts/hindsight-daemon.sh status   # → healthy
```

No file patches required. The upstream `hindsight_api/engine/cross_encoder.py`
and `hindsight_api/engine/embeddings.py` work as-shipped under
`sentence-transformers>=5.0` (which is what the hindsight code was actually
written for — 5.x restored `model_kwargs=` as the canonical kwarg name).

## Root cause (the part that was missed in the original patches)

| Symptom | True cause | Pre-2026-05-24 workaround | Durable fix |
|---|---|---|---|
| `TypeError: CrossEncoder got unexpected keyword 'model_kwargs'` | venv had `sentence-transformers 3.2.1` (which uses `automodel_args=`), but hindsight code calls `model_kwargs=` | Patch 1: edit `cross_encoder.py` to use `automodel_args=` | `sentence-transformers>=5.0` in `hindsight` extra — restores the API the code expects |
| `RuntimeError: Numpy is not available` in thread pool | numpy 2.x installed but torch 2.2.2 is ABI-bound to numpy 1.x | Patch 2: edit `embeddings.py` to skip `.numpy()` (`convert_to_numpy=False`) **and** Patch 3: `pip install 'numpy<2'` | Conditional pin: `numpy<2` on Intel Mac; `numpy==2.4.3` elsewhere |
| Patches lost on every `pip install --upgrade` | venv files aren't tracked; the patches were forensic, not curative | "Re-apply the patches" | Install constraints come from `pyproject.toml`, not the venv |

## Why Intel Mac is special

PyPI dropped Intel macOS wheels for PyTorch after **2.2.2**. The newest
torch you can install on Intel Mac is therefore 2.2.2 (this is the
constraint behind the `numpy<2` requirement). The pin in
`pyproject.toml`'s `hindsight` extra is:

```toml
"torch==2.2.2; sys_platform == 'darwin' and platform_machine == 'x86_64'",
"torch>=2.6.0; sys_platform != 'darwin' or platform_machine != 'x86_64'",
```

If/when Liping moves to Apple Silicon or Linux, the second branch lets
the install take a modern torch built against numpy 2.x.

## Emergency fallback — applying the patches by hand

Only do this if you can't move sentence-transformers off 3.x for some
reason. All three are reverts of upstream behavior, not improvements.

### Patch 1: `model_kwargs` → `automodel_args`

**File:** `~/.hermes/hermes-agent/venv/lib/python3.11/site-packages/hindsight_api/engine/cross_encoder.py` (line ~235)

```python
# Upstream (works with sentence-transformers >=5.0):
self._model = CrossEncoder(..., model_kwargs={"low_cpu_mem_usage": False}, ...)
# Patched (works with sentence-transformers 3.0-3.2):
self._model = CrossEncoder(..., automodel_args={"low_cpu_mem_usage": False}, ...)
```

### Patch 2: `convert_to_numpy=True` → `False`

**File:** `~/.hermes/hermes-agent/venv/lib/python3.11/site-packages/hindsight_api/engine/embeddings.py` (line ~207)

```python
# Upstream:
embeddings = self._model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
# Patched:
embeddings = self._model.encode(texts, convert_to_numpy=False, show_progress_bar=False)
```

The downstream `[emb.tolist() for emb in embeddings]` works on both numpy
arrays and torch tensors. **Note: this patch was always defensive — with
numpy <2 actually installed, the upstream `True` works fine. Patch 3
makes Patch 2 unnecessary.**

### Patch 3: `numpy<2` pin

```bash
~/.hermes/hermes-agent/venv/bin/pip3 install 'numpy<2'
```

This is the only one of the three that has a durable form: it's now baked
into pyproject's `voice` extra as a platform-conditional pin.

## Snapshot before mucking

If you do end up re-patching, first snapshot the affected files so you
can roll back:

```bash
SNAP=~/hermes-backups/hindsight-patch-$(date +%Y%m%d-%H%M%S)
mkdir -p $SNAP
cp ~/.hermes/hermes-agent/venv/lib/python3.11/site-packages/hindsight_api/engine/{cross_encoder,embeddings}.py $SNAP/
~/.hermes/hermes-agent/venv/bin/pip3 freeze > $SNAP/pip-freeze.txt
```

## Verification

```bash
bash ~/.hermes/scripts/hindsight-daemon.sh restart
curl -s http://localhost:9177/health   # → {"status":"healthy","database":"connected"}
tail ~/.hindsight/profiles/hermes.log  # → look for "Embeddings: local provider initialized (dim: 768)"
```

Healthy means: the API booted, the BGE embedding model loaded, and the
local reranker loaded. No need to inspect the patched files.
