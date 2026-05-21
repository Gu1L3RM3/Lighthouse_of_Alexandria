from pathlib import Path

from core.settings import ASSETS_DIR


class LetterAssetResolver:
    LANGUAGE_SUFFIX = {
        "en": "en",
        "pt-BR": "pt",
    }

    def __init__(self, language: str, images_root: str | Path | None = None):
        self.language = language
        self.images_root = Path(images_root or (Path(ASSETS_DIR) / "images"))

    def resolve(self, letter_id: str) -> str:
        suffix = self.LANGUAGE_SUFFIX.get(self.language, "en")
        localized_rel = Path("letters") / f"{letter_id}_{suffix}.png"
        base_rel = Path("letters") / f"{letter_id}.png"

        if (self.images_root / localized_rel).exists():
            return localized_rel.as_posix()
        if (self.images_root / base_rel).exists():
            return base_rel.as_posix()
        return localized_rel.as_posix()
