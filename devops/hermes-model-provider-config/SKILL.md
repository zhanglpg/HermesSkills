---
name: hermes-model-provider-config
description: Hermes model/provider/fallback config and verification.
version: 1.0.1
author: Hermes Agent
license: MIT
tags: [Hermes, config, model, provider, fallback, alibaba, deepseek]
metadata:
  hermes:
    tags: [Hermes, config, model, provider, fallback]
    related_skills: [hermes-reasoning-config, hermes-backup]
---

# Hermes Model / Provider / Fallback Configuration

Changing which model answers, which provider serves it, and what Hermes falls back to when the primary fails. Applies to `hermes config set`, `hermes fallback`, and edits to `~/.hermes/config.yaml`.

## When to Use

- "What model / fallback am I on?"
- Set, replace, reorder, or clear the fallback chain.
- Switch the primary model or provider, or point one at a new endpoint.
- A configured model 401s, 404s, or is rejected as unknown on its provider.

## Read the current state first

```bash
hermes config get model.default; hermes config get model.provider
hermes config get fallback_providers
hermes fallback list        # canonical view: primary + ordered chain + entry base_urls
```

`hermes fallback list` is the fastest, least noisy answer to "what model am I on / what is the fallback?" — prefer it over dumping config.yaml.

## 1. Resolve the provider id — it is not the model vendor

The user names models ("qwen", "glm", "deepseek"); config routes by provider id. Check, in this order:

1. `custom_providers:` and `providers:` entries in `~/.hermes/config.yaml` (`name`, `base_url`, `models`).
2. Built-in provider plugins: `~/.hermes/hermes-agent/plugins/model-providers/<name>/__init__.py` — the `ProviderProfile` shows `env_vars` and default `base_url`.
3. Aliases in `hermes_cli/providers.py`. Qwen models are served by `alibaba` (aliases `dashscope`, `aliyun`, `qwen-dashscope`); `qwen-oauth` (portal.qwen.ai) is a separate provider; a `bailian` custom provider may front the DashScope coding endpoint.

Confirm the model id exists on that endpoint before writing config: the per-endpoint model list is cached in `~/.hermes/cache/endpoint_model_metadata.json` (`{base_url: {models: {...}}}`), or probe one tiny completion. Details: `references/provider-endpoints.md`.

Watch the base_url overlay: a named provider can take its URL from the environment (`alibaba` → `DASHSCOPE_BASE_URL`, read as `HermesOverlay(base_url_env_var=...)`). A token-plan key 401s against the provider's stock public URL — check the relevant `*_BASE_URL` in `~/.hermes/.env`, and pin `base_url` in the entry when the fallback must not silently drift.

When the user's name has no matching provider id, say which id you used and why in the reply instead of guessing silently.

## 2. Write with `hermes config set`

`patch` and `write_file` refuse `~/.hermes/config.yaml` (security guard). Use the CLI:

```bash
hermes config set model.default <model>
hermes config set model.provider <provider>
# list-of-dict values: pass a Python/JSON literal, it is parsed into real YAML
hermes config set fallback_providers "[{'provider': 'alibaba', 'model': 'qwen3.8-flash', 'base_url': 'https://<host>/compatible-mode/v1'}]"
```

- Entry shape: `{provider, model, base_url?, api_mode?}`. Set the whole chain in one call — `fallback_providers` is the single source of truth and replaces rather than appends.
- `hermes fallback add|remove|clear` exist, but `add`/`remove` open an interactive picker; use them only on a real TTY.
- Say plainly whether you replaced or appended an existing fallback entry; users care about losing a working slot.
- Back up first: `cp ~/.hermes/config.yaml ~/.hermes/cache/scratch/config.yaml.bak-$(date +%Y%m%d-%H%M%S)`.

## 3. Verify it actually works — twice

**(a) The target model works at all** — one real turn through the CLI (this exercises provider resolution, auth, api_mode, and reasoning params, unlike a bare curl):

```bash
hermes chat -m <model> --provider <provider> -q "Reply with exactly: OK" --oneshot -Q
```

**(b) The fallback fires** — break the primary on purpose, then restore:

```bash
hermes config set model.default <nonexistent-model>
hermes chat -q "Reply with exactly: FALLBACK-WORKS" --oneshot -Q   # expect the fallback's answer
hermes config set model.default <original>
hermes config get model.default                                     # confirm restored
```

Keep the broken window to one command chain (write, test, restore in the same shell line) so cron jobs or other sessions cannot pick up the broken primary. Finish with `hermes fallback list` + `hermes config check`.

**Do not** import Hermes internals from the project's own `.venv`: the `hermes_cli` bootstrap re-execs into its pinned runtime interpreter with `-I`, dropping that venv's site-packages, so `import yaml` (and every Hermes module) fails there. The interpreter that *does* work is the staged runtime venv that `hermes doctor` prints as `Runtime venv staged (<path>)` — run `<path>/bin/python` with cwd `~/.hermes/hermes-agent` and `import hermes_cli.config` succeeds. Read the path from doctor output; the hash directories change on reinstall. Use it as the escape hatch for config helpers that have no CLI verb (e.g. `save_env_value` / `remove_env_value` for `.env` keys), and still prefer a real `hermes chat` turn for verifying model routing.

## Pitfalls

- The commented `# fallback_model:` example near the bottom of `config.yaml` (openrouter / claude-sonnet) is inert documentation. `fallback_providers` is what runs; do not add both keys — the legacy `fallback_model` is merged/normalized and creates two sources of truth.
- Never print API keys to answer "is it configured?" — read the key's presence and length (`DASHSCOPE_API_KEY` in `~/.hermes/.env`) instead. Redact when echoing provider blocks.
- `hermes config set` on a key the running version does not recognise is refused unless `--force`; a typo therefore fails loudly — do not "fix" it by hand-editing YAML.
- Report the final state the user can re-read later: primary model+provider, fallback entry with its base_url, the backup path, and how each was verified.
