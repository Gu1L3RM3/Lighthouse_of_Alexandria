import pygame
from pygame import Rect
from core.ecs import Entity
from core.components.position import Position
from core.components.area_trigger import AreaTrigger
from core.components.animation_sprite import AnimateSprite
from core.components.sprite import Sprite
from core.components.light_component import LightComponent
from core.managers.resource_manager import ResourceManager
from core.managers.event_manager import EventManager
from core.components.always_on_top import AlwaysOnTop
from entities.player import Player
from entities.itens.item import Item
from core.managers.scene_manager import SceneManager
from scenes.circuit_editor import CircuitEditor
class ControlPannel(Item):
    def __init__(self,x,y,active,props):
        super().__init__(x,y,active,props)
        self.rm =  ResourceManager.get()
        self.event_manager =  EventManager.get()
        self.animations = self.rm.load_sprite_sheet("control_pannel",(32,32),trim_transparent=False)

        self.done = False
        



        self.animate = AnimateSprite(self.animations)

        self.area = Rect(x,y,32,48)

        self.solution_value :float|None=  None
        self.active =  active
        self.solution_type =  props['type_solution']
        self.target_component =  props['target_component']
        self.component_for_area = int(props['component_for_area'])
        self.pannel_id = props['pannel_id'] # Deve ser diferente de qualquer outro dentre todas as fases
        self.name_file = 'pannel'+self.pannel_id
        self.action_type = 'pannel_'+ props['action']+self.pannel_id
        
        self.add(
            Position(x,y),
            AlwaysOnTop(),
            self.animate,
            Sprite(self.animations['idle'][0]),
            AreaTrigger(self.area,on_entered=self.on_collect,active=self.active),
            LightComponent()
        )
        self.animate.play('idle')

  

    def action(self):
        self.event_manager.post({'type':self.action_type})
        self.done = True

        

    
    def on_collect(self,entity:Entity):
        if isinstance(entity,Player):
            SceneManager.get().active_scene = CircuitEditor(pygame.display.get_surface(),file=self.name_file)
            
            

