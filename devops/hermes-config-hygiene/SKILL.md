---
name: hermes-config-hygiene
description: Fix Hermes .env/config deprecation warnings via doctor.
version: 1.0.0
author: Hermes Agent
license: MIT
tags: [Hermes, config, env, deprecation, doctor, migration]
metadata:
  hermes:
    tags: [Hermes, config, env, deprecation, doctor, migration]
    related_skills: [hermes-model-provider-config, hermes-backup]
---

# Hermes Config Hygiene

Clearing the legacy settings Hermes reports at startup and in `hermes doctor`:
`.env` keys superseded by `config.yaml`, deprecated config keys, stale provider
and plugin entries. The deliverable is a MIGRATED setting — never a suppressed
banner.

## When to Use

- Startup banner `⚠ Deprecated .env settings detected: …`
- `hermes doctor` lines `⚠ Deprecated: <KEY> (use <replacement>)`
- Moving anything out of `~/.hermes/.env` into `~/.hermes/config.yaml`
- "Fix the warning Hermes prints when it starts"

## Procedure

### 1. Name the exact offender — two different scanners

| Scanner | Where | Scope |
|---|---|---|
| Startup banner | `warn_deprecated_cwd_env_vars()` in `hermes_cli/config.py` | `MESSAGING_CWD`, `TERMINAL_CWD` only |
| `hermes doctor` | `_DEPRECATED_ENV_VARS`, `_DEPRECATED_CONFIG_KEYS` in `hermes_cli/doctor_config.py` | every deprecated env var + config key |

Install root `~/.hermes/hermes-agent`. Cheap authoritative check:

```bash
cd ~/.hermes/hermes-agent && ./.hermes/bin/hermes doctor 2>&1 | grep -i -B1 -A2 'Deprecated'
```

If the startup banner names something the doctor list does not, locate the
emitter before editing: `grep -rn "<message fragment>" --include=*.py .`

### 2. Find the canonical replacement, then measure the behaviour delta

Read the replacement's resolver BEFORE deleting the legacy key and show the two
produce the same value. For cwd that is
`gateway/cwd_placeholder.py::resolve_placeholder_terminal_cwd`: an explicit
`terminal.cwd` wins; a placeholder (`.`, `auto`, `cwd`) on the `local` backend
resolves to `MESSAGING_CWD`, else `Path.home()`. So when the legacy value equals
`Path.home()`, deleting it is behaviour-neutral — while "fixing" it by pinning
`terminal.cwd: /home/<user>` pushes EVERY session, including CLI runs started in
another project, into that one directory. Prefer removal over pinning.

### 3. Back up, then edit `.env` through Hermes' own helpers

```bash
cd ~/.hermes && cp .env .env.bak-$(date +%Y%m%dT%H%M%SZ)
```

`hermes config set|unset` operates on `config.yaml` only — there is no CLI verb
for `.env` keys. Use the shipped writers so line normalisation, `0600` mode, the
env lock and the in-process cache all stay consistent:

```bash
cd ~/.hermes/hermes-agent
PY=<the path printed by: hermes doctor | grep 'Runtime venv staged'>/bin/python
$PY -c "from hermes_cli.config import remove_env_value, load_env; print('removed:', remove_env_value('MESSAGING_CWD')); print('still present:', 'MESSAGING_CWD' in load_env())"
# save_env_value('KEY', 'value') is the write counterpart
```

Hand-editing `.env` works but forfeits the lock, mode preservation and
normalisation. Never `patch`/`write_file` `~/.hermes/config.yaml`; use
`hermes config set`.

### 4. Verify in both directions

```bash
cd ~/.hermes/hermes-agent && ./.hermes/bin/hermes doctor 2>&1 | grep -i -A1 deprecated   # ✓ No deprecated config keys or env vars
diff ~/.hermes/.env.bak-<stamp> ~/.hermes/.env          # exactly the removed line(s)
ls -l ~/.hermes/.env                                    # still -rw-------
```

A one-sided "no output" check also passes when you edited the wrong file, so
run both controls against the detector function:

- negative — live home prints nothing;
- positive — a copy of the OLD `.env` still prints the banner.

`HERMES_ENV_PATH` is NOT honoured (`get_env_path()` is `get_hermes_home()/'.env'`),
so reproduce with a scratch home holding the old file:

```bash
T=$(mktemp -d "$HOME/.hermes/cache/scratch/envctl.XXXXXX"); cp ~/.hermes/.env.bak-<stamp> "$T/.env"
cd ~/.hermes/hermes-agent && HERMES_HOME=$T $PY -c "from hermes_cli.config import warn_deprecated_cwd_env_vars as w; w()"
rm -rf "$T"
```

### 5. Make it take effect without collateral damage

The running gateway holds the old environment in memory, so the banner survives
until restart. `hermes gateway restart` REFUSES while chat turns are live and
lists them, offering `--yes` as the override — never pass `--yes` when the
listing includes the current conversation (`local:dm`, your own running turn).
Verify at function level instead (step 4), and tell the user the banner clears on
the next restart.

## Pitfalls

- State what the edit does to behaviour. "Warning gone" is not the success
  criterion; "warning gone and resolution unchanged" is. Show the resolver's
  output for the before/after value.
- `MESSAGING_CWD` is usually just `Path.home()`; removal needs no `terminal.cwd`
  edit at all. Empty or commented keys are never flagged.
- `.env.bak-*` snapshots are not read by the detectors — keeping them is safe and
  is what makes the positive control possible.
- `hermes doctor` also reports unrelated legacy findings (`custom_providers`
  entries with no `providers:` twin, retired plugins, retired models). Treat each
  as its own deliberate migration with its own target shape; do not bundle them
  into one "cleanup" edit.
- Deprecated keys can be bridged into the process environment at runtime
  (`terminal.cwd` → `TERMINAL_CWD`); the detectors read the FILE, so a bridged
  var in a live process is not evidence of a problem.
- Key→replacement map and the cwd decision table: `references/deprecated-key-map.md`.

For model/provider/fallback routing keys use `hermes-model-provider-config`; for
snapshotting the whole `~/.hermes` tree before bulk edits use `hermes-backup`.
