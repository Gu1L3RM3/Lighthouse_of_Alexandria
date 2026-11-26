import subprocess

from test_ralph import RALPH, git, make_repo, ralph_refs, run_ralph, summary_rows


PLAN_TASKS = (
    "- [x] T-00 done task — done when: ok\n"
    "- [ ] T-01 small task — done when: test passes\n"
    "  decided: already settled\n"
    "- [ ] T-02 next task — done when: test passes\n"
    "- [ ] T-03 third task — done when: test passes\n"
)


def run_plan(repo, env, n: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(RALPH), "--plan", str(n)],
        capture_output=True,
        check=False,
        cwd=repo,
        env=env,
        text=True,
        timeout=30,
    )


def test_plan_proposes_lines_only_for_tasks_without_decisions(tmp_path):
    repo, env, calls, verify_count = make_repo(tmp_path, "success", PLAN_TASKS)
    base = git(repo, "rev-parse", "HEAD")

    result = run_plan(repo, env, 5)

    assert result.returncode == 0, result.stderr
    prompts = calls.read_text()
    assert prompts.count("decide/SKILL.md") == 2
    assert "T-01" not in prompts and "task/SKILL.md" not in prompts
    tasks = (repo / "TASKS.md").read_text()
    assert "  proposed: T-02 uses the stdlib" in tasks
    assert "  proposed: T-03 uses the stdlib" in tasks
    assert "- [ ] T-02" in tasks
    assert git(repo, "log", "--format=%s", f"{base}..HEAD").splitlines() == [
        "docs(tasks): propose decisions for T-03",
        "docs(tasks): propose decisions for T-02",
    ]
    assert git(repo, "status", "--porcelain") == ""
    assert not verify_count.exists()
    assert [row["result"] for row in summary_rows(env)] == ["planned", "planned"]


def test_plan_respects_the_task_limit(tmp_path):
    repo, env, calls, _ = make_repo(tmp_path, "success", PLAN_TASKS)

    result = run_plan(repo, env, 1)

    assert result.returncode == 0, result.stderr
    assert calls.read_text().count("decide/SKILL.md") == 1
    assert "proposed: T-03" not in (repo / "TASKS.md").read_text()


def test_plan_that_touches_other_files_is_discarded_and_preserved(tmp_path):
    repo, env, _, _ = make_repo(tmp_path, "success", PLAN_TASKS)
    base = git(repo, "rev-parse", "HEAD")
    env["FAKE_PLAN"] = "other"

    result = run_plan(repo, env, 1)

    assert result.returncode == 0, result.stderr
    assert git(repo, "rev-parse", "HEAD") == base
    assert git(repo, "status", "--porcelain") == ""
    [ref] = ralph_refs(repo)
    assert git(repo, "show", f"{ref}:other.txt") == "code"
    [row] = summary_rows(env)
    assert row["result"] == "failed"
    assert "TASKS.md" in row["reason"]


def test_plan_without_new_lines_is_not_committed(tmp_path):
    repo, env, _, _ = make_repo(tmp_path, "success", PLAN_TASKS)
    base = git(repo, "rev-parse", "HEAD")
    env["FAKE_PLAN"] = "none"

    result = run_plan(repo, env, 5)

    assert result.returncode == 0, result.stderr
    assert git(repo, "rev-parse", "HEAD") == base
    assert [row["task"] for row in summary_rows(env)] == ["T-02", "T-03"]


def test_task_with_unreviewed_proposed_lines_stops_the_loop(tmp_path):
    tasks = "- [ ] T-01 small task — done when: ok\n  proposed: use the stdlib\n"
    repo, env, calls, _ = make_repo(tmp_path, "success", tasks)

    result = run_ralph(repo, env)

    assert result.returncode != 0
    assert "proposed:" in result.stderr
    assert not calls.exists()


def test_task_without_decided_lines_gets_a_warning(tmp_path):
    repo, env, _, _ = make_repo(tmp_path, "success")

    result = run_ralph(repo, env)

    assert result.returncode == 0, result.stderr
    assert "sem linhas decided:" in result.stdout


def test_a_blocked_task_stops_the_loop_by_default(tmp_path):
    repo, env, calls, _ = make_repo(tmp_path, "success")
    env["FAKE_MODE_T_01"] = "blocked"

    result = run_ralph(repo, env, max_tasks=2)

    assert result.returncode == 0, result.stderr
    assert calls.read_text().count("--permission-mode") == 1
    assert "depende" in result.stdout
    tasks = (repo / "TASKS.md").read_text()
    assert "- [!] T-01" in tasks and "- [ ] T-02" in tasks


def test_permission_denial_stops_the_run_and_leaves_the_task_pending(tmp_path):
    repo, env, calls, _ = make_repo(tmp_path, "denied")
    env["FAKE_UNTRACKED"] = "1"

    result = run_ralph(repo, env, max_tasks=2)

    assert result.returncode != 0
    assert calls.read_text().count("--permission-mode") == 1
    assert "permissão negada" in result.stdout
    assert "cat > x.py <<EOF" in result.stdout
    assert "- [ ] T-01" in (repo / "TASKS.md").read_text()
    assert git(repo, "status", "--porcelain") == ""
    [row] = summary_rows(env)
    assert row["result"] == "denied"
    assert row["reason"].startswith("permissão negada: cat > x.py <<EOF")
    [ref] = ralph_refs(repo)
    assert row["recovery_ref"] == ref


def test_prompt_asks_for_file_tools_and_single_allowlisted_commands(tmp_path):
    repo, env, calls, _ = make_repo(tmp_path, "success")

    run_ralph(repo, env)

    prompt = calls.read_text()
    assert "Read/Grep/Glob/Edit/Write" in prompt
    assert "um comando por vez" in prompt
