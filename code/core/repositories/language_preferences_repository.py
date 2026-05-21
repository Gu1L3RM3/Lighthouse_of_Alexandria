import json
from pathlib import Path

from core.settings import DEFAULT_LANGUAGE, PREFERENCES_FILE


class LanguagePreferencesRepository:
    SCHEMA_VERSION = 1

    def __init__(self, preferences_file: str | Path | None = None):
        self.preferences_file = Path(preferences_file or PREFERENCES_FILE)
        self.preferences_file.parent.mkdir(parents=True, exist_ok=True)

    def load_language(self) -> str:
        if not self.preferences_file.exists():
            return DEFAULT_LANGUAGE

        try:
            data = json.loads(self.preferences_file.read_text(encoding="utf-8"))
        except Exception:
            return DEFAULT_LANGUAGE

        if not isinstance(data, dict):
            return DEFAULT_LANGUAGE
        if int(data.get("schema_version", -1)) != self.SCHEMA_VERSION:
            return DEFAULT_LANGUAGE

        language = data.get("language", DEFAULT_LANGUAGE)
        if not isinstance(language, str) or not language.strip():
            return DEFAULT_LANGUAGE
        return language

    def save_language(self, language: str) -> None:
        payload = {
            "schema_version": self.SCHEMA_VERSION,
            "language": str(language),
        }
        tmp_file = self.preferences_file.with_suffix(self.preferences_file.suffix + ".tmp")
        try:
            tmp_file.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            tmp_file.replace(self.preferences_file)
        except Exception:
            pass
