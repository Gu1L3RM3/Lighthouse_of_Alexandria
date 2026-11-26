#!/usr/bin/env bash
# Stop: Claude may only finish when the fast check passes.
# Runs only if code changed since the last passing check; output is cut to the log tail.
INPUT=$(cat)
# Do not loop: if this hook already sent Claude back once, let it stop.
[ "$(echo "$INPUT" | jq -r '.stop_hook_active // false')" = "true" ] && exit 0

ROOT="${CLAUDE_PROJECT_DIR:-$PWD}"
cd "$ROOT" || exit 0
git rev-parse --git-dir >/dev/null 2>&1 || exit 0
[ -x scripts/verify.sh ] || exit 0

# Documentation-only changes need no verification.
git status --porcelain | grep -qvE '\.md$' || exit 0

STATE_FILE="$(git rev-parse --git-path harness-verified)"
STATE=$({ git status --porcelain; git diff HEAD 2>/dev/null; git ls-files -o --exclude-standard -z | xargs -0 -r sha1sum; } | sha1sum | cut -d' ' -f1)
[ -f "$STATE_FILE" ] && [ "$(cat "$STATE_FILE")" = "$STATE" ] && exit 0

if ! OUT=$(scripts/verify.sh fast 2>&1); then
  echo "$OUT" >&2
  echo "The fast check failed. Fix the root cause (do not silence it) and finish again. If the failure comes from the owner's uncommitted changes, say so instead of editing them." >&2
  exit 2
fi
echo "$STATE" >"$STATE_FILE"
exit 0
