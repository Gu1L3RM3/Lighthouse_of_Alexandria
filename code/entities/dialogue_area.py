from core.ecs import Entity
from core.components.position import Position
from core.components.dialogue import Dialogue
class DialogueArea(Entity):
    def __init__(self,x:int,y:int,width:int,height:int,list_dialogue:list[str],name:str,active_status:bool):
        super().__init__()
        self.name=name
        if not self.name:
            raise Exception("DialogueArea's name can't be empty or null")
        size=(width,height)
        
        self.add(
            Position(x,y),
            Dialogue(
                lines=list_dialogue,
                size_dialogue=size,
                auto_start=True,
                active_status=active_status,
            )
        )
        

        
        