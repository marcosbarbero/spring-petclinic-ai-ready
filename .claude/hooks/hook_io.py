"""Shared helpers for Claude Code hooks.

Extracted because two hooks needed the same eight lines of JSON parsing. That is the
rule this repo applies to itself: **if a script is needed twice, it becomes a tool.**
Inline scripts are written once, debugged never, and duplicated forever.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def payload() -> dict:
    """The hook's JSON input from stdin. Never raises — a malformed payload
    must not break the agent's turn."""
    try:
        return json.load(sys.stdin)
    except Exception:
        return {}


def target_path(data: dict | None = None) -> str:
    """The file the tool is acting on, or '' when there isn't one."""
    d = data if data is not None else payload()
    ti = d.get("tool_input") or {}
    return ti.get("file_path") or ti.get("path") or ""


def repo_root() -> Path | None:
    try:
        out = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True, timeout=10)
        return Path(out.stdout.strip()) if out.returncode == 0 else None
    except Exception:
        return None


def git(*args: str, cwd: Path | None = None) -> str:
    try:
        out = subprocess.run(["git", *args], capture_output=True, text=True,
                             timeout=15, cwd=cwd)
        return out.stdout if out.returncode == 0 else ""
    except Exception:
        return ""
