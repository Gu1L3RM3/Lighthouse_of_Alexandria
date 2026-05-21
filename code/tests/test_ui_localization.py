import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pygame

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from core.managers.audio_manager import AudioManager
from core.managers.input_manager import InputManager
from core.managers.language_service import LanguageService
from core.managers.resource_manager import ResourceManager
from core.managers.scene_manager import SceneManager
from core.repositories.language_preferences_repository import LanguagePreferencesRepository
from core.ui.widgets.text import Text
from scenes.help_scene import HelpScene


class _DummyHelpSceneManager:
    def can_resume_help_scene(self):
        return False

    def resume_from_help(self, duration: float = 0.35):
        _ = duration

    def start_fade(self, name: str, duration: float = 0.35):
        _ = (name, duration)


class _DummyAudioManager:
    def play_ui(self, filename: str, volume: float = 1.0):
        _ = (filename, volume)


class _DummyPromptInputManager:
    def get_prompt_items(self, context: str):
        _ = context
        return []


class HelpSceneLocalizationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.font.init()
        pygame.display.set_mode((32, 32))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.preferences_path = Path(self.temp_dir.name) / "preferences.json"
        self.repository = LanguagePreferencesRepository(self.preferences_path)
        self.language_service = LanguageService(repository=self.repository)
        self.screen = pygame.Surface((1280, 720))

    def tearDown(self):
        self.temp_dir.cleanup()

    def _fake_load_image(self, filename: str, colorkey=None, size=None):
        _ = (filename, colorkey)
        final_size = size or (64, 64)
        return pygame.Surface(final_size, pygame.SRCALPHA)

    def _fake_load_font(self, filename: str, size: int):
        _ = filename
        return pygame.font.Font(None, size)

    def _build_scene(self):
        original_set_text = Text.set_text

        def tracked_set_text(self, new_text: str, new_pos_center: tuple[int, int]):
            self.debug_text = new_text
            original_set_text(self, new_text, new_pos_center)

        with (
            patch.object(SceneManager, "get", return_value=_DummyHelpSceneManager()),
            patch.object(AudioManager, "get", return_value=_DummyAudioManager()),
            patch.object(InputManager, "get", return_value=_DummyPromptInputManager()),
            patch.object(LanguageService, "get", return_value=self.language_service),
            patch.object(ResourceManager, "load_image", new=self._fake_load_image),
            patch.object(ResourceManager, "load_font", new=self._fake_load_font),
            patch.object(Text, "set_text", new=tracked_set_text),
        ):
            return HelpScene(self.screen)

    def test_help_scene_uses_english_copy_by_default(self):
        scene = self._build_scene()

        self.assertEqual(scene.back_button.text_widget.debug_text, "BACK")
        self.assertEqual(scene.sections[0]["title"], "Basic Controls")

    def test_help_scene_uses_portuguese_copy_after_language_change(self):
        self.language_service.set_language("pt-BR")
        scene = self._build_scene()

        self.assertEqual(scene.back_button.text_widget.debug_text, "VOLTAR")
        self.assertEqual(scene.sections[0]["title"], "Controles Basicos")


class InputManagerLocalizationTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.preferences_path = Path(self.temp_dir.name) / "preferences.json"
        self.repository = LanguagePreferencesRepository(self.preferences_path)
        self.language_service = LanguageService(repository=self.repository)
        self.input_manager = InputManager()
        self.input_manager.last_input_source = "keyboard"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_generic_level_prompt_items_use_english_labels_by_default(self):
        with patch.object(LanguageService, "get", return_value=self.language_service):
            self.assertEqual(
                self.input_manager.get_prompt_items("generic_level"),
                [("B", "bomb"), ("CORE", "editor"), ("F1", "help"), ("ESC", "menu")],
            )

    def test_generic_level_prompt_items_switch_to_portuguese(self):
        self.language_service.set_language("pt-BR")

        with patch.object(LanguageService, "get", return_value=self.language_service):
            self.assertEqual(
                self.input_manager.get_prompt_items("generic_level"),
                [("B", "bomba"), ("NUCLEO", "editor"), ("F1", "ajuda"), ("ESC", "menu")],
            )


if __name__ == "__main__":
    unittest.main()
