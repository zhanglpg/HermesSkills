#!/usr/bin/env python3
"""Census + latest 40 unread INBOX messages (id, date, from, subject).

Reads the Gmail app password from the macOS Keychain service used by
himalaya. Override account/service via GMAIL_ACCOUNT / GMAIL_KEYCHAIN_SERVICE.
"""
import imaplib, email, os, ssl, subprocess, sys
from email.header import decode_header
from email.utils import parsedate_to_datetime

USER = os.environ.get("GMAIL_ACCOUNT", "zhanglpg@gmail.com")
SERVICE = os.environ.get("GMAIL_KEYCHAIN_SERVICE", "himalaya-gmail")

pw = subprocess.run(
    ["security", "find-generic-password", "-a", USER, "-s", SERVICE, "-w"],
    capture_output=True, text=True, check=True,
).stdout.strip()

ctx = ssl.create_default_context()
conn = imaplib.IMAP4_SSL("imap.gmail.com", 993, ssl_context=ctx, timeout=20)
conn.login(USER, pw)
conn.select("INBOX", readonly=True)

status, data = conn.search(None, "UNSEEN")
ids = data[0].split()
print(f"UNREAD_COUNT={len(ids)}")

def dec_hdr(raw):
    if not raw:
        return ""
    return "".join(
        t.decode(e or "utf-8", errors="replace") if isinstance(t, bytes) else t
        for t, e in decode_header(raw)
    )

# newest 40 unread — never unbounded; inboxes can carry 80k+ unread
for mid in ids[-40:]:
    status, msg_data = conn.fetch(mid, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])")
    msg = email.message_from_bytes(msg_data[0][1])
    frm = dec_hdr(msg.get("From"))
    subj = dec_hdr(msg.get("Subject"))
    date = msg.get("Date", "")
    try:
        date = parsedate_to_datetime(date).strftime("%m-%d %H:%M")
    except Exception:
        pass
    print(f"{mid.decode()}\t{date}\t{frm}\t{subj}")

conn.logout()
