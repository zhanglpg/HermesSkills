"""Markdown-aware chunker: no code fences, table header prepending, Discord-safe.

Usage: python3 chunk_brief.py [/path/to/brief.md]

Outputs chunks labeled **(Chunk N/T)** ready for Discord delivery.
Each chunk is self-contained markdown under 1850 chars.
Tables split across chunks get header row prepended to continuation chunks.
No code fences — raw markdown renders properly in Discord.
"""
import sys, re

path = sys.argv[1] if len(sys.argv) > 1 else '/tmp/full_brief.md'
with open(path) as f:
    text = f.read()

MAX = 1850
LABEL_FMT = '**(Chunk {n}/{total})**'

def is_table_line(s):
    s = s.strip()
    return s.startswith('|') and s.endswith('|')

def is_table_sep(s):
    s = s.strip()
    return s.startswith('|') and '---' in s and s.endswith('|')

def find_table_header(lines, start=0):
    """Return (header_idx, header_line, sep_line) or None."""
    for i in range(start, len(lines) - 1):
        if is_table_line(lines[i]) and is_table_sep(lines[i + 1]):
            return (i, lines[i], lines[i + 1])
    return None

# ── Paragraph-based greedy combine ──────────────────────────────
paras = text.split('\n\n')
chunks_raw = []
current = ''

for p in paras:
    sep = '\n\n' if current else ''
    trial = current + sep + p
    if len(trial) <= MAX:
        current = trial
    else:
        if current:
            chunks_raw.append(current)

        if len(p) > MAX:
            # ── Oversize paragraph: split by lines ──
            lines = p.split('\n')
            hdr_info = find_table_header(lines)

            sub = ''
            saw_first_header = (hdr_info is not None)
            current_hdr = None

            for idx, line in enumerate(lines):
                # Track table headers as we encounter them
                if is_table_line(line) and idx + 1 < len(lines) and is_table_sep(lines[idx + 1]):
                    current_hdr = (line, lines[idx + 1])

                ls = '\n' if sub else ''

                # Determine if we need to prepend header to a new sub-chunk
                need_prefix = False
                prefix = ''
                if current_hdr and not sub and saw_first_header:
                    need_prefix = True
                    prefix = current_hdr[0] + '\n' + current_hdr[1] + '\n'

                test = sub + ls + line
                if len(prefix + test) <= MAX:
                    sub += ls + line
                else:
                    if sub:
                        chunks_raw.append(prefix + sub)
                    new_prefix = current_hdr[0] + '\n' + current_hdr[1] + '\n' if current_hdr and saw_first_header else ''
                    if len(new_prefix + line) <= MAX:
                        sub = new_prefix + line
                    else:
                        # Line+prefix still too big
                        chunks_raw.append(line)
                        sub = ''

            if sub:
                chunks_raw.append(sub)
            current = ''
        else:
            current = p

if current:
    chunks_raw.append(current)

# ── Post-processing ────────────────────────────────────────────

# 1. Merge orphan chunks (<80 chars) with neighbors
merged = []
for c in chunks_raw:
    if merged and len(c) < 80:
        merged[-1] = merged[-1] + '\n\n' + c
    else:
        merged.append(c)

# 2. Scan for orphaned table rows (chunks starting with |data| but no header)
#    Prepend the most recently seen table header
final = []
last_table_header = None

for c in merged:
    lines = c.split('\n')
    needs_header = False

    if len(lines) >= 1 and is_table_line(lines[0]):
        if not (len(lines) >= 2 and is_table_sep(lines[1])):
            needs_header = True

    # Track headers seen in this chunk for downstream chunks
    for i in range(len(lines) - 1):
        if is_table_line(lines[i]) and is_table_sep(lines[i + 1]):
            last_table_header = (lines[i], lines[i + 1])
            break

    if needs_header and last_table_header:
        hdr, sep = last_table_header
        c = hdr + '\n' + sep + '\n' + c

    final.append(c)

# 3. Deduplicate HN table headers
seen_hn = False
deduped = []
for c in final:
    if '| Story | Points | Comments |' in c[:80]:
        if seen_hn:
            continue
        seen_hn = True
    deduped.append(c)

# ── Report & Output ────────────────────────────────────────────
total = len(deduped)
print(f'Total chunks: {total}')
for i, c in enumerate(deduped):
    s = len(c)
    status = "OK" if s <= MAX else f"OVERFLOW by {s - MAX}"
    print(f'Chunk {i+1}: {s} chars {status}')

print('---CHUNKS---')
for i, c in enumerate(deduped):
    label = LABEL_FMT.format(n=i + 1, total=total)
    prefixed = label + '\n' + c
    print(f'\n=== CHUNK {i+1}/{total} ({len(prefixed)} chars) ===')
    print(prefixed)
