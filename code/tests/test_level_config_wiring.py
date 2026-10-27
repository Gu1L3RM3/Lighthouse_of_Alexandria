import os
import subprocess
import sys
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Levels pull in many singletons (fonts, managers); a fresh process keeps them from leaking into other tests.
BUILD_LEVELS = textwrap.dedent(
    """
    from unittest.mock import patch
    import pygame
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))

    from core.level_config import LevelConfig
    from scenes.fases.generic_level_3 import GenericLevel3
    from scenes.fases.final_level import FinalLevel
    from scenes.fases.generic_level_4 import GenericLevel4
    from scenes.fases.generic_level_5 import GenericLevel5
    from scenes.fases.generic_level_6 import GenericLevel6
    from scenes.fases.generic_level_7 import GenericLevel7

    LEVELS = (
        (GenericLevel3, "generic_levels_3/fase_3"),
        (GenericLevel4, "generic_levels_4/fase_4"),
        (GenericLevel5, "generic_levels_5/fase_5"),
        (GenericLevel6, "generic_levels_6/fase_6"),
        (GenericLevel7, "generic_levels_7/fase_7"),
        (FinalLevel, "final_fase/fase_8"),
    )

    default = GenericLevel3(screen, level_path="generic_levels_3/fase_3")
    assert default.circuit_validator_system.tolerance_percent == 2.0
    assert default.bomb_manager.max_bombs == 8
    assert default.ghost_system.respawn_seconds == 10.0

    custom = LevelConfig(tolerance_percent=9.0, bomb_count=3, ghost_respawn_seconds=4.5)
    for level_class, level_path in LEVELS:
        with patch.object(LevelConfig, "for_level", return_value=custom) as loader:
            level = level_class(screen, level_path=level_path)
        loader.assert_called_with(level_path)
        assert level.circuit_validator_system.tolerance_percent == 9.0, level_path
        assert level.bomb_manager.max_bombs == 3, level_path
        assert level.ghost_system.respawn_seconds == 4.5, level_path
    """
)


class LevelConfigWiringTest(unittest.TestCase):
    def test_every_stage_reads_its_level_config_and_keeps_defaults_without_one(self):
        env = dict(os.environ, SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
        result = subprocess.run(
            [sys.executable, "-c", BUILD_LEVELS],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
