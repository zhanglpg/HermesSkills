---
name: hindsight-venv-patches
description: Re-apply compatibility patches to Hindsight API after pip upgrades. Fixes sentence-transformers, NumPy/PyTorch incompatibility, and embedding dimension alignment.
category: devops
---

# Hindsight Venv Patches

After `pip install --upgrade` of the hindsight_api package (or sentence-transformers/PyTorch),
these patches must be re-applied. Without them, Hindsight will crash on startup.

## Patch 1: cross_encoder.py — model_kwargs → automodel_args

**File:** `~/.hermes/hermes-agent/venv/lib/python3.11/site-packages/hindsight_api/engine/cross_encoder.py`
**Line ~235:** Change `model_kwargs=` to `automodel_args=`

**Why:** Newer sentence-transformers (3.x+) renamed the `CrossEncoder.__init__` parameter from
`model_kwargs` to `automodel_args`. Without this, the reranker crashes:
`TypeError: CrossEncoder.__init__() got an unexpected keyword argument 'model_kwargs'`

**Fix:**
```python
# OLD (line ~235):
                self._model = CrossEncoder(
                    self.model_name,
                    device=device,
                    model_kwargs={"low_cpu_mem_usage": False},
                    trust_remote_code=self.trust_remote_code,
                )
# NEW:
                self._model = CrossEncoder(
                    self.model_name,
                    device=device,
                    automodel_args={"low_cpu_mem_usage": False},
                    trust_remote_code=self.trust_remote_code,
                )
```

## Patch 2: embeddings.py — convert_to_numpy=False

**File:** `~/.hermes/hermes-agent/venv/lib/python3.11/site-packages/hindsight_api/engine/embeddings.py`
**Line ~207:** Change `convert_to_numpy=True` to `convert_to_numpy=False`

**Why:** PyTorch 2.2.2 compiles against NumPy 1.x. When NumPy 2.x is installed, calling
`.numpy()` on tensors in a thread pool (used by sentence-transformers) crashes:
`RuntimeError: Numpy is not available`

The `convert_to_numpy=False` flag returns PyTorch tensors, and `.tolist()` on tensors
works without NumPy. The code on line 208 already calls `.tolist()` which works on both
NumPy arrays and PyTorch tensors.

**Fix:**
```python
# OLD (line ~207):
        embeddings = self._model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
# NEW:
        embeddings = self._model.encode(texts, convert_to_numpy=False, show_progress_bar=False)
```

## Patch 3: NumPy version pin

**Command:**
```bash
~/.hermes/hermes-agent/venv/bin/pip3 install 'numpy<2'
```

**Why:** PyTorch 2.2.2 was compiled against NumPy 1.x and produces warnings/errors with NumPy 2.x.
Downgrading to NumPy 1.26.x is a workaround. The permanent fix is upgrading PyTorch to 2.5+.

## Verification

After applying all patches, restart Hindsight:
```bash
bash ~/.hermes/scripts/hindsight-daemon.sh restart
bash ~/.hermes/scripts/hindsight-daemon.sh status
```

Should show `healthy`. Check logs for "Connection verified: openai/deepseek-v4-flash"
and no ERROR lines during startup.

## Notes

- These patches target files inside the venv — they are NOT tracked by git and will
  be lost on `pip install --upgrade`.
- The daemon script (`~/.hermes/scripts/hindsight-daemon.sh`) handles LLM config
  (from config.yaml) and embedding model override (`BAAI/bge-base-en-v1.5`, 768-dim).
- If the embedding dimension mismatch error returns (768 vs 384), the daemon script's
  `HINDSIGHT_API_EMBEDDINGS_LOCAL_MODEL` setting ensures the correct model is used.
