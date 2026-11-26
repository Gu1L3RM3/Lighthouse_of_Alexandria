#!/usr/bin/env bash
# PreToolUse: exit 2 blocks the action and hands the reason back to Claude.
# Irreversible and risky actions stay with the human.
# HARNESS_UNATTENDED=1 (set by ralph.sh) adds: no releases, no edits to the harness
# or CI, and level data only when the task allows it (HARNESS_LEVEL_DATA=1).
# This is a regex safety net, not a sandbox.
INPUT=$(cat) || exit 2
command -v jq >/dev/null 2>&1 || { echo "BLOCKED: guard.sh needs jq (sudo apt install jq)." >&2; exit 2; }
TOOL=$(echo "$INPUT" | jq -r '.tool_name // empty')
ROOT="${CLAUDE_PROJECT_DIR:-$PWD}"
UNATTENDED="${HARNESS_UNATTENDED:-0}"

block() { echo "BLOCKED: $1" >&2; exit 2; }
# Start of a command: line start or after ; & | ( $( and prefixes such as sudo, env, VAR=...
CMD_START='(^|[;&|(]|\$\()[[:space:]]*((sudo|env|time|nohup|command|exec)[[:space:]]+|[A-Za-z_][A-Za-z0-9_]*=[^[:space:]]*[[:space:]]+)*'
GIT='([^[:space:];&|()]*/)?git([[:space:]]+-[Cc][[:space:]]+[^[:space:]]+)*[[:space:]]+'

check_path() {
  local file relative pattern
  file="$(realpath -m -- "$1")"
  # Patterns apply to the path inside the project, so a checkout that happens to
  # live under .claude/ or build/ is not blocked as a whole.
  case "$file" in
    "$(realpath -m -- "$ROOT")"/*) relative="${file#"$(realpath -m -- "$ROOT")"/}" ;;
    *) relative="${file#/}" ;;
  esac
  [ "$(basename "$file")" = ".env.example" ] && return 0
  while IFS= read -r pattern; do
    case "$pattern" in ''|'#'*) continue ;; esac
    # shellcheck disable=SC2254
    case "/$relative" in
      $pattern) block "$relative matches '$pattern' (.claude/protected-paths). Stop and ask the human." ;;
    esac
  done <"$ROOT/.claude/protected-paths"
  [ "$UNATTENDED" = 1 ] || return 0
  case "$relative" in
    .claude/*|scripts/*|.github/*|ruff.toml)
      block "unattended sessions cannot change the harness or CI ($relative). Mark the task [!]." ;;
    code/circuitos/*|assets/maps/*)
      [ "${HARNESS_LEVEL_DATA:-0}" = 1 ] ||
        block "level data ($relative) needs 'level-data: yes' in the task. Mark the task [!]." ;;
  esac
}

case "$TOOL" in
  Edit|Write|MultiEdit|NotebookEdit)
    F=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.notebook_path // empty')
    [ -z "$F" ] || check_path "$F"
    ;;
  Bash)
    C=$(echo "$INPUT" | jq -r '.tool_input.command // empty')
    # Shell indirection hides the real command: refuse a push behind eval, xargs or sh -c.
    if echo "$C" | grep -qE '(^|[;&|[:space:]])(eval|xargs|((ba|z)?sh[[:space:]]+-c))([[:space:]]|$)' \
      && echo "$C" | grep -qE '([^[:space:]]*/)?git[[:space:]]+push'; then
      block "indirect git push (--force cannot be ruled out). Run an explicit push."
    fi
    # A heredoc body is data (git commit -F - <<'EOF') unless it feeds a shell.
    # After that, quoted text such as -m "..." is data too.
    S=$(echo "$C" | awk '
      skip { if ($0 ~ "^[ \t]*" tag "[ \t]*$") skip = 0; next }
      {
        print
        if (match($0, /<<-?[ \t]*["\x27]?[A-Za-z_][A-Za-z0-9_]*/)) {
          t = substr($0, RSTART, RLENGTH); sub(/^<<-?[ \t]*["\x27]?/, "", t)
          if ($0 !~ /(^|[;&|( \t])(bash|sh|zsh|ssh)[ \t][^<]*<</ && $0 !~ /(^|[;&|( \t])(bash|sh|zsh)[ \t]*<</) { tag = t; skip = 1 }
        }
      }' | sed -E "s/'[^']*'//g; s/\"[^\"]*\"//g")
    if echo "$S" | grep -qE "${CMD_START}${GIT}push\b"; then
      P=$(echo "$S" | grep -oE 'push\b[^;&|)]*' | head -1)
      echo "$P" | grep -qE -- '(--force|--mirror|[[:space:]]-[a-zA-Z]*f[a-zA-Z]*([[:space:]]|$)|[[:space:]]\+[^[:space:]]+)' && block "git push --force, never."
      echo "$P" | grep -qE -- '[[:space:]](--all|--branches)([[:space:]]|$)' && block "git push --all includes main; push only the work branch."
      echo "$P" | grep -qE '[[:space:]:](refs/heads/)?main([[:space:]]|$)' && block "never push to main: merging there publishes a release, through a PR."
      # Without an explicit refspec the current branch is pushed.
      if ! echo "$P" | grep -qE '^push([[:space:]]+-[^[:space:]]+)*[[:space:]]+[^-[:space:]][^[:space:]]*[[:space:]]+[^-[:space:]]'; then
        [ "$(git -C "$ROOT" branch --show-current 2>/dev/null)" = main ] && block "you are on main: never push to main."
      fi
    fi
    # The tree often holds the owner's experiments (level data, figures): stage by name.
    echo "$S" | grep -qE "${CMD_START}${GIT}add\b[^;&|]*[[:space:]](-[a-zA-Z]*[Au][a-zA-Z]*|--all|--update|\.|:/|\*)([[:space:]]|$|[;&|])" &&
      block "stage files by name (git add path ...), never everything at once."
    echo "$S" | grep -qE "${CMD_START}${GIT}commit\b[^;&|]*[[:space:]](-[a-zA-Z]*a[a-zA-Z]*|--all)([[:space:]]|$|[;&|])" &&
      block "git commit -a stages every tracked change; add files by name."
    if [ "$UNATTENDED" = 1 ]; then
      echo "$S" | grep -qE "${CMD_START}(gh[[:space:]]+(pr[[:space:]]+merge|release|workflow[[:space:]]+run)|${GIT}tag\b)" &&
        block "merging, tagging and releasing are the human's decision."
    fi
    echo "$S" | grep -qE 'rm[[:space:]]+-[a-zA-Z]+[[:space:]]+(/|~|\$HOME)([[:space:]]|$)' && block "recursive rm on / or home."
    echo "$S" | grep -qE '(curl|wget)[^|]*\|[[:space:]]*(sudo[[:space:]]+)?(ba)?sh' && block "no curl | sh."
    ;;
esac
exit 0
