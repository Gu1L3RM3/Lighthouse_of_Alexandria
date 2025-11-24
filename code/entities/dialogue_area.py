from core.ecs import Entity
from core.components.position import Position
from core.components.dialogue import Dialogue
class DialogueArea(Entity):
    def __init__(self, x:int, y:int, width:int, height:int, list_dialogue:list[str], name:str, active_status:bool):
        super().__init__()
        self.name = name.strip()
        if not self.name:
            raise ValueError("DialogueArea's name can't be empty or null")

        self.list_dialogue = list(list_dialogue or [])  # sempre lista

        size = (width, height)

        self.add(
            Position(x, y),
            Dialogue(
                lines=self.list_dialogue,
                size_dialogue=size,
                auto_start=True,
                active_status=active_status,
            )
        )

    def add_dialogue_text(self, text_list: list[str]):
        if not text_list:
            return
        
        self.list_dialogue.extend(text_list)

        dialogue: Dialogue = self.get(Dialogue)
        dialogue.lines = self.list_dialogue[:]  # cópia segura
