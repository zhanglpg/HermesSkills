---
name: hermes-reasoning-config
description: How Hermes handles reasoning/thinking parameters across providers — architecture, source files, and how to add provider-specific support. Use when configuring thinking effort for a new provider or debugging why reasoning params aren't being sent.
version: 1.1.0
author: Hermes Agent
tags: [Hermes, reasoning, thinking, provider, DeepSeek, Kimi, PR, open-source]
---

# Hermes Reasoning/Thinking Configuration

Understanding and modifying how Hermes passes reasoning/thinking parameters to LLM providers.

## Architecture Overview

### 1. Config → Parsed Reasoning Config

**File:** `hermes_constants.py`

| Config value | `parse_reasoning_effort()` output |
|---|---|
| `reasoning_effort: medium` | `{"enabled": True, "effort": "medium"}` |
| `reasoning_effort: max` | `{"enabled": True, "effort": "max"}` |
| `reasoning_effort: xhigh` | `{"enabled": True, "effort": "xhigh"}` |
| `reasoning_effort: none` | `{"enabled": False}` |
| Empty/unset | `None` |

Valid efforts: `minimal`, `low`, `medium`, `high`, `xhigh`, `max`.

### 2. Reasoning Config → API Parameters

**Modern path (provider profiles):** Registered providers (DeepSeek, Kimi, etc.) implement a `ProviderProfile` subclass with `build_api_kwargs_extras()` in `plugins/model-providers/<name>/__init__.py`. This is the preferred extension point — see the DeepSeek profile for a worked example.

**Legacy fallback:** `agent/transports/chat_completions.py` — method `build_api_kwargs()` handles unregistered/unknown providers through direct provider-specific conditionals. New providers SHOULD use the profile system; the legacy path is for ad-hoc / one-off endpoints.

The parsed reasoning config flows to the transport layer as `reasoning_config` in `params`. **Each provider gets different treatment:**

| Provider | `reasoning_effort` (top-level) | `thinking` (extra_body) | `reasoning` (extra_body) |
|---|---|---|---|
| **Kimi** | ✅ Lines 207-220 | ✅ Lines 234-241 | ❌ |
| **DeepSeek** | ✅ Lines 222-235 | ✅ Lines 258-268 | ❌ |
| **OpenRouter** | ❌ | ❌ | ✅ Lines 270-284 (when `supports_reasoning=True`) |
| **Nous** | ❌ | ❌ | ✅ (same block, Nous-specific logic) |
| **GitHub Models** | ❌ | ❌ | ✅ (uses `github_reasoning_extra`) |
| **Custom providers** | ❌ | ❌ | ❌ — **only handles `think: false`** (line 286-292) |
| **Anthropic** | N/A | N/A | Handled by `anthropic_adapter.py` |
| **Codex** | N/A | N/A | Handled by `codex.py` |

### 3. `supports_reasoning_extra_body()` gate

**File:** `run_agent.py` line 7586-7621

Only returns `True` for:
- `nousresearch.com` base URL
- `ai-gateway.vercel.sh` base URL
- GitHub Models with reasoning-capable models
- **OpenRouter** with specific model prefixes: `deepseek/`, `anthropic/`, `openai/`, `x-ai/`, `google/gemini-2`, `qwen/qwen3`

**Direct API endpoints** (e.g. `api.deepseek.com`, `api.z.ai`) return `False` — these get NO reasoning extra_body.

## How to Add Reasoning Support for a New Provider

**Preferred approach (provider profile):** Create a `ProviderProfile` subclass in `plugins/model-providers/<name>/__init__.py` with a `build_api_kwargs_extras()` method returning `(extra_body, top_level)` dicts. Register via `register_provider()`. See `plugins/model-providers/deepseek/__init__.py` for the canonical example.

**Legacy approach (direct fallback):** Only use this for unregistered/one-off providers. Below is the legacy pattern that patches `chat_completions.py` and `run_agent.py` directly.

### Step 1: Provider detection in `run_agent.py` (~line 7500)

Add a detection flag alongside `_is_kimi`:

```python
_is_newprovider = (
    self.provider == "newprovider"
    or base_url_host_matches(self.base_url, "api.newprovider.com")
)
```

Then pass it to `build_kwargs()` (after `is_kimi=_is_kimi,`):

```python
is_newprovider=_is_newprovider,
```

### Step 2: Handle in `chat_completions.py`

**a) Add to docstring** (~line 100):
```python
is_newprovider: bool
```

**b) Extract from params** (~line 190):
```python
is_newprovider = params.get("is_newprovider", False)
```

**c) Add top-level reasoning_effort** (after Kimi block ~line 220):
```python
if is_newprovider:
    _np_thinking_off = bool(
        reasoning_config
        and isinstance(reasoning_config, dict)
        and reasoning_config.get("enabled") is False
    )
    if not _np_thinking_off:
        _np_effort = "high"
        if reasoning_config and isinstance(reasoning_config, dict):
            _e = (reasoning_config.get("effort") or "").strip().lower()
            if _e in ("low", "medium", "high", "xhigh", "max"):
                _np_effort = _e
        api_kwargs["reasoning_effort"] = _np_effort
```

**d) Add extra_body.thinking** (after Kimi extra_body block ~line 257):
```python
if is_newprovider:
    _np_thinking_enabled = True
    if reasoning_config and isinstance(reasoning_config, dict):
        if reasoning_config.get("enabled") is False:
            _np_thinking_enabled = False
    extra_body["thinking"] = {
        "type": "enabled" if _np_thinking_enabled else "disabled",
    }
```

### Step 3: If provider uses effort levels outside `VALID_REASONING_EFFORTS`

Add to `hermes_constants.py`:
```python
VALID_REASONING_EFFORTS = ("minimal", "low", "medium", "high", "xhigh", "max")
```

### What to verify for each provider

1. **API docs**: Does the provider use `reasoning_effort` (top-level) or `thinking` (extra_body) or both?
2. **Default state**: Is thinking enabled by default? What's the default effort?
3. **Effort mapping**: Does the provider remap effort levels (e.g. DeepSeek maps `xhigh` → `max`, `medium` → `high`)?
4. **Tool call compatibility**: Does the provider require `reasoning_content` on every assistant tool-call message for replay? (Kimi and DeepSeek both do — see `_needs_kimi_tool_reasoning()` and `_needs_deepseek_tool_reasoning()` in `run_agent.py`)

## Key Files

| File | What |
|---|---|
| `~/.hermes/config.yaml` | User config — `reasoning_effort` value |
| `hermes_constants.py` | `parse_reasoning_effort()` / `VALID_REASONING_EFFORTS` — config string → dict |
| `plugins/model-providers/<name>/__init__.py` | **Provider profile** — modern path; `build_api_kwargs_extras()` returns `(extra_body, top_level)` |
| `plugins/model-providers/deepseek/__init__.py` | Canonical example — DeepSeek reasoning profile |
| `agent/transports/chat_completions.py` | `build_api_kwargs()` — legacy fallback; provider-specific conditionals |
| `run_agent.py` | `_supports_reasoning_extra_body()` — gates extra_body |
| `run_agent.py` | `_needs_deepseek_tool_reasoning()` — tool-call reasoning requirement |
| `agent/anthropic_adapter.py` | Anthropic-specific reasoning handling |
| `agent/transports/codex.py` | Codex Responses API reasoning |

## DeepSeek-Specific Notes

DeepSeek reasoning is handled by the **provider profile** system, NOT the legacy fallback path in `chat_completions.py`. The profile lives at:

**`plugins/model-providers/deepseek/__init__.py`** — `DeepSeekProfile(ProviderProfile)`

### Wire shape (sent by the profile)

```json
{
  "reasoning_effort": "<low|medium|high|max>",
  "extra_body": {"thinking": {"type": "enabled" | "disabled"}}
}
```

### Behaviour

- Thinking is **enabled by default**; effort defaults to **high** (DeepSeek server default)
- Effort mapping: `xhigh`/`max` → `"max"`. `low`/`medium`/`high` passed through.
- Only applied to thinking-capable models: `deepseek-v4-*`, `deepseek-v5-*`, `deepseek-reasoner`. V3 (`deepseek-chat`) is a no-op.
- Requires `reasoning_content` on every assistant tool-call message for replay — handled in `run_agent.py` via `_needs_deepseek_tool_reasoning()`
- **Provider detection** (`run_agent.py`): `provider == "deepseek"` OR `"deepseek" in model` OR `api.deepseek.com` base URL

### History

- Original PR #16448 (zhanglpg fork) targeted the legacy `chat_completions.py` fallback path — that approach is now superseded by the provider profile system
- The local branch `feat/deepseek-reasoning-effort` is obsolete and can be deleted
- **Config**: Set `reasoning_effort: max` (or `xhigh`) in `~/.hermes/config.yaml` under `agent:`
