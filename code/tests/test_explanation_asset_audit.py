import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from core.localization.explanation_asset_audit import (
    audit_explanation_assets,
    build_explanation_asset_manifest_lines,
    expected_explanation_image_path,
)
from scenes.fases.explanation_content import EXPLANATION_CONTENT


class ExplanationAssetAuditTest(unittest.TestCase):
    def test_expected_english_path_uses_en_folder(self):
        self.assertEqual(
            expected_explanation_image_path("explanations/ohm_law_ptbr/01_visao_geral.png", "en"),
            "explanations/ohm_law_en/01_visao_geral.png",
        )

    def test_audit_reports_missing_english_localized_images(self):
        content = {
            "exp_fase_3": {
                "dialog_1": {
                    "images": ["explanations/topic_ptbr/01.png"],
                    "captions": ["caption"],
                }
            }
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            images_root = Path(temp_dir)
            source = images_root / "explanations" / "topic_ptbr" / "01.png"
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_bytes(b"pt")

            issues = audit_explanation_assets(
                content,
                images_root=images_root,
                language="en",
                require_localized_images=True,
            )

        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].kind, "missing_localized")
        self.assertEqual(issues[0].asset_path, "explanations/topic_en/01.png")

    def test_audit_accepts_existing_english_localized_images(self):
        content = {
            "exp_fase_3": {
                "dialog_1": {
                    "images": ["explanations/topic_ptbr/01.png"],
                    "captions": ["caption"],
                }
            }
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            images_root = Path(temp_dir)
            source = images_root / "explanations" / "topic_ptbr" / "01.png"
            localized = images_root / "explanations" / "topic_en" / "01.png"
            source.parent.mkdir(parents=True, exist_ok=True)
            localized.parent.mkdir(parents=True, exist_ok=True)
            source.write_bytes(b"pt")
            localized.write_bytes(b"en")

            issues = audit_explanation_assets(
                content,
                images_root=images_root,
                language="en",
                require_localized_images=True,
            )

        self.assertEqual(issues, [])

    def test_manifest_marks_missing_assets(self):
        content = {
            "exp_fase_3": {
                "dialog_1": {
                    "images": ["explanations/topic_ptbr/01.png"],
                    "captions": ["caption"],
                }
            }
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            lines = build_explanation_asset_manifest_lines(
                content,
                images_root=Path(temp_dir),
                language="en",
            )

        self.assertIn("- [MISSING] explanations/topic_en/01.png", lines)

    def test_real_explanation_entries_keep_image_and_caption_counts_in_sync(self):
        for phase, dialogues in EXPLANATION_CONTENT.items():
            for dialogue_name, entry in dialogues.items():
                images = list(entry.get("images", []))
                captions = list(entry.get("captions", []))
                self.assertEqual(
                    len(images),
                    len(captions),
                    f"{phase}/{dialogue_name} possui contagens diferentes de imagens e legendas.",
                )


if __name__ == "__main__":
    unittest.main()
