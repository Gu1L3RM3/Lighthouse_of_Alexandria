from core.ecs import Entity
from core.components.position import Position
from core.components.dialogue import Dialogue


class DialogueArea(Entity):
    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        list_dialogue: list[str],
        name: str,
        active_status: bool,
        auto_start: bool = False,
        stealth_bonus_enabled: bool = True,
        stealth_bonus_duration: float = 4.0,
        stealth_bonus_once: bool = True,
    ):
        super().__init__()
        self.name = name.strip()
        if not self.name:
            raise ValueError("DialogueArea's name can't be empty or null")

        self.list_dialogue = list(list_dialogue or [])
        self.stealth_bonus_enabled = bool(stealth_bonus_enabled)
        self.stealth_bonus_duration = float(stealth_bonus_duration)
        self.stealth_bonus_once = bool(stealth_bonus_once)
        self._stealth_bonus_consumed = False

        size = (width, height)
        self.add(
            Position(x, y),
            Dialogue(
                lines=self.list_dialogue,
                size_dialogue=size,
                auto_start=auto_start,
                active_status=active_status,
            ),
        )

    def add_dialogue_text(self, text_list: list[str]):
        if not text_list:
            return
        self.list_dialogue.extend(text_list)
        dialogue: Dialogue = self.get(Dialogue)
        dialogue.lines = self.list_dialogue[:]

    def can_grant_stealth_bonus(self) -> bool:
        if not self.stealth_bonus_enabled or self.stealth_bonus_duration <= 0:
            return False
        if self.stealth_bonus_once and self._stealth_bonus_consumed:
            return False
        return True

    def mark_stealth_bonus_consumed(self):
        self._stealth_bonus_consumed = True
