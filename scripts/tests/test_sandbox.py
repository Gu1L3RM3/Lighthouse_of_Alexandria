import subprocess
from pathlib import Path

from sandbox import copy_project


def make_repo(root: Path) -> Path:
    files = {
        ".gitignore": "ignored.txt\n",
        "main.py": "print('hi')\n",
        "code/circuitos/panel.json": "{}\n",
        "ignored.txt": "secret\n",
    }
    for name, content in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "add", ".gitignore", "main.py"], cwd=root, check=True)
    return root


def test_copies_tracked_and_new_files_but_not_ignored_ones(tmp_path):
    source = make_repo(tmp_path / "repo")

    copy = copy_project(source, tmp_path / "copy")

    assert (copy / "main.py").read_text() == "print('hi')\n"
    assert (copy / "code/circuitos/panel.json").exists()
    assert not (copy / "ignored.txt").exists()


def test_writing_in_the_copy_leaves_the_source_untouched(tmp_path):
    source = make_repo(tmp_path / "repo")

    copy = copy_project(source, tmp_path / "copy")
    (copy / "code/circuitos/panel.json").write_text("changed")

    assert (source / "code/circuitos/panel.json").read_text() == "{}\n"


def test_skips_files_deleted_from_the_working_tree(tmp_path):
    source = make_repo(tmp_path / "repo")
    (source / "main.py").unlink()

    copy = copy_project(source, tmp_path / "copy")

    assert not (copy / "main.py").exists()
