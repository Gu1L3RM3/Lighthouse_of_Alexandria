import subprocess

from fakes import clean_environment, git, init_repo, install_script, write


def make_repo(tmp_path):
    repo = init_repo(tmp_path / "game")
    install_script(repo, "scripts/wt.sh")
    write(repo / "main.py", "x = 1\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "base")
    return repo


def wt(repo, *args):
    return subprocess.run(
        ["bash", "scripts/wt.sh", *args],
        cwd=repo, env=clean_environment(), capture_output=True, text=True, timeout=20,
    )


def test_new_creates_a_sibling_worktree_without_the_uncommitted_work(tmp_path):
    repo = make_repo(tmp_path)
    write(repo / "main.py", "experiment\n")

    result = wt(repo, "new", "login")

    folder = tmp_path / "game-wt-login"
    assert result.returncode == 0, result.stderr
    assert git(folder, "branch", "--show-current") == "wt/login"
    assert (folder / "main.py").read_text() == "x = 1\n"
    assert (repo / "main.py").read_text() == "experiment\n"


def test_rm_removes_the_folder_and_keeps_the_branch(tmp_path):
    repo = make_repo(tmp_path)
    wt(repo, "new", "login")

    result = wt(repo, "rm", "login")

    assert result.returncode == 0, result.stderr
    assert not (tmp_path / "game-wt-login").exists()
    assert "wt/login" in git(repo, "branch", "--list", "wt/login")


def test_new_from_a_worktree_still_names_folders_after_the_main_checkout(tmp_path):
    repo = make_repo(tmp_path)
    wt(repo, "new", "one")

    wt(tmp_path / "game-wt-one", "new", "two")

    assert (tmp_path / "game-wt-two").is_dir()
