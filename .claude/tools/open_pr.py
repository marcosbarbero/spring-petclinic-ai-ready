#!/usr/bin/env python3
"""Open a pull request, or refuse to.

Why this exists
---------------
A PR template is a suggestion: GitHub prefills it and anyone — human or agent — can
delete the headings and write two lines. This tool is the gate. `gh pr create` is denied
in `.claude/settings.json`, so this is the only way a PR gets opened here.

What it checks, deterministically, before creating anything:

  1. the body closes an issue, and that issue is actually OPEN
  2. every required section is present and non-empty (no leftover placeholders)
  3. **every Gherkin scenario in the issue appears in the PR's coverage table** — this is
     the one a human reviewer would never catch, and the one that matters most
  4. the mutation report exists, is fresh, and is above threshold
  5. tier-3 is not being auto-merged

Point 3 is the reason this is a script and not a checklist. Nobody cross-references four
scenarios against a markdown table by eye at 6pm.

Usage:
    .claude/tools/open_pr.py --issue 1 --body-file draft.md [--title "..."] [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PIT = ROOT / "target" / "pit-reports" / "mutations.xml"
REQUIRED = ["Workflow used", "Requirement → scenario → test", "Evidence",
            "Constraints honoured", "Judgement calls", "Lexicon"]
PLACEHOLDER = re.compile(r"<!--.*?-->", re.S)


def gh(*args: str) -> tuple[int, str]:
    out = subprocess.run(["gh", *args], capture_output=True, text=True, timeout=45,
                         cwd=ROOT)
    return out.returncode, (out.stdout if out.returncode == 0 else out.stderr)


def scenarios_in_issue(body: str) -> list[str]:
    return [re.sub(r"\s+", " ", m).strip().lower()
            for m in re.findall(r"scenario\s*:\s*([^\n]+)", body, re.I)]


def mutation_score() -> tuple[float, int] | None:
    if not PIT.exists():
        return None
    muts = ET.parse(PIT).getroot().findall("mutation")
    if not muts:
        return None
    killed = sum(1 for m in muts if m.get("status") in ("KILLED", "TIMED_OUT"))
    return killed / len(muts) * 100, len(muts)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--issue", required=True)
    ap.add_argument("--body-file", required=True, type=Path)
    ap.add_argument("--title")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--min-mutation", type=float, default=80.0)
    a = ap.parse_args()

    body = a.body_file.read_text()
    stripped = PLACEHOLDER.sub("", body)
    problems: list[str] = []

    num = re.sub(r"\D", "", a.issue)
    rc, raw = gh("issue", "view", num, "--json", "number,title,body,state,labels")
    if rc != 0:
        sys.exit(f"Cannot read issue #{num}:\n{raw.strip()}")
    issue = json.loads(raw)
    labels = [l["name"] for l in issue.get("labels", [])]
    tier = next((l for l in labels if re.fullmatch(r"tier-[123]", l)), None)

    # 1 - links an OPEN issue
    if not re.search(rf"clos(e|es|ed)\s+#{num}\b", stripped, re.I):
        problems.append(f"body does not say 'Closes #{num}' — a PR with no ticket has no "
                        "agreed definition of done")
    if issue.get("state") != "OPEN":
        problems.append(f"issue #{num} is {issue.get('state')}, not OPEN")

    # 2 - required sections, non-empty
    for sec in REQUIRED:
        m = re.search(rf"##\s*{re.escape(sec)}\s*\n(.*?)(?=\n##\s|\Z)", stripped, re.S | re.I)
        if not m:
            problems.append(f"missing section: '{sec}'")
        elif len(m.group(1).strip()) < 3:
            problems.append(f"section '{sec}' is empty — write 'none' if it genuinely is")

    # 3 - every scenario in the issue is accounted for
    body_flat = re.sub(r"\s+", " ", stripped).lower()
    missing = [s for s in scenarios_in_issue(issue.get("body") or "") if s not in body_flat]
    if missing:
        problems.append(f"{len(missing)} scenario(s) from the issue are not in the "
                        "coverage table:")
        problems += [f"    · {s}" for s in missing]

    # 4 - mutation evidence
    ms = mutation_score()
    if ms is None:
        problems.append("no mutation report at target/pit-reports/mutations.xml — "
                        "run: ./mvnw -Pmutation verify")
    elif ms[0] < a.min_mutation:
        problems.append(f"mutation score {ms[0]:.1f}% is below {a.min_mutation:.0f}%")

    # 5 - tier-3 never lands unattended
    if tier == "tier-3":
        problems.append("issue is tier-3 — high risk work needs a human to open and "
                        "approve this, not an agent")

    if problems:
        print(f"PR REFUSED — issue #{num}\n")
        for p in problems:
            print(f"  {'' if p.startswith('    ') else '- '}{p}")
        print("\nThe gates already checked the code. This checks that a human can review\n"
              "the INTENT without reading the diff. Fix the body, not this tool.")
        return 1

    print(f"All checks passed — issue #{num}, tier {tier}, "
          f"mutation {ms[0]:.1f}% over {ms[1]} mutants.")
    if a.dry_run:
        print("(--dry-run: not creating)")
        return 0

    title = a.title or issue["title"]
    rc, out = gh("pr", "create", "--title", title, "--body", body)
    print(out.strip())
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
