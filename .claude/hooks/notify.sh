#!/usr/bin/env bash
# Notification: tells you when Claude is waiting (useful with parallel sessions).
MSG="Claude is waiting for you: $(basename "${CLAUDE_PROJECT_DIR:-$PWD}")"
if command -v notify-send >/dev/null 2>&1; then notify-send "Claude Code" "$MSG"
elif command -v osascript >/dev/null 2>&1; then osascript -e 'on run argv' -e 'display notification (item 1 of argv) with title "Claude Code"' -e 'end run' "$MSG"
else printf '\a' >&2; fi
exit 0
