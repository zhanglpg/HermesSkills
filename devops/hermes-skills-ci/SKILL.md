---
name: hermes-skills-ci
description: "Use when pushing HermesSkills: lint, format, pytest gate."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [ci, lint, ruff, github-actions, skills-repo]
    related_skills: [github-pr-workflow]
---

# HermesSkills Repo: CI Gate Before Push

## Overview

The user's public skills repo (`~/.hermes/skills`, GitHub `zhanglpg/HermesSkills`) enforces strict CI on every push to `main`:

```yaml
ruff check .          # lint (E, F, W, I; E501 ignored)
ruff format --check . # formatting
pytest tests/         # 139 tests
```

Any push that skips these turns the branch red. Liping has explicitly asked that the linter be fixed before every submit — treat a green local gate as part of "done".

## When to Use

- Before committing or pushing anything to `~/.hermes/skills` (HermesSkills repo)
- When CI on zhanglpg/HermesSkills is red and you need to find/fix the cause
- Before submitting any skill change that touches `scripts/*.py`
- Don't use for the upstream `hermes-agent` repo — see `hermes-contributing` for that

## Why it "constantly breaks"

1. **Unpinned ruff in CI.** `pip install ruff` used to grab the newest release; ruff 0.17 added **Markdown code-fence formatting**, which suddenly wanted to reformat 114 `SKILL.md` files with no code change from anyone. Ruff is now pinned (`ruff==0.17.3`) in `.github/workflows/ci.yml` and `pyproject.toml`, and `**/*.md` is `extend-exclude`d from ruff so skill docs never churn. Do not unpin it casually.
2. **New scripts written without running the formatter.** Most script edits arrive unformatted (line wrapping, import order). Always run `ruff format` on the repo before committing.
3. **Archived/vendored trees.** `.archive/`, `.curator_backups/`, `.curator_state/`, `.hub/`, `.locks/` are excluded via `extend-exclude`; don't lint them by hand and don't re-add them to scope.

## Local gate (run before every commit/push)

```bash
cd ~/.hermes/skills
ruff check . && ruff format --check .
/tmp/skills-venv/bin/python -m pytest tests/ -q   # see bootstrap below
```

If formatting fails: `ruff format .` then re-run `ruff check .` and the tests. Three commands, in this order — `ruff check --fix .` first is fine when lint errors exist (it fixes import order / unused imports), then `ruff format .`.

## Environment bootstrap (macOS, no Python 3.11+ installed)

System `python3` is 3.9 (Apple CLT) and lacks the deps. Use uv:

```bash
uv venv --python 3.11 /tmp/skills-venv
uv pip install --python /tmp/skills-venv/bin/python pytest pytest-cov pandas yfinance ruff==0.17.3
```

`ruff` is also installed at `~/Library/Python/3.9/bin/ruff` (pip --user); put it on PATH if `ruff: command not found`:

```bash
export PATH="$HOME/Library/Python/3.9/bin:$PATH"
```

## Pre-commit hook (already installed)

Tracking `.githooks/pre-commit` runs `ruff check .` and `ruff format --check .` on every commit. Activate once per clone:

```bash
git config core.hooksPath .githooks
```

It is deliberately lint-only (fast); tests still belong to `pytest tests/` before push and to CI.

## Pitfalls

1. **Do not run `ruff format` with a newer ruff than the pin.** A different version can reflow Python and Markdown differently, producing a huge diff and failing CI against the pinned version. Check `ruff --version` == 0.17.3.
2. **`ruff format` may reformat Markdown code fences** if `**/*.md` is removed from `extend-exclude`. Leave that exclusion in place; skill docs are hand-tuned.
3. **`pytest` from the wrong interpreter** silently uses stale system deps. Always use `/tmp/skills-venv/bin/python -m pytest tests/`, never bare `pytest`.
4. **Commit only intended files.** `git status` first; exclude `*.db`, `__pycache__`, `.DS_Store`, `.usage.json`, curator state. `.gitignore` covers most, but check before `git add -A`.
5. **Duplicated skill scripts** exist (`productivity/docx` vs `productivity/microsoft-office`, xlsx copies). Fixing one copy but not the other leaves CI red — run the repo-wide commands, not per-file fixes.

## Verification Checklist

- [ ] `ruff check .` → "All checks passed!"
- [ ] `ruff format --check .` → "N files already formatted"
- [ ] `/tmp/skills-venv/bin/python -m pytest tests/ -q` → all pass
- [ ] `git status --porcelain` contains only intended files
- [ ] After push: `gh run list --repo zhanglpg/HermesSkills --limit 1` shows success

## One-Shot Recipe

```bash
cd ~/.hermes/skills
export PATH="$HOME/Library/Python/3.9/bin:$PATH"
ruff check --fix . && ruff format . && ruff check . && ruff format --check .
/tmp/skills-venv/bin/python -m pytest tests/ -q
git add -A && git status --porcelain
git commit -m "chore: <description>" && git push
gh run list --repo zhanglpg/HermesSkills --limit 1
```
