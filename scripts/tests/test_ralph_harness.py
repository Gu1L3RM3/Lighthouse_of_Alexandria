"""What this project adds to the unattended runner."""

from pathlib import Path

import pytest

from fakes import ROOT
from test_ralph import make_repo, run_ralph, summary_rows

LEVEL_TASK = "- [ ] T-01 tune a level — done when: test passes\n  level-data: yes\n"


def test_refuses_to_run_in_the_main_checkout(tmp_path):
    repo, env, calls, _ = make_repo(tmp_path, "success")
    main_checkout = tmp_path / "main"
    # The main checkout may hold the owner's experiments, and the runner resets the tree.
    import subprocess

    subprocess.run(["git", "switch", "-q", "-c", "other"], cwd=main_checkout, check=True)

    result = run_ralph(main_checkout, env)

    assert result.returncode != 0
    assert "worktree" in result.stderr
    assert not calls.exists()


def test_sessions_run_unattended_with_their_own_permissions(tmp_path):
    repo, env, calls, _ = make_repo(tmp_path, "success")

    run_ralph(repo, env)

    assert f"--settings {repo}/scripts/ralph-settings.json" in calls.read_text()
    assert Path(env["CLAUDE_ENV_FILE"]).read_text().strip() == "unattended=1 strict=1 level=0"


def test_spending_ceilings_apply_by_default(tmp_path):
    repo, env, calls, _ = make_repo(tmp_path, "success")
    del env["HARNESS_BUDGET_USD"], env["HARNESS_RUN_BUDGET_USD"]

    run_ralph(repo, env)

    assert "--max-budget-usd 2" in calls.read_text()
    state = Path(env["HARNESS_LOG_DIR"]) / "run.state"
    assert "budget=10" in state.read_text()


def test_a_task_can_allow_level_data(tmp_path):
    repo, env, _, _ = make_repo(tmp_path, "success", LEVEL_TASK)
    env["FAKE_TOUCH"] = "code/circuitos/panel.json"

    result = run_ralph(repo, env)

    assert result.returncode == 0, result.stderr
    assert "level=1" in Path(env["CLAUDE_ENV_FILE"]).read_text()
    assert summary_rows(env)[0]["result"] == "passed"


@pytest.mark.parametrize(
    "path",
    ["scripts/verify-extra.sh", ".claude/settings.json", ".github/workflows/ci.yml", "ruff.toml",
     "code/circuitos/panel.json", "assets/maps/level.tmx"],
)
def test_an_attempt_that_changes_protected_files_is_rejected_before_judging(tmp_path, path):
    repo, env, _, verify_count = make_repo(tmp_path, "success")
    env.update(FAKE_TOUCH=path, HARNESS_RETRIES="1")

    result = run_ralph(repo, env)

    assert result.returncode == 0, result.stderr
    row = summary_rows(env)[0]
    assert row["result"] == "failed"
    assert path in row["reason"]
    assert row["recovery_ref"].startswith("refs/ralph/T-01/")
    assert verify_count.read_text().strip() == "1"  # preflight only
    assert not (repo / path).exists()


def test_moving_a_protected_file_away_is_rejected(tmp_path):
    repo, env, _, verify_count = make_repo(tmp_path, "success")
    env.update(FAKE_MOVE="scripts/ralph-settings.json", HARNESS_RETRIES="1")

    run_ralph(repo, env)

    row = summary_rows(env)[0]
    assert row["result"] == "failed"
    assert "scripts/ralph-settings.json" in row["reason"]
    assert verify_count.read_text().strip() == "1"


def test_a_sentence_style_task_block_is_ready(tmp_path):
    tasks = (
        "- [x] T-01 finished prerequisite\n"
        "- [ ] T-02 written like the TASKS.md template\n"
        "  depends on: T-01.\n"
        "  DoR: ready.\n"
    )
    repo, env, calls, _ = make_repo(tmp_path, "success", tasks)

    result = run_ralph(repo, env)

    assert result.returncode == 0, result.stderr
    assert "T-02" in calls.read_text()


def test_the_runner_can_pick_a_task_from_this_projects_queue(tmp_path):
    tasks = (ROOT / "TASKS.md").read_text()
    repo, env, calls, _ = make_repo(tmp_path, "success", tasks)

    result = run_ralph(repo, env)

    assert result.returncode == 0, result.stderr
    assert "T-02" in calls.read_text()
