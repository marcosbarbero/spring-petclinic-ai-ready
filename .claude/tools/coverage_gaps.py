#!/usr/bin/env python3
"""Uncovered lines, for the files you actually changed.

Why this exists
---------------
"Improve the coverage" sends an agent into a multi-megabyte HTML report, or worse,
into reading every source file. The useful answer is: *these specific lines, in the
files on this branch, are not covered.* That is a few hundred tokens.

Deterministic. Scopes to the diff by default, which is also the only sane way to
apply a coverage gate to a codebase that predates it.

Usage:
    .claude/tools/coverage_gaps.py            # only files changed vs main
    .claude/tools/coverage_gaps.py --all      # whole module
"""
from __future__ import annotations
import argparse, subprocess, sys, xml.etree.ElementTree as ET
from pathlib import Path

REPORT = Path("target/site/jacoco/jacoco.xml")

def changed_files() -> set[str]:
    names: set[str] = set()
    for cmd in (["git","diff","--name-only"],
                ["git","diff","--cached","--name-only"],
                ["git","diff","--name-only","main...HEAD"]):
        try:
            out = subprocess.run(cmd, capture_output=True, text=True, timeout=10).stdout
            names |= {l.strip() for l in out.splitlines() if l.strip().endswith(".java")}
        except Exception:
            pass
    return {Path(n).stem for n in names if "/main/" in n}

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()

    if not REPORT.exists():
        sys.exit(f"No JaCoCo report at {REPORT}\nRun: ./mvnw verify")

    scope = None if args.all else changed_files()
    if scope is not None and not scope:
        print("No changed production files vs main — nothing to check.")
        return 0

    root = ET.parse(REPORT).getroot()
    total_missed = 0
    reported = 0

    for pkg in root.findall("package"):
        for sf in pkg.findall("sourcefile"):
            stem = sf.get("name", "").removesuffix(".java")
            if scope is not None and stem not in scope:
                continue
            missed = [ln for ln in sf.findall("line")
                      if int(ln.get("mi", 0)) > 0 or int(ln.get("mb", 0)) > 0]
            if not missed:
                continue
            reported += 1
            total_missed += len(missed)
            print(f"\n{pkg.get('name','').replace('/','.')}.{stem}")
            for ln in missed:
                nr, mi, mb = ln.get("nr"), int(ln.get("mi",0)), int(ln.get("mb",0))
                why = "no branch coverage" if mb and not mi else \
                      "partially covered branch" if mb else "not executed"
                print(f"  L{nr:<5} {why}")

    label = "all files" if args.all else f"{len(scope)} changed file(s)"
    if not reported:
        print(f"Fully covered across {label}.")
        return 0
    print(f"\n{total_missed} uncovered line(s) across {reported} file(s) — scope: {label}")
    return 1

if __name__ == "__main__":
    raise SystemExit(main())
