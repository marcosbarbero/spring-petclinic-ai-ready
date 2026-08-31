#!/usr/bin/env python3
"""UserPromptSubmit: inject relevant prior knowledge, unasked.

This is what makes the lexicon actually work.

Telling an agent "search the lexicon first" is an instruction, and instructions are
followed most of the time. This hook removes the choice: every prompt is scored against
the lexicon and any strong match is injected as context before the model sees the task.
Nobody has to remember, because nobody is asked.

Deliberately conservative — it stays silent unless a match is strong, and caps at 3
entries. A memory that injects noise on every turn gets ignored like every other banner.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from hook_io import payload, repo_root  # noqa: E402


def main() -> int:
    prompt = (payload().get("prompt") or "").strip()
    if len(prompt) < 12:
        return 0
    root = repo_root()
    if root is None:
        return 0
    try:
        out = subprocess.run(
            [".claude/tools/lexicon.py", "recall", prompt, "--limit", "3", "--threshold", "4"],
            cwd=root, capture_output=True, text=True, timeout=15)
        if out.returncode == 0 and out.stdout.strip():
            print(out.stdout)   # stdout on UserPromptSubmit becomes model context
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
