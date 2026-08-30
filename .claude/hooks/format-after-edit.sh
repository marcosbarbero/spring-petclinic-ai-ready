#!/usr/bin/env bash
# PostToolUse: format Java automatically after the agent writes it.
#
# The agent should never spend a token on formatting, and should never see a
# formatting failure. Formatting is a solved, deterministic problem — so solve it
# deterministically instead of asking a language model to remember a style guide.
#
# Deterministic first. Agent on failure.

set -uo pipefail

target=$(cat | python3 -c '
import json,sys
try: d=json.load(sys.stdin)
except Exception: print(""); raise SystemExit
ti=d.get("tool_input") or {}
print(ti.get("file_path") or ti.get("path") or "")
' 2>/dev/null)

case "$target" in
  *.java) ;;
  *) exit 0 ;;
esac

root=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0
cd "$root" || exit 0

# Quiet, and never block the agent: formatting is a convenience, not a gate.
# The gate is spring-javaformat:validate in pre-push.
if ./mvnw -q -o spring-javaformat:apply >/dev/null 2>&1 \
   || ./mvnw -q spring-javaformat:apply >/dev/null 2>&1; then
  echo "formatted: ${target#"$root"/}" >&2
fi
exit 0
