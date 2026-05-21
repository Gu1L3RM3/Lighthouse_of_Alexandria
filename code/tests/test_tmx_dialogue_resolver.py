import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from core.localization.tmx_dialogue_resolver import TmxDialogueResolver
from core.managers.entity_manager import EntityManager
from core.managers.language_service import LanguageService
from core.map.spawners.spawn import DialogueAreaSpawner
from core.repositories.language_preferences_repository import LanguagePreferencesRepository
from entities.dialogue_area import DialogueArea


class TmxDialogueResolverTest(unittest.TestCase):
    def test_uses_english_dialogue_when_language_is_english(self):
        resolver = TmxDialogueResolver(language="en")
        properties = {
            "dialogo": "Ola;Tudo bem?",
            "dialogo_en": "Hello;How are you?",
        }

        self.assertEqual(resolver.resolve_lines(properties), ["Hello", "How are you?"])

    def test_falls_back_to_portuguese_when_english_dialogue_is_missing(self):
        resolver = TmxDialogueResolver(language="en")
        properties = {
            "dialogo": "Ola;Tudo bem?",
        }

        self.assertEqual(resolver.resolve_lines(properties), ["Ola", "Tudo bem?"])


class DialogueAreaSpawnerLanguageTest(unittest.TestCase):
    def setUp(self):
        self.entity_manager = EntityManager()
        self.tilemap = SimpleNamespace(tmx_file="dummy_map")
        self.obj = SimpleNamespace(
            x=10,
            y=20,
            width=30,
            height=40,
            name="dialog_1",
            properties={
                "dialogo": "Ola;Tudo bem?",
                "dialogo_en": "Hello;How are you?",
                "active_status": True,
            },
        )

    def test_spawner_uses_english_dialogue_when_language_is_english(self):
        service = LanguageService(
            repository=LanguagePreferencesRepository(Path.cwd() / "code" / "save" / "test_preferences_spawner_en.json")
        )
        service.set_language("en")
        spawner = DialogueAreaSpawner()

        with patch.object(LanguageService, "get", return_value=service):
            spawner.spawn(self.obj, self.entity_manager, self.tilemap)

        dialogue_area = self.entity_manager.get_entities_by_class(DialogueArea)[0]
        self.assertEqual(dialogue_area.list_dialogue, ["Hello", "How are you?"])

    def test_spawner_falls_back_to_portuguese_when_english_dialogue_is_missing(self):
        service = LanguageService(
            repository=LanguagePreferencesRepository(Path.cwd() / "code" / "save" / "test_preferences_spawner_pt.json")
        )
        service.set_language("en")
        spawner = DialogueAreaSpawner()
        obj = SimpleNamespace(
            x=10,
            y=20,
            width=30,
            height=40,
            name="dialog_1",
            properties={
                "dialogo": "Ola;Tudo bem?",
                "active_status": True,
            },
        )

        with patch.object(LanguageService, "get", return_value=service):
            spawner.spawn(obj, self.entity_manager, self.tilemap)

        dialogue_area = self.entity_manager.get_entities_by_class(DialogueArea)[0]
        self.assertEqual(dialogue_area.list_dialogue, ["Ola", "Tudo bem?"])

    def test_uses_portuguese_dialogue_when_language_is_portuguese(self):
        resolver = TmxDialogueResolver(language="pt-BR")
        properties = {
            "dialogo": "Ola;Tudo bem?",
            "dialogo_en": "Hello;How are you?",
        }

        self.assertEqual(resolver.resolve_lines(properties), ["Ola", "Tudo bem?"])


if __name__ == "__main__":
    unittest.main()
