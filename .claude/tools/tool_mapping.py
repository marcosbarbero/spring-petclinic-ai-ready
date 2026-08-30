#!/usr/bin/env python3
"""The tool registry: look tools up by key instead of reasoning about a directory.

Why this exists
---------------
Discovery has to live somewhere. Listing every tool in CLAUDE.md works, but that file is
loaded on every turn, so the list costs tokens forever and grows without bound. Putting
it in a README instead just moves the cost — the agent still has to read prose and infer
which tool applies.

So: one machine-readable registry, and one tool to query it. CLAUDE.md references only
this script. An agent runs `tool_mapping.py list` once, gets keys and one-line summaries,
then `get <key>` for the detail of the one it actually needs. Recall by key, not by
re-reading and re-reasoning.

`check` is the part that keeps it honest — a registry that drifts from the directory is
worse than no registry, so drift fails the build.

Usage:
    tool_mapping.py list                 # keys + summaries (start here)
    tool_mapping.py get <key>            # full record for one tool
    tool_mapping.py check                # registry vs directory; exit 1 on drift
    tool_mapping.py readme               # regenerate README.md from the registry
    tool_mapping.py register --key k --path p --summary s --use-when w [...]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).parent
MAPPING = TOOLS_DIR / "mapping.json"
SELF = Path(__file__).name


def load() -> dict:
    if not MAPPING.exists():
        return {"version": 1, "tools": {}}
    return json.loads(MAPPING.read_text())


def save(data: dict) -> None:
    MAPPING.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def cmd_list(data: dict, _: argparse.Namespace) -> int:
    tools = data.get("tools", {})
    if not tools:
        print("No tools registered.")
        return 0
    print(f"{len(tools)} tool(s). Use `tool_mapping.py get <key>` for detail.\n")
    width = max(len(k) for k in tools)
    for key in sorted(tools):
        print(f"  {key:<{width}}  {tools[key]['summary']}")
    print("\nDeterministic first. Agent on failure — reach for these before reading "
          "a generated report or writing a one-off script.")
    return 0


def cmd_get(data: dict, args: argparse.Namespace) -> int:
    tool = data.get("tools", {}).get(args.key)
    if not tool:
        print(f"No tool registered under '{args.key}'.\n", file=sys.stderr)
        cmd_list(data, args)
        return 1
    print(f"{args.key}\n{'-' * len(args.key)}")
    print(f"path      {tool['path']}")
    print(f"summary   {tool['summary']}")
    print(f"use when  {tool['use_when']}")
    if tool.get("replaces"):
        print(f"replaces  {tool['replaces']}")
    if tool.get("example"):
        print(f"\nexample\n  {tool['example']}")
    return 0


def cmd_check(data: dict, _: argparse.Namespace) -> int:
    tools = data.get("tools", {})
    root = TOOLS_DIR.parent.parent
    problems: list[str] = []

    for key, tool in sorted(tools.items()):
        if not (root / tool["path"]).exists():
            problems.append(f"'{key}' maps to {tool['path']}, which does not exist")
        for field in ("summary", "use_when"):
            if not tool.get(field):
                problems.append(f"'{key}' has no {field}")

    registered = {Path(t["path"]).name for t in tools.values()}
    on_disk = {p.name for p in TOOLS_DIR.glob("*.py")
               if p.name not in (SELF, "hook_io.py") and not p.name.startswith("_")}
    for orphan in sorted(on_disk - registered):
        problems.append(f"{orphan} exists but is not registered — nobody will discover it")

    if problems:
        print("TOOL REGISTRY DRIFT\n")
        for p in problems:
            print(f"  - {p}")
        print("\nA registry that disagrees with the directory is worse than no registry.\n"
              "Fix with: tool_mapping.py register --key ... , then tool_mapping.py readme")
        return 1

    print(f"Registry OK — {len(tools)} tool(s), all present, none orphaned.")
    return 0


def cmd_readme(data: dict, _: argparse.Namespace) -> int:
    tools = data.get("tools", {})
    lines = [
        "# Toolbox",
        "",
        "<!-- GENERATED FROM mapping.json BY tool_mapping.py — DO NOT EDIT BY HAND. -->",
        "<!-- Regenerate: .claude/tools/tool_mapping.py readme                      -->",
        "",
        "Deterministic scripts. No model involved: same input, same output, every time.",
        "",
        "Agents should not read this file — it is for humans. Agents use",
        "`tool_mapping.py list` and `tool_mapping.py get <key>`, which is cheaper than",
        "parsing prose and cannot drift from the registry.",
        "",
        "| key | what it does | use when |",
        "|---|---|---|",
    ]
    for key in sorted(tools):
        t = tools[key]
        lines.append(f"| `{key}` | {t['summary']} | {t['use_when']} |")
    lines += [
        "",
        "## Adding a tool",
        "",
        "```bash",
        ".claude/tools/tool_mapping.py register \\",
        "  --key my-tool --path .claude/tools/my_tool.py \\",
        '  --summary "one line" --use-when "the situation that calls for it"',
        ".claude/tools/tool_mapping.py readme    # regenerate this file",
        "```",
        "",
        "`tool_mapping.py check` runs in pre-push and fails if a tool exists on disk but",
        "is not registered. An unregistered tool is an undiscoverable tool.",
        "",
    ]
    (TOOLS_DIR / "README.md").write_text("\n".join(lines))
    print(f"Wrote {TOOLS_DIR / 'README.md'} ({len(tools)} tools)")
    return 0


def cmd_register(data: dict, args: argparse.Namespace) -> int:
    data.setdefault("tools", {})[args.key] = {
        "path": args.path,
        "summary": args.summary,
        "use_when": args.use_when,
        "replaces": args.replaces or "",
        "example": args.example or "",
    }
    save(data)
    print(f"Registered '{args.key}'. Now run: tool_mapping.py readme")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("list")
    g = sub.add_parser("get"); g.add_argument("key")
    sub.add_parser("check")
    sub.add_parser("readme")
    r = sub.add_parser("register")
    r.add_argument("--key", required=True)
    r.add_argument("--path", required=True)
    r.add_argument("--summary", required=True)
    r.add_argument("--use-when", required=True, dest="use_when")
    r.add_argument("--replaces")
    r.add_argument("--example")
    args = ap.parse_args()

    data = load()
    return {
        None: cmd_list, "list": cmd_list, "get": cmd_get,
        "check": cmd_check, "readme": cmd_readme, "register": cmd_register,
    }[args.cmd](data, args)


if __name__ == "__main__":
    raise SystemExit(main())
