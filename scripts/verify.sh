#!/usr/bin/env bash
# verify.sh [fast|full|web]: the one judge of "done", quiet unless something fails.
#   fast  lint (real errors only) + unit tests; runs in the Stop hook, takes seconds
#   full  fast + boot every scene + harness tests and web check when those areas changed
#   web   only the browser check of the web build
#   web-needed  exit 0 if web code changed since the base (used by CI), 1 otherwise
# Env: HARNESS_STRICT=1 fails on skipped checks (CI, unattended runs);
#      HARNESS_BASE overrides the ref used to find changed files (default origin/main);
#      HARNESS_PYTHON overrides the interpreter.
set -u
LEVEL="${1:-full}"
case "$LEVEL" in fast|full|web|web-needed) ;; *) echo "usage: verify.sh [fast|full|web|web-needed]" >&2; exit 2 ;; esac
ROOT="$(git rev-parse --show-toplevel)" || exit 1
cd "$ROOT" || exit 1

WEB_PATHS='^(main\.py|web/|pygbag\.ini|requirements-e2e\.txt|scripts/(web_smoke|sandbox)\.py|code/game\.py|code/core/(touch_[a-z_]*|web_storage_sync|settings)\.py|code/core/managers/input_manager\.py|code/core/ui/)'
HARNESS_PATHS='^(scripts/|\.claude/)'

find_python() {
  if [ -n "${HARNESS_PYTHON:-}" ]; then echo "$HARNESS_PYTHON"; return; fi
  # Worktrees have no .venv of their own: fall back to the main checkout's.
  local main_checkout
  main_checkout="$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")"
  for candidate in "$ROOT/.venv/bin/python" "$main_checkout/.venv/bin/python"; do
    [ -x "$candidate" ] && { echo "$candidate"; return; }
  done
  echo python3
}
PY="$(find_python)"
export SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYTHONDONTWRITEBYTECODE=1

LOG="$(mktemp)"
trap 'rm -f "$LOG"' EXIT
skipped=0

has_modules() { "$PY" -c "import $1" >/dev/null 2>&1; }

skip() {
  echo "SKIPPED $1: $2"
  skipped=$((skipped + 1))
}

step() {
  local name="$1"
  shift
  if ! timeout "${VERIFY_TIMEOUT:-600}" "$@" >"$LOG" 2>&1; then
    echo "verify($LEVEL) FAILED at $name: $*"
    tail -n "${VERIFY_TAIL:-60}" "$LOG"
    exit 1
  fi
  grep -E '^(SKIPPED|smoke:|web:)' "$LOG" || true
}

changed_files() {
  local base
  base="$(git merge-base "${HARNESS_BASE:-origin/main}" HEAD 2>/dev/null)" || base=""
  # Without a base every file counts as changed, so no check is silently dropped.
  if [ -z "$base" ]; then git ls-files; else git diff --name-only "$base"; fi
  git ls-files --others --exclude-standard
}

# Not `grep -q`: quitting early would close the pipe on the writer.
touched() { changed_files | grep -E "$1" >/dev/null; }

if [ "$LEVEL" = web-needed ]; then
  touched "$WEB_PATHS"
  exit $?
fi

lint() {
  if has_modules ruff; then step lint "$PY" -m ruff check --quiet .
  else skip lint "ruff is not installed (pip install -r requirements-dev.txt)"; fi
}

web_check() {
  if has_modules "playwright, pygbag"; then step web "$PY" scripts/web_smoke.py
  else skip web "playwright/pygbag are not installed (pip install -r requirements-e2e.txt)"; fi
}

if [ "$LEVEL" = web ]; then
  web_check
else
  lint
  step tests "$PY" -m unittest discover -s code/tests
fi

if [ "$LEVEL" = full ]; then
  step scenes "$PY" scripts/smoke_scenes.py
  if touched "$HARNESS_PATHS"; then
    if has_modules pytest; then step harness "$PY" -m pytest -q scripts/tests
    else skip harness "pytest is not installed (pip install -r requirements-dev.txt)"; fi
  fi
  if touched "$WEB_PATHS"; then web_check; fi
fi

if [ "$skipped" -gt 0 ]; then
  if [ "${HARNESS_STRICT:-0}" = 1 ]; then
    echo "verify($LEVEL) FAILED: $skipped check(s) skipped in strict mode"
    exit 1
  fi
  echo "verify($LEVEL) OK, but $skipped check(s) did not run"
  exit 0
fi
# Remember a full pass of a clean HEAD so ship-branch does not repeat it.
if [ "$LEVEL" = full ] && [ -z "$(git status --porcelain)" ]; then
  git rev-parse HEAD >"$(git rev-parse --git-path harness-full-verified)"
fi
echo "verify($LEVEL) OK"
