from core.settings import DEFAULT_LANGUAGE
from core.repositories.language_preferences_repository import LanguagePreferencesRepository


class LanguageService:
    _instance = None
    SUPPORTED_LANGUAGES = ("en", "pt-BR")
    MENU_LABELS = {
        "en": {
            "resume_initial": "RESUME LEVEL",
            "resume_continue": "CONTINUE JOURNEY",
            "resume_empty": "NO SAVE AVAILABLE",
            "start": "NEW JOURNEY",
            "credits": "CREDITS",
            "exit": "EXIT",
            "language_button": "LANGUAGE: ENGLISH",
            "title_subtitle": "Story, puzzles and electricity",
            "title_tagline": "pixel adventure",
        },
        "pt-BR": {
            "resume_initial": "RETOMAR FASE",
            "resume_continue": "CONTINUAR JORNADA",
            "resume_empty": "SEM SAVE ATIVO",
            "start": "INICIAR JORNADA",
            "credits": "CREDITOS",
            "exit": "SAIR",
            "language_button": "IDIOMA: PORTUGUES",
            "title_subtitle": "Historia, enigmas e eletricidade",
            "title_tagline": "aventura pixel",
        },
    }

    def __init__(self, repository: LanguagePreferencesRepository | None = None):
        self.repository = repository or LanguagePreferencesRepository()
        self.current_language = self._normalize_language(self.repository.load_language())

    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = LanguageService()
        return cls._instance

    @classmethod
    def reset_instance(cls):
        cls._instance = None

    def _normalize_language(self, language: str | None) -> str:
        if language in self.SUPPORTED_LANGUAGES:
            return language
        return DEFAULT_LANGUAGE

    def get_current_language(self) -> str:
        return self.current_language

    def set_language(self, language: str) -> str:
        normalized = self._normalize_language(language)
        self.current_language = normalized
        self.repository.save_language(normalized)
        return normalized

    def toggle_language(self) -> str:
        next_language = "pt-BR" if self.current_language == "en" else "en"
        return self.set_language(next_language)

    def get_menu_label(self, key: str) -> str:
        labels = self.MENU_LABELS.get(self.current_language, self.MENU_LABELS[DEFAULT_LANGUAGE])
        return labels.get(key, key)
