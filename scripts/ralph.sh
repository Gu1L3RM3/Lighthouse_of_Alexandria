#!/usr/bin/env bash
# ralph.sh [max_tasks]
# Runs tasks in clean sessions, accepts only verified commits, and opens the PR at the end.
# Run it in a linked worktree (scripts/wt.sh new <name>): failed attempts are reset away.
# Every session gets HARNESS_UNATTENDED=1 and the permissions in scripts/ralph-settings.json;
# attempts that change the harness, CI or undeclared level data are rejected.
# ralph.sh status
# Shows the active run (task, attempt, elapsed time, cost versus budget), the last run's
# attempts, blocked tasks, and saved refs. Works with a dirty tree and on any branch.
# ralph.sh --plan [max_tasks]
# Planning only: runs /decide unattended for pending tasks without decided:/proposed: lines,
# accepts only new proposed: lines in TASKS.md (one commit per task), then stops. A human reviews
# and changes proposed: to decided:; the normal loop refuses tasks that still have proposed:.
# Primary variables: HARNESS_RETRIES(2), HARNESS_TASK_TIMEOUT(1800),
# HARNESS_MODEL, HARNESS_MAX_TURNS(60), HARNESS_SHIP(1).
# Cost:
#   HARNESS_BUDGET_USD     per-attempt ceiling (--max-budget-usd), default 2; empty disables.
#                          This is a client estimate, may be exceeded, and includes subagents.
#   HARNESS_RUN_BUDGET_USD entire-run ceiling (default 10, empty disables): sums summary.tsv cost_usd after each attempt and
#                          starts no further attempt or task when exhausted; the interrupted task
#                          returns to [ ] and /ship still runs (and appears in the summary).
#   An attempt without JSON (timeout, crash) uses HARNESS_BUDGET_USD as its estimated cost.
# Optional and off by default: HARNESS_EFFORT (--effort), HARNESS_CACHE_FLAG=1
# (--exclude-dynamic-system-prompt-sections). They are passed only when `claude --help` lists them.
# Blocked or discarded attempts are saved at refs/ralph/<task>/t<n>-<stamp> (see summary.tsv).
# With legacy tasks, the loop stops at the first [!] (HARNESS_CONTINUE_ON_BLOCK=1 continues).
# Explicit depends on: fields let independent ready tasks continue after a block.
# Notifications (notify-send/osascript; HARNESS_NOTIFY_CMD=<command> receives the message,
# HARNESS_NOTIFY=0 disables): blocked task, denied permission, exhausted budget, and run completion.
# A command denied by permission mode is an environment issue, not a task issue: the run stops,
# the task remains [ ], and the command appears in the summary (adjust the allowlist or prompt).
set -uo pipefail

ROOT="$(git rev-parse --show-toplevel)" || exit 1
cd "$ROOT" || exit 1

PLAN=0
if [ "${1:-}" = "--plan" ]; then
  PLAN=1
  shift
fi
MAX="${1:-5}"
RETRIES="${HARNESS_RETRIES:-2}"
TASKS="${HARNESS_TASKS:-TASKS.md}"
MODE="${HARNESS_PERMISSION_MODE:-dontAsk}"
LOG="${HARNESS_LOG_DIR:-$(git rev-parse --git-path harness-logs)}"
SUMMARY="$LOG/summary.tsv"
mkdir -p "$LOG"

die() { echo "ralph: $1" >&2; exit 1; }
STATE="$LOG/run.state"

state_get() { sed -n "s/^$1=//p" "$STATE" 2>/dev/null | tail -n1; }

show_status() {
  local pid task attempt retries started budget branch finished now cost
  echo "ralph: $ROOT (logs em $LOG)"
  pid="$(state_get pid)"
  finished="$(state_get finished)"
  if [ -n "$pid" ] && [ -z "$finished" ] && kill -0 "$pid" 2>/dev/null; then
    task="$(state_get task)" attempt="$(state_get attempt)" retries="$(state_get retries)"
    started="$(state_get started)" branch="$(state_get branch)"
    now="$(date +%s)"
    printf 'rodando: %s, tentativa %s de %s, há %dm%02ds (pid %s, branch %s)\n' \
      "$task" "$attempt" "$retries" $(( (now - started) / 60 )) $(( (now - started) % 60 )) \
      "$pid" "$branch"
  elif [ -n "$pid" ] && [ -z "$finished" ]; then
    echo "nenhuma execução em andamento (a última, pid $pid, foi interrompida)"
  else
    echo "nenhuma execução em andamento"
  fi
  if [ -f "$SUMMARY" ]; then
    cost="$(LC_ALL=C awk -F'\t' 'NR > 1 && $6 != "" { t += $6 } END { printf "%.2f", t }' "$SUMMARY")"
    budget="$(state_get budget)"
    if [ -n "$budget" ]; then echo "custo: US\$ $cost de US\$ $budget"
    else echo "custo: US\$ $cost (sem HARNESS_RUN_BUDGET_USD)"; fi
    if [ "$(wc -l < "$SUMMARY")" -gt 1 ]; then
      echo "tentativas:"
      LC_ALL=C awk -F'\t' 'NR > 1 { printf "  %-8s t%-2s %-8s US$ %5.2f  %3s turnos  %s\n",
        $2, $3, $5, $6, $7, substr($8, 1, 100) }' "$SUMMARY"
    fi
  fi
  if [ -f "$TASKS" ] && grep -qE '^[[:space:]]*- \[!\]' "$TASKS"; then
    echo "tasks travadas:"
    awk '/^[[:space:]]*- \[!\]/ { sub(/^[[:space:]]*- /, ""); print "  " substr($0, 1, 120); show = 1; next }
      show && /^[[:space:]]+(nota|note):/ { sub(/^[[:space:]]+/, ""); print "    " substr($0, 1, 160) }
      { show = 0 }' "$TASKS"
  fi
  if [ -n "$(git for-each-ref refs/ralph/ 2>/dev/null)" ]; then
    echo "refs guardados (git diff <base> <ref>; git update-ref -d <ref> depois de recuperar):"
    git for-each-ref --format='  %(refname)  %(subject)' refs/ralph/
  fi
}

if [ "${1:-}" = "status" ]; then
  show_status
  exit 0
fi

notify() {
  [ "${HARNESS_NOTIFY:-1}" = 1 ] || return 0
  local msg="[$(basename "$ROOT")] $1"
  if [ -n "${HARNESS_NOTIFY_CMD:-}" ]; then "$HARNESS_NOTIFY_CMD" "$msg" >/dev/null 2>&1
  elif command -v notify-send >/dev/null 2>&1; then notify-send "ralph" "$msg" >/dev/null 2>&1
  elif command -v osascript >/dev/null 2>&1; then
    osascript -e 'on run argv' -e 'display notification (item 1 of argv) with title "ralph"' \
      -e 'end run' "$msg" >/dev/null 2>&1
  fi
  return 0
}

write_state() {
  printf 'pid=%s\nbranch=%s\ntask=%s\nattempt=%s\nretries=%s\nstarted=%s\nbudget=%s\n' \
    "$$" "$BRANCH" "$1" "$2" "$3" "$(date +%s)" "${HARNESS_RUN_BUDGET_USD:-}" > "$STATE"
}

for required in claude git jq timeout sha256sum; do
  command -v "$required" >/dev/null 2>&1 || die "$required não encontrado no PATH"
done
[ -f "$TASKS" ] || die "$TASKS não encontrado"
[ -x scripts/verify.sh ] || die "scripts/verify.sh não é executável"
# Logs inside the worktree that are not ignored would enter snapshots and be removed by git clean.
LOG_ABS="$(cd "$LOG" && pwd -P)"
GIT_DIR_ABS="$(cd "$(git rev-parse --git-dir)" && pwd -P)"
case "$LOG_ABS/" in
  "$GIT_DIR_ABS"/*) ;;
  "$(pwd -P)"/*)
    git check-ignore -q "$LOG_ABS/summary.tsv" ||
      die "HARNESS_LOG_DIR ($LOG) está dentro da árvore; adicione-o ao .gitignore ou use outro lugar" ;;
esac

[ "$(git rev-parse --path-format=absolute --git-dir)" != "$(git rev-parse --path-format=absolute --git-common-dir)" ] ||
  die "rode em uma worktree (scripts/wt.sh new <nome>): entre tentativas o runner faz git reset --hard e git clean"
SETTINGS="$ROOT/scripts/ralph-settings.json"
[ -f "$SETTINGS" ] || die "$SETTINGS não encontrado"

BRANCH="$(git branch --show-current)"
case "$BRANCH" in
  ""|main|master) die "rode em uma branch de trabalho, nunca em ${BRANCH:-HEAD destacado}" ;;
esac
[ -z "$(git status --porcelain)" ] || die "árvore de trabalho suja; commit ou stash antes do loop"

HARNESS_BUDGET_USD="${HARNESS_BUDGET_USD-2}"
HARNESS_RUN_BUDGET_USD="${HARNESS_RUN_BUDGET_USD-10}"
# Strict: a check that cannot run (missing tool) fails instead of passing silently.
export HARNESS_UNATTENDED=1 HARNESS_STRICT=1 HARNESS_LEVEL_DATA=0

write_state preflight 0 0
trap 'printf "finished=%s\n" "$(date +%s)" >> "$STATE"' EXIT

FULL_VERIFIED="$(git rev-parse --git-path harness-full-verified)"
HEAD_AT_START="$(git rev-parse HEAD)"
if [ "$PLAN" = 0 ]; then
  if [ -f "$FULL_VERIFIED" ] && [ "$(tr -d '[:space:]' < "$FULL_VERIFIED")" = "$HEAD_AT_START" ]; then
    echo "Preflight: skipping full verification; this clean HEAD is already verified."
  else
    echo "Preflight: verificando o baseline..."
    scripts/verify.sh full ||
      die "o baseline falhou; corrija o ambiente ou a branch antes de gastar tokens"
  fi
fi

extra=(--settings "$SETTINGS")
HELP="$(claude --help 2>&1 || true)"
echo "$HELP" | grep -q -- '--max-turns' && extra+=(--max-turns "${HARNESS_MAX_TURNS:-60}")
if [ -n "${HARNESS_BUDGET_USD:-}" ] && echo "$HELP" | grep -q -- '--max-budget-usd'; then
  extra+=(--max-budget-usd "$HARNESS_BUDGET_USD")
fi
[ -n "${HARNESS_MODEL:-}" ] && extra+=(--model "$HARNESS_MODEL")
if [ -n "${HARNESS_EFFORT:-}" ] && echo "$HELP" | grep -q -- '--effort'; then
  extra+=(--effort "$HARNESS_EFFORT")
fi
if [ "${HARNESS_CACHE_FLAG:-0}" = 1 ] && echo "$HELP" | grep -q -- '--exclude-dynamic-system-prompt-sections'; then
  extra+=(--exclude-dynamic-system-prompt-sections)
fi
json_output=0
if echo "$HELP" | grep -q -- '--output-format'; then
  extra+=(--output-format json)
  json_output=1
fi

# Returns indented task metadata following the task at line $1.
task_block() {
  awk -v n="$1" 'NR > n { if ($0 ~ /^[[:space:]]+[^[:space:]]/) print; else exit }' "$TASKS"
}

# Selects the first pending task whose explicit dependencies are completed and whose DoR is ready.
# The result is "ready|line|id", or "blocked|details" when pending tasks exist but none can start.
# A task without depends on: or DoR: remains ready, preserving the legacy one-line task format.
select_ready_task() {
  awk '
    function finish_task() { current = "" }
    /^[[:space:]]*- \[[ x!]\][[:space:]]+/ {
      finish_task()
      match($0, /\[[ x!]\]/)
      state = substr($0, RSTART + 1, 1)
      rest = substr($0, RSTART + RLENGTH)
      sub(/^[[:space:]]+/, "", rest)
      split(rest, words, /[[:space:]]+/)
      current = words[1]
      status[current] = state
      line[current] = NR
      order[++count] = current
      if (state == " ") pending[current] = 1
      next
    }
    /^[[:space:]]+depends on:[[:space:]]*/ && current != "" {
      value = $0
      sub(/^[[:space:]]+depends on:[[:space:]]*/, "", value)
      gsub(/[^[:alnum:]_.-]/, " ", value)
      amount = split(value, words, /[[:space:]]+/)
      for (i = 1; i <= amount; i++) if (words[i] ~ /^T-[[:alnum:]_.-]+$/) {
        dependencies[current] = dependencies[current] " " words[i]
      }
      next
    }
    /^[[:space:]]+DoR:[[:space:]]*/ && current != "" {
      value = $0
      sub(/^[[:space:]]+DoR:[[:space:]]*/, "", value)
      sub(/[[:space:]]+$/, "", value)
      dor[current] = tolower(value)
      next
    }
    /^[^[:space:]]/ || /^$/ { finish_task() }
    END {
      pending_count = 0
      blocked = ""
      for (i = 1; i <= count; i++) {
        id = order[i]
        if (!pending[id]) continue
        pending_count++
        missing = ""
        if (id in dor && dor[id] != "ready") missing = "DoR " dor[id]
        pieces = split(dependencies[id], deps, /[[:space:]]+/)
        for (j = 1; j <= pieces; j++) if (deps[j] != "" && !(deps[j] in status && status[deps[j]] == "x")) {
          # Test membership first: reading status[...] would create the key.
          state = (deps[j] in status) ? "[" status[deps[j]] "]" : "missing"
          missing = missing (missing ? ", " : "") deps[j] " " state
        }
        if (!missing) { print "ready|" line[id] "|" id; exit }
        blocked = blocked (blocked ? "; " : "") id ": " missing
      }
      if (pending_count) print "blocked|" blocked
    }
  ' "$TASKS"
}

# Sets task_extra and TASK_RETRIES from one optional, comma-separated execution: line:
# execution: model=<name>, effort=<level>, max-turns=<integer>, retries=<integer>
configure_task_execution() {
  local block="$1" task_id="$2" execution value key raw
  local model="${HARNESS_MODEL:-}" effort="${HARNESS_EFFORT:-}"
  local max_turns="${HARNESS_MAX_TURNS:-60}"
  TASK_RETRIES="$RETRIES"
  execution="$(printf '%s\n' "$block" | sed -nE 's/^[[:space:]]+execution:[[:space:]]*//p' | head -n1)"
  if [ -n "$execution" ]; then
    IFS=',' read -r -a execution_parts <<< "$execution"
    for raw in "${execution_parts[@]}"; do
      value="$(printf '%s' "$raw" | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//')"
      case "$value" in
        model=*) model="${value#model=}"; [[ "$model" =~ ^[A-Za-z0-9._:/-]{1,100}$ ]] || die "$task_id has an invalid execution model" ;;
        effort=*) effort="${value#effort=}"; [[ "$effort" =~ ^(low|medium|high)$ ]] || die "$task_id has an invalid execution effort" ;;
        max-turns=*) max_turns="${value#max-turns=}"; [[ "$max_turns" =~ ^[1-9][0-9]{0,2}$ ]] && [ "$max_turns" -le 200 ] || die "$task_id has an invalid execution max-turns" ;;
        retries=*) TASK_RETRIES="${value#retries=}"; [[ "$TASK_RETRIES" =~ ^[1-9][0-9]?$ ]] && [ "$TASK_RETRIES" -le 10 ] || die "$task_id has an invalid execution retries" ;;
        *) die "$task_id has an invalid execution override: $value" ;;
      esac
    done
  fi
  task_extra=(--settings "$SETTINGS")
  echo "$HELP" | grep -q -- '--max-turns' && task_extra+=(--max-turns "$max_turns")
  if [ -n "${HARNESS_BUDGET_USD:-}" ] && echo "$HELP" | grep -q -- '--max-budget-usd'; then
    task_extra+=(--max-budget-usd "$HARNESS_BUDGET_USD")
  fi
  [ -n "$model" ] && task_extra+=(--model "$model")
  if [ -n "$effort" ] && echo "$HELP" | grep -q -- '--effort'; then
    task_extra+=(--effort "$effort")
  fi
  if [ "${HARNESS_CACHE_FLAG:-0}" = 1 ] && echo "$HELP" | grep -q -- '--exclude-dynamic-system-prompt-sections'; then
    task_extra+=(--exclude-dynamic-system-prompt-sections)
  fi
  [ "$json_output" = 1 ] && task_extra+=(--output-format json)
}

printf 'timestamp\ttask\tattempt\tseconds\tresult\tcost_usd\tturns\treason\tcommit\trecovery_ref\n' > "$SUMMARY"
done_n=0
blocked_n=0
START="$(git rev-parse --short HEAD)"

record_attempt() {
  local task="$1" attempt="$2" seconds="$3" result="$4" output="$5"
  local reason="${6:-}" commit="${7:-}" ref="${8:-}"
  local cost="" turns=""
  if [ "$json_output" = 1 ] && jq -e . "$output" >/dev/null 2>&1; then
    cost="$(jq -r '.total_cost_usd // empty' "$output")"
    turns="$(jq -r '.num_turns // empty' "$output")"
  fi
  if [ -z "$cost" ] && [ "$json_output" = 1 ]; then
    # Without JSON (timeout, crash), actual spend is unknown; use the attempt ceiling.
    if [ -n "${HARNESS_BUDGET_USD:-}" ]; then
      cost="$HARNESS_BUDGET_USD"
      reason="${reason:+$reason; }custo estimado (sem JSON)"
    else
      reason="${reason:+$reason; }custo desconhecido (sem JSON)"
    fi
  fi
  reason="$(printf '%s' "$reason" | tr '\t\n' '  ' | cut -c1-200)"
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
    "$(date -Iseconds)" "$task" "$attempt" "$seconds" "$result" "$cost" "$turns" \
    "$reason" "$commit" "$ref" >> "$SUMMARY"
}

# Saves everything an attempt produced (commits since $base plus tracked and untracked changes)
# in refs/ralph/<task>/t<attempt>-<stamp>, without touching the index or worktree.
# Prints the created ref (empty if there was nothing). Never overwrites an existing ref.
preserve_attempt() {
  local task="$1" attempt="$2" reason="$3" base="$4"
  local head index tree snapshot ref candidate n=1
  head="$(git rev-parse HEAD)" || return 1
  index="$(git rev-parse --git-path "ralph-index.$$")"
  rm -f "$index"
  GIT_INDEX_FILE="$index" git read-tree "$head" &&
    GIT_INDEX_FILE="$index" git add -A &&
    tree="$(GIT_INDEX_FILE="$index" git write-tree)" || { rm -f "$index"; return 1; }
  rm -f "$index"
  # The [!] marker and note in TASKS.md are not recoverable work: mark_blocked recreates them.
  if git diff --quiet "$base" "$tree" -- . ":(exclude)$TASKS"; then
    return 0
  fi
  snapshot="$(printf 'ralph: %s t%s preservada\n\n%s\n' "$task" "$attempt" "$reason" |
    git commit-tree "$tree" -p "$head")" || return 1
  ref="refs/ralph/$task/t$attempt-$(date +%Y%m%d%H%M%S)"
  candidate="$ref"
  while git show-ref --verify -q "$candidate"; do
    n=$((n + 1))
    candidate="$ref-$n"
  done
  # An empty old value makes update-ref fail when the ref already exists.
  git update-ref "$candidate" "$snapshot" "" || return 1
  echo "$candidate"
}

# Saves the attempt in recovery_ref. If it cannot be saved, stop the loop: never discard work
# without a copy. After recording it, reset_to_base discards the worktree.
preserve_or_die() {
  local task="$1" attempt="$2" reason="$3" base="$4"
  recovery_ref="$(preserve_attempt "$task" "$attempt" "$reason" "$base")" ||
    die "não consegui preservar a tentativa $attempt de $task; a árvore ficou como está"
  [ -z "$recovery_ref" ] || echo "   trabalho preservado em $recovery_ref"
}

reset_to_base() {
  git reset -q --hard "$1" && git clean -fdq
}

# Indented lines the agent added to TASKS.md (the [!] note), in any position.
agent_note() {
  git diff -U0 "$1" -- "$TASKS" | sed -n 's/^+\([[:space:]]\{1,\}[^[:space:]].*\)$/\1/p' |
    sed -E 's/^[[:space:]]+((note|nota|reason|motivo):[[:space:]]*)?//' |
    awk 'NR > 1 { printf "; " } { printf "%s", $0 }'
}

# Commands permission mode denied during the session (the first line of each), separated by " | ".
denied_commands() {
  jq -r '[.permission_denials[]? | (.tool_input.command // .tool_name // "?") | tostring
    | split("\n")[0]] | unique | join(" | ")' "$1" 2>/dev/null | cut -c1-300
}

# Files an unattended attempt must never change, compared with its base commit. Checked
# here, not only in the guard hook, because a shell command could get past a hook.
forbidden_changes() {
  local pattern='^(\.claude/|scripts/|\.github/|ruff\.toml$)'
  [ "$HARNESS_LEVEL_DATA" = 1 ] || pattern="$pattern|^(code/circuitos/|assets/maps/)"
  git diff --name-only "$1" HEAD | grep -E "$pattern" | paste -sd ' ' -
}

run_cost() {
  LC_ALL=C awk -F'\t' 'NR > 1 && $6 != "" { total += $6 } END { printf "%.4f", total }' "$SUMMARY"
}

run_budget_exceeded() {
  [ -n "${HARNESS_RUN_BUDGET_USD:-}" ] &&
    LC_ALL=C awk -v spent="$(run_cost)" -v cap="$HARNESS_RUN_BUDGET_USD" 'BEGIN { exit !(spent >= cap) }'
}

mark_blocked() {
  local base="$1" line="$2" reason="$3"
  [ -z "$(git status --porcelain)" ] && [ "$(git rev-parse HEAD)" = "$base" ] ||
    die "mark_blocked chamado com trabalho não preservado"
  sed -i "${line}s/\[ \]/[!]/" "$TASKS"
  # ENVIRON (rather than sed a\ or awk -v) preserves the literal note, including backslashes.
  NOTE="  nota: $reason" awk -v n="$line" '{ print } NR == n { print ENVIRON["NOTE"] }' \
    "$TASKS" > "$TASKS.ralph" && mv "$TASKS.ralph" "$TASKS"
  git add "$TASKS"
  git commit -q -m "chore: mark task as needing human input"
}

budget_note=""
env_stop=""
stop_for_budget() {
  budget_note="orçamento da execução esgotado (US\$ $(run_cost) de US\$ $HARNESS_RUN_BUDGET_USD)"
  echo "Parando: $budget_note; não começo outra tentativa nem task."
  notify "$budget_note"
  [ "$done_n" -eq 0 ] || [ "${HARNESS_SHIP:-1}" != 1 ] ||
    echo "O /ship-branch ainda roda para as $done_n task(s) já feitas."
}

# "<line> <ID>" for each pending task without decided:/proposed: lines.
undecided_tasks() {
  awk 'function flush() { if (cand && !has) print cand, id; cand = 0 }
    /^[[:space:]]*- \[/ { flush(); if ($0 ~ /^[[:space:]]*- \[ \]/) { cand = NR; has = 0; id = $4 }; next }
    /^[[:space:]]+(decided|proposed):/ { has = 1; next }
    /^[^[:space:]]/ || /^$/ { flush() }
    END { flush() }' "$TASKS"
}

if [ "$PLAN" = 1 ]; then
  tried=" "
  planned_n=0
  for ((i = 1; i <= MAX; i++)); do
    if run_budget_exceeded; then
      stop_for_budget
      break
    fi
    # Each task is attempted once per run, even when it remains without metadata.
    hit="$(undecided_tasks | while read -r n id; do
      case "$tried" in *" $id "*) ;; *) echo "$n $id"; break ;; esac
    done)"
    [ -n "$hit" ] || { echo "Nenhuma task [ ] sem linhas decided:/proposed:."; break; }
    num="${hit%% *}"
    task_id="${hit#* }"
    tried="$tried$task_id "
    task_line="$(sed -n "${num}p" "$TASKS")"
    base="$(git rev-parse HEAD)"
    echo "== [plano $i/$MAX] $task_id"
    write_state "$task_id (plano)" 1 1

    stamp="$(date +%Y%m%d-%H%M%S)-${task_id}-plan"
    output="$LOG/$stamp.json"
    errors="$LOG/$stamp.err"
    prompt="Siga .claude/skills/decide/SKILL.md para esta task EXATA (linha $num de $TASKS): $task_line
Execução sem supervisão: não pergunte nada, escreva só linhas proposed: (com a alternativa de cada questão aberta), não implemente nada e não faça commit; o runner confere o diff e commita.
Use só Read/Grep/Glob/Edit/Write para arquivos; no Bash, um comando por vez da allowlist, sem |, &&, ;, redirecionamento ou heredoc."
    started="$(date +%s)"
    timeout "${HARNESS_TASK_TIMEOUT:-1800}" claude -p "$prompt" --permission-mode "$MODE" "${extra[@]}" >"$output" 2>"$errors"
    claude_rc=$?
    seconds=$(( $(date +%s) - started ))

    changed="$( { git diff --name-only "$base"; git ls-files --others --exclude-standard; } | sort -u)"
    added="$(git diff -U0 "$base" -- "$TASKS" | grep -E '^\+[^+]' || true)"
    failure=""
    if [ "$claude_rc" -eq 124 ]; then
      failure="timeout após ${HARNESS_TASK_TIMEOUT:-1800}s"
    elif [ "$claude_rc" -ne 0 ]; then
      failure="Claude terminou com exit $claude_rc"
    elif [ -n "$changed" ] && [ "$changed" != "$TASKS" ]; then
      failure="mudou arquivos além de $TASKS: $(echo "$changed" | grep -vxF "$TASKS" | paste -sd ' ' -)"
    elif echo "$added" | grep -qE '^\+[[:space:]]*- \[[x!]\]|^\+[[:space:]]+decided:'; then
      failure="marcou task ou escreveu decided: sem revisão humana"
    elif ! echo "$added" | grep -qE '^\+[[:space:]]+proposed:'; then
      failure="nenhuma linha proposed: nova em $TASKS"
    fi

    if [ -z "$failure" ]; then
      git reset -q --soft "$base"
      git add "$TASKS"
      git commit -q -m "docs(tasks): propose decisions for $task_id"
      record_attempt "$task_id" 1 "$seconds" planned "$output" "" "$(git rev-parse HEAD)" ""
      planned_n=$((planned_n + 1))
      echo "   linhas proposed: commitadas."
    else
      echo "   plano descartado: $failure"
      head_commit="$(git rev-parse HEAD)"
      [ "$head_commit" != "$base" ] || head_commit=""
      preserve_or_die "$task_id" 1 "$failure" "$base"
      record_attempt "$task_id" 1 "$seconds" failed "$output" "$failure" "$head_commit" "$recovery_ref"
      reset_to_base "$base"
    fi
  done
  echo "Resumo do plano: $planned_n task(s) com linhas proposed:."
  notify "ralph --plan terminou: $planned_n task(s) com linhas proposed:; US\$ $(run_cost)"
  [ -z "$budget_note" ] || echo "Parou por $budget_note."
  echo "Custo: US\$ $(run_cost). Métricas: $SUMMARY"
  echo "Revise: git diff $START..HEAD -- $TASKS; troque proposed: por decided: (ou rode /decide <ID>)."
  exit 0
fi

for ((i = 1; i <= MAX; i++)); do
  if run_budget_exceeded; then
    stop_for_budget
    break
  fi
  selection="$(select_ready_task)"
  [ -n "$selection" ] || { echo "Sem tasks pendentes em $TASKS."; break; }
  if [[ "$selection" = blocked\|* ]]; then
    die "pending tasks have unmet or missing dependencies: ${selection#blocked|}"
  fi
  IFS='|' read -r _ num task_id <<< "$selection"
  task_line="$(sed -n "${num}p" "$TASKS")"

  [ -z "$(git status --porcelain)" ] || die "árvore suja antes de $task_id"
  block="$(task_block "$num")"
  if echo "$block" | grep -qE '^[[:space:]]+proposed:'; then
    die "$task_id tem linhas proposed: não revisadas; troque por decided: (ou rode /decide $task_id) antes do loop"
  fi
  configure_task_execution "$block" "$task_id"
  if echo "$block" | grep -qiE '^[[:space:]]+level-data:[[:space:]]*yes[[:space:]]*$'; then
    HARNESS_LEVEL_DATA=1
  else
    HARNESS_LEVEL_DATA=0
  fi
  base="$(git rev-parse HEAD)"
  echo "== [$i/$MAX] $task_id"
  echo "$block" | grep -qE '^[[:space:]]+decided:' ||
    echo "   aviso: $task_id sem linhas decided:; o agente pode parar pedindo decisão (veja ralph.sh --plan)"

  ok=0
  previous_failure=""
  previous_signature=""
  attempts_used=0
  for ((attempt = 1; attempt <= TASK_RETRIES; attempt++)); do
    if [ "$attempt" -gt 1 ] && run_budget_exceeded; then
      stop_for_budget
      ok=3
      break
    fi
    attempts_used="$attempt"
    write_state "$task_id" "$attempt" "$TASK_RETRIES"
    stamp="$(date +%Y%m%d-%H%M%S)-${task_id}-t${attempt}"
    output="$LOG/$stamp.json"
    errors="$LOG/$stamp.err"
    prompt="Siga .claude/skills/task/SKILL.md para esta task EXATA (linha $num de $TASKS): $task_line
Não escolha outra task. Rode apenas os testes focados e scripts/verify.sh fast; o runner fará o full final. Se precisar de decisão humana, marque [!] e pare.
Sessão sem supervisão: leia, procure e altere arquivos só com as ferramentas Read/Grep/Glob/Edit/Write. No Bash, rode um comando por vez da allowlist (git, os comandos de teste/lint do projeto, scripts/verify.sh), sem |, &&, ;, redirecionamento ou heredoc; qualquer outro comando é negado."
    if [ -n "$previous_failure" ]; then
      prompt="$prompt

A tentativa anterior foi descartada. Não repita a mesma estratégia. Evidência final:
${previous_failure:0:4000}"
    fi

    started="$(date +%s)"
    timeout "${HARNESS_TASK_TIMEOUT:-1800}" claude -p "$prompt" --permission-mode "$MODE" "${task_extra[@]}" >"$output" 2>"$errors"
    claude_rc=$?
    seconds=$(( $(date +%s) - started ))
    marker="$(sed -n "${num}p" "$TASKS")"
    head_commit="$(git rev-parse HEAD)"
    [ "$head_commit" != "$base" ] || head_commit=""

    denied="$(denied_commands "$output")"
    if [ -n "$denied" ] && ! echo "$marker" | grep -qE '^[[:space:]]*- \[x\]'; then
      reason="permissão negada: $denied"
      preserve_or_die "$task_id" "$attempt" "$reason" "$base"
      record_attempt "$task_id" "$attempt" "$seconds" denied "$output" \
        "$reason" "$head_commit" "$recovery_ref"
      reset_to_base "$base"
      env_stop="$reason"
      notify "$task_id parou: $reason"
      ok=4
      break
    fi

    if echo "$marker" | grep -qE '^[[:space:]]*- \[!\]'; then
      reason="$(agent_note "$base")"
      [ -n "$reason" ] || reason="o agente pediu uma decisão humana"
      preserve_or_die "$task_id" "$attempt" "$reason" "$base"
      record_attempt "$task_id" "$attempt" "$seconds" blocked "$output" \
        "$reason" "$head_commit" "$recovery_ref"
      reset_to_base "$base"
      mark_blocked "$base" "$num" "$reason; veja $errors${recovery_ref:+; trabalho em $recovery_ref}"
      notify "$task_id travou: $reason"
      blocked_n=$((blocked_n + 1))
      ok=2
      break
    fi

    failure=""
    if [ "$claude_rc" -eq 124 ]; then
      failure="timeout após ${HARNESS_TASK_TIMEOUT:-1800}s"
    elif [ "$claude_rc" -ne 0 ]; then
      failure="Claude terminou com exit $claude_rc"
    elif ! echo "$marker" | grep -qE '^[[:space:]]*- \[x\]'; then
      failure="o agente não marcou a task como concluída"
    elif [ -n "$(git status --porcelain)" ]; then
      failure="o agente deixou mudanças sem commit"
    elif [ "$(git rev-parse HEAD)" = "$base" ]; then
      failure="o agente não criou o commit da task"
    elif protected="$(forbidden_changes "$base")" && [ -n "$protected" ]; then
      failure="mudou arquivos protegidos: $protected"
    else
      verify_log="$LOG/$stamp-verify.log"
      if scripts/verify.sh full >"$verify_log" 2>&1; then
        git rev-parse HEAD > "$FULL_VERIFIED"
        record_attempt "$task_id" "$attempt" "$seconds" passed "$output" "" "$head_commit" ""
        ok=1
        break
      fi
      failure="verify full falhou:"$'\n'"$(tail -n 30 "$verify_log")"
    fi

    evidence="$(jq -r '.result // .error // empty' "$output" 2>/dev/null || true)"
    [ -n "$evidence" ] || evidence="$(tail -n 30 "$errors" 2>/dev/null)"
    previous_failure="$failure
$evidence"
    signature="$(printf '%s' "$previous_failure" | sha256sum | cut -d' ' -f1)"
    echo "   tentativa $attempt falhou: ${failure%%$'\n'*}"
    preserve_or_die "$task_id" "$attempt" "${failure%%$'\n'*}" "$base"
    record_attempt "$task_id" "$attempt" "$seconds" failed "$output" \
      "${failure%%$'\n'*}" "$head_commit" "$recovery_ref"
    reset_to_base "$base"

    if [ -n "$previous_signature" ] && [ "$signature" = "$previous_signature" ]; then
      echo "   mesma falha repetida; não gastarei outra tentativa."
      break
    fi
    previous_signature="$signature"
  done

  if [ "$ok" = 1 ]; then
    done_n=$((done_n + 1))
    echo "   OK."
  elif [ "$ok" = 3 ]; then
    echo "   $task_id continua [ ] para a próxima execução."
    break
  elif [ "$ok" = 4 ]; then
    echo "   Parando: $env_stop"
    echo "   $task_id continua [ ]; ajuste a allowlist (.claude/settings.json) ou o prompt e rode de novo."
    break
  elif [ "$ok" = 0 ]; then
    mark_blocked "$base" "$num" "loop desistiu após $attempts_used tentativa(s); veja $SUMMARY"
    notify "$task_id travou: loop desistiu após $attempts_used tentativa(s)"
    blocked_n=$((blocked_n + 1))
    echo "   marcada [!]."
  fi
  if [ "$ok" != 1 ] && [ "${HARNESS_CONTINUE_ON_BLOCK:-0}" != 1 ]; then
    if grep -qE '^[[:space:]]+depends on:' "$TASKS"; then
      echo "   $task_id is blocked; continuing with independent tasks whose dependencies are satisfied."
    else
      echo "   Parando: as próximas tasks dependem de $task_id (HARNESS_CONTINUE_ON_BLOCK=1 seguiria)."
      break
    fi
  fi
done

ship_result="não solicitado"
if [ "$done_n" -gt 0 ] && [ "${HARNESS_SHIP:-1}" = 1 ]; then
  echo "Fechando a branch com /ship-branch..."
  write_state ship 1 1
  HARNESS_LEVEL_DATA=0
  ship_log="$LOG/$(date +%Y%m%d-%H%M%S)-ship.json"
  started="$(date +%s)"
  timeout "${HARNESS_SHIP_TIMEOUT:-1800}" claude -p \
    "Siga .claude/skills/ship-branch/SKILL.md para fechar esta branch e abrir o PR. Não faça merge." \
    --permission-mode "$MODE" "${extra[@]}" >"$ship_log" 2>"${ship_log%.json}.err"
  ship_rc=$?
  if [ "$ship_rc" -eq 0 ]; then ship_result="concluído"; else ship_result="falhou; veja $ship_log"; fi
  record_attempt ship 1 "$(( $(date +%s) - started ))" \
    "$([ "$ship_rc" -eq 0 ] && echo shipped || echo failed)" "$ship_log"
fi

echo "Resumo: $done_n feitas, $blocked_n travadas; ship $ship_result."
notify "ralph terminou: $done_n feitas, $blocked_n travadas; US\$ $(run_cost); ship $ship_result"
[ -z "$budget_note" ] || echo "Parou por $budget_note."
echo "Custo: US\$ $(run_cost). Métricas: $SUMMARY"
echo "Revise: git log --oneline $START..HEAD"
[ -z "$env_stop" ] || exit 1
