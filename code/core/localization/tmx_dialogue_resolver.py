class TmxDialogueResolver:
    def __init__(self, language: str):
        self.language = language

    def resolve_lines(self, properties: dict) -> list[str]:
        if self.language == "en":
            raw_dialogue = properties.get("dialogo_en") or properties.get("dialogo", "")
        else:
            raw_dialogue = properties.get("dialogo", "")

        if not isinstance(raw_dialogue, str) or not raw_dialogue:
            return []
        return [line.strip() for line in raw_dialogue.split(";") if line.strip()]
