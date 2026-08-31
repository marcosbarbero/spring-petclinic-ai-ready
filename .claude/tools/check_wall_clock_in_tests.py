#!/usr/bin/env python3
"""Tests must not read the wall clock. This is the gate that makes that true.

Why this exists
---------------
A test that calls LocalDate.now() is dated relative to whenever it happens to run.
It passes all day and fails at a midnight rollover, in a timezone nobody is awake
in, on a machine nobody is watching -- and because it looks like a flake, it gets
re-run rather than fixed. The fix is always the same: literal dates in the test,
and an injected Clock in production when the test genuinely needs to control
"today".

Knowing that is not enough. `docs/lexicon/entries/clock-dependent-tests.md` has
said so for a while and twelve calls still exist. A rule that binds by author
discipline is a suggestion; this is the sensor that makes it a rule.

How it binds without breaking the tree
--------------------------------------
A ratchet, not a wall. `baseline.json` records how many violations each file has
TODAY. The gate does not care whether a violation is good -- it cares whether the
count went UP. So:

  * day one, actual == baseline everywhere, the build is green, nothing changes
  * adding a thirteenth violation fails, even in a file that already had twelve
  * REMOVING one also fails, until the baseline is lowered to match

That last rule is what makes it a ratchet rather than a decoration. A per-file
suppression would let a cleaned-up file silently regress back to its old count;
here the number can only travel one way.

Deliberately not merge-base scoped. Diffing against origin/main needs full git
history, and CI checks out shallow by default -- a gate that quietly degrades to
"no violations found" on a shallow clone is worse than no gate, because it reads
as verified. A committed baseline needs no history at all.

Usage:
    check_wall_clock_in_tests.py              # the gate: exit 1 on any regression
    check_wall_clock_in_tests.py --audit      # print the backlog, always exit 0
    check_wall_clock_in_tests.py --update-baseline   # record reality, then review the diff
    check_wall_clock_in_tests.py --self-test  # prove the gate still detects what it claims

Wired into the build at the `validate` phase in pom.xml, so `./mvnw verify` runs
it -- which means the pre-push hook and CI run the same entry point, not two
definitions of passing.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEST_ROOT = ROOT / "src" / "test" / "java"
BASELINE = Path(__file__).resolve().parent / "wall_clock_baseline.json"

# Wall-clock time sources. Each reads "now" from the machine, so a test built on
# one is dated by when it ran. Clock.fixed(...) is deliberately absent -- that is
# the cure, not the disease.
BANNED = [
    (r"\b(?:LocalDate|LocalDateTime|LocalTime|Instant|ZonedDateTime|OffsetDateTime"
     r"|OffsetTime|Year|YearMonth|MonthDay)\s*\.\s*now\s*\(\s*\)", "java.time now()"),
    (r"\bnew\s+Date\s*\(\s*\)", "new Date()"),
    (r"\bSystem\s*\.\s*(?:currentTimeMillis|nanoTime)\s*\(\s*\)", "System clock"),
    (r"\bCalendar\s*\.\s*getInstance\s*\(\s*\)", "Calendar.getInstance()"),
    (r"\bClock\s*\.\s*(?:systemUTC|systemDefaultZone|system)\s*\(", "Clock.system*()"),
]
PATTERNS = [(re.compile(p), label) for p, label in BANNED]

# A trailing marker for the rare case that survives review, so it is a decision on
# the line rather than an invisible allowance in a JSON file.
ALLOW_MARKER = re.compile(r"//\s*allow-wall-clock:\s*\S")

HINT = """
  How to comply:
    - Use a literal date:  LocalDate.of(2020, 1, 15)   not  LocalDate.now()
    - If the test must control what production thinks "today" is, production has
      to take a Clock. Inject java.time.Clock and use Clock.fixed(...) in the test.
    - If a call genuinely must read the wall clock, end the line with
      `// allow-wall-clock: <reason>` -- a reason, not a bare marker.
  Background: .claude/tools/lexicon.py get deterministic-test-dates
"""


def strip_noise(line: str) -> str:
    """Blank out string literals and line comments so they cannot trip a pattern.

    A javadoc sentence mentioning LocalDate.now() is prose, not a call, and a gate
    that fails on prose is a gate people learn to route around. Crude on purpose:
    no Java parser in the standard library, and the cost of being slightly
    conservative here is a missed violation, not a false one.
    """
    line = re.sub(r'"(?:\\.|[^"\\])*"', '""', line)
    return re.sub(r"//.*$|/\*.*?\*/", "", line)


def scan(path: Path) -> list[tuple[int, str, str]]:
    """Return (line number, label, source line) for each violation in one file."""
    found = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as exc:  # unreadable == unverifiable
        raise SystemExit(f"cannot read {path}: {exc}")
    for n, raw in enumerate(lines, 1):
        if ALLOW_MARKER.search(raw):
            continue
        code = strip_noise(raw)
        for pattern, label in PATTERNS:
            if pattern.search(code):
                found.append((n, label, raw.strip()))
                break
    return found


def survey() -> dict[str, list[tuple[int, str, str]]]:
    """Every test file with at least one violation, keyed by repo-relative path."""
    if not TEST_ROOT.is_dir():
        raise SystemExit(f"test root not found: {TEST_ROOT}\n"
                         "  The gate cannot verify what it cannot find, so this is a "
                         "failure, not a pass.")
    out = {}
    for path in sorted(TEST_ROOT.rglob("*.java")):
        hits = scan(path)
        if hits:
            out[path.relative_to(ROOT).as_posix()] = hits
    return out


def load_baseline() -> dict[str, dict]:
    if not BASELINE.exists():
        raise SystemExit(f"baseline missing: {BASELINE}\n"
                         "  Create it with --update-baseline. A gate with no baseline "
                         "cannot tell a regression from the status quo.")
    try:
        data = json.loads(BASELINE.read_text())
    except json.JSONDecodeError as exc:
        raise SystemExit(f"baseline is not valid JSON: {exc}")
    return data.get("files", {})


def write_baseline(current: dict[str, list], previous: dict[str, dict]) -> None:
    files = {}
    for path, hits in sorted(current.items()):
        prior = previous.get(path, {})
        files[path] = {
            "count": len(hits),
            "reason": prior.get("reason", "pre-existing; see issue #8"),
        }
    BASELINE.write_text(json.dumps(
        {
            "_comment": "Wall-clock violations in tests, grandfathered so the gate "
                        "could land without breaking the tree. Counts ratchet DOWN "
                        "only. Regenerate with check_wall_clock_in_tests.py "
                        "--update-baseline. Backlog: issue #8.",
            "files": files,
        }, indent=2) + "\n")


def report(current: dict[str, list], baseline: dict[str, dict]) -> list[str]:
    """The whole gate. Returns a list of problems; empty means green."""
    problems = []

    for path, hits in sorted(current.items()):
        allowed = baseline.get(path, {}).get("count", 0)
        if len(hits) > allowed:
            problems.append(
                f"{path}: {len(hits)} wall-clock use(s), baseline allows {allowed}")
            for n, label, src in hits[allowed:] if allowed else hits:
                problems.append(f"    {path}:{n}  {label}   {src}")

    # The other direction: a baseline must not outlive what it excuses, or it rots
    # into a licence to reintroduce exactly what was cleaned up.
    for path, entry in sorted(baseline.items()):
        actual = len(current.get(path, []))
        allowed = entry.get("count", 0)
        if not (ROOT / path).exists():
            problems.append(
                f"{path}: baselined but the file no longer exists — drop the entry")
        elif actual < allowed:
            problems.append(
                f"{path}: {actual} wall-clock use(s) left but baseline still allows "
                f"{allowed} — lower it (--update-baseline). The ratchet only turns "
                f"one way.")

    return problems


def audit(current: dict[str, list], baseline: dict[str, dict]) -> None:
    total = sum(len(h) for h in current.values())
    if not total:
        print("No wall-clock time sources in src/test/java. Backlog empty.")
        return
    print(f"{total} wall-clock use(s) in {len(current)} file(s) — backlog, issue #8\n")
    for path, hits in sorted(current.items()):
        entry = baseline.get(path, {})
        mark = "" if path in baseline else "   [NOT BASELINED — this fails the gate]"
        print(f"  {path}  ({len(hits)}){mark}")
        if entry.get("reason"):
            print(f"      reason: {entry['reason']}")
        for n, label, src in hits:
            print(f"      :{n}  {label}   {src}")
        print()


def self_test() -> int:
    """Prove the detector still detects. A gate nobody tests is a gate that rots.

    Covers the scenarios on issue #7: a new call is caught, prose and allow-marked
    lines are not, and the ratchet reports both directions.
    """
    cases = [
        ("LocalDate.now()", "\t\tpet.setBirthDate(LocalDate.now());", True),
        ("chained now()", "\t\tvar d = LocalDate.now().plusDays(1);", True),
        ("Instant.now()", "\t\tInstant t = Instant.now();", True),
        ("new Date()", "\t\tDate d = new Date();", True),
        ("currentTimeMillis", "\t\tlong t = System.currentTimeMillis();", True),
        ("Calendar.getInstance", "\t\tvar c = Calendar.getInstance();", True),
        ("Clock.systemUTC", "\t\tvar c = Clock.systemUTC();", True),
        ("literal date", "\t\tpet.setBirthDate(LocalDate.of(2020, 1, 15));", False),
        ("fixed clock", "\t\tvar c = Clock.fixed(instant, ZoneOffset.UTC);", False),
        ("comment prose", "\t\t// never call LocalDate.now() in a test", False),
        ("string literal", '\t\tvar s = "LocalDate.now()";', False),
        ("allow marker", "\t\tvar d = LocalDate.now(); // allow-wall-clock: measures "
                         "real elapsed time", False),
    ]
    failures = []
    with tempfile.TemporaryDirectory() as tmp:
        probe = Path(tmp) / "Probe.java"
        for name, line, should_flag in cases:
            probe.write_text(line + "\n", encoding="utf-8")
            flagged = bool(scan(probe))
            if flagged != should_flag:
                failures.append(
                    f"  {name}: expected {'a hit' if should_flag else 'no hit'}, "
                    f"got {'a hit' if flagged else 'no hit'}")

        # The ratchet, both directions, without touching the real baseline.
        probe.write_text("LocalDate.now();\nInstant.now();\n", encoding="utf-8")
        two = {"p": scan(probe)}
        if not report(two, {"p": {"count": 1}}):
            failures.append("  ratchet: an increase over baseline was not reported")
        if not report({}, {"p": {"count": 1}}):
            failures.append("  ratchet: a stale/deleted baseline entry was not reported")

    for line in failures:
        print(line)
    print(f"self-test: {len(cases) + 2 - len(failures)}/{len(cases) + 2} passed")
    return 1 if failures else 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Fail the build when a test reads the wall clock.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=HINT)
    ap.add_argument("--audit", action="store_true",
                    help="print the outstanding backlog and exit 0")
    ap.add_argument("--update-baseline", action="store_true",
                    help="record current counts as the new baseline, then review the diff")
    ap.add_argument("--self-test", action="store_true",
                    help="prove the detector still detects what it claims to")
    args = ap.parse_args()

    if args.self_test:
        return self_test()

    current = survey()

    if args.update_baseline:
        previous = load_baseline() if BASELINE.exists() else {}
        write_baseline(current, previous)
        total = sum(len(h) for h in current.values())
        print(f"Baseline updated: {total} violation(s) across {len(current)} file(s).")
        print("Review the diff before committing — this file is the only thing "
              "standing between the tree and a silent regression.")
        return 0

    baseline = load_baseline()

    if args.audit:
        audit(current, baseline)
        return 0

    problems = report(current, baseline)
    if problems:
        print("Tests must not read the wall clock.\n")
        for p in problems:
            print(f"  {p}" if not p.startswith("    ") else p)
        print(HINT)
        return 1

    total = sum(len(h) for h in current.values())
    print(f"wall clock in tests: OK ({total} baselined, none new) — "
          f"backlog: issue #8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
