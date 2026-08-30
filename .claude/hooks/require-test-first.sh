#!/usr/bin/env bash
# PreToolUse hook: refuse to let production code be written before a test exists.
#
# This is the determinism gate. Asking an agent to "do TDD" works most of the time.
# Exit code 2 works every time.
#
# Allows the edit when ANY of these is true:
#   - the target is not production Java (tests, docs, config, resources)
#   - the branch already has a new or changed file under src/test
#   - the escape hatch HARNESS_SKIP_TEST_FIRST=1 is set (for demos and emergencies)
#
# Exit 0 = allow, exit 2 = block and tell the model why.

set -uo pipefail

payload=$(cat)

target=$(printf '%s' "$payload" | python3 -c '
import json, sys
try:
    d = json.load(sys.stdin)
except Exception:
    print(""); raise SystemExit
ti = d.get("tool_input") or {}
print(ti.get("file_path") or ti.get("path") or "")
' 2>/dev/null)

# Not a path we guard -> allow.
case "$target" in
  */src/main/java/*) ;;
  *) exit 0 ;;
esac

if [ "${HARNESS_SKIP_TEST_FIRST:-0}" = "1" ]; then
  echo "require-test-first: bypassed via HARNESS_SKIP_TEST_FIRST=1" >&2
  exit 0
fi

repo_root=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0
cd "$repo_root" || exit 0

# Base to compare against: the default branch if we can find it, else just the worktree.
base=""
for cand in main master; do
  if git rev-parse --verify --quiet "$cand" >/dev/null 2>&1; then base="$cand"; break; fi
done

changed_tests=$(
  {
    git diff --name-only -- 'src/test' 2>/dev/null
    git diff --cached --name-only -- 'src/test' 2>/dev/null
    git ls-files --others --exclude-standard -- 'src/test' 2>/dev/null
    if [ -n "$base" ] && [ "$(git rev-parse HEAD)" != "$(git rev-parse "$base")" ]; then
      git diff --name-only "$base"...HEAD -- 'src/test' 2>/dev/null
    fi
  } | sort -u | grep -c . || true
)

if [ "${changed_tests:-0}" -gt 0 ]; then
  exit 0
fi

cat >&2 <<'MSG'
BLOCKED by the harness: test-first.

You are editing production code under src/main/java, but this branch has no new or
modified test under src/test.

Write the failing test first, then implement. The test is the specification — if you
cannot express the requirement as a failing test, the requirement is not yet clear
enough to implement.

This is a gate, not a preference. It is not negotiable by prompting, and editing this
hook is denied in .claude/settings.json.
MSG
exit 2
