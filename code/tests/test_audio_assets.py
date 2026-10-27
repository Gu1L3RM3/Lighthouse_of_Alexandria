import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOUNDS_DIR = ROOT.parent / "assets" / "sounds"
AUDIO_EXTENSIONS = (".ogg", ".wav", ".flac", ".mp3")
AUDIO_REFERENCE = re.compile(r"""["']((?:music|sfx)/[\w/.-]+\.(?:ogg|wav|flac|mp3))["']""")


def referenced_audio_paths() -> dict[str, str]:
    references = {}
    for path in ROOT.rglob("*.py"):
        if "tests" in path.parts:
            continue
        for match in AUDIO_REFERENCE.finditer(path.read_text(encoding="utf-8")):
            references[match.group(1)] = str(path.relative_to(ROOT))
    return references


class AudioAssetTests(unittest.TestCase):
    def test_finds_audio_references(self):
        self.assertIn("sfx/ui_click.ogg", referenced_audio_paths())

    def test_referenced_audio_files_exist(self):
        missing = [
            f"{audio} ({source})"
            for audio, source in referenced_audio_paths().items()
            if not (SOUNDS_DIR / audio).is_file()
        ]
        self.assertEqual(missing, [])

    def test_shipped_audio_is_ogg(self):
        # Uncompressed/other formats bloat the release build.
        not_ogg = [
            str(path.relative_to(SOUNDS_DIR))
            for path in SOUNDS_DIR.rglob("*")
            if path.suffix.lower() in AUDIO_EXTENSIONS and path.suffix.lower() != ".ogg"
        ]
        self.assertEqual(not_ogg, [])


if __name__ == "__main__":
    unittest.main()
