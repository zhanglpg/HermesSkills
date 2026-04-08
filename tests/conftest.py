"""Root conftest — adds each skill's scripts/ directory to sys.path so bare
imports (e.g. ``from storage import QueueDB``) resolve the same way they do
when the entry-point scripts run."""

import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent

_SKILL_SCRIPT_DIRS = [
    _REPO_ROOT / "openclaw-imports" / "paper-queue" / "scripts",
    _REPO_ROOT / "openclaw-imports" / "wiki-manager" / "scripts",
    _REPO_ROOT / "openclaw-imports" / "check-market-movers" / "scripts",
]

for d in _SKILL_SCRIPT_DIRS:
    path_str = str(d)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

# Set AGENT_DATA_DIR so modules that read it at import time don't warn / fail
os.environ.setdefault("AGENT_DATA_DIR", "/tmp/hermes-test")
