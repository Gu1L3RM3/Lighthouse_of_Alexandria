import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from core.level_config import LevelConfig, LevelConfigError
from core.settings import GENERIC_LEVEL_BOMB_COUNT_PER_LEVEL, GENERIC_LEVEL_GHOST_RESPAWN_SECONDS


class LevelConfigTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name) / "level.json"

    def tearDown(self):
        self._tmp.cleanup()

    def _write(self, payload):
        self.path.write_text(json.dumps(payload), encoding="utf-8")

    def test_missing_file_uses_current_game_defaults(self):
        config = LevelConfig.load(self.path)

        self.assertEqual(config.tolerance_percent, 2.0)
        self.assertEqual(config.bomb_count, GENERIC_LEVEL_BOMB_COUNT_PER_LEVEL)
        self.assertEqual(config.ghost_respawn_seconds, GENERIC_LEVEL_GHOST_RESPAWN_SECONDS)
        self.assertEqual(config.title, "")

    def test_file_overrides_only_the_fields_it_sets(self):
        self._write({"tolerance_percent": 5, "title": "Ponte"})

        config = LevelConfig.load(self.path)

        self.assertEqual(config.tolerance_percent, 5.0)
        self.assertEqual(config.title, "Ponte")
        self.assertEqual(config.bomb_count, GENERIC_LEVEL_BOMB_COUNT_PER_LEVEL)

    def test_negative_bomb_count_is_rejected_with_field_name(self):
        self._write({"bomb_count": -1})

        with self.assertRaisesRegex(LevelConfigError, "bomb_count"):
            LevelConfig.load(self.path)

    def test_non_numeric_tolerance_is_rejected(self):
        self._write({"tolerance_percent": "muito"})

        with self.assertRaisesRegex(LevelConfigError, "tolerance_percent"):
            LevelConfig.load(self.path)

    def test_invalid_json_is_reported_as_level_config_error(self):
        self.path.write_text("{", encoding="utf-8")

        with self.assertRaises(LevelConfigError):
            LevelConfig.load(self.path)

    def test_round_trip_writes_only_non_default_fields(self):
        LevelConfig(title="Ponte", tolerance_percent=3.0).save(self.path)

        self.assertEqual(json.loads(self.path.read_text(encoding="utf-8")), {"title": "Ponte", "tolerance_percent": 3.0})
        self.assertEqual(LevelConfig.load(self.path).tolerance_percent, 3.0)


if __name__ == "__main__":
    unittest.main()
