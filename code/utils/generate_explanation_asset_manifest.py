from __future__ import annotations

import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
CODE_DIR = ROOT_DIR / "code"
ASSETS_DIR = ROOT_DIR / "assets"
IMAGES_DIR = ASSETS_DIR / "images"
MANIFEST_PATH = ROOT_DIR / "docs" / "plans" / "EXPLANATION_IMAGE_CHECKLIST_EN.md"

if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from core.localization.explanation_asset_audit import build_explanation_asset_manifest_lines  # noqa: E402
from scenes.fases.explanation_content import EXPLANATION_CONTENT  # noqa: E402


def main() -> int:
    lines = build_explanation_asset_manifest_lines(
        EXPLANATION_CONTENT,
        images_root=IMAGES_DIR,
        language="en",
    )
    MANIFEST_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Manifesto gerado em {MANIFEST_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
