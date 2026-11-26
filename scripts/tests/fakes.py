"""Shared helpers: throwaway git repositories and a fake Python interpreter."""

import os
import shutil
import stat
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    ).stdout.strip()


def write(path: Path, content: str, executable: bool = False) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    if executable:
        path.chmod(path.stat().st_mode | stat.S_IEXEC)
    return path


def init_repo(repo: Path) -> Path:
    repo.mkdir(parents=True, exist_ok=True)
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.email", "harness@example.invalid")
    git(repo, "config", "user.name", "Harness Test")
    return repo


def install_script(repo: Path, relative: str) -> Path:
    target = repo / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / relative, target)
    return target


def clean_environment(**extra: str) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith(("HARNESS_", "CLAUDE_"))}
    env.update(extra)
    return env


# Logs every call; FAKE_MISSING names modules that fail to import, FAKE_FAIL
# makes any call whose arguments contain it fail.
FAKE_PYTHON = """#!/usr/bin/env bash
echo "$*" >> "$FAKE_LOG"
if [ "$1" = -c ]; then
  case "$2" in *"${FAKE_MISSING:-__none__}"*) exit 1 ;; esac
  exit 0
fi
case "$*" in *"${FAKE_FAIL:-__none__}"*) echo "boom from $*"; exit 1 ;; esac
exit 0
"""
