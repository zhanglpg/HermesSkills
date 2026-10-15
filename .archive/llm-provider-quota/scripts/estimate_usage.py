#!/usr/bin/env python3
"""Estimate local usage against an LLM provider from Hermes state.db.

Read-only against ~/.hermes/state.db, table session_model_usage.
Filters rows by billing_base_url substring (default: token-plan).

Usage:
  python3 estimate_usage.py                    # token-plan, 5h/24h/7d windows
  python3 estimate_usage.py --url-sub dashscope --days 14
"""
import argparse
import datetime
import os
import sqlite3
import time


def fmt(ts: float) -> str:
    return datetime.datetime.fromtimestamp(ts).strftime('%m-%d %H:%M')


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', default=os.path.expanduser('~/.hermes/state.db'))
    ap.add_argument('--url-sub', default='token-plan',
                    help='billing_base_url substring filter')
    ap.add_argument('--days', type=int, default=7)
    args = ap.parse_args()

    db = sqlite3.connect(args.db)
    cur = db.cursor()
    now = time.time()
    flt = "billing_base_url LIKE ?"
    arg = (f'%{args.url_sub}%',)

    print(f'now = {fmt(now)}   filter: {arg[0]}\n')
    print(f"{'window':<14} {'calls':>6} {'in_tok':>12} {'out_tok':>10} {'cache_rd':>13} {'reason':>11}")
    for label, secs in [('last 5h', 5 * 3600), ('last 24h', 24 * 3600),
                        (f'last {args.days}d', args.days * 86400)]:
        row = cur.execute(
            f"""SELECT COALESCE(SUM(api_call_count),0), COALESCE(SUM(input_tokens),0),
                       COALESCE(SUM(output_tokens),0), COALESCE(SUM(cache_read_tokens),0),
                       COALESCE(SUM(reasoning_tokens),0)
                FROM session_model_usage WHERE {flt} AND last_seen >= ?""",
            (*arg, now - secs)).fetchone()
        print(f'{label:<14} {row[0]:>6} {row[1]:>12,} {row[2]:>10,} {row[3]:>13,} {row[4]:>11,}')

    print('\nDaily breakdown:')
    for row in cur.execute(
            f"""SELECT date(last_seen,'unixepoch','localtime') d, SUM(api_call_count),
                       SUM(input_tokens), SUM(output_tokens), SUM(cache_read_tokens)
                FROM session_model_usage WHERE {flt}
                GROUP BY d ORDER BY d DESC LIMIT ?""", (arg[0], args.days + 2)):
        print(f'  {row[0]}  calls={row[1]:>5}  in={row[2]:>12,} out={row[3]:>9,} cache_rd={row[4]:>12,}')

    print('\nModels:')
    for row in cur.execute(
            f"""SELECT model, SUM(input_tokens)+SUM(output_tokens) t
                FROM session_model_usage WHERE {flt} AND last_seen >= ?
                GROUP BY model ORDER BY t DESC""", (*arg, now - args.days * 86400)):
        print(f'  {row[0]:<24} {row[1]:>14,}')

    # Rolling-window hint: a >26h gap before continuous daily use suggests
    # where the current window opened.
    print('\nPer-day activity span (gaps >26h hint at rolling-window starts):')
    rows = cur.execute(
            f"""SELECT MIN(first_seen), MAX(last_seen), date(first_seen,'unixepoch','localtime') d
                FROM session_model_usage WHERE {flt}
                GROUP BY d ORDER BY d DESC LIMIT 15""", arg).fetchall()
    prev_max = None
    for mn, mx, d in rows:
        gap = ''
        if prev_max and (prev_max - mx) > 26 * 3600:
            gap = f'  <-- gap {(prev_max - mx) / 3600:.1f}h before'
        print(f'  {d}: {fmt(mn)} .. {fmt(mx)}{gap}')
        prev_max = mx

    first = cur.execute(
        f"SELECT MIN(first_seen) FROM session_model_usage WHERE {flt}", arg).fetchone()[0]
    if first:
        print(f'\nFirst-ever matching usage in DB: {fmt(first)}')


if __name__ == '__main__':
    main()
