import subprocess
from pathlib import Path

import pytest

from fakes import FAKE_PYTHON, clean_environment, git, init_repo, install_script, write


@pytest.fixture
def repo(tmp_path):
    repo = init_repo(tmp_path / "repo")
    install_script(repo, "scripts/verify.sh")
    write(repo / "code/core/linear.py", "x = 1\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "base")
    git(repo, "switch", "-q", "-c", "feat/x")
    write(tmp_path / "python", FAKE_PYTHON, executable=True)
    return repo


def verify(repo: Path, level: str, **env: str):
    log = repo.parent / "calls.log"
    log.unlink(missing_ok=True)
    result = subprocess.run(
        ["bash", "scripts/verify.sh", level],
        cwd=repo,
        env=clean_environment(
            HARNESS_PYTHON=str(repo.parent / "python"),
            HARNESS_BASE="main",
            FAKE_LOG=str(log),
            **env,
        ),
        capture_output=True,
        text=True,
        timeout=30,
    )
    calls = log.read_text() if log.exists() else ""
    return result, calls


def commit(repo: Path, path: str) -> None:
    write(repo / path, "changed\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", f"change {path}")


def verified_head(repo: Path) -> str:
    marker = repo / ".git/harness-full-verified"
    return marker.read_text().strip() if marker.exists() else ""


def test_fast_runs_lint_and_unit_tests_only(repo):
    result, calls = verify(repo, "fast")

    assert result.returncode == 0, result.stdout
    assert "-m ruff check" in calls
    assert "-m unittest discover -s code/tests" in calls
    assert "smoke" not in calls


def test_a_failing_step_shows_its_output_and_stops(repo):
    result, calls = verify(repo, "full", FAKE_FAIL="unittest")

    assert result.returncode == 1
    assert "boom from" in result.stdout
    assert "smoke_scenes.py" not in calls


def test_full_boots_the_scenes_and_skips_checks_for_untouched_areas(repo):
    commit(repo, "code/core/linear.py")

    result, calls = verify(repo, "full")

    assert result.returncode == 0, result.stdout
    assert "scripts/smoke_scenes.py" in calls
    assert "pytest" not in calls
    assert "web_smoke.py" not in calls


@pytest.mark.parametrize(
    "path",
    ["main.py", "web/alexandria.tmpl", "pygbag.ini", "code/core/touch_gamepad.py",
     "code/core/ui/board_view.py", "code/core/web_storage_sync.py"],
)
def test_full_runs_the_web_check_when_web_code_changes(repo, path):
    commit(repo, path)

    _, calls = verify(repo, "full")

    assert "scripts/web_smoke.py" in calls


def test_full_counts_uncommitted_web_changes(repo):
    write(repo / "web/alexandria.tmpl", "draft\n")

    _, calls = verify(repo, "full")

    assert "scripts/web_smoke.py" in calls


@pytest.mark.parametrize("path", ["scripts/ralph.sh", ".claude/hooks/guard.sh"])
def test_full_tests_the_harness_when_it_changes(repo, path):
    commit(repo, path)

    _, calls = verify(repo, "full")

    assert "-m pytest -q scripts/tests" in calls


def test_a_missing_tool_is_reported_and_does_not_cache_the_head(repo):
    commit(repo, "web/alexandria.tmpl")

    result, calls = verify(repo, "full", FAKE_MISSING="playwright")

    assert result.returncode == 0
    assert "SKIPPED" in result.stdout
    assert "web_smoke.py" not in calls
    assert verified_head(repo) == ""


def test_strict_mode_turns_a_skip_into_a_failure(repo):
    commit(repo, "web/alexandria.tmpl")

    result, _ = verify(repo, "full", FAKE_MISSING="playwright", HARNESS_STRICT="1")

    assert result.returncode == 1
    assert "SKIPPED" in result.stdout


def test_a_clean_full_pass_remembers_the_verified_head(repo):
    commit(repo, "code/core/linear.py")

    verify(repo, "full")

    assert verified_head(repo) == git(repo, "rev-parse", "HEAD")


def test_web_level_runs_only_the_web_check(repo):
    _, calls = verify(repo, "web")

    assert "web_smoke.py" in calls
    assert "unittest" not in calls


@pytest.mark.parametrize(("path", "expected"), [("web/alexandria.tmpl", 0), ("code/core/linear.py", 1)])
def test_web_needed_answers_whether_web_code_changed_without_running_checks(repo, path, expected):
    commit(repo, path)

    result, calls = verify(repo, "web-needed")

    assert result.returncode == expected, result.stdout
    assert calls == ""
