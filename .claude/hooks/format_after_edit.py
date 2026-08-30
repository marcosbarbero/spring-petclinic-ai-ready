#!/usr/bin/env python3
"""PostToolUse: format Java automatically after the agent writes it.

The agent should never spend a token on formatting, and should never see a formatting
failure. Formatting is a solved, deterministic problem — so solve it deterministically
instead of asking a language model to remember a style guide.

Never blocks: formatting is a convenience here. The gate is
`spring-javaformat:validate` in pre-push.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from hook_io import repo_root, target_path  # noqa: E402


def main() -> int:
    target = target_path()
    if not target.endswith(".java"):
        return 0
    root = repo_root()
    if root is None:
        return 0
    for extra in (["-o"], []):  # try offline first; fall back to online
        try:
            r = subprocess.run(["./mvnw", "-q", *extra, "spring-javaformat:apply"],
                               cwd=root, capture_output=True, timeout=180)
            if r.returncode == 0:
                try:
                    rel = Path(target).relative_to(root)
                except ValueError:
                    rel = Path(target)
                print(f"formatted: {rel}", file=sys.stderr)
                return 0
        except Exception:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
