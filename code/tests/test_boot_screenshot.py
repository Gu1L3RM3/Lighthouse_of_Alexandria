import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from sandbox import copy_project

BOOT_TIMEOUT_SECONDS = 60
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


class BootScreenshotTests(unittest.TestCase):
    def test_auto_stop_saves_the_last_frame_to_the_requested_path(self):
        with tempfile.TemporaryDirectory() as folder:
            project = copy_project(PROJECT_ROOT, Path(folder) / "project")
            screenshot = Path(folder) / "frame.png"
            env = dict(
                os.environ,
                SDL_VIDEODRIVER="dummy",
                SDL_AUDIODRIVER="dummy",
                ALEX_START_SCENE="help",
                ALEX_PROFILE_SECONDS="0.2",
                ALEX_SCREENSHOT_PATH=str(screenshot),
            )

            result = subprocess.run(
                [sys.executable, "main.py"],
                cwd=project,
                env=env,
                capture_output=True,
                text=True,
                timeout=BOOT_TIMEOUT_SECONDS,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(screenshot.is_file(), result.stdout)
            self.assertEqual(screenshot.read_bytes()[:8], PNG_SIGNATURE)


if __name__ == "__main__":
    unittest.main()
