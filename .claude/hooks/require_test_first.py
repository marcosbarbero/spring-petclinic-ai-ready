#!/usr/bin/env python3
"""PreToolUse: refuse to let production code be written before a test exists.

This is the determinism gate. Asking an agent to "do TDD" works most of the time.
Exit code 2 works every time.

Allows the edit when any of these holds:
  - the target is not production Java (tests, docs, config, resources)
  - the branch already has a new or changed file under src/test
  - HARNESS_SKIP_TEST_FIRST=1 is set (demos and emergencies)

Exit 0 = allow. Exit 2 = block, and tell the model why.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from hook_io import git, repo_root, target_path  # noqa: E402

BLOCKED = """\
BLOCKED by the harness: test-first.

You are editing production code under src/main/java, but this branch has no new or
modified test under src/test.

Write the failing test first, then implement. The test is the specification — if you
cannot express the requirement as a failing test, the requirement is not yet clear
enough to implement.

This is a gate, not a preference. It is not negotiable by prompting, and editing this
hook is denied in .claude/settings.json.
"""


def main() -> int:
    target = target_path()
    if "/src/main/java/" not in target:
        return 0
    if os.environ.get("HARNESS_SKIP_TEST_FIRST") == "1":
        print("require-test-first: bypassed via HARNESS_SKIP_TEST_FIRST=1", file=sys.stderr)
        return 0

    root = repo_root()
    if root is None:
        return 0

    changed: set[str] = set()
    for args in (("diff", "--name-only", "--", "src/test"),
                 ("diff", "--cached", "--name-only", "--", "src/test"),
                 ("ls-files", "--others", "--exclude-standard", "--", "src/test")):
        changed |= {l for l in git(*args, cwd=root).splitlines() if l.strip()}

    for base in ("main", "master"):
        if git("rev-parse", "--verify", "--quiet", base, cwd=root).strip():
            head = git("rev-parse", "HEAD", cwd=root).strip()
            if head and head != git("rev-parse", base, cwd=root).strip():
                changed |= {l for l in git("diff", "--name-only", f"{base}...HEAD",
                                           "--", "src/test", cwd=root).splitlines() if l.strip()}
            break

    if changed:
        return 0

    print(BLOCKED, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
