import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from core.localization.letter_asset_resolver import LetterAssetResolver


class LetterAssetResolverTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.images_root = Path(self.temp_dir.name) / "images"
        (self.images_root / "letters").mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_resolves_english_variant_when_present(self):
        (self.images_root / "letters" / "letter_1_en.png").write_bytes(b"en")
        resolver = LetterAssetResolver(language="en", images_root=self.images_root)

        self.assertEqual(resolver.resolve("letter_1"), "letters/letter_1_en.png")

    def test_resolves_portuguese_variant_when_present(self):
        (self.images_root / "letters" / "letter_1_pt.png").write_bytes(b"pt")
        resolver = LetterAssetResolver(language="pt-BR", images_root=self.images_root)

        self.assertEqual(resolver.resolve("letter_1"), "letters/letter_1_pt.png")

    def test_falls_back_to_base_asset_when_localized_variant_is_missing(self):
        (self.images_root / "letters" / "letter_1.png").write_bytes(b"base")
        resolver = LetterAssetResolver(language="en", images_root=self.images_root)

        self.assertEqual(resolver.resolve("letter_1"), "letters/letter_1.png")

    def test_returns_default_localized_path_when_no_asset_exists_yet(self):
        resolver = LetterAssetResolver(language="en", images_root=self.images_root)

        self.assertEqual(resolver.resolve("letter_2"), "letters/letter_2_en.png")


if __name__ == "__main__":
    unittest.main()
