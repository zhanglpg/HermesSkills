---
name: gmail-imap-toolkit
description: "Bulk Gmail via imaplib + X-GM-RAW when himalaya throttles."
version: 1.0.0
author: curator
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [Email, Gmail, IMAP, Python, Triage, Bulk]
    related_skills: [himalaya]
---

# Gmail IMAP Toolkit

Programmatic Gmail access with Python `imaplib` + Gmail's `X-GM-RAW`
search extension. Complements the `himalaya` skill: use himalaya for
single-message reads/sends and quick CLI checks; use this toolkit for
bulk scans, inbox triage, and any time himalaya starts timing out.

## When to use what

| Task | Tool |
|------|------|
| Read/reply/send one known message | himalaya |
| List ≤ 20 recent envelopes | himalaya |
| Bulk search / unread census / newsletter triage | **this toolkit** |
| "Find mail from real humans" | **this toolkit** (`category:personal`) |
| himalaya timing out on every command | **this toolkit**, with backoff (see Throttling) |

## Credentials

Reuse the app password himalaya already stores in macOS Keychain
(same account, no extra setup):

```python
import subprocess
USER = "you@gmail.com"
pw = subprocess.run(
    ["security", "find-generic-password", "-a", USER, "-s", "himalaya-gmail", "-w"],
    capture_output=True, text=True, check=True,
).stdout.strip()
```

If himalaya isn't configured, see the himalaya skill for Keychain setup.

## Gmail IMAP throttling (read this first)

Gmail throttles **per source IP**, and the symptom is sneaky: a fresh
`imaplib` connection does NOT fix it. During active throttling:

- `socket.create_connection(('imap.gmail.com', 993))` succeeds in <1s
- ...then the connection **hangs waiting for the `* OK` IMAP banner**
  and eventually `read timeout`s — before LOGIN is even attempted.
- Mid-session, the same thing appears as a `socket.timeout` on the
  LOGIN or SEARCH response after several consecutive queries.

This is not a network problem and not a himalaya bug — it is Gmail
refusing to greet new connections from your IP for a while.

**Recovery pattern** (validated 2026-08): sleep ~60s, retry. A bare
connectivity probe (`IMAP4_SSL` + immediate `logout()`) is the
cheapest way to test whether the ban lifted. Retry loop with growing
backoff:

```python
for attempt in range(5):
    try:
        conn = connect()   # IMAP4_SSL + login + select
        break
    except Exception:
        time.sleep(45 * (attempt + 1))   # 45s, 90s, 135s, 180s
```

**Prevention:** one connection per task; don't open a new connection
immediately after closing one; avoid `page-size 200`-style scans;
keep consecutive IMAP sessions spaced by seconds-to-minutes. Note the
ban can re-engage within minutes after a burst — a run that worked
60s ago is no guarantee the next connect succeeds instantly.

## X-GM-RAW search syntax

`X-GM-RAW` accepts full Gmail web-search syntax (`is:unread`,
`category:personal`, `newer_than:14d`, `from:`, `subject:`,
`has:attachment`, ...). Two quoting pitfalls (both hit in production):

```python
# WRONG — BAD Could not parse command:
conn.search('UTF-8', 'X-GM-RAW', query.encode())

# RIGHT — query wrapped in double quotes, charset arg None:
conn.search(None, 'X-GM-RAW', '"is:unread newer_than:14d"')
```

Rule: the X-GM-RAW argument is a single IMAP quoted string — the whole
Gmail query must sit inside `"..."` inside the Python string. Do not
pass a charset argument with X-GM-RAW.

Useful triage queries:

| Query | Meaning |
|-------|---------|
| `is:unread category:personal newer_than:30d` | unread mail Gmail sorted into the Personal tab — best "real humans" signal |
| `is:unread category:primary newer_than:30d` | unread Primary-tab mail |
| `is:unread newer_than:14d` | all unread, 14 days, any category |
| `from:someone@example.com newer_than:7d` | recent mail from one sender |

## Real-person triage recipe

For "what actually needs a reply?" on a newsletter-flooded inbox:

1. Try `is:unread category:personal newer_than:30d` — if Gmail's
   categorization is reliable for this account, this alone is the
   answer (authoritative, zero regex).
2. Fallback for uncategorized mail: list `is:unread newer_than:14d`
   headers and drop bulk senders with a regex on the `From` header:
   `newsletter|noreply|no-reply|digest|alert|notification|promo|
   marketing|mailer|substack|beehiv|ghost\.io|@e\.|@notice\.|
   @service\.|news@|updates?@` plus account-specific sender domains.
   See `scripts/find-personal-unread.py` for the full filter.

## Bulk-listing etiquette

- Fetch only headers: `BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)]`
  — `PEEK` avoids clearing the unread flag, and header-only fetches
  are ~100x cheaper than `RFC822`.
- Decode headers with `email.header.decode_header` (RFC2047); parse
  dates with `email.utils.parsedate_to_datetime`.
- Never list the whole unread set unbounded — inboxes can carry
  80k+ unread messages. Always constrain with `newer_than:` and cap
  output (`ids[-40:]`).

## Scripts

- `scripts/unread-inbox.py` — census + latest 40 unread INBOX
  messages (id, date, from, subject).
- `scripts/find-personal-unread.py` — the real-person triage recipe
  with connect retry/backoff built in.

Both read the account from the `GMAIL_ACCOUNT` env var (default
`zhanglpg@gmail.com`) and the keychain service from
`GMAIL_KEYCHAIN_SERVICE` (default `himalaya-gmail`). Run them
directly: `python3 <skill_dir>/scripts/find-personal-unread.py`.
Live working copies also exist at `~/.hermes/scripts/` — keep the
skill copies canonical when editing.

## Pitfalls

- **himalaya does not accept Gmail operators.** `himalaya envelope
  list "is:unread"` is a parser error (`expected not, date, before,
  ...`). The himalaya equivalent is `himalaya envelope list
  "not flag seen"`. One more reason to reach for X-GM-RAW here for
  anything Gmail-flavored.
- **Throttle ≠ tool failure.** Do not conclude "imaplib is broken" or
  swap tools when the banner hangs — sleep 60s and retry first.
- **Readonly select** (`conn.select("INBOX", readonly=True)`) for
  pure-listing jobs so nothing accidentally mutates flags.
