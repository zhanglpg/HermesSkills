# Python imaplib Fallback for Bulk Email Queries

When himalaya encounters IMAP timeouts (common after 4+ queries or large-page scans of Gmail All Mail), fall back to Python's `imaplib` which uses fresh connections per task.

## Pattern: Fetch + Search + Read

```python
import imaplib, email, ssl, subprocess

ctx = ssl.create_default_context()

# Get password from macOS Keychain
pw = subprocess.run(
    ['security', 'find-generic-password', '-a', 'you@gmail.com', '-s', 'himalaya-gmail', '-w'],
    capture_output=True, text=True
).stdout.strip()

conn = imaplib.IMAP4_SSL('imap.gmail.com', 993, ssl_context=ctx, timeout=10)
conn.login('you@gmail.com', pw)
conn.select('INBOX')

# Search with Gmail IMAP criteria
status, data = conn.search(None, '(FROM schoology)')
# Or: '(FROM schoology)', 'SUBJECT "Weekly"'
# Or: '(SINCE "26-May-2026")'

ids = data[0].split()
print(f"Found {len(ids)} matching messages")

# Fetch specific messages
for mid in ids[-5:]:  # last 5
    status, msg_data = conn.fetch(mid, '(RFC822)')
    msg = email.message_from_bytes(msg_data[0][1])
    body = ''
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == 'text/plain':
                body = part.get_payload(decode=True).decode(errors='ignore')
                break
    else:
        body = msg.get_payload(decode=True).decode(errors='ignore')

conn.logout()
```

## Search Criteria Reference

| IMAP criterion | Example |
|---------------|---------|
| `FROM` | `(FROM "schoology")` |
| `SUBJECT` | `SUBJECT "Weekly"` |
| `SINCE` | `(SINCE "24-May-2026")` |
| `BEFORE` | `(BEFORE "01-Jun-2026")` |
| Combined | `(FROM schoology SUBJECT "Weekly" SINCE "18-May-2026")` |

## When to Use imaplib vs himalaya

| Scenario | Tool |
|----------|------|
| Quick inbox check (≤ 20 msgs) | himalaya |
| Bulk scan / search across folders | imaplib |
| Programmatic extraction (parse body) | imaplib |
| Sending email | himalaya `template send` |
| Reading a single known email | himalaya `message read <id>` |
| After 3+ himalaya timeouts | imaplib |
