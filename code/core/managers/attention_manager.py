from pygame import Vector2
from core.components.position import Position
from core.components.dialogue import Dialogue
from core.managers.entity_manager import EntityManager
from entities.attention_point import AttentionPoint
from entities.dialogue_area import DialogueArea

class AttentionManager:
    def __init__(self,entity_manager:EntityManager):
        super().__init__()

        self.current_area_dialogue = 1
        self.entity_manager = entity_manager

        self.attention_point :AttentionPoint= self.entity_manager.get_entities_by_class(AttentionPoint)[0]
        self.dialog_areas_list :list[DialogueArea]= self.entity_manager.get_entities_by_class(DialogueArea)

        self._create_dict_dialogue_areas()
    def _create_dict_dialogue_areas(self):
        self.dialog_areas:dict[str,DialogueArea]={}
        for dialog_area in self.dialog_areas_list:
            self.dialog_areas[dialog_area.name] = dialog_area

    def set_attention_position_after_event(self,events):
        
        if not self.attention_point.list_points:
            self.entity_manager.remove_entity(self.attention_point)
            return
        pos :Position= self.attention_point.get(Position)
        new_pos =  self.attention_point.list_points[0]
        pos.pos = Vector2(new_pos[0],new_pos[1])
        del self.attention_point.list_points[0]
    def set_dialogue_area_after_event(self,events):
        if not self.dialog_areas:
            return

        self.current_area_dialogue+=1
        name = f'dialog_{self.current_area_dialogue}' 

        dialogue_area=self.dialog_areas.get(name,None)
        if not dialogue_area:
            return
        
        dialogue:Dialogue= dialogue_area.get(Dialogue)
        dialogue.active_status=True
        


        


    
    

    