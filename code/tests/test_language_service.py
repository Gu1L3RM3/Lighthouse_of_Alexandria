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
from core.managers.life_manager import LifeManager
from core.managers.resource_manager import ResourceManager
from core.managers.save_game_manager import SaveGameManager
from core.managers.scene_manager import SceneManager
from core.repositories.language_preferences_repository import LanguagePreferencesRepository
from core.managers.language_service import LanguageService
from core.ui.widgets.text import Text
from scenes.main_menu_scene import MainMenuScene


class LanguagePreferencesRepositoryTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.preferences_path = Path(self.temp_dir.name) / "preferences.json"
        self.repository = LanguagePreferencesRepository(self.preferences_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_load_defaults_to_english_when_file_does_not_exist(self):
        self.assertEqual(self.repository.load_language(), "en")

    def test_save_and_load_language(self):
        self.repository.save_language("pt-BR")
        self.assertEqual(self.repository.load_language(), "pt-BR")

    def test_invalid_json_falls_back_to_english(self):
        self.preferences_path.write_text("{invalid", encoding="utf-8")
        self.assertEqual(self.repository.load_language(), "en")


class LanguageServiceTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.preferences_path = Path(self.temp_dir.name) / "preferences.json"
        self.repository = LanguagePreferencesRepository(self.preferences_path)
        self.service = LanguageService(repository=self.repository)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_service_starts_in_english_by_default(self):
        self.assertEqual(self.service.get_current_language(), "en")

    def test_toggle_language_persists_choice(self):
        self.assertEqual(self.service.toggle_language(), "pt-BR")
        reloaded = LanguageService(repository=LanguagePreferencesRepository(self.preferences_path))
        self.assertEqual(reloaded.get_current_language(), "pt-BR")

    def test_unsupported_language_falls_back_to_english(self):
        self.assertEqual(self.service.set_language("fr"), "en")
        self.assertEqual(self.service.get_current_language(), "en")

    def test_menu_labels_follow_current_language(self):
        self.assertEqual(self.service.get_menu_label("start"), "NEW JOURNEY")
        self.service.set_language("pt-BR")
        self.assertEqual(self.service.get_menu_label("start"), "INICIAR JORNADA")


class _DummySceneManager:
    def can_resume_scene(self):
        return False

    def resume_from_menu(self, duration: float = 0.35):
        _ = duration

    def start_fade(self, name: str, duration: float = 0.5):
        _ = (name, duration)

    def start_new_journey(self, start_scene_name: str = "home_scene", duration: float = 0.6):
        _ = (start_scene_name, duration)


class _DummyLifeManager:
    max_lives = 10

    def reset_lives(self):
        pass

    def set_state(self, current_lives: int, max_lives: int):
        _ = (current_lives, max_lives)


class _DummyAudioManager:
    def play_ui(self, filename: str, volume: float = 1.0):
        _ = (filename, volume)


class _DummySaveManager:
    def has_save(self):
        return False

    def clear_save(self):
        pass

    def load_game(self):
        return None


class _DummyInputManager:
    def get_prompt_items(self, context: str):
        _ = context
        return []


class MainMenuSceneLanguageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.font.init()
        pygame.display.set_mode((32, 32))
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

    def test_menu_scene_starts_in_english_and_has_language_button(self):
        original_set_text = Text.set_text

        def tracked_set_text(self, new_text: str, new_pos_center: tuple[int, int]):
            self.debug_text = new_text
            original_set_text(self, new_text, new_pos_center)

        with (
            patch.object(SceneManager, "get", return_value=_DummySceneManager()),
            patch.object(LifeManager, "get", return_value=_DummyLifeManager()),
            patch.object(AudioManager, "get", return_value=_DummyAudioManager()),
            patch.object(SaveGameManager, "get", return_value=_DummySaveManager()),
            patch.object(InputManager, "get", return_value=_DummyInputManager()),
            patch.object(LanguageService, "get", return_value=self.language_service),
            patch.object(ResourceManager, "load_image", new=self._fake_load_image),
            patch.object(ResourceManager, "load_font", new=self._fake_load_font),
            patch.object(Text, "set_text", new=tracked_set_text),
        ):
            scene = MainMenuScene(self.screen)
            scene.start()

        self.assertEqual(self.language_service.get_current_language(), "en")
        self.assertEqual(scene.start_button.text_widget.debug_text, "NEW JOURNEY")
        self.assertEqual(scene.credits_button.text_widget.debug_text, "CREDITS")
        self.assertEqual(scene.exit_button.text_widget.debug_text, "EXIT")
        self.assertEqual(scene.resume_button.text_widget.debug_text, "NO SAVE AVAILABLE")
        self.assertTrue(hasattr(scene, "language_button"))
        self.assertEqual(scene.language_button.text_widget.debug_text, "LANGUAGE: ENGLISH")

    def test_menu_scene_updates_labels_after_language_toggle(self):
        original_set_text = Text.set_text

        def tracked_set_text(self, new_text: str, new_pos_center: tuple[int, int]):
            self.debug_text = new_text
            original_set_text(self, new_text, new_pos_center)

        with (
            patch.object(SceneManager, "get", return_value=_DummySceneManager()),
            patch.object(LifeManager, "get", return_value=_DummyLifeManager()),
            patch.object(AudioManager, "get", return_value=_DummyAudioManager()),
            patch.object(SaveGameManager, "get", return_value=_DummySaveManager()),
            patch.object(InputManager, "get", return_value=_DummyInputManager()),
            patch.object(LanguageService, "get", return_value=self.language_service),
            patch.object(ResourceManager, "load_image", new=self._fake_load_image),
            patch.object(ResourceManager, "load_font", new=self._fake_load_font),
            patch.object(Text, "set_text", new=tracked_set_text),
        ):
            scene = MainMenuScene(self.screen)
            scene.start()
            scene.toggle_language()

        self.assertEqual(self.language_service.get_current_language(), "pt-BR")
        self.assertEqual(scene.start_button.text_widget.debug_text, "INICIAR JORNADA")
        self.assertEqual(scene.credits_button.text_widget.debug_text, "CREDITOS")
        self.assertEqual(scene.exit_button.text_widget.debug_text, "SAIR")
        self.assertEqual(scene.resume_button.text_widget.debug_text, "SEM SAVE ATIVO")
        self.assertEqual(scene.language_button.text_widget.debug_text, "IDIOMA: PORTUGUES")


if __name__ == "__main__":
    unittest.main()
