#!/usr/bin/env python3
"""Own the pull request body: create it or update it, but always validate it.

Why this exists
---------------
A PR template is a suggestion. GitHub prefills it and anyone — human or agent — can
delete the headings and write two lines. This tool is the gate. Both `gh pr create` and
`gh pr edit` are denied in `.claude/settings.json`, so this is the only way a PR body is
written here.

What it checks, deterministically, before writing anything:

  1. the body closes an issue, and that issue is actually OPEN
  2. every required section is present and non-empty (no leftover placeholders)
  3. **every Gherkin scenario in the issue appears in the PR's coverage table** — this is
     the one a human reviewer would never catch, and the one that matters most
  4. the mutation report exists and is above threshold
  5. tier-3 is not being auto-merged

Point 3 is the reason this is a script and not a checklist. Nobody cross-references four
scenarios against a markdown table by eye at 6pm.

Create and update run the SAME checks
-------------------------------------
This tool used to be `open_pr.py` and could only create. That was a hole, not a missing
convenience: `gh pr edit` is denied too, so once a body needed correcting — a reviewer
asks for a clearer coverage table, a rename lands, a judgement call turns out wrong —
there was no sanctioned route at all. The choice was to leave the body stale or widen the
permission file, and a validated body that then silently drifts out of date is precisely
what this tool exists to prevent.

So `update` is not a lighter path. It runs the identical validation set, because an
update that skipped the checks would just be `gh pr edit` wearing a hat.

Usage:
    pr.py create --issue 1 --body-file draft.md [--title "..."] [--dry-run]
    pr.py update --issue 1 --body-file draft.md [--pr 9] [--dry-run]

`update` resolves the PR from the current branch when `--pr` is not given.
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


def load_issue(num: str) -> dict:
    rc, raw = gh("issue", "view", num, "--json", "number,title,body,state,labels")
    if rc != 0:
        sys.exit(f"Cannot read issue #{num}:\n{raw.strip()}")
    return json.loads(raw)


def resolve_pr(explicit: str | None) -> dict:
    """The PR to update: the one given, else the one for the current branch.

    Asking the caller to look up a number they have already got open in a browser is
    friction that gets routed around, and routing around this tool is the failure mode
    it exists to prevent.
    """
    args = ["pr", "view", "--json", "number,state,title"]
    if explicit:
        args.insert(2, re.sub(r"\D", "", explicit))
    rc, raw = gh(*args)
    if rc != 0:
        sys.exit("Cannot find the pull request to update.\n"
                 f"{raw.strip()}\n"
                 "  Pass --pr <number>, or push the branch and open one with "
                 "`pr.py create`.")
    return json.loads(raw)


def validate(body: str, issue: dict, num: str, min_mutation: float) -> list[str]:
    """Every check, shared by create and update. There is no lighter path."""
    stripped = PLACEHOLDER.sub("", body)
    problems: list[str] = []

    # 1 - links an OPEN issue
    if not re.search(rf"clos(e|es|ed)\s+#{num}\b", stripped, re.I):
        problems.append(f"body does not say 'Closes #{num}' — a PR with no ticket has no "
                        "agreed definition of done")
    if issue.get("state") != "OPEN":
        problems.append(f"issue #{num} is {issue.get('state')}, not OPEN")

    # 2 - required sections, non-empty
    for sec in REQUIRED:
        m = re.search(rf"##\s*{re.escape(sec)}\s*\n(.*?)(?=\n##\s|\Z)", stripped,
                      re.S | re.I)
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
    elif ms[0] < min_mutation:
        problems.append(f"mutation score {ms[0]:.1f}% is below {min_mutation:.0f}%")

    # 5 - tier-3 never lands unattended
    labels = [l["name"] for l in issue.get("labels", [])]
    if next((l for l in labels if re.fullmatch(r"tier-[123]", l)), None) == "tier-3":
        problems.append("issue is tier-3 — high risk work needs a human to open and "
                        "approve this, not an agent")

    return problems


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Create or update a pull request body, or refuse to.")
    sub = ap.add_subparsers(dest="action", required=True)

    for name, help_text in (("create", "open a new PR"),
                            ("update", "replace an existing PR's body")):
        p = sub.add_parser(name, help=help_text)
        p.add_argument("--issue", required=True)
        p.add_argument("--body-file", required=True, type=Path)
        p.add_argument("--dry-run", action="store_true")
        p.add_argument("--min-mutation", type=float, default=80.0)
        if name == "create":
            p.add_argument("--title")
        else:
            p.add_argument("--pr", help="PR number; defaults to the current branch's PR")

    a = ap.parse_args()

    if not a.body_file.is_file():
        sys.exit(f"No such body file: {a.body_file}")
    body = a.body_file.read_text()
    num = re.sub(r"\D", "", a.issue)
    issue = load_issue(num)

    # Resolved before validation so a wrong PR number fails fast and cheap, rather than
    # after a clean validation report that then turns out to target nothing.
    target = resolve_pr(getattr(a, "pr", None)) if a.action == "update" else None
    if target and target.get("state") != "OPEN":
        sys.exit(f"PR #{target['number']} is {target['state']}, not OPEN — "
                 "a landed PR's body is a record, not a draft.")

    problems = validate(body, issue, num, a.min_mutation)
    if problems:
        verb = "OPENED" if a.action == "create" else "UPDATED"
        print(f"PR NOT {verb} — issue #{num}\n")
        for p in problems:
            print(f"  {'' if p.startswith('    ') else '- '}{p}")
        print("\nThe gates already checked the code. This checks that a human can review\n"
              "the INTENT without reading the diff. Fix the body, not this tool.")
        return 1

    ms = mutation_score()
    labels = [l["name"] for l in issue.get("labels", [])]
    tier = next((l for l in labels if re.fullmatch(r"tier-[123]", l)), None)
    print(f"All checks passed — issue #{num}, tier {tier}, "
          f"mutation {ms[0]:.1f}% over {ms[1]} mutants.")

    if a.action == "create":
        if a.dry_run:
            print("(--dry-run: not creating)")
            return 0
        rc, out = gh("pr", "create", "--title", a.title or issue["title"], "--body", body)
        print(out.strip())
        return rc

    if a.dry_run:
        print(f"(--dry-run: not updating PR #{target['number']} — {target['title']})")
        return 0
    rc, out = gh("pr", "edit", str(target["number"]), "--body-file", str(a.body_file))
    print(out.strip() if out.strip() else f"Updated PR #{target['number']}.")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
