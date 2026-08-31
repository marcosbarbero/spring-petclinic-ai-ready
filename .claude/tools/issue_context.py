#!/usr/bin/env python3
"""Turn a GitHub issue number into a validated, compact work brief.

Why this exists
---------------
The naive version of "implement gh#42" is: let the agent shell out to `gh`, read a wall
of JSON with reactions, timelines and author avatars, and infer the requirements. That
is expensive and non-deterministic — two runs can read the same issue differently.

This script does the boring part deterministically: fetch, validate, extract. It emits
a brief the agent can act on, or it refuses. Refusing early is the point — a ticket that
cannot be implemented unattended should fail before an agent burns a single token on it.

Exit codes:
    0  brief printed, safe to proceed
    1  issue is not implementable (reasons printed)
    2  tier 3 — human sign-off required, do not auto-implement

Usage:
    .claude/tools/issue_context.py 42
    .claude/tools/issue_context.py gh#42
"""

from __future__ import annotations

import json
import re
import subprocess
import sys


def gh_issue(number: str) -> dict:
    try:
        out = subprocess.run(
            ["gh", "issue", "view", number, "--json",
             "number,title,body,labels,state,assignees"],
            capture_output=True, text=True, timeout=30,
        )
    except FileNotFoundError:
        sys.exit("gh CLI not found. Install it, or pass the issue body on stdin.")
    if out.returncode != 0:
        sys.exit(f"Could not read issue {number}:\n{out.stderr.strip()}")
    return json.loads(out.stdout)


def scenarios(body: str) -> list[str]:
    """Extract Gherkin scenarios verbatim. These ARE the acceptance criteria."""
    found, current = [], []
    for line in body.splitlines():
        if re.match(r"\s*scenario\s*:", line, re.I):
            if current:
                found.append("\n".join(current).rstrip())
            current = [line.strip()]
        elif current:
            if re.match(r"\s*(given|when|then|and|but)\b", line, re.I):
                current.append("  " + line.strip())
            elif line.strip() and not line.strip().startswith("#"):
                if re.match(r"\s*(#{1,6}\s|```)", line):
                    found.append("\n".join(current).rstrip())
                    current = []
    if current:
        found.append("\n".join(current).rstrip())
    return found


def architecture(area: str | None) -> str:
    """Inline the slice's map entry so the agent never has to search for the code.

    Deterministic lookup beats exploration: the structure is a fact about the repo,
    not something to rediscover with grep every session.
    """
    if not area:
        return ""
    try:
        out = subprocess.run([".claude/tools/arch_map.py", "get", area],
                             capture_output=True, text=True, timeout=15)
        return out.stdout.strip() if out.returncode == 0 else ""
    except Exception:
        return ""


def section(body: str, name: str) -> str:
    """Match a heading by its opening words, tolerating trailing text.

    Headings are written for humans: "## Current behaviour - and how you verified it".
    Requiring an exact match makes the tool refuse well-formed tickets, which trains
    people to fight the gate instead of using it.
    """
    m = re.search(rf"^#+\s*{name}\b[^\n]*\n(.*?)(?=\n#+\s|\Z)", body, re.I | re.S | re.M)
    return m.group(1).strip() if m else ""


def main() -> int:
    if len(sys.argv) < 2:
        sys.exit("usage: issue_context.py <issue-number>")
    number = re.sub(r"^(gh)?#?", "", sys.argv[1], flags=re.I)

    issue = gh_issue(number)
    body = issue.get("body") or ""
    labels = [l["name"] for l in issue.get("labels", [])]
    tier = next((l for l in labels if re.fullmatch(r"tier-[123]", l)), None)
    area = next((l.split(":", 1)[1] for l in labels if l.startswith("area:")), None)

    problems: list[str] = []
    scen = scenarios(body)
    if not scen:
        problems.append("no Gherkin scenarios — there are no acceptance criteria to build against")
    elif len(scen) < 2:
        problems.append("only one scenario — the boundary case is missing")
    if not tier:
        problems.append("no tier-1/tier-2/tier-3 label — the tier decides how this lands")
    if not area:
        problems.append("no area: label — say which feature slice owns this "
                        "(see .claude/tools/arch_map.py list)")
    if not section(body, "context"):
        problems.append("no Context section — nothing explains what is broken or why")
    if not section(body, "current behaviour"):
        problems.append("no 'Current behaviour' section — the ticket asserts a gap without "
                        "saying how it was verified. Unverified premises get implemented.")
    if not section(body, "outcome"):
        problems.append("no Outcome section")
    reqs = re.findall(r"^\s*\d+[.)]\s+\S", body, re.M)
    if not section(body, "requirements") or not reqs:
        problems.append("no numbered Requirements — scenarios prove requirements, "
                        "they do not replace them")
    elif len(scen) < len(reqs):
        problems.append(f"{len(reqs)} requirement(s) but only {len(scen)} scenario(s)")
    if not section(body, "constraints"):
        problems.append("no Constraints section — nothing says what must NOT change")
    if issue.get("state") != "OPEN":
        problems.append(f"issue is {issue.get('state')}")

    if problems:
        print(f"REFUSED — issue #{issue['number']} is not implementable unattended\n")
        for p in problems:
            print(f"  - {p}")
        print("\nFix the ticket, not the agent. An issue an agent cannot implement is one\n"
              "a new joiner cannot implement either.")
        return 1

    print(f"# Work brief — issue #{issue['number']}")
    print(f"# {issue['title']}")
    print(f"# tier: {tier}   area: {area}   labels: {', '.join(labels)}\n")
    arch = architecture(area)
    if arch:
        print("## Where this lives  (from the architecture map — do not go looking)")
        print(arch + "\n")
    print("## Context\n" + section(body, "context"))
    cur = section(body, "current behaviour")
    if cur:
        print("\n## Current behaviour, as claimed by the ticket\n" + cur)
        print("\n>> VERIFY THIS FIRST. Write a test asserting the current behaviour at the\n"
              ">> level a user hits it. If it PASSES, the gap does not exist — stop and say so.")
    print("\n## Outcome\n" + section(body, "outcome"))
    print("\n## Requirements — the specification\n" + section(body, "requirements"))
    print(f"\n## Test scenarios — {len(scen)}, proving the requirements above")
    print("## Each maps to at least one test. Requirements say WHAT; these say HOW YOU KNOW.\n")
    for s in scen:
        print(s + "\n")
    print("## Constraints\n" + section(body, "constraints"))
    oos = section(body, "out of scope")
    if oos:
        print("\n## Out of scope\n" + oos)

    if tier == "tier-3":
        print("\n" + "=" * 68)
        print("TIER 3 — HIGH RISK. Do not auto-implement or auto-merge.")
        print("Plan only, then stop and wait for a human.")
        print("=" * 68)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
