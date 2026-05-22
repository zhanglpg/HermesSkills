# Contributing Guide Excerpt

From https://hermes-agent.nousresearch.com/docs/developer-guide/contributing (as of 2026-05-01)

## Contribution Priorities

1. Bug fixes — crashes, incorrect behavior, data loss
2. Cross-platform compatibility — macOS, different Linux distros, WSL2
3. Security hardening — shell injection, prompt injection, path traversal
4. Performance and robustness — retry logic, error handling, graceful degradation
5. New skills — broadly useful ones (see Creating Skills)
6. New tools — rarely needed; most capabilities should be skills
7. Documentation — fixes, clarifications, new examples

## Development Setup

```bash
git clone --recurse-submodules https://github.com/NousResearch/hermes-agent.git
cd hermes-agent
uv venv venv --python 3.11
export VIRTUAL_ENV="$(pwd)/venv"
uv pip install -e ".[all,dev]"
uv pip install -e "./tinker-atropos"
# Optional: npm install
```

Config: `mkdir -p ~/.hermes/{cron,sessions,logs,memories,skills}`
`cp cli-config.yaml.example ~/.hermes/config.yaml`

## Run Tests

```bash
pytest tests/ -v
```

## Code Style

- PEP 8 with practical exceptions (no strict line length enforcement)
- Comments: Only when explaining non-obvious intent, trade-offs, or API quirks
- Error handling: Catch specific exceptions. Use logger.warning()/logger.error() with exc_info=True
- Cross-platform: Never assume Unix
- Profile-safe paths: Use get_hermes_home() from hermes_constants

## Cross-Platform Rules

- `termios` and `fcntl` are Unix-only — always catch ImportError + NotImplementedError
- File encoding: catch UnicodeDecodeError when loading .env
- Process management: os.setsid(), os.killpg() differ across platforms
- Path separators: use pathlib.Path not string concatenation

## Security

Existing protections: sudo password piping via shlex.quote(), dangerous command detection, cron prompt injection scanner, write deny list with os.path.realpath(), skills security scanner, code execution sandbox, container hardening.

Contributing security-sensitive code: use shlex.quote(), resolve symlinks with os.path.realpath() before access checks, don't log secrets, catch broad exceptions around tool execution.

## Commit Messages

```
Type    Use for
fix     Bug fixes
feat    New features
docs    Documentation
test    Tests
refactor Code restructuring
chore   Build, CI, dependency updates

Scopes: cli, gateway, tools, skills, agent, install, whatsapp, security
```
