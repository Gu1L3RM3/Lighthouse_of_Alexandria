import json
import subprocess
from pathlib import Path

import pytest

from fakes import clean_environment, git, init_repo, install_script, write

BLOCKED = 2
# Records each run; fails while a file called "broken" exists.
FAKE_VERIFY = """#!/usr/bin/env bash
echo "$1" >> .git/verify-runs
[ -f broken ] && { echo "verify(fast) FAILED at tests"; exit 1; }
exit 0
"""


@pytest.fixture
def repo(tmp_path):
    repo = init_repo(tmp_path / "repo")
    install_script(repo, ".claude/hooks/stop-verify.sh")
    write(repo / "scripts/verify.sh", FAKE_VERIFY, executable=True)
    write(repo / "main.py", "x = 1\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "base")
    return repo


def stop(repo: Path, active: bool = False):
    return subprocess.run(
        ["bash", ".claude/hooks/stop-verify.sh"],
        input=json.dumps({"stop_hook_active": active}),
        cwd=repo,
        env=clean_environment(CLAUDE_PROJECT_DIR=str(repo)),
        capture_output=True,
        text=True,
        timeout=20,
    )


def runs(repo: Path) -> list[str]:
    log = repo / ".git/verify-runs"
    return log.read_text().split() if log.exists() else []


def test_nothing_runs_without_changes(repo):
    assert stop(repo).returncode == 0
    assert runs(repo) == []


def test_documentation_only_changes_are_not_verified(repo):
    write(repo / "NOTES.md", "text\n")

    assert stop(repo).returncode == 0
    assert runs(repo) == []


def test_a_failing_check_sends_the_output_back(repo):
    write(repo / "broken", "")

    result = stop(repo)

    assert result.returncode == BLOCKED
    assert "FAILED at tests" in result.stderr


def test_a_second_stop_is_not_blocked_again(repo):
    write(repo / "broken", "")

    assert stop(repo, active=True).returncode == 0


def test_an_unchanged_tree_is_verified_once(repo):
    write(repo / "main.py", "x = 2\n")

    stop(repo)
    stop(repo)

    assert runs(repo) == ["fast"]


def test_a_new_edit_is_verified_again(repo):
    write(repo / "new.py", "a = 1\n")
    stop(repo)
    write(repo / "new.py", "a = 2\n")
    stop(repo)

    assert runs(repo) == ["fast", "fast"]
