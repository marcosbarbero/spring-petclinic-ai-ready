#!/usr/bin/env python3
"""The architecture registry: look up where code lives instead of searching for it.

Why this exists
---------------
"Add validation to pet birth dates" normally begins with an agent globbing the tree,
grepping for `Pet`, opening half a dozen files and inferring the structure — a few
thousand tokens spent rediscovering something that has not changed since 2013, and
rediscovered again next session because none of it persists.

The structure is a fact about the repo, so it belongs in a file, not in a model's
reasoning. `arch_map.py locate owner` returns the paths, the classes, and the rules
that apply — deterministically, in a few hundred tokens.

Same shape as `tool_mapping.py` on purpose: `list`, `get`, `check`, `readme`. One idea,
applied twice, is cheaper to learn than two.

`check` is what keeps it honest. A map that disagrees with the tree is worse than no map,
so drift fails the build.

Usage:
    arch_map.py list                # slices + responsibilities
    arch_map.py get <slice>         # everything about one slice
    arch_map.py locate <slice>      # just the paths, for piping into a prompt
    arch_map.py rules               # the dependency rules, and what enforces them
    arch_map.py check               # map vs reality; exit 1 on drift
    arch_map.py readme              # regenerate docs/architecture/README.md
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAPPING = ROOT / "docs" / "architecture" / "mapping.json"


def load() -> dict:
    if not MAPPING.exists():
        sys.exit(f"No architecture map at {MAPPING}")
    return json.loads(MAPPING.read_text())


def cmd_list(d: dict, _: argparse.Namespace) -> int:
    style = d.get("style", {})
    print(f"{style.get('name', 'architecture')}")
    print(f"{style.get('summary', '')}\n")
    slices = d["slices"]
    width = max(len(k) for k in slices)
    for key in sorted(slices):
        print(f"  {key:<{width}}  {slices[key]['responsibility']}")
    print(f"\nADR: {style.get('adr')}")
    print(f"Enforced by: {style.get('enforced_by')}")
    print("\n`arch_map.py get <slice>` for detail, `locate <slice>` for just paths.")
    return 0


def cmd_get(d: dict, args: argparse.Namespace) -> int:
    sl = d["slices"].get(args.slice)
    if not sl:
        print(f"Unknown slice '{args.slice}'. Known: {', '.join(sorted(d['slices']))}",
              file=sys.stderr)
        return 1
    print(f"{args.slice}\n{'-' * len(args.slice)}")
    print(f"package        {sl['package']}")
    print(f"source         {sl['source_path']}")
    print(f"tests          {sl['test_path']}")
    print(f"responsibility {sl['responsibility']}")
    print(f"owns           {', '.join(sl['owns'])}")
    for kind, names in (sl.get("entrypoints") or {}).items():
        print(f"  {kind:<12} {', '.join(names)}")
    print(f"may depend on  {', '.join(sl['may_depend_on']) or '(nothing)'}")
    print(f"MUST NOT       {', '.join(sl['must_not_depend_on']) or '(no restrictions)'}")
    if sl.get("notes"):
        print(f"\nnote: {sl['notes']}")
    return 0


def cmd_locate(d: dict, args: argparse.Namespace) -> int:
    sl = d["slices"].get(args.slice)
    if not sl:
        print(f"Unknown slice '{args.slice}'", file=sys.stderr)
        return 1
    print(sl["source_path"])
    print(sl["test_path"])
    return 0


def cmd_rules(d: dict, _: argparse.Namespace) -> int:
    print("Dependency rules (enforced by ArchitectureRulesTest, not by good intentions)\n")
    for key in sorted(d["slices"]):
        sl = d["slices"][key]
        allow = ", ".join(sl["may_depend_on"]) or "nothing"
        deny = ", ".join(sl["must_not_depend_on"]) or "-"
        print(f"  {key:<8} may depend on: {allow}")
        if sl["must_not_depend_on"]:
            print(f"  {'':<8} must NOT:      {deny}")
    print(f"\n{d['style']['enforced_by']}")
    return 0


def cmd_check(d: dict, _: argparse.Namespace) -> int:
    problems: list[str] = []
    mapped_classes: dict[str, str] = {}

    for key, sl in sorted(d["slices"].items()):
        src = ROOT / sl["source_path"]
        if not src.is_dir():
            problems.append(f"'{key}' source_path {sl['source_path']} does not exist")
            continue
        on_disk = {p.stem for p in src.glob("*.java") if p.stem != "package-info"}
        listed = set(sl["owns"])
        for missing in sorted(listed - on_disk):
            problems.append(f"'{key}' lists {missing}, which is not in {sl['source_path']}")
        for unlisted in sorted(on_disk - listed):
            problems.append(f"{unlisted} exists in '{key}' but is not in the map")
        for cls in listed:
            if cls in mapped_classes:
                problems.append(f"{cls} claimed by both '{mapped_classes[cls]}' and '{key}'")
            mapped_classes[cls] = key
        overlap = set(sl["may_depend_on"]) & set(sl["must_not_depend_on"])
        if overlap:
            problems.append(f"'{key}' both allows and forbids: {', '.join(sorted(overlap))}")
        for dep in sl["may_depend_on"]:
            if dep not in d["slices"]:
                problems.append(f"'{key}' may_depend_on unknown slice '{dep}'")

    enforcer = ROOT / d["style"]["enforced_by"]
    if not enforcer.exists():
        problems.append(f"enforced_by points at {d['style']['enforced_by']}, which is missing")

    src_root = ROOT / "src/main/java" / d["root_package"].replace(".", "/")
    if src_root.is_dir():
        pkgs = {p.name for p in src_root.iterdir() if p.is_dir()}
        for orphan in sorted(pkgs - set(d["slices"])):
            problems.append(f"package '{orphan}' exists but is not a mapped slice")

    if problems:
        print("ARCHITECTURE MAP DRIFT\n")
        for p in problems:
            print(f"  - {p}")
        print("\nThe map is how an agent finds anything without searching. A map that\n"
              "disagrees with the tree sends it confidently to the wrong place.\n"
              "Fix docs/architecture/mapping.json, then: arch_map.py readme")
        return 1

    print(f"Architecture map OK — {len(d['slices'])} slices, "
          f"{len(mapped_classes)} classes, no drift.")
    return 0


def cmd_readme(d: dict, _: argparse.Namespace) -> int:
    st = d["style"]
    out = [
        "# Architecture",
        "",
        "<!-- GENERATED FROM mapping.json BY .claude/tools/arch_map.py — DO NOT EDIT. -->",
        "<!-- Regenerate: .claude/tools/arch_map.py readme                            -->",
        "",
        f"**{st['name']}**",
        "",
        st["summary"],
        "",
        f"Decision: [{st['adr']}]({Path(st['adr']).name})  ·  "
        f"Enforced by: `{Path(st['enforced_by']).name}`",
        "",
        "Agents should not read this file — it is for humans. Agents use",
        "`.claude/tools/arch_map.py get <slice>`, which is cheaper and cannot drift.",
        "",
        "| slice | responsibility | may depend on | must not |",
        "|---|---|---|---|",
    ]
    for key in sorted(d["slices"]):
        sl = d["slices"][key]
        out.append(f"| `{key}` | {sl['responsibility']} | "
                   f"{', '.join(sl['may_depend_on']) or '—'} | "
                   f"{', '.join(sl['must_not_depend_on']) or '—'} |")
    out += ["", "## Slices", ""]
    for key in sorted(d["slices"]):
        sl = d["slices"][key]
        out += [f"### `{key}`", "",
                f"- package: `{sl['package']}`",
                f"- source: `{sl['source_path']}`",
                f"- tests: `{sl['test_path']}`",
                f"- owns: {', '.join('`' + c + '`' for c in sl['owns'])}"]
        if sl.get("notes"):
            out += ["", f"> {sl['notes']}"]
        out += [""]
    (MAPPING.parent / "README.md").write_text("\n".join(out))
    print(f"Wrote {MAPPING.parent / 'README.md'}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("list")
    for name in ("get", "locate"):
        s = sub.add_parser(name); s.add_argument("slice")
    for name in ("rules", "check", "readme"):
        sub.add_parser(name)
    args = ap.parse_args()
    d = load()
    return {None: cmd_list, "list": cmd_list, "get": cmd_get, "locate": cmd_locate,
            "rules": cmd_rules, "check": cmd_check, "readme": cmd_readme}[args.cmd](d, args)


if __name__ == "__main__":
    raise SystemExit(main())
