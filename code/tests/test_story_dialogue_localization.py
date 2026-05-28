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

        self.assertIn("Archimedes: Focus on the target resistor R3.", hints)
        self.assertEqual(hints[0], "Archimedes: Kevin... I did not expect this. Is that man really your father?")

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

    def test_dynamic_panel_hints_are_available_in_english(self):
        from core.localization.story_dialogue_catalog import StoryDialogueCatalog

        catalog = StoryDialogueCatalog(language="en")

        self.assertEqual(
            catalog.get_level3_panel_hint(2, "voltage", "12 V"),
            "Archimedes: To activate panel 2, the resistor in the circuit must have a voltage close to 12 V.",
        )
        self.assertEqual(
            catalog.get_level5_panel_hint(3, "current", "R1 ~= 2 A, R2 ~= 3 A"),
            "Archimedes: To activate panel 3, the currents should be approximately: R1 ~= 2 A, R2 ~= 3 A",
        )
        self.assertTrue(catalog.get_level6_panel_hint(4, "thevenin").startswith("Archimedes: Panel 4:"))
        self.assertEqual(
            catalog.get_final_level_intro()[0],
            "Archimedes: Kevin, your father ran to the top with the Photon Heart.",
        )

    def test_dynamic_panel_hints_switch_to_portuguese(self):
        from core.localization.story_dialogue_catalog import StoryDialogueCatalog

        catalog = StoryDialogueCatalog(language="pt-BR")

        self.assertEqual(
            catalog.get_level3_panel_hint(1, "power", "24 W"),
            "Arquimedes: Para ativar o painel 1 o resistor do circuito deve ter potencia proxima de 24 W.",
        )
        self.assertTrue(catalog.get_level6_panel_hint(2, "norton").startswith("Arquimedes: Painel 2:"))


if __name__ == "__main__":
    unittest.main()
