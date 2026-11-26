from test_ralph import blocked_run, git, make_repo, ralph_refs, run_ralph, summary_rows


def test_blocked_task_preserves_its_commit_in_a_recovery_ref(tmp_path):
    repo, env = blocked_run(tmp_path, FAKE_COMMIT="1")

    [ref] = ralph_refs(repo)
    assert ref.startswith("refs/ralph/T-01/t1-")
    assert git(repo, "show", f"{ref}:committed.txt") == "committed by T-01"
    assert "feat(T-01): partial work" in git(repo, "log", "--format=%s", ref)
    [row] = summary_rows(env)
    assert row["result"] == "blocked"
    assert row["recovery_ref"] == ref
    assert row["reason"] == "test DB is at a newer migration"
    assert row["commit"] == git(repo, "rev-parse", f"{ref}^")


def test_blocked_task_preserves_a_dirty_tracked_file(tmp_path):
    repo, _ = blocked_run(tmp_path, FAKE_DIRTY="1")

    [ref] = ralph_refs(repo)
    assert git(repo, "show", f"{ref}:README.md") == "original\nedited by T-01"
    assert (repo / "README.md").read_text() == "original\n"


def test_blocked_task_preserves_an_untracked_file(tmp_path):
    repo, _ = blocked_run(tmp_path, FAKE_UNTRACKED="1")

    [ref] = ralph_refs(repo)
    assert git(repo, "show", f"{ref}:untracked.txt") == "untracked by T-01"
    assert not (repo / "untracked.txt").exists()


def test_preserved_tree_equals_the_agent_changes_and_the_branch_ends_clean_at_base(tmp_path):
    repo, env, _, _ = make_repo(tmp_path, "blocked")
    base = git(repo, "rev-parse", "HEAD")
    env.update(FAKE_COMMIT="1", FAKE_DIRTY="1", FAKE_UNTRACKED="1")

    result = run_ralph(repo, env)

    assert result.returncode == 0, result.stderr
    [ref] = ralph_refs(repo)
    assert ref in result.stdout
    assert git(repo, "diff", "--name-status", base, ref).splitlines() == [
        "M\tREADME.md",
        "M\tTASKS.md",
        "A\tcommitted.txt",
        "A\tuntracked.txt",
    ]
    assert git(repo, "status", "--porcelain") == ""
    assert git(repo, "rev-parse", "HEAD^") == base
    assert git(repo, "diff", "--name-only", base, "HEAD") == "TASKS.md"


def test_two_failed_attempts_keep_two_distinct_refs(tmp_path):
    repo, env, _, _ = make_repo(tmp_path, "failure")
    env.update(FAKE_COMMIT="1", FAKE_UNTRACKED="1")

    result = run_ralph(repo, env)

    assert result.returncode == 0, result.stderr
    refs = ralph_refs(repo)
    assert len(refs) == 2
    assert {ref.split("/")[3].split("-")[0] for ref in refs} == {"t1", "t2"}
    assert [row["recovery_ref"] for row in summary_rows(env)] == sorted(refs)
    assert git(repo, "status", "--porcelain") == ""


def test_next_task_starts_from_a_clean_tree_after_a_blocked_one(tmp_path):
    repo, env, _, _ = make_repo(tmp_path, "success")
    env.update(FAKE_MODE_T_01="blocked", FAKE_COMMIT="1", FAKE_DIRTY="1", FAKE_UNTRACKED="1")
    env["HARNESS_CONTINUE_ON_BLOCK"] = "1"

    result = run_ralph(repo, env, max_tasks=2)

    assert result.returncode == 0, result.stderr
    seen = (tmp_path / "claude-seen").read_text().split("== T-02\n", 1)[1]
    assert "committed.txt" not in seen
    assert "untracked.txt" not in seen
    assert " M " not in seen and "??" not in seen
    tasks = (repo / "TASKS.md").read_text()
    assert "- [!] T-01" in tasks and "- [x] T-02" in tasks


def test_run_budget_stops_before_the_next_task(tmp_path):
    repo, env, calls, _ = make_repo(tmp_path, "success")
    env["HARNESS_RUN_BUDGET_USD"] = "0.01"

    result = run_ralph(repo, env, max_tasks=2)

    assert result.returncode == 0, result.stderr
    assert "orçamento da execução" in result.stdout
    assert calls.read_text().count("--permission-mode") == 1
    tasks = (repo / "TASKS.md").read_text()
    assert "- [x] T-01" in tasks and "- [ ] T-02" in tasks


def test_run_budget_still_ships_the_tasks_already_done(tmp_path):
    repo, env, calls, _ = make_repo(tmp_path, "success")
    env.update(HARNESS_RUN_BUDGET_USD="0.01", HARNESS_SHIP="1")

    result = run_ralph(repo, env, max_tasks=2)

    assert result.returncode == 0, result.stderr
    assert "/ship-branch ainda roda" in result.stdout
    assert "ship-branch/SKILL.md" in calls.read_text()


def test_blocked_reason_is_read_wherever_the_agent_wrote_it(tmp_path):
    tasks = "- [ ] T-01 small task — done when: test passes\n  decided: use the stdlib\n"
    repo, env, _, _ = make_repo(tmp_path, "blocked", tasks)
    env.update(FAKE_NOTE="  destructive migration needed", FAKE_NOTE_AFTER="decided:")

    result = run_ralph(repo, env)

    assert result.returncode == 0, result.stderr
    [row] = summary_rows(env)
    assert row["reason"] == "destructive migration needed"
    assert "nota: destructive migration needed" in (repo / "TASKS.md").read_text()


def test_attempt_without_json_counts_the_attempt_budget_as_its_cost(tmp_path):
    repo, env, _, _ = make_repo(tmp_path, "nojson")
    env.update(HARNESS_BUDGET_USD="0.5", HARNESS_RETRIES="1")

    result = run_ralph(repo, env)

    assert result.returncode == 0, result.stderr
    [row] = summary_rows(env)
    assert row["cost_usd"] == "0.5"
    assert "custo estimado" in row["reason"]


def test_run_budget_is_checked_between_retries(tmp_path):
    repo, env, calls, _ = make_repo(tmp_path, "nojson")
    env.update(HARNESS_BUDGET_USD="0.5", HARNESS_RUN_BUDGET_USD="0.6", HARNESS_RETRIES="3")

    result = run_ralph(repo, env)

    assert result.returncode == 0, result.stderr
    assert calls.read_text().count("--permission-mode") == 2
    assert "orçamento da execução" in result.stdout
    assert "- [ ] T-01" in (repo / "TASKS.md").read_text()
    assert git(repo, "status", "--porcelain") == ""


def test_ship_session_cost_is_recorded(tmp_path):
    repo, env, _, _ = make_repo(tmp_path, "success")
    env["HARNESS_SHIP"] = "1"

    result = run_ralph(repo, env)

    assert result.returncode == 0, result.stderr
    ship = [row for row in summary_rows(env) if row["task"] == "ship"]
    assert [row["cost_usd"] for row in ship] == ["0.03"]


def test_log_dir_inside_the_worktree_must_be_ignored(tmp_path):
    repo, env, calls, _ = make_repo(tmp_path, "failure")
    env["HARNESS_LOG_DIR"] = str(repo / "logs")

    result = run_ralph(repo, env)

    assert result.returncode != 0
    assert "HARNESS_LOG_DIR" in result.stderr
    assert not calls.exists()


def test_ignored_log_dir_inside_the_worktree_survives_a_discarded_attempt(tmp_path):
    repo, env, _, _ = make_repo(tmp_path, "failure")
    (repo / ".gitignore").write_text("logs/\n")
    git(repo, "add", ".gitignore")
    git(repo, "commit", "-q", "-m", "ignore logs")
    env.update(HARNESS_LOG_DIR=str(repo / "logs"), HARNESS_RETRIES="1", FAKE_UNTRACKED="1")

    result = run_ralph(repo, env)

    assert result.returncode == 0, result.stderr
    [row] = summary_rows(env)
    assert row["result"] == "failed"
    [ref] = ralph_refs(repo)
    assert "logs" not in git(repo, "ls-tree", "--name-only", ref).splitlines()


def test_failure_reason_is_a_single_clean_line(tmp_path):
    repo, env, _, _ = make_repo(tmp_path, "success")
    env.update(VERIFY_FAIL_FROM="2", HARNESS_RETRIES="1")

    result = run_ralph(repo, env)

    assert result.returncode == 0, result.stderr
    [row] = summary_rows(env)
    assert row["reason"] == "verify full falhou:"
    [ref] = ralph_refs(repo)
    assert "\\n" not in git(repo, "log", "-1", "--format=%B", ref)


def test_blocked_reason_with_backslashes_is_kept_verbatim(tmp_path):
    repo, env, _, _ = make_repo(tmp_path, "blocked")
    env["FAKE_NOTE"] = "  note: path C:\\data\\new ends in \\"

    result = run_ralph(repo, env)

    assert result.returncode == 0, result.stderr
    tasks = (repo / "TASKS.md").read_text().splitlines()
    assert tasks[0].startswith("- [!] T-01")
    assert tasks[1].startswith("  nota: path C:\\data\\new ends in \\; veja ")
    assert tasks[2].startswith("- [ ] T-02")


def test_block_without_code_changes_creates_no_ref(tmp_path):
    repo, env = blocked_run(tmp_path)

    assert ralph_refs(repo) == []
    [row] = summary_rows(env)
    assert row["recovery_ref"] == ""
