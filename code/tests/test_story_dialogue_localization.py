import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from core.managers.language_service import LanguageService
from core.repositories.language_preferences_repository import LanguagePreferencesRepository


class StoryDialogueCatalogTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.preferences_path = Path(self.temp_dir.name) / "preferences.json"
        self.repository = LanguagePreferencesRepository(self.preferences_path)
        self.language_service = LanguageService(repository=self.repository)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_father_story_dialogue_is_english_by_default(self):
        from core.localization.story_dialogue_catalog import StoryDialogueCatalog

        catalog = StoryDialogueCatalog(language=self.language_service.get_current_language())

        self.assertEqual(
            catalog.get_generic_level_7_father_dialogue()[0],
            "Father: Kevin... so you made it this far.",
        )

    def test_arquimedes_story_hints_include_translated_target_line(self):
        from core.localization.story_dialogue_catalog import StoryDialogueCatalog

        catalog = StoryDialogueCatalog(language="en")
        hints = catalog.get_generic_level_7_arquimedes_hints("R3")

        self.assertIn("Arquimedes: Focus on the target resistor R3.", hints)
        self.assertEqual(hints[0], "Arquimedes: Kevin... I did not expect this. Is that man really your father?")

    def test_player_thought_dialogue_switches_to_portuguese(self):
        from core.localization.story_dialogue_catalog import StoryDialogueCatalog

        self.language_service.set_language("pt-BR")
        catalog = StoryDialogueCatalog(language=self.language_service.get_current_language())

        self.assertEqual(
            catalog.get_generic_level_7_player_thought_dialogue()[0],
            "Kevin: Naoo... ele realmente enlouqueceu.",
        )

    def test_npc_dialogues_are_available_in_english(self):
        from core.localization.story_dialogue_catalog import StoryDialogueCatalog

        catalog = StoryDialogueCatalog(language="en")

        self.assertEqual(catalog.get_npc_dialogue("arquimedes")[0], "Life is like water flowing from a spring.")
        self.assertEqual(catalog.get_npc_dialogue("father")[0], "Hi son, shall we continue our circuit studies?")
        self.assertEqual(catalog.get_npc_dialogue("guard")[0], "I need to study for tomorrow's exam.")
        self.assertEqual(catalog.get_npc_dialogue("professor")[0], "Hello student!")


if __name__ == "__main__":
    unittest.main()
