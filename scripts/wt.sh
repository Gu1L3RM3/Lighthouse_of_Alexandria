#!/usr/bin/env bash
# wt.sh new <name> [base] | ls | rm <name>
# Sibling worktrees (branch wt/<name>) for parallel or unattended sessions. They start
# from origin/main, so the main checkout's uncommitted work stays where it is.
set -euo pipefail
MAIN="$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")"
cmd="${1:-}"
name="${2:-}"

usage() { echo "usage: wt.sh new <name> [base] | ls | rm <name>" >&2; exit 1; }

case "$cmd" in
  new)
    [ -n "$name" ] || usage
    base="${3:-}"
    if [ -z "$base" ]; then
      if git remote get-url origin >/dev/null 2>&1; then
        git fetch -q origin || echo "wt: fetch failed, using the last known origin/main" >&2
        base=origin/main
      else
        base=HEAD
      fi
    fi
    dir="$MAIN-wt-$name"
    git worktree add --no-track -b "wt/$name" "$dir" "$base"
    echo "Ready: cd \"$dir\" && claude"
    ;;
  ls) git worktree list ;;
  rm)
    [ -n "$name" ] || usage
    git worktree remove "$MAIN-wt-$name"
    echo "Worktree removed. Branch wt/$name kept (delete it after the merge: git branch -d wt/$name)."
    ;;
  *) usage ;;
esac
