import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pygame

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from core.localization.scene_copy_catalog import SceneCopyCatalog, resolve_explanation_image_path
from core.managers.audio_manager import AudioManager
from core.managers.input_manager import InputManager
from core.managers.language_service import LanguageService
from core.managers.resource_manager import ResourceManager
from core.managers.scene_manager import SceneManager
from core.repositories.language_preferences_repository import LanguagePreferencesRepository
from core.ui.widgets.text import Text
from scenes.credits_scene import CreditsScene
from scenes.fases.explanation_content import get_phase_dialogue_media_for_language


class _DummySceneManager:
    def start_fade(self, name: str, duration: float = 0.45):
        _ = (name, duration)


class _DummyAudioManager:
    def play_ui(self, filename: str, volume: float = 1.0):
        _ = (filename, volume)


class _DummyInputManager:
    def get_prompt_button(self, action: str):
        return action.upper()

    def is_action_just_pressed(self, action: str):
        _ = action
        return False


class SceneCopyCatalogTest(unittest.TestCase):
    def test_english_scene_copy_exists_for_remaining_scenes(self):
        copy = SceneCopyCatalog("en")

        self.assertEqual(copy.get("credits_back_button"), "BACK TO MENU")
        self.assertEqual(copy.get("lighthouse_title"), "THE LIGHT OF THE LIGHTHOUSE RETURNS")
        self.assertEqual(copy.get("death_lives_label"), "ATTEMPTS")
        self.assertEqual(copy.get("confirm_yes"), "YES")

    def test_explanation_content_uses_english_captions_with_image_fallback(self):
        media = get_phase_dialogue_media_for_language("exp_fase_3", "en")
        entry = media["dialog_1"]

        self.assertEqual(entry["captions"][0], "Ohm's Law: overview of the basic concepts.")
        self.assertTrue(entry["images"][0].endswith("ohm_law_ptbr/01_visao_geral.png"))

    def test_explanation_image_path_prefers_english_variant_when_it_exists(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            assets_root = Path(temp_dir)
            english_asset = assets_root / "images" / "explanations" / "sample_en" / "01.png"
            english_asset.parent.mkdir(parents=True, exist_ok=True)
            english_asset.write_bytes(b"test")

            with patch("core.localization.scene_copy_catalog.ASSETS_DIR", assets_root):
                path = resolve_explanation_image_path("explanations/sample_ptbr/01.png", "en")

        self.assertEqual(path, "explanations/sample_en/01.png")


class CreditsSceneLocalizationTest(unittest.TestCase):
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
        return pygame.Surface(size or (64, 64), pygame.SRCALPHA)

    def _fake_load_font(self, filename: str, size: int):
        _ = filename
        return pygame.font.Font(None, size)

    def _build_scene(self):
        original_set_text = Text.set_text

        def tracked_set_text(self, new_text: str, new_pos_center: tuple[int, int]):
            self.debug_text = new_text
            original_set_text(self, new_text, new_pos_center)

        with (
            patch.object(SceneManager, "get", return_value=_DummySceneManager()),
            patch.object(AudioManager, "get", return_value=_DummyAudioManager()),
            patch.object(InputManager, "get", return_value=_DummyInputManager()),
            patch.object(LanguageService, "get", return_value=self.language_service),
            patch.object(ResourceManager, "load_image", new=self._fake_load_image),
            patch.object(ResourceManager, "load_font", new=self._fake_load_font),
            patch.object(Text, "set_text", new=tracked_set_text),
        ):
            return CreditsScene(self.screen)

    def test_credits_scene_defaults_to_english(self):
        scene = self._build_scene()

        self.assertEqual(scene.back_button.text_widget.debug_text, "BACK TO MENU")
        self.assertEqual(scene.credit_lines[0], "Project")

    def test_credits_scene_switches_to_portuguese(self):
        self.language_service.set_language("pt-BR")
        scene = self._build_scene()

        self.assertEqual(scene.back_button.text_widget.debug_text, "VOLTAR AO MENU")
        self.assertEqual(scene.credit_lines[0], "Projeto")


if __name__ == "__main__":
    unittest.main()
