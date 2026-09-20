#!/usr/bin/env python3
"""Real-person triage: find unread mail from actual humans, not newsletters.

Strategy:
  1. Gmail's own categorization via X-GM-RAW (category:personal /
     category:primary, last 30 days) — authoritative when Gmail has
     sorted the mail.
  2. Fallback: all unread from the last 14 days, dropping bulk
     senders with a regex on the From header.

Includes connect retry/backoff for Gmail IP throttling (banner hang).
"""
import imaplib, ssl, subprocess, email, os, re, time, sys
from email.header import decode_header
from email.utils import parsedate_to_datetime

USER = os.environ.get("GMAIL_ACCOUNT", "zhanglpg@gmail.com")
SERVICE = os.environ.get("GMAIL_KEYCHAIN_SERVICE", "himalaya-gmail")

pw = subprocess.run(
    ["security", "find-generic-password", "-a", USER, "-s", SERVICE, "-w"],
    capture_output=True, text=True, check=True,
).stdout.strip()

def dec(raw):
    if not raw:
        return ""
    return "".join(
        t.decode(e or "utf-8", errors="replace") if isinstance(t, bytes) else t
        for t, e in decode_header(raw)
    )

def connect():
    ctx = ssl.create_default_context()
    conn = imaplib.IMAP4_SSL("imap.gmail.com", 993, ssl_context=ctx, timeout=20)
    conn.login(USER, pw)
    conn.select("INBOX", readonly=True)
    return conn

# Bulk-sender filter for the From header. Extend with account-specific
# newsletter domains as they show up.
bulk = re.compile(
    r"newsletter|noreply|no-reply|no_reply|digest|alert|notification|mail\.|@e\.|news@|"
    r"updates?@|promo|marketing|notify|mailer|substack|beehiv|ghost\.io|email\.|inbox|"
    r"@notice\.|@service\.|quora|medium|hustle|quartz|seekingalpha|gurufocus|nytimes|"
    r"codecademy|reddit|aliyun|credit|apple|usps|govdelivery|dzone|businessinsider|"
    r"subscriptions?@|billing|receipt|invoice|linkedin|github\.com|twitter|x\.com|"
    r"facebook|instagram|amazon|paypal|slack|discord|telegram", re.I)

conn = None
for attempt in range(5):
    try:
        conn = connect()
        break
    except Exception as e:
        wait = 45 * (attempt + 1)
        print(f"[attempt {attempt + 1} connect failed: {type(e).__name__}; "
              f"sleeping {wait}s]", file=sys.stderr)
        time.sleep(wait)
if conn is None:
    print("GAVE UP connecting after 5 attempts (Gmail IP throttling?)")
    sys.exit(1)

try:
    # X-GM-RAW quoting: query must be one double-quoted IMAP string,
    # and no charset argument — otherwise 'BAD Could not parse command'.
    for q in ["is:unread category:personal newer_than:30d",
              "is:unread category:primary newer_than:30d"]:
        st, data = conn.search(None, "X-GM-RAW", '"%s"' % q)
        print(q, "->", len(data[0].split()))

    st, data = conn.search(None, "X-GM-RAW", '"is:unread newer_than:14d"')
    ids = data[0].split()
    print(f"ALL_UNREAD_14D={len(ids)}")
    for mid in ids:
        st, md = conn.fetch(mid, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])")
        m = email.message_from_bytes(md[0][1])
        frm = dec(m.get("From"))
        subj = dec(m.get("Subject"))
        d = m.get("Date", "")
        try:
            d = parsedate_to_datetime(d).strftime("%m-%d %H:%M")
        except Exception:
            pass
        if not bulk.search(frm):
            print(f"{mid.decode()}\t{d}\t{frm}\t{subj}")
finally:
    try:
        conn.logout()
    except Exception:
        pass
