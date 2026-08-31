#!/usr/bin/env python3
"""Stop: if this session changed production code and recorded nothing, say so.

Honest about its limits. Retrieval can be fully automatic (see lexicon_recall.py);
CAPTURE cannot, because "was that surprising?" is a judgement no script can make. A hook
that forced an entry on every session would fill the lexicon with noise, and a lexicon
full of noise is worse than an empty one.

So this does the one deterministic thing available: it notices that production code
changed and no entry was added, and asks at the only moment the answer is still fresh.
Non-blocking by design - the cost of a missing entry is real but small; the cost of
blocking a finished session is not.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from hook_io import git, repo_root  # noqa: E402

NUDGE = """\
This session changed production code but added no lexicon entry.

If anything here was non-obvious - a framework behaviour that surprised you, a boundary
that was not what it looked like, a build failure with a cause you had to hunt for - the
next session will pay for it again unless you write it down now:

  .claude/tools/lexicon.py add --key <slug> --title "..." \\
    --problem "..." --solution "..." --why "..." --tags a,b

If it was all routine, ignore this.
"""


def main() -> int:
    root = repo_root()
    if root is None:
        return 0
    changed = git("status", "--porcelain", cwd=root) + \
        git("diff", "--name-only", "HEAD~1", cwd=root)
    touched_src = any("src/main/java" in l for l in changed.splitlines())
    recorded = any("docs/lexicon/entries" in l for l in changed.splitlines())
    if touched_src and not recorded:
        print(NUDGE, file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
