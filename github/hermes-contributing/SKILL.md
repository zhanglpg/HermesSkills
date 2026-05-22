---
name: hermes-contributing
description: |
  Prepare and validate PR submissions to NousResearch/hermes-agent upstream.
  Trigger when: user wants to contribute code, check PR compliance, or fix
  a PR to meet upstream standards. Covers commit format (Conventional Commits
  with scope), local validation (ruff + pytest), and PR body requirements
  per the project's Contributing guide.
---

# Hermes Agent Contributing

Contribution guide: https://hermes-agent.nousresearch.com/docs/developer-guide/contributing

Local checkout: `~/.hermes/hermes-agent/`

## Branch Naming

```
fix/description        # Bug fixes
feat/description       # New features
docs/description       # Documentation
test/description       # Tests
refactor/description   # Code restructuring
```

## Commit Format (Conventional Commits)

**REQUIRED:** `<type>(<scope>): <description>` — scope is mandatory, not optional.

Allowed scopes: `cli, gateway, tools, skills, agent, install, whatsapp, security`

```
# CORRECT:
feat(agent): pass reasoning_effort to DeepSeek API
fix(security): prevent shell injection in sudo password piping

# WRONG (missing scope):
feat: add DeepSeek reasoning support
```

Fix a commit message (non-interactive): `git commit --amend -m "feat(agent): full message"` (use `-m` because EDITER=sed may not work in Hermes environment). Then push to fork.

Fix PR title: `gh pr edit <NUMBER> --title "feat(agent): ..."`
Fix PR body: `gh pr edit <NUMBER> --body-file /tmp/pr_body.txt`

## PR Body Requirements

Per the Contributing guide, include:
1. **What changed and why**
2. **How to test it**
3. **What platforms you tested on** — explicitly list (e.g. "Tested on: macOS 14 Intel")
4. **Any related issues**

## Pre-Push Validation

Before pushing (or as a PR compliance check), run from the repo root:

```bash
# 1. Ruff on changed files only
cd ~/.hermes/hermes-agent
ruff check agent/transports/chat_completions.py hermes_constants.py run_agent.py

# 2. Relevant tests
python -m pytest tests/agent/transports/test_chat_completions.py -q
python -m pytest tests/run_agent/ -k "deepseek or reasoning" -q
```

**Pitfall:** `ruff check .` on the whole repo produces ~40+ pre-existing E402 errors in `run_agent.py` (deliberate import ordering for `.env` loading). Only check the files actually changed.

## Pushing (Fork vs Upstream)

The local checkout has two remotes:
- `origin` → `NousResearch/hermes-agent` (upstream, read-only for PRs)
- `fork` → `zhanglpg/hermes-agent` (your fork, push target)

**Always push PR branches to `fork`, not `origin`:**

```bash
git push --force-with-lease fork feat/my-branch
```

**Pitfall:** `--force-with-lease` can reject with "stale info" if the local tracking ref for the fork branch is out of date. Fix by fetching first:

```bash
git fetch fork feat/my-branch
git push --force-with-lease fork feat/my-branch
```

## CI

CI may not auto-run on fork PRs. A maintainer must approve workflow runs. If CI column is empty in `gh pr view`, the PR hasn't been approved for CI yet.

## Quick PR Check

```bash
cd ~/.hermes/hermes-agent
gh pr view <NUMBER> --json title,state,body,reviews,comments,statusCheckRollup,additions,deletions,files,headRefName,baseRefName
gh pr checks <NUMBER>
```

## Reference

Full contributing guide excerpt at `references/contributing-guide.md` — includes code style rules, cross-platform compatibility rules, security considerations, and development setup.

## License

MIT License — implicit agreement by contributing. No formal CLA.
