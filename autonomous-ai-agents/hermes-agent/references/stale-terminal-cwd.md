# Stale TERMINAL_CWD — Terminal Dead on Arrival

## Symptom Signature

Every terminal command fails immediately with exit code 126:

```
/bin/bash: line 1: cd: /Users/lipingzhang/.openclaw/workspace: No such file or directory
```

Even `bash --norc --noprofile -c 'echo hello'` fails identically — proving it is NOT a bashrc issue.

## Mechanism

### 1. Gateway bridges `.env` → `TERMINAL_CWD` (`gateway/run.py` ~line 907-910)

```python
_configured_cwd = os.environ.get("TERMINAL_CWD", "")
if not _configured_cwd:
    _fallback = os.getenv("MESSAGING_CWD") or str(Path.home())
    os.environ["TERMINAL_CWD"] = _fallback
```

When `TERMINAL_CWD` is unset at startup, the gateway falls back to `MESSAGING_CWD` from `.env`, then to `$HOME`.

### 2. Terminal tool reads `TERMINAL_CWD` as cwd (`tools/terminal_tool.py` ~line 1033)

```python
cwd = os.getenv("TERMINAL_CWD", default_cwd)
```

### 3. `_wrap_command` injects `cd` before every command (`tools/environments/base.py` ~line 446)

```python
quoted_cwd = self._quote_cwd_for_cd(cwd)
parts.append(f"builtin cd -- {quoted_cwd} || exit 126")
```

**This is the kill shot.** The `cd` runs before the actual command. If the cwd doesn't exist, bash exits 126 before the command ever executes.

### 4. CLI mode skips the config bridge for gateway processes (`cli.py` ~line 597-602)

```python
_is_gateway = os.environ.get("_HERMES_GATEWAY") == "1"
if env_var == "TERMINAL_CWD":
    if _is_gateway:
        continue  # trust gateway's own bridge
```

So `terminal.cwd` in config.yaml is ignored inside the gateway — the `.env` value wins.

## Fix

### Step 1: Check

```bash
grep 'TERMINAL_CWD\|MESSAGING_CWD' ~/.hermes/.env
```

### Step 2: Fix the .env

If `MESSAGING_CWD` points to a nonexistent path:

```bash
sed -i '' 's|MESSAGING_CWD=.*|MESSAGING_CWD=$HOME|' ~/.hermes/.env
```

### Step 3: Restart

```bash
hermes gateway restart
```

## Diagnostic Technique (Terminal Dead)

When the terminal tool is completely broken, use `execute_code` to bypass it:

```python
import os, subprocess

# Check what's set
for var in ['TERMINAL_CWD', 'MESSAGING_CWD']:
    print(f"{var}={os.environ.get(var, 'NOT SET')}")

# Fix .env file
env_path = '/Users/lipingzhang/.hermes/.env'
with open(env_path) as f:
    lines = f.readlines()
new_lines = []
for line in lines:
    if line.startswith('MESSAGING_CWD='):
        new_lines.append(f'MESSAGING_CWD={os.path.expanduser("~")}\n')
    else:
        new_lines.append(line)
with open(env_path, 'w') as f:
    f.writelines(new_lines)
```

## Common After OpenClaw Migration

The OpenClaw migration writes `MESSAGING_CWD` to the old `~/.openclaw/workspace` path (see `optional-skills/migration/openclaw-migration/scripts/openclaw_to_hermes.py` line 1341). After deletion of `~/.openclaw/`, the terminal dies silently.
