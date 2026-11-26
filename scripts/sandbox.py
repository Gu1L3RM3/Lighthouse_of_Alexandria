"""Throwaway copies of the project, for runs that must not touch the real one.

Booting the game rewrites circuit and save files, so every end-to-end check
runs in a copy.
"""

import shutil
import subprocess
from pathlib import Path


def copy_project(source: Path, destination: Path) -> Path:
    """Copy the working tree (tracked and new files, never ignored ones)."""
    listing = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=source,
        check=True,
        capture_output=True,
    ).stdout
    for name in listing.decode("utf-8").split("\0"):
        origin = source / name
        if not name or not origin.is_file():
            continue
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(origin, target)
    return destination
