#!/usr/bin/env python3
"""Durable memory: have we solved this class of problem before?

Why this exists
---------------
Three registries, three different questions:

    tool_mapping.py   what tools exist
    arch_map.py       where the code lives
    lexicon.py        HOW WE SOLVED THIS BEFORE

Without the third, every session re-derives the same discoveries from scratch. Somebody
once spent real tokens finding out that Spring expands `rejectValue` codes so
`getCode()` never returns the code you passed — and then the session ended and that
knowledge evaporated. The next session pays for it again.

An entry costs a minute to write and is recalled for the price of one `search`. Write one
whenever something was non-obvious, surprising, or cost you a wrong turn.

**This is the loop that makes a harness get better instead of just staying green.** Every
escaped surprise becomes an entry, the same way every escaped defect becomes a gate.

Usage:
    lexicon.py search <term>     # START HERE — "have I seen this before?"
    lexicon.py list              # every entry, one line each
    lexicon.py get <key>         # the full entry
    lexicon.py tags              # browse by tag
    lexicon.py check             # structural validation; runs in pre-push
    lexicon.py readme            # regenerate docs/lexicon/README.md
    lexicon.py add --key k --title t --problem p --solution s --why w [--tags a,b]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENTRIES = ROOT / "docs" / "lexicon" / "entries"
FIELDS = ("title", "problem", "solution", "why")

# One file per entry, not one file for all entries. Search does not care - the tool
# reads the corpus, the agent never does - but WRITING does: a single shared file is a
# merge-conflict magnet the moment two branches both record a lesson, and it destroys
# per-lesson git history. New entry = new file = no conflict, readable diff, real blame.


def _parse(path: Path) -> dict:
    text = path.read_text()
    m = re.match(r"---\n(.*?)\n---\n(.*)", text, re.S)
    meta_raw, body = (m.group(1), m.group(2)) if m else ("", text)
    e: dict = {"tags": [], "seen_in": [], "example": ""}
    for line in meta_raw.splitlines():
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        k, v = k.strip(), v.strip()
        if k in ("tags", "seen_in"):
            e[k] = [t.strip() for t in v.strip("[]").split(",") if t.strip()]
        else:
            e[k] = v.strip('"')
    for field in ("problem", "solution", "why"):
        sec = re.search(rf"##\s*{field}\s*\n(.*?)(?=\n##\s|\Z)", body, re.I | re.S)
        e[field] = sec.group(1).strip() if sec else ""
    ex = re.search(r"##\s*example\s*\n+```[a-z]*\n(.*?)```", body, re.I | re.S)
    if ex:
        e["example"] = ex.group(1).strip()
    e.setdefault("title", path.stem)
    return e


def load() -> dict:
    entries = {}
    if ENTRIES.is_dir():
        for f in sorted(ENTRIES.glob("*.md")):
            entries[f.stem] = _parse(f)
    return {"version": 1, "entries": entries}


def save_entry(key: str, e: dict) -> Path:
    ENTRIES.mkdir(parents=True, exist_ok=True)
    fm = ["---", f"key: {key}", f"title: {e['title']}",
          "tags: [" + ", ".join(e.get("tags", [])) + "]"]
    if e.get("seen_in"):
        fm.append("seen_in: [" + ", ".join(e["seen_in"]) + "]")
    fm.append("---")
    body = ["", "## Problem", "", e["problem"], "", "## Solution", "", e["solution"],
            "", "## Why", "", e["why"], ""]
    if e.get("example"):
        body += ["## Example", "", "```java", e["example"], "```", ""]
    path = ENTRIES / f"{key}.md"
    path.write_text("\n".join(fm + body))
    return path


def show(key: str, e: dict, full: bool = True) -> None:
    print(f"{key}\n{'-' * len(key)}")
    print(f"{e['title']}\n")
    print(f"PROBLEM   {e['problem']}")
    print(f"SOLUTION  {e['solution']}")
    if full:
        print(f"WHY       {e['why']}")
        if e.get("example"):
            print(f"\nexample\n  {e['example']}")
        meta = []
        if e.get("tags"):
            meta.append("tags: " + ", ".join(e["tags"]))
        if e.get("seen_in"):
            meta.append("seen in: " + ", ".join(e["seen_in"]))
        if meta:
            print("\n" + "   ".join(meta))


def cmd_search(d: dict, args: argparse.Namespace) -> int:
    term = args.term.lower()
    hits = []
    for key, e in d["entries"].items():
        hay = " ".join([key, e["title"], e["problem"], e["solution"], e["why"],
                        " ".join(e.get("tags", []))]).lower()
        if term in hay:
            hits.append((key, e))
    if not hits:
        print(f"Nothing in the lexicon for '{args.term}'.")
        print("\nIf you are about to work this out from scratch, that is worth recording\n"
              "when you are done:  lexicon.py add --key ... ")
        return 1
    print(f"{len(hits)} entr{'y' if len(hits) == 1 else 'ies'} for '{args.term}':\n")
    for key, e in sorted(hits):
        show(key, e, full=len(hits) == 1)
        print()
    if len(hits) > 1:
        print("`lexicon.py get <key>` for the reasoning behind any of these.")
    return 0


def cmd_recall(d: dict, args: argparse.Namespace) -> int:
    """Used by the UserPromptSubmit hook. Ranked, capped, silent on no match."""
    stop = {"the", "and", "for", "with", "that", "this", "from", "into", "when", "what",
            "how", "why", "does", "not", "you", "are", "was", "can", "add", "fix", "make",
            "use", "get", "set", "run", "why", "its", "our", "all", "any", "but", "has"}
    terms = {w for w in re.findall(r"[a-zA-Z][a-zA-Z0-9_-]{2,}", args.text.lower())
             if w not in stop}
    scored = []
    for key, e in d["entries"].items():
        title = (key + " " + e["title"]).lower()
        tags = " ".join(e.get("tags", [])).lower()
        body = (e["problem"] + " " + e["solution"] + " " + e["why"]).lower()
        score = sum(3 for t in terms if t in title) + \
                sum(2 for t in terms if t in tags) + \
                sum(1 for t in terms if t in body)
        if score >= args.threshold:
            scored.append((score, key, e))
    if not scored:
        return 0
    scored.sort(reverse=True, key=lambda x: (x[0], x[1]))
    print("Relevant prior knowledge from the project lexicon "
          "(recalled automatically — you have solved these before):\n")
    for _, key, e in scored[: args.limit]:
        print(f"- **{e['title']}** (`{key}`)")
        print(f"  - problem: {e['problem']}")
        print(f"  - solution: {e['solution']}")
        if e.get("example"):
            print(f"  - example: `{e['example'].splitlines()[0]}`")
    print("\n`.claude/tools/lexicon.py get <key>` for the full reasoning.")
    return 0


def cmd_list(d: dict, _: argparse.Namespace) -> int:
    entries = d["entries"]
    if not entries:
        print("Lexicon is empty.")
        return 0
    width = max(len(k) for k in entries)
    print(f"{len(entries)} entries. `lexicon.py get <key>` for detail, "
          f"`search <term>` to look something up.\n")
    for key in sorted(entries):
        print(f"  {key:<{width}}  {entries[key]['title']}")
    return 0


def cmd_get(d: dict, args: argparse.Namespace) -> int:
    e = d["entries"].get(args.key)
    if not e:
        print(f"No entry '{args.key}'.", file=sys.stderr)
        return cmd_list(d, args) or 1
    show(args.key, e)
    return 0


def cmd_tags(d: dict, _: argparse.Namespace) -> int:
    by_tag: dict[str, list[str]] = {}
    for key, e in d["entries"].items():
        for t in e.get("tags", []) or ["(untagged)"]:
            by_tag.setdefault(t, []).append(key)
    for tag in sorted(by_tag):
        print(f"{tag}\n  " + "\n  ".join(sorted(by_tag[tag])))
    return 0


def cmd_check(d: dict, _: argparse.Namespace) -> int:
    problems = []
    for key, e in sorted(d["entries"].items()):
        for f in FIELDS:
            if not e.get(f):
                problems.append(f"'{key}' has no {f}")
        if len(e.get("problem", "")) < 25:
            problems.append(f"'{key}' problem is too vague to match against later")
        if not e.get("tags"):
            problems.append(f"'{key}' has no tags — it will be hard to find by search")
    if problems:
        print("LEXICON PROBLEMS\n")
        for p in problems:
            print(f"  - {p}")
        print("\nAn entry nobody can find is an entry nobody will use.")
        return 1
    print(f"Lexicon OK — {len(d['entries'])} entries, all searchable.")
    return 0


def cmd_readme(d: dict, _: argparse.Namespace) -> int:
    out = ["# Lexicon — how we solved this before", "",
           "<!-- GENERATED FROM mapping.json BY .claude/tools/lexicon.py — DO NOT EDIT. -->",
           "<!-- Regenerate: .claude/tools/lexicon.py readme                            -->", "",
           "Durable memory for recurring problems. Every entry is something that was once",
           "worked out the hard way, written down so it is never worked out again.",
           "",
           "Agents should not read this file — they use `lexicon.py search <term>`, which",
           "is cheaper and returns only the relevant entry.",
           "", "| key | problem | solution |", "|---|---|---|"]
    for key in sorted(d["entries"]):
        e = d["entries"][key]
        out.append(f"| `{key}` | {e['problem']} | {e['solution']} |")
    out += ["", "## Adding an entry", "",
            "Write one whenever something was non-obvious, surprising, or cost you a wrong",
            "turn. The bar is low on purpose — a minute now, recalled forever.", "",
            "```bash", ".claude/tools/lexicon.py add \\",
            "  --key spring-error-codes-are-expanded \\",
            '  --title "..." --problem "..." --solution "..." --why "..." \\',
            "  --tags spring,validation", "```", ""]
    (ENTRIES.parent / "README.md").write_text("\n".join(out))
    print(f"Wrote {ENTRIES.parent / 'README.md'}")
    return 0


def cmd_add(d: dict, a: argparse.Namespace) -> int:
    d.setdefault("entries", {})[a.key] = {
        "title": a.title, "problem": a.problem, "solution": a.solution, "why": a.why,
        "example": a.example or "",
        "tags": [t.strip() for t in (a.tags or "").split(",") if t.strip()],
        "seen_in": [s.strip() for s in (a.seen_in or "").split(",") if s.strip()],
    }
    path = save_entry(a.key, d["entries"][a.key])
    print(f"Recorded '{a.key}' -> {path.relative_to(ROOT)}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd")
    s = sub.add_parser("search"); s.add_argument("term")
    r = sub.add_parser("recall"); r.add_argument("text")
    r.add_argument("--limit", type=int, default=3); r.add_argument("--threshold", type=int, default=3)
    g = sub.add_parser("get"); g.add_argument("key")
    for n in ("list", "tags", "check", "readme"):
        sub.add_parser(n)
    a = sub.add_parser("add")
    for f in ("key", "title", "problem", "solution", "why"):
        a.add_argument(f"--{f}", required=True)
    a.add_argument("--example"); a.add_argument("--tags"); a.add_argument("--seen-in", dest="seen_in")
    args = ap.parse_args()
    d = load()
    return {None: cmd_list, "list": cmd_list, "search": cmd_search, "get": cmd_get,
            "tags": cmd_tags, "check": cmd_check, "readme": cmd_readme,
            "recall": cmd_recall, "add": cmd_add}[args.cmd](d, args)


if __name__ == "__main__":
    raise SystemExit(main())
