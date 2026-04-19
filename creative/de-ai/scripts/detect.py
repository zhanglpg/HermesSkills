#!/usr/bin/env python3
"""Detect AI-generated writing patterns in markdown/text files.

Usage:
    python3 detect.py <file.md>
    python3 detect.py <file.md> --json       # machine-readable output
    python3 detect.py <file.md> --stats      # summary counts only
"""

import re
import sys
import json

PATTERNS = {
    "hedging_filler": {
        "label": "Hedging filler",
        "patterns": [
            re.compile(
                r"(?:It(?:'s| is) (?:important|worth|crucial|essential|interesting)"
                r" to (?:note|mention|highlight|emphasize|point out|observe) that)",
                re.I,
            ),
            re.compile(r"(?:It (?:should|must) be (?:noted|mentioned|emphasized) that)", re.I),
            re.compile(r"^(?:Interestingly|Notably|Importantly|Crucially|Remarkably),\s", re.I | re.M),
            re.compile(r"(?:It bears mentioning|As we shall see|As mentioned (?:earlier|above|previously))", re.I),
        ],
    },
    "not_x_but_y": {
        "label": "Not-X-but-Y crutch",
        "patterns": [
            re.compile(
                r"(?:(?:is|was|are) not (?:about )?.{3,40}(?:\.|,|;|—) (?:It |it |but |rather )(?:is|was|are) )", re.I
            ),
            re.compile(r"(?:The (?:root cause|real issue|key|answer|question|point) is not .{3,40}, (?:it|but))", re.I),
            re.compile(r"(?:This is not about .{3,40} — (?:it's|it is) about)", re.I),
            re.compile(r"(?:Rather than (?:focusing on|addressing|looking at) .{3,40}, we)", re.I),
            re.compile(r"(?:The question is not .{3,40} but )", re.I),
        ],
    },
    "formulaic_transitions": {
        "label": "Formulaic transition",
        "patterns": [
            re.compile(r"^(?:Furthermore|Moreover|Additionally|In addition),?\s", re.I | re.M),
            re.compile(r"^(?:To that end|In this regard|With that in mind|Building on this),?\s", re.I | re.M),
            re.compile(r"^(?:Taken together|As previously mentioned),?\s", re.I | re.M),
            re.compile(r"(?:It is also worth (?:noting|mentioning))", re.I),
        ],
    },
    "excessive_adverbs": {
        "label": "Excessive adverb",
        "patterns": [
            re.compile(
                r"\b(?:significantly|fundamentally|remarkably|undeniably|arguably|essentially"
                r"|increasingly|ultimately|inherently)\b",
                re.I,
            ),
        ],
    },
    "grandiose_framing": {
        "label": "Grandiose framing",
        "patterns": [
            re.compile(r"(?:In the (?:rapidly )?(?:evolving|changing|emerging) landscape of)", re.I),
            re.compile(
                r"(?:represents? a (?:paradigm shift|fundamental shift|sea change|watershed moment))", re.I
            ),
            re.compile(r"(?:revolutioniz(?:ing|es?|ed))", re.I),
            re.compile(r"(?:a (?:cornerstone|testament|beacon) of)", re.I),
            re.compile(r"(?:paving the way for|at the forefront of)", re.I),
        ],
    },
    "structural_tics": {
        "label": "Structural tic",
        "patterns": [
            re.compile(r"(?:In the (?:next|following) section,? we)", re.I),
            re.compile(r"^In conclusion,?\s", re.I | re.M),
            re.compile(r"^In summary,?\s", re.I | re.M),
            re.compile(r"(?:As (?:we )?(?:discussed|described|mentioned|noted) (?:in |above|earlier|previously))", re.I),
        ],
    },
}


def detect(text, filename="<stdin>"):
    """Return list of (line_number, category, label, matched_text, full_line)."""
    findings = []
    lines = text.split("\n")
    for i, line in enumerate(lines, 1):
        # Skip code blocks
        if line.strip().startswith("```") or line.strip().startswith("|"):
            continue
        # Skip frontmatter
        if i <= 3 and line.strip() == "---":
            continue
        for category, info in PATTERNS.items():
            for pattern in info["patterns"]:
                for match in pattern.finditer(line):
                    findings.append(
                        {
                            "line": i,
                            "category": category,
                            "label": info["label"],
                            "match": match.group(),
                            "context": line.strip(),
                            "file": filename,
                        }
                    )
    return findings


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    filepath = sys.argv[1]
    flags = set(sys.argv[2:])

    with open(filepath) as f:
        text = f.read()

    findings = detect(text, filepath)

    if "--json" in flags:
        print(json.dumps(findings, indent=2))
        return

    if "--stats" in flags:
        counts = {}
        for f in findings:
            counts[f["label"]] = counts.get(f["label"], 0) + 1
        print(f"Total: {len(findings)} AI patterns detected\n")
        for label, count in sorted(counts.items(), key=lambda x: -x[1]):
            print(f"  {count:3d}  {label}")
        return

    if not findings:
        print("No AI patterns detected.")
        return

    print(f"Found {len(findings)} AI patterns:\n")
    for f in findings:
        print(f"  L{f['line']:4d}  [{f['label']}]")
        print(f"         matched: \"{f['match']}\"")
        print(f"         context: {f['context'][:120]}")
        print()


if __name__ == "__main__":
    main()
