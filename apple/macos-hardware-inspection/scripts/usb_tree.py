#!/usr/bin/env python3
"""Print the compact macOS IOUSB plane tree with vendor/product ids.

Why this exists: system_profiler SPUSBDataType can report an empty device
list while USB devices are enumerated. The IOUSB plane always shows them,
and the tree shape is what reveals which devices belong to a display (its
internal hub lists brand-named children such as "<Brand> Monitor Controls"
and "<Brand> Monitor Headset MIC").

Usage:  python3 usb_tree.py
"""

import re
import subprocess

PROP_VID = re.compile(r'"idVendor" = (\d+)')
PROP_PID = re.compile(r'"idProduct" = (\d+)')
PROP_NAME = re.compile(r'"USB Product Name" = "([^"]*)"')


def records(text):
    """One record per '+-o' node, carrying any properties it owns."""
    out = []
    current = None
    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("+-o "):
            if current is not None:
                out.append(current)
            current = {
                "indent": len(line) - len(stripped),
                "node": stripped[4:].split("  <class")[0].strip(),
                "vid": None,
                "pid": None,
                "product": None,
            }
            continue
        if current is None:
            continue
        match = PROP_VID.search(line)
        if match:
            current["vid"] = int(match.group(1))
        match = PROP_PID.search(line)
        if match:
            current["pid"] = int(match.group(1))
        match = PROP_NAME.search(line)
        if match:
            current["product"] = match.group(1)
    if current is not None:
        out.append(current)
    return out


def main():
    raw = subprocess.run(["ioreg", "-p", "IOUSB", "-w0", "-l"], capture_output=True).stdout
    for record in records(raw.decode("utf-8", "ignore")):
        if record["node"] == "Root":
            continue
        ids = ""
        if record["vid"] is not None:
            ids = "vid=0x%04x pid=0x%04x" % (record["vid"], record["pid"] or 0)
        print("%s%-44s %s %s" % ("  " * (record["indent"] // 2), record["node"], ids, record["product"] or ""))


main()
