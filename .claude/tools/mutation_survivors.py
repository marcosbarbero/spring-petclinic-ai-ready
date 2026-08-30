#!/usr/bin/env python3
"""Report surviving mutants, compactly.

Why this exists
---------------
PIT writes a ~2MB HTML report. An agent asked to "improve the mutation score" will
happily read that report into its context window, burn 40k tokens, and still summarise
it badly. This script reads the XML and prints the handful of lines that actually
matter — usually under 400 tokens.

That difference is the whole argument for a toolbox: the answer was always small.
Only the artifact was big.

Deterministic. No model involved. Same input, same output, every time.

Usage:
    .claude/tools/mutation_survivors.py [--limit N] [--json] [target/pit-reports/mutations.xml]
"""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

DEFAULT_REPORT = Path("target/pit-reports/mutations.xml")


def load(path: Path) -> list[dict]:
    if not path.exists():
        sys.exit(
            f"No PIT report at {path}\n"
            "Run: ./mvnw -Pmutation verify"
        )
    root = ET.parse(path).getroot()
    out = []
    for m in root.findall("mutation"):
        out.append({
            "status": m.get("status", "?"),
            "cls": (m.findtext("mutatedClass") or "").split(".")[-1],
            "pkg": ".".join((m.findtext("mutatedClass") or "").split(".")[:-1]),
            "method": m.findtext("mutatedMethod") or "?",
            "line": int(m.findtext("lineNumber") or 0),
            "desc": m.findtext("description") or "",
        })
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("report", nargs="?", type=Path, default=DEFAULT_REPORT)
    ap.add_argument("--limit", type=int, default=25)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    muts = load(args.report)
    if not muts:
        print("No mutations generated — check <targetClasses> in the pitest config.")
        return 0

    killed = sum(1 for m in muts if m["status"] in ("KILLED", "TIMED_OUT"))
    survivors = [m for m in muts if m["status"] == "SURVIVED"]
    no_cov = [m for m in muts if m["status"] == "NO_COVERAGE"]
    score = killed / len(muts) * 100

    if args.json:
        print(json.dumps({
            "score": round(score, 1), "total": len(muts), "killed": killed,
            "survived": len(survivors), "no_coverage": len(no_cov),
            "survivors": survivors[: args.limit],
        }, indent=2))
        return 0 if not survivors else 1

    print(f"mutation score {score:.1f}%   {killed}/{len(muts)} killed")
    print(f"  survived: {len(survivors)}   no coverage: {len(no_cov)}")

    if not survivors and not no_cov:
        print("\nNothing survived. Your tests actually check the code.")
        return 0

    def show(title: str, rows: list[dict], hint: str) -> None:
        if not rows:
            return
        print(f"\n{title}  ({len(rows)})\n{hint}")
        by_cls: dict[str, list[dict]] = {}
        for m in rows:
            by_cls.setdefault(m["cls"], []).append(m)
        shown = 0
        for cls, ms in sorted(by_cls.items(), key=lambda kv: -len(kv[1])):
            print(f"  {cls}")
            for m in sorted(ms, key=lambda x: x["line"]):
                if shown >= args.limit:
                    print(f"    … {len(rows) - shown} more")
                    return
                print(f"    L{m['line']:<5} {m['method']:<24} {m['desc']}")
                shown += 1

    show("SURVIVED — the code changed and no test noticed",
         survivors,
         "  Each line below is a behaviour change your suite would ship.")
    show("NO COVERAGE — never executed by any test",
         no_cov,
         "  These are not assertion gaps; they are untested paths.")

    print("\nFix the survivors by asserting the behaviour, not by adding more tests "
          "that call the method.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
