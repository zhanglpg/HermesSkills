# Provider ids, credential env vars, and endpoint overlays

How a provider id in `config.yaml` maps to a key, a base URL, and a model list. Use when a model name works in the vendor console but 401s, 404s, or "unknown model" in Hermes.

## Resolution order for one provider id

| Step | Source | What it decides |
|---|---|---|
| 1 | `custom_providers:` / `providers:` in `~/.hermes/config.yaml` | name, base_url, api_key inline, `models:` list |
| 2 | `plugins/model-providers/<id>/__init__.py` (`ProviderProfile`) | `env_vars`, alias tuple, default base_url |
| 3 | `hermes_cli/providers.py` (`HermesOverlay`) | `base_url_env_var` — env override of the stock URL |
| 4 | `~/.hermes/.env` | the key and the `*_BASE_URL` that actually get used |

A provider is only "configured" when 1 or 2 supplies a key env var that is non-empty in step 4.

## Credential env vars seen on this machine

- `DASHSCOPE_API_KEY` — `alibaba` provider (Qwen + multi-vendor models on DashScope / Alibaba token plan).
- `ALIBABA_CODING_PLAN_API_KEY` / `ALIBABA_CODING_PLAN_BASE_URL` — Alibaba coding-plan provider (`alibaba-coding-plan`).
- `DEEPSEEK_API_KEY` — `deepseek`.
- `ZAI_API_KEY` / `GLM_API_KEY` — `zai` (GLM models).
- `BAILIAN_API_KEY` — the `bailian` custom provider (DashScope coding endpoint, qwen/glm/kimi/MiniMax ids).
- `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`/`ANTHROPIC_TOKEN`, `GOOGLE_API_KEY`, `KIMI_API_KEY`.

Keys with a plan-specific prefix (e.g. `sk-sp-`) belong to a subscription/token-plan endpoint, not the stock public API. Match the key to the endpoint in `*_BASE_URL` before blaming Hermes.

## Verifying a model id without spending a session

1. `~/.hermes/cache/endpoint_model_metadata.json` — `{base_url: {at, models: {<id>: {name}}}}`, written when Hermes lists an endpoint's models. Fastest check that `qwen3.8-flash`-style ids exist.
2. `GET {base_url}/models` with `Authorization: Bearer $KEY` — the authoritative live list, but plan keys often restrict it.
3. One minimal `POST {base_url}/chat/completions` with `max_tokens` ~16 — proves key + model + endpoint together.

A model can exist on the plan endpoint while `GET /models` 401s (plan keys may be scoped to inference only) — a 401 there does not mean the model is missing.

## Provider aliases worth knowing

`alibaba` = `dashscope`, `aliyun`, `qwen-dashscope` (Qwen models live here). `qwen-oauth` = portal.qwen.ai OAuth path, a different provider. `opencode-zen` is the pre-rename id of `opencode`; `zen` is a short alias. Fallback entries are normalized to the canonical id, so an alias and the canonical name for the same backend count as one slot.
