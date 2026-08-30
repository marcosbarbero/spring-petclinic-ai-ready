#!/usr/bin/env python3
"""Validate that an issue is actually implementable before an agent starts on it.

Why this exists
---------------
A markdown issue template is a suggestion; people delete the headings. This is a gate.
Run it in CI on issue open, or locally before starting work.

It refuses vague tickets deterministically: no Gherkin, no acceptance criteria, no
risk tier, no constraints -> exit 1, with the reason. No model judgement involved.

Usage:
    .claude/tools/check_issue.py issue.md
    gh issue view 42 --json body -q .body | .claude/tools/check_issue.py -
"""
from __future__ import annotations
import re, sys
from pathlib import Path

def read() -> str:
    if len(sys.argv) < 2:
        sys.exit("usage: check_issue.py <file|->")
    return sys.stdin.read() if sys.argv[1] == "-" else Path(sys.argv[1]).read_text()

def main() -> int:
    body = read()
    low = body.lower()
    problems: list[str] = []

    if not re.search(r"##\s*context", low):
        problems.append("no '## Context' section — nothing explains what is broken or why it matters")

    if not re.search(r"##\s*outcome", low):
        problems.append("no '## Outcome' section — state what is true after this ships")

    reqs = re.findall(r"^\s*\d+[.)]\s+\S", body, re.M)
    if not re.search(r"##\s*requirements", low):
        problems.append("no '## Requirements' section — Gherkin is how you PROVE a "
                        "requirement, not a substitute for stating one")
    elif not reqs:
        problems.append("'## Requirements' is present but empty — number what the system must do")

    gherkin = re.findall(r"scenario:", low)
    if not gherkin:
        problems.append("no Gherkin scenario — acceptance criteria must be executable prose")
    else:
        for kw in ("given", "when", "then"):
            if kw not in low:
                problems.append(f"Gherkin is incomplete: no '{kw.capitalize()}' step")
        if len(gherkin) < 2:
            problems.append(
                f"only {len(gherkin)} scenario — cover the boundary, not just the happy path")

    if not re.search(r"tier[- ]?[123]\b", low):
        problems.append("no risk tier (tier-1/2/3) — the tier decides how this lands")

    if not re.search(r"##\s*constraints", low):
        problems.append("no '## Constraints' section — say what must NOT change")
    elif "do not modify existing tests" not in low and "don't modify existing tests" not in low:
        problems.append(
            "constraints do not forbid modifying existing tests "
            "(the single highest-value constraint in AI-assisted work)")

    if reqs and gherkin and len(gherkin) < len(reqs):
        problems.append(
            f"{len(reqs)} requirement(s) but only {len(gherkin)} scenario(s) — "
            "a requirement with no scenario will not get tested")

    words = len(re.findall(r"\w+", body))
    if words < 40:
        problems.append(f"body is {words} words — too thin to implement unattended")

    if problems:
        print("ISSUE REJECTED — not ready for implementation\n")
        for p in problems:
            print(f"  - {p}")
        print("\nA ticket an agent cannot implement unattended is a ticket a new joiner\n"
              "cannot implement either. Fix the ticket, not the agent.")
        return 1

    print(f"Issue OK — {len(reqs)} requirement(s), {len(gherkin)} scenario(s), "
          "tier set, context and constraints present.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
