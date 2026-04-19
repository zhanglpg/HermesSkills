---
name: hindsight-setup
description: "Set up and troubleshoot Hindsight agent memory on macOS (especially Intel Macs without MLX). Covers daemon configuration, embeddings/reranker provider selection, and workarounds for the hindsight-embed CLI."
version: 1.0
---

# Hindsight Agent Memory — Setup & Troubleshooting

## When to Use
- Setting up Hindsight for the first time
- Hindsight API crashes or fails to start
- `hindsight-embed` CLI fails with dependency resolution errors
- Migrating from local embeddings to remote providers

## Architecture

Hindsight has two components:
1. **hindsight-api** — The API server (works on any platform with correct providers)
2. **hindsight-embed** — The CLI client (uses `uv` runtime dependency resolution that may pull platform-incompatible deps)

The API server is the important part. The embed CLI is optional — Hermes tools (`hindsight_recall`, `hindsight_retain`, `hindsight_reflect`) call the HTTP API directly.

## Quick Health Check

```bash
curl -s http://localhost:9177/health
# Expected: {"status":"healthy","database":"connected"}
```

## Configuration

### Env File Location
`~/.hindsight/profiles/hermes.env`

### Working Config for Intel Mac (no MLX/torch)

```bash
HINDSIGHT_API_LLM_PROVIDER=gemini
HINDSIGHT_API_LLM_API_KEY=<your-gemini-api-key>
HINDSIGHT_API_LLM_MODEL=gemini-2.5-flash
HINDSIGHT_API_LOG_LEVEL=info
HINDSIGHT_API_EMBEDDINGS_PROVIDER=google          # NOT "gemini" — that's invalid
HINDSIGHT_API_EMBEDDINGS_GEMINI_MODEL=gemini-embedding-001
HINDSIGHT_API_RERANKER_PROVIDER=rrf                # NOT "local" — crashes on Intel Mac
```

### Provider Name Pitfalls

| What you want | Correct provider name | Wrong name | Why wrong |
|---|---|---|---|
| Gemini embeddings | `google` | `gemini` | `gemini` is not a valid embeddings provider — only `local`, `tei`, `openai`, `cohere`, `google`, `litellm`, `litellm-sdk` |
| Gemini LLM | `gemini` | `google` | LLM provider namespace is different from embeddings |
| No reranking | `rrf` | `none` or `disabled` | `rrf` is the passthrough provider (RRF scoring without neural reranking) |

## Common Failure Modes

### 1. `litellm` embeddings — "Failed to connect to LiteLLM proxy at localhost:4000"

The `litellm` embeddings provider expects a **running LiteLLM proxy server** at `http://localhost:4000`. It does NOT make direct API calls.

**Fix:** Use `google` provider instead, which calls the Gemini API directly with the same API key.

### 2. Reranker `local` — NumPy 2.x / torch crash

```
RuntimeError: Failed to connect to LiteLLM proxy at http://localhost:4000
A module that was compiled using NumPy 1.x cannot be run in NumPy 2.4.4
```

The `local` reranker loads `sentence_transformers` → `torch`, which may crash on Intel Mac due to NumPy version mismatch.

**Fix:** Set `HINDSIGHT_API_RERANKER_PROVIDER=rrf` to disable neural reranking.

### 3. `hindsight-embed` CLI fails — "uv resolves [all] extras requiring MLX"

The embed CLI uses `uv` for runtime dependency resolution which pulls `[all]` extras including MLX (Apple Silicon only). This makes the entire CLI unusable on Intel Mac.

**Fix:** Use the HTTP API directly (port 9177) or the daemon wrapper script. The Hermes agent tools already do this.

### 4. API key overwritten with literal `***`

When using `write_file` to update the env file, be careful not to write literal `***` as the API key (it appears masked in tool output but the file needs the real key).

**Fix:** Source the existing env and use shell variable expansion:
```bash
cat > ~/.hindsight/profiles/hermes.env << 'EOF'
HINDSIGHT_API_LLM_PROVIDER=gemini
EOF
echo "HINDSIGHT_API_LLM_API_KEY=$HINDSIGHT_API_LLM_API_KEY" >> ~/.hindsight/profiles/hermes.env
cat >> ~/.hindsight/profiles/hermes.env << 'EOF'
...remaining vars...
EOF
```

## Daemon Wrapper

A wrapper script at `~/.hermes/scripts/hindsight-daemon.sh` provides start/stop/status:

```bash
bash ~/.hermes/scripts/hindsight-daemon.sh start   # Starts API with health check
bash ~/.hermes/scripts/hindsight-daemon.sh status   # Shows PID + health
bash ~/.hermes/scripts/hindsight-daemon.sh stop     # Graceful shutdown
```

Key design decisions:
- **No `--daemon` flag** — runs API directly under `nohup` (no fork confusion)
- **Health-check loop** — waits up to 15s for `/health` endpoint before declaring success
- **PID file** at `~/.hindsight/profiles/hermes.pid`

## Starting the API Manually

```bash
set -a; source ~/.hindsight/profiles/hermes.env; set +a
~/.hermes/hermes-agent/venv/bin/hindsight-api --port 9177
```

## Verifying Startup

Check the log for these lines:
```
Embeddings: provider=google
Reranker: provider=rrf
Application startup complete.
Uvicorn running on http://0.0.0.0:9177
```

If you see `Application startup failed. Exiting.` — check the log above for the specific error.

## Installed Versions (reference)

| Package | Version | Notes |
|---------|---------|-------|
| hindsight_api | 0.5.3 | API server |
| hindsight_client | 0.5.3 | Client library |
| hindsight_embed | 0.5.3 | CLI (broken on Intel Mac) |
| fastmcp | 3.2.4 | Had breaking change removing `stateless_http` param |

## Available Embeddings Providers

`local`, `tei`, `openai`, `cohere`, `google`, `litellm`, `litellm-sdk`

## Available Reranker Providers

`local`, `tei`, `cohere`, `zeroentropy`, `siliconflow`, `google`, `flashrank`, `litellm`, `litellm-sdk`, `rrf`, `jina-mlx`
