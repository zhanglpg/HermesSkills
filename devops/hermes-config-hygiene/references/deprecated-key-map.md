# Deprecated key → replacement map

Re-read the source tuples before quoting this table — the list grows.

- `hermes_cli/doctor_config.py` → `_DEPRECATED_ENV_VARS`, `_DEPRECATED_CONFIG_KEYS`
- `hermes_cli/config.py` → `warn_deprecated_cwd_env_vars()` — startup banner, cwd keys only

## Env vars in `~/.hermes/.env`

Flagged only when the value is non-empty; a commented or empty key passes.

| Legacy | Replacement |
|---|---|
| `TERMINAL_CWD` | `terminal.cwd` in config.yaml |
| `MESSAGING_CWD` | `terminal.cwd` in config.yaml |
| `HERMES_TOOL_PROGRESS` | `display.tool_progress` (ignored since config floor v12) |
| `HERMES_TOOL_PROGRESS_MODE` | `display.tool_progress` |
| `QQ_HOME_CHANNEL` | `QQBOT_HOME_CHANNEL` |
| `QQ_HOME_CHANNEL_NAME` | `QQBOT_HOME_CHANNEL_NAME` |

Process environment is deliberately not scanned: `os.environ` receives bridged
values such as `terminal.cwd → TERMINAL_CWD` and would false-positive. Only the
on-disk `.env` counts, so a bridged var inside a running process is not a problem.

## Config keys in `config.yaml`

| Legacy | Replacement |
|---|---|
| `display.tool_progress_overrides` | `display.platforms` |
| `delegation.max_async_children` | `delegation.max_concurrent_children` |
| `compression.summary_model` | `auxiliary.compression` |
| `compression.summary_provider` | `auxiliary.compression` |
| `compression.summary_base_url` | `auxiliary.compression` |

## `terminal.cwd` resolution decision table

Canonical setting is `terminal.cwd` in config.yaml; the gateway bridges it to
`TERMINAL_CWD`. Resolution lives in `gateway/cwd_placeholder.py`
(`resolve_placeholder_terminal_cwd`) and `gateway/run_bootstrap.py`.

| `terminal.cwd` | backend | result |
|---|---|---|
| explicit absolute path | any | that path |
| `.` / `auto` / `cwd` | `local` | `MESSAGING_CWD` if set, else `Path.home()` |
| `.` / `auto` / `cwd` | `docker` + mount-cwd-to-workspace + host `MESSAGING_CWD` | that host path (mapped to `/workspace`) |
| `.` / `auto` / `cwd` | any other backend | unset — sandbox default |

Implication: with a placeholder and the `local` backend, a legacy `MESSAGING_CWD`
equal to the home directory can be deleted with zero behaviour change. Setting an
explicit `terminal.cwd` instead pins every session — CLI included — to that one
directory, which is a different, usually unwanted, behaviour change.

Preserve parity by printing the resolved value before and after:

```bash
cd ~/.hermes/hermes-agent && $PY -c "from gateway.cwd_placeholder import resolve_placeholder_terminal_cwd as r; print(r(configured_cwd='.', terminal_backend='local', messaging_cwd=None, docker_mount_cwd_to_workspace=False, home_fallback=str(__import__('pathlib').Path.home())))"
```
