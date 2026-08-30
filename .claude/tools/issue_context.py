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


def section(body: str, name: str) -> str:
    m = re.search(rf"#+\s*{name}\s*\n(.*?)(?=\n#+\s|\Z)", body, re.I | re.S)
    return m.group(1).strip() if m else ""


def main() -> int:
    if len(sys.argv) < 2:
        sys.exit("usage: issue_context.py <issue-number>")
    number = re.sub(r"^(gh)?#?", "", sys.argv[1], flags=re.I)

    issue = gh_issue(number)
    body = issue.get("body") or ""
    labels = [l["name"] for l in issue.get("labels", [])]
    tier = next((l for l in labels if re.fullmatch(r"tier-[123]", l)), None)

    problems: list[str] = []
    scen = scenarios(body)
    if not scen:
        problems.append("no Gherkin scenarios — there are no acceptance criteria to build against")
    elif len(scen) < 2:
        problems.append("only one scenario — the boundary case is missing")
    if not tier:
        problems.append("no tier-1/tier-2/tier-3 label — the tier decides how this lands")
    if not section(body, "outcome"):
        problems.append("no Outcome section")
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
    print(f"# tier: {tier}   labels: {', '.join(labels)}\n")
    print("## Outcome\n" + section(body, "outcome"))
    print(f"\n## Acceptance criteria — {len(scen)} scenario(s)")
    print("## Each of these must map to at least one test. They are the definition of done.\n")
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
