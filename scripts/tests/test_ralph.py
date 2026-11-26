import os
import stat
import subprocess
from pathlib import Path

RALPH = Path(__file__).resolve().parents[1] / "ralph.sh"


def write_executable(path: Path, content: str) -> None:
    path.write_text(content)
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


TASKS = (
    "- [ ] T-01 small task — done when: test passes\n"
    "- [ ] T-02 next task — done when: test passes\n"
)


def make_repo(
    tmp_path: Path, mode: str, tasks: str = TASKS
) -> tuple[Path, dict[str, str], Path, Path]:
    main_checkout = tmp_path / "main"
    repo = main_checkout
    fake_bin = tmp_path / "bin"
    logs = tmp_path / "logs"
    calls = tmp_path / "claude-calls"
    verify_count = tmp_path / "verify-count"
    (repo / "scripts").mkdir(parents=True)
    fake_bin.mkdir()

    (repo / "TASKS.md").write_text(tasks)
    (repo / "README.md").write_text("original\n")
    write_executable(
        repo / "scripts" / "verify.sh",
        """#!/usr/bin/env bash
# A question, not a check: it does not count as a verification run.
if [ "$1" = security-needed ]; then [ -n "${FAKE_SECURITY_NEEDED:-}" ]; exit; fi
count=0
[ ! -f "$VERIFY_COUNT_FILE" ] || count=$(cat "$VERIFY_COUNT_FILE")
count=$((count + 1))
echo "$count" > "$VERIFY_COUNT_FILE"
if [ -n "${VERIFY_FAIL_FROM:-}" ] && [ "$count" -ge "$VERIFY_FAIL_FROM" ]; then
  printf 'E first failing line\nE second failing line\n'
  exit 1
fi
echo "verify($1) OK"
""",
    )
    write_executable(
        fake_bin / "claude",
        """#!/usr/bin/env bash
if [ "${1:-}" = "--help" ]; then
  echo "--max-turns --max-budget-usd --output-format --effort"
  echo "--exclude-dynamic-system-prompt-sections"
  exit 0
fi
printf '%s\n' "$*" >> "$CLAUDE_CALLS_FILE"
if printf '%s' "$*" | grep -q 'web-security/SKILL.md'; then
  case "${FAKE_SECURITY:-pass}" in
    pass) verdict="$(printf 'No findings.\\nSECURITY: PASS')" ;;
    blocked) verdict="$(printf 'site/index.html: XSS\\nSECURITY: BLOCKED')" ;;
    missing) verdict='Looks fine to me.' ;;
    buried) verdict="$(printf 'SECURITY: PASS\\nBut one page could not be reviewed.')" ;;
    edit) echo patched > patched.txt; verdict='SECURITY: PASS' ;;
    crash) exit 1 ;;
  esac
  jq -cn --arg result "$verdict" '{result: $result, total_cost_usd: 0.07, num_turns: 6}'
  exit 0
fi
echo "unattended=${HARNESS_UNATTENDED:-} strict=${HARNESS_STRICT:-} level=${HARNESS_LEVEL_DATA:-}" >> "$CLAUDE_ENV_FILE"
task="$(printf '%s' "$*" | grep -oE 'T-[0-9]+' | head -n1)"
[ -n "$task" ] || { echo '{"result":"shipped","total_cost_usd":0.03}'; exit 0; }  # /ship
{ echo "== $task"; git status --porcelain; ls; } >> "$CLAUDE_SEEN_FILE"
if printf '%s' "$*" | grep -q 'decide/SKILL.md'; then  # ralph --plan
  case "${FAKE_PLAN:-ok}" in
    ok|other)
      PROPOSED="  proposed: $task uses the stdlib (alternative: a new dependency)" \\
        awk -v t="$task" '{ print } index($0, t) && /- \\[ \\]/ { print ENVIRON["PROPOSED"] }' \\
        TASKS.md > TASKS.md.new && mv TASKS.md.new TASKS.md ;;
  esac
  [ "${FAKE_PLAN:-ok}" != other ] || echo "code" > other.txt
  echo '{"result":"proposed","total_cost_usd":0.05,"num_turns":4}'
  exit 0
fi
# Hold the session open until the test releases it (to observe a run in progress).
while [ -n "${FAKE_HOLD_UNTIL:-}" ] && [ ! -f "$FAKE_HOLD_UNTIL" ]; do sleep 0.05; done
mode_var="FAKE_MODE_${task//-/_}"
mode="${!mode_var:-$FAKE_CLAUDE_MODE}"
if [ -n "${FAKE_COMMIT:-}" ] && [ "$mode" != success ]; then
  echo "committed by $task" > committed.txt
  git add committed.txt
  git commit -q -m "feat($task): partial work"
fi
if [ -n "${FAKE_DIRTY:-}" ] && [ "$mode" != success ]; then
  echo "edited by $task" >> README.md
fi
if [ -n "${FAKE_UNTRACKED:-}" ] && [ "$mode" != success ]; then
  echo "untracked by $task" > untracked.txt
fi
case "$mode" in
  success)
    sed -i "/$task/s/\\[ \\]/[x]/" TASKS.md
    echo implemented > result.txt
    git add TASKS.md result.txt
    if [ -n "${FAKE_TOUCH:-}" ]; then
      mkdir -p "$(dirname "$FAKE_TOUCH")"; echo tampered >> "$FAKE_TOUCH"; git add "$FAKE_TOUCH"
    fi
    [ -z "${FAKE_MOVE:-}" ] || git mv "$FAKE_MOVE" moved-away
    git commit -q -m "feat($task): implement task"
    echo '{"result":"done","total_cost_usd":0.01,"num_turns":3}'
    exit 0 ;;
  blocked)
    sed -i "/$task/s/\\[ \\]/[!]/" TASKS.md
    # awk + ENVIRON keeps the note byte for byte (backslashes included).
    FAKE_NOTE="${FAKE_NOTE-  note: test DB is at a newer migration}" \\
      FAKE_NOTE_AFTER="${FAKE_NOTE_AFTER:-$task}" \\
      awk '{ print } $0 ~ ENVIRON["FAKE_NOTE_AFTER"] && ENVIRON["FAKE_NOTE"] != "" && !done {
             print ENVIRON["FAKE_NOTE"]; done = 1 }' TASKS.md > TASKS.md.new
    mv TASKS.md.new TASKS.md
    echo '{"result":"blocked","total_cost_usd":0.02,"num_turns":5}'
    exit 0 ;;
  denied)  # dontAsk refused a command; the agent gives up and marks [!]
    sed -i "/$task/s/\\[ \\]/[!]/" TASKS.md
    denial='{"tool_name":"Bash","tool_input":{"command":"cat > x.py <<EOF\\nprint(1)\\nEOF"}}'
    echo '{"result":"blocked","total_cost_usd":0.04,"num_turns":9,'
    echo "\\"permission_denials\\":[$denial]}"
    exit 0 ;;
  nojson)  # killed mid-run (timeout or crash): no JSON, a different error each time
    echo "boom $(date +%s%N)" >&2
    exit 1 ;;
esac
echo '{"result":"same failure"}'
exit 1
""",
    )

    notifications = tmp_path / "notifications"
    write_executable(
        fake_bin / "fake-notify", f'#!/usr/bin/env bash\nprintf "%s\\n" "$*" >> {notifications}\n'
    )

    write_executable(repo / "scripts" / "ralph-settings.json", "{}\n")
    subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)
    subprocess.run(["git", "config", "user.name", "Harness Test"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "harness@example.invalid"], cwd=repo, check=True)
    subprocess.run(["git", "add", "TASKS.md", "README.md", "scripts"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "initial"], cwd=repo, check=True)
    repo = tmp_path / "repo"
    subprocess.run(
        ["git", "worktree", "add", "-q", "-b", "work", str(repo)], cwd=main_checkout, check=True
    )

    env = {
        **{k: v for k, v in os.environ.items() if not k.startswith("HARNESS_")},
        "PATH": f"{fake_bin}:{os.environ['PATH']}",
        "CLAUDE_CALLS_FILE": str(calls),
        "CLAUDE_SEEN_FILE": str(tmp_path / "claude-seen"),
        "FAKE_CLAUDE_MODE": mode,
        "HARNESS_LOG_DIR": str(logs),
        # Never pop real desktop notifications from the test suite.
        "HARNESS_NOTIFY_CMD": str(fake_bin / "fake-notify"),
        "HARNESS_RETRIES": "3",
        "HARNESS_SHIP": "0",
        # Empty disables the default ceilings; tests that need one set it.
        "HARNESS_BUDGET_USD": "",
        "HARNESS_RUN_BUDGET_USD": "",
        "CLAUDE_ENV_FILE": str(tmp_path / "claude-env"),
        "VERIFY_COUNT_FILE": str(verify_count),
    }
    return repo, env, calls, verify_count


def run_ralph(
    repo: Path, env: dict[str, str], max_tasks: int = 1
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(RALPH), str(max_tasks)],
        capture_output=True,
        check=False,
        cwd=repo,
        env=env,
        text=True,
        timeout=30,
    )


def test_accepts_committed_task_only_after_external_full_verify(tmp_path: Path) -> None:
    repo, env, calls, verify_count = make_repo(tmp_path, "success")

    result = run_ralph(repo, env)

    assert result.returncode == 0, result.stderr
    assert "- [x] T-01" in (repo / "TASKS.md").read_text()
    assert (repo / "result.txt").read_text().strip() == "implemented"
    assert verify_count.read_text().strip() == "2"  # preflight + final judge
    assert "runner fará o full final" in calls.read_text()
    assert "\tpassed\t" in (Path(env["HARNESS_LOG_DIR"]) / "summary.tsv").read_text()


def test_stops_retrying_when_the_same_failure_repeats(tmp_path: Path) -> None:
    repo, env, calls, verify_count = make_repo(tmp_path, "failure")

    result = run_ralph(repo, env)

    assert result.returncode == 0, result.stderr
    assert "mesma falha repetida" in result.stdout
    assert "- [!] T-01" in (repo / "TASKS.md").read_text()
    assert calls.read_text().count("--permission-mode") == 2
    assert verify_count.read_text().strip() == "1"  # preflight only


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], capture_output=True, check=True, cwd=repo, text=True
    ).stdout.strip()


def ralph_refs(repo: Path) -> list[str]:
    return git(repo, "for-each-ref", "--format=%(refname)", "refs/ralph/").splitlines()


def summary_rows(env: dict[str, str]) -> list[dict[str, str]]:
    header, *rows = (Path(env["HARNESS_LOG_DIR"]) / "summary.tsv").read_text().splitlines()
    return [dict(zip(header.split("\t"), row.split("\t"), strict=True)) for row in rows]


def blocked_run(tmp_path: Path, **changes: str) -> tuple[Path, dict[str, str]]:
    repo, env, _, _ = make_repo(tmp_path, "blocked")
    env.update(changes)
    result = run_ralph(repo, env)
    assert result.returncode == 0, result.stderr
    return repo, env


def test_optional_flags_are_not_passed_by_default(tmp_path: Path) -> None:
    repo, env, calls, _ = make_repo(tmp_path, "success")

    run_ralph(repo, env)

    assert "--effort" not in calls.read_text()
    assert "--exclude-dynamic-system-prompt-sections" not in calls.read_text()


def test_optional_flags_are_passed_when_set(tmp_path: Path) -> None:
    repo, env, calls, _ = make_repo(tmp_path, "success")
    env.update(HARNESS_EFFORT="medium", HARNESS_CACHE_FLAG="1")

    run_ralph(repo, env)

    assert "--effort medium" in calls.read_text()
    assert "--exclude-dynamic-system-prompt-sections" in calls.read_text()


def test_preflight_skips_a_clean_head_already_verified_by_full(tmp_path: Path) -> None:
    repo, env, _, verify_count = make_repo(tmp_path, "success")

    first = run_ralph(repo, env)
    second = run_ralph(repo, env)

    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr
    # First run: preflight + task judge. Second: only the task judge after a cached clean HEAD.
    assert verify_count.read_text().strip() == "3"
    assert "skipping full verification" in second.stdout


def test_selects_an_independent_task_when_an_earlier_pending_task_is_blocked(tmp_path: Path) -> None:
    tasks = (
        "- [ ] T-01 blocked prerequisite — done when: ready\n"
        "  depends on: T-99\n"
        "- [ ] T-02 independent result — done when: ready\n"
    )
    repo, env, calls, _ = make_repo(tmp_path, "success", tasks)

    result = run_ralph(repo, env)

    assert result.returncode == 0, result.stderr
    assert "T-02" in calls.read_text()
    final_tasks = (repo / "TASKS.md").read_text()
    assert "- [ ] T-01" in final_tasks
    assert "- [x] T-02" in final_tasks


def test_reports_unmet_or_missing_dependencies_when_no_task_is_ready(tmp_path: Path) -> None:
    tasks = "- [ ] T-01 blocked prerequisite — done when: ready\n  depends on: T-99\n"
    repo, env, calls, _ = make_repo(tmp_path, "success", tasks)

    result = run_ralph(repo, env)

    assert result.returncode != 0
    assert "unmet or missing dependencies" in result.stderr
    assert "T-99 missing" in result.stderr
    assert not calls.exists()


def test_skips_a_task_with_a_non_ready_definition_of_ready(tmp_path: Path) -> None:
    tasks = (
        "- [ ] T-01 needs a decision — done when: ready\n"
        "  DoR: not ready\n"
        "- [ ] T-02 ready result — done when: ready\n"
        "  DoR: ready\n"
    )
    repo, env, calls, _ = make_repo(tmp_path, "success", tasks)

    result = run_ralph(repo, env)

    assert result.returncode == 0, result.stderr
    assert "T-02" in calls.read_text()
    final_tasks = (repo / "TASKS.md").read_text()
    assert "- [ ] T-01" in final_tasks
    assert "- [x] T-02" in final_tasks


def test_task_execution_overrides_apply_only_to_the_selected_task(tmp_path: Path) -> None:
    tasks = (
        "- [ ] T-01 tailored task — done when: ready\n"
        "  execution: model=custom-model, effort=high, max-turns=7, retries=2\n"
    )
    repo, env, calls, _ = make_repo(tmp_path, "success", tasks)
    env.update(HARNESS_MODEL="global-model", HARNESS_EFFORT="low", HARNESS_MAX_TURNS="60")

    result = run_ralph(repo, env)

    assert result.returncode == 0, result.stderr
    invocation = calls.read_text()
    assert "--model custom-model" in invocation
    assert "--effort high" in invocation
    assert "--max-turns 7" in invocation
    assert "global-model" not in invocation

