# -*- mode: python ; coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(SPECPATH).resolve()
OUTPUT_NAME = "Alexandria"
ICON_CANDIDATES = [
    PROJECT_ROOT / "assets" / "images" / "icon" / "game_icon.ico",
    PROJECT_ROOT / "assets" / "images" / "icon" / "game_icon.png",
]
ICON_PATH = next((path for path in ICON_CANDIDATES if path.exists()), None)

ASSET_ALLOWED_EXTS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".ttf",
    ".wav",
    ".ogg",
    ".flac",
    ".mp3",
    ".tmx",
    ".tsx",
    ".txt",
}
ASSET_EXCLUDED_EXTS = {
    ".aseprite",
    ".xcf",
    ".zip",
    ".psd",
    ".kra",
    ".pdn",
    ".raw",
    ".log",
    ".md",
    ".pdf",
}
EXCLUDED_DIR_NAMES = {"__pycache__", ".git", ".idea", ".vscode"}


def collect_filtered_tree(
    base_dir: Path,
    target_root: Path,
    allowed_exts: set[str],
    excluded_exts: set[str] | None = None,
) -> list[tuple[str, str]]:
    excluded_exts = excluded_exts or set()
    datas: list[tuple[str, str]] = []
    for file_path in base_dir.rglob("*"):
        if not file_path.is_file():
            continue

        rel_path = file_path.relative_to(base_dir)
        if any(part.lower() in EXCLUDED_DIR_NAMES for part in rel_path.parts):
            continue

        suffix = file_path.suffix.lower()
        if suffix in excluded_exts:
            continue
        if allowed_exts and suffix not in allowed_exts:
            continue

        target_dir = str((target_root / rel_path.parent).as_posix())
        datas.append((str(file_path), target_dir))
    return datas


datas: list[tuple[str, str]] = []
datas.extend(
    collect_filtered_tree(
        PROJECT_ROOT / "assets",
        target_root=Path("assets"),
        allowed_exts=ASSET_ALLOWED_EXTS,
        excluded_exts=ASSET_EXCLUDED_EXTS,
    )
)
datas.extend(
    collect_filtered_tree(
        PROJECT_ROOT / "code" / "circuitos",
        target_root=Path("code") / "circuitos",
        allowed_exts={".json"},
    )
)
datas.extend(
    collect_filtered_tree(
        PROJECT_ROOT / "code" / "ltspice",
        target_root=Path("code") / "ltspice",
        allowed_exts={".asc", ".net"},
    )
)


a = Analysis(
    ["main.py"],
    pathex=[
        str(PROJECT_ROOT),
        str(PROJECT_ROOT / "code"),
    ],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "pytest",
        "pdb",
        "IPython",
        "jupyter",
        "matplotlib",
        "PIL",
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=OUTPUT_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ICON_PATH) if ICON_PATH is not None else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name=OUTPUT_NAME,
)
