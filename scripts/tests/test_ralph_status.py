import subprocess
import time

from test_ralph import RALPH, blocked_run, make_repo, ralph_refs, run_ralph


def ralph_status(repo, env) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(RALPH), "status"],
        capture_output=True,
        check=False,
        cwd=repo,
        env=env,
        text=True,
        timeout=30,
    )


def notifications(tmp_path) -> str:
    path = tmp_path / "notifications"
    return path.read_text() if path.exists() else ""


def test_status_shows_the_task_in_progress_and_the_budget(tmp_path):
    repo, env, _, _ = make_repo(tmp_path, "success")
    release = tmp_path / "release"
    env.update(FAKE_HOLD_UNTIL=str(release), HARNESS_RUN_BUDGET_USD="5")
    run = subprocess.Popen(
        ["bash", str(RALPH), "1"],
        cwd=repo,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        status = ""
        for _ in range(100):
            status = ralph_status(repo, env).stdout
            if "rodando" in status:
                break
            time.sleep(0.05)
        assert "rodando: T-01, tentativa 1" in status
        assert f"pid {run.pid}" in status
        assert "US$ 0.00 de US$ 5" in status
    finally:
        release.touch()
        run.wait(timeout=30)

    after = ralph_status(repo, env)
    assert after.returncode == 0, after.stderr
    assert "nenhuma execução em andamento" in after.stdout
    assert "T-01" in after.stdout and "passed" in after.stdout


def test_status_lists_attempts_blocked_tasks_and_recovery_refs(tmp_path):
    repo, env = blocked_run(tmp_path, FAKE_COMMIT="1")
    [ref] = ralph_refs(repo)

    result = ralph_status(repo, env)

    assert result.returncode == 0, result.stderr
    assert "blocked" in result.stdout
    assert "0.02" in result.stdout
    assert "test DB is at a newer migration" in result.stdout
    assert "[!] T-01" in result.stdout
    assert ref in result.stdout


def test_status_works_on_a_dirty_tree_without_a_previous_run(tmp_path):
    repo, env, calls, _ = make_repo(tmp_path, "success")
    (repo / "README.md").write_text("dirty\n")

    result = ralph_status(repo, env)

    assert result.returncode == 0, result.stderr
    assert "nenhuma execução em andamento" in result.stdout
    assert not calls.exists()


def test_a_blocked_task_sends_a_notification(tmp_path):
    blocked_run(tmp_path)

    sent = notifications(tmp_path)
    assert "T-01 travou" in sent
    assert "test DB is at a newer migration" in sent


def test_a_permission_denial_sends_a_notification(tmp_path):
    repo, env, _, _ = make_repo(tmp_path, "denied")

    run_ralph(repo, env)

    assert "permissão negada: cat > x.py <<EOF" in notifications(tmp_path)


def test_the_end_of_a_run_sends_a_summary_notification(tmp_path):
    repo, env, _, _ = make_repo(tmp_path, "success")

    run_ralph(repo, env)

    assert "ralph terminou: 1 feitas, 0 travadas" in notifications(tmp_path)


def test_notifications_can_be_turned_off(tmp_path):
    repo, env, _, _ = make_repo(tmp_path, "blocked")
    env["HARNESS_NOTIFY"] = "0"

    run_ralph(repo, env)

    assert notifications(tmp_path) == ""
