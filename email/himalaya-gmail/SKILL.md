---
name: himalaya-gmail
version: 1
author: Hermes Agent
license: MIT
description: Read and send Gmail from the CLI via himalaya v2.
metadata:
  hermes:
    tags: [email, gmail, himalaya, imap, smtp]
    related_skills: [email-inbox-triage]
---

# himalaya v2 → Gmail (already configured)

## When to Use

Any request to read, search, triage, draft or send email on this machine. The
account is already set up; do not re-run the wizard unless auth is broken.

## Current configuration

- Account name: `gmail` (default) — `zhanglpg@gmail.com`
- Config: `~/Library/Application Support/himalaya/config.toml` (**v2 path**, not v1's `~/.config/himalaya/`)
- Auth: Gmail app password, read from macOS Keychain via
  `security find-generic-password -a himalaya-gmail -w`
- IMAP `imaps://imap.gmail.com:993`, SMTP `smtps://smtp.gmail.com:465`, SASL PLAIN

Verify health before blaming the network:

```bash
himalaya account check            # expects: imap: OK / smtp: OK
himalaya envelope list -s 5       # newest 5
```

## Commands (v2 syntax)

```bash
himalaya envelope list -s 20                      # newest 20
himalaya envelope list -f INBOX -s 10             # by mailbox
himalaya message read <ID>                        # full body
himalaya message read <ID> --preview              # headers + first lines
himalaya flag add <ID> --flag seen
himalaya message move <ID> 'Archive'
printf 'To: a@b.c\nSubject: hi\n\nbody' | himalaya message send
himalaya message reply <ID> --all                 # opens $EDITOR; avoid in agent runs
```

For agent use, prefer `message compose`-free paths: build the full RFC 5322 text
and pipe it to `himalaya message send`, so nothing blocks on an editor. Add
`--save Sent` (or omit `--no-save`) so the copy lands in Gmail's Sent folder.

## Setup pitfalls (cost real time)

1. **v2 ≠ v1 config.** v1 used `~/.config/himalaya/config.toml` with
   `backend.*` / `message.send.backend.*` and `password.command`. v2 uses root
   `[accounts.<name>]` tables with dotted keys (`imap.server`, `imap.sasl.plain.passwd.command`)
   and lives under `~/Library/Application Support/himalaya/`. Copy-pasting a v1
   config yields "unrecognized field" errors.
2. **The wizard tests the connection BEFORE saving, and the Keychain lookup is
   `-a <entry>` — account attribute, not `-s`, not the email address.** If the
   item is missing it aborts at "IMAP connection failed" and writes no config.
   Create it first:
   ```bash
   printf 'add-generic-password -a "himalaya-gmail" -s "himalaya-gmail" -w "<app-password>" -U\n' | security -i
   ```
   Piping through `security -i` keeps the secret out of argv and shell history.
3. **Gmail app passwords need 2FA enabled** and only work with PLAIN/LOGIN, not
   OAuth mechanisms. Choose `PLAIN (username + password)`.
4. **`himalaya json-schema` is output schemas, not config** — useless for
   discovering TOML keys. The wizard is the reliable way to get a v2-correct file.
5. **Driving the wizard needs a PTY.** `terminal(background=true, pty=true)` then
   `process_manage(action='submit', data=...)` — note the parameter is `data`, not
   `text`; a wrong key sends only a newline and the prompt re-renders as empty.
   Choose the highlighted default with an empty submit.

## Safety

Sending is an external action: draft, show the user, and send only after explicit
approval. Never paste the app password into chat, logs, or a config file — it
belongs in Keychain only.
