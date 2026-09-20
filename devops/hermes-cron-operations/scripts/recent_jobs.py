#!/usr/bin/env python3
"""List Hermes cron jobs by creation date (newest first).

Usage: python3 recent_jobs.py [N]
  N = number of most recent jobs to show (default: all)

The `cronjob action='list'` tool output has no created_at field;
~/.hermes/cron/jobs.json is the only reliable source of job age.
Do NOT use jobs.json mtime — the scheduler rewrites it every tick.
"""
import json
import os
import sys

JOBS_FILE = os.path.expanduser("~/.hermes/cron/jobs.json")


def main() -> int:
    limit = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else None
    try:
        with open(JOBS_FILE) as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"ERROR: {JOBS_FILE} not found")
        return 1

    jobs = data if isinstance(data, list) else data.get("jobs") or list(data.values())
    jobs.sort(key=lambda j: j.get("created_at") or "", reverse=True)
    if limit:
        jobs = jobs[:limit]

    for j in jobs:
        created = (j.get("created_at") or "?")[:16].replace("T", " ")
        last = j.get("last_status") or "never-run"
        print(
            f"{created} | {j.get('name', '?')} | {j.get('schedule_display', '?')} "
            f"| enabled={j.get('enabled')} | last={last} | deliver={j.get('deliver')}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
