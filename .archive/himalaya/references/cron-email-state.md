# Cron-Friendly Email State Tracking

When building cron jobs that periodically check email, track the last-check timestamp to avoid re-processing old emails and to provide a `SINCE` window for IMAP queries.

## Pattern: State File + Dual-Mode Script

One script with two modes:
- **Read mode** (default): outputs the search window for the email fetcher
- **Update mode** (`--update`): records current time as new checkpoint after successful processing

```python
#!/usr/bin/env python3
import json, sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

STATE_FILE = Path.home() / ".hermes/cron/email-state.json"
BUFFER_HOURS = 1  # overlap to avoid missing boundary emails

def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return None

now = datetime.now(timezone.utc)

if "--update" in sys.argv:
    state = load_state() or {}
    state["last_check"] = now.isoformat()
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))
    print(f"UPDATED last_check={state['last_check']}")
else:
    state = load_state()
    since = now - timedelta(hours=24) if not state else (
        datetime.fromisoformat(state["last_check"]) - timedelta(hours=BUFFER_HOURS)
    )
    print(f"SINCE_TS={since.isoformat()}")
    print(f"SINCE_DATE={since.strftime('%Y-%m-%d')}")
    print(f"IS_FIRST_RUN={'true' if not state else 'false'}")
```

## Cron Integration

In the cron job definition, set `script` to the state-reader script. The script's stdout is injected into the prompt as context before the agent runs. After processing, the agent calls `python3 script.py --update`.

```yaml
# Example cron setup
schedule: "0 8,12,16,20 * * *"
script: "email-check-state.py"
# Agent prompt receives: SINCE_TS=..., SINCE_DATE=..., IS_FIRST_RUN=...
# Agent uses SINCE_DATE in IMAP search, then calls --update at end
```

## Gmail IMAP SINCE Query

```
(SINCE "DD-Mon-YYYY")   e.g. (SINCE "24-May-2026")
```

Note: Gmail IMAP uses `DD-Mon-YYYY` format, not ISO. Convert `SINCE_DATE` (YYYY-MM-DD) to this format before passing to IMAP.
