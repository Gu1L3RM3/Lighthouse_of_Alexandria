from pygame import Rect
import pygame
from entities.itens.item import Item
from core.components.area_trigger import AreaTrigger
from core.components.sprite import Sprite
from core.components.position import Position
from core.components.always_on_top import AlwaysOnTop
from core.components.label_component import LabelComponent
from core.components.light_component import LightComponent
from core.managers.event_manager import EventManager
from entities.player import Player
from core.settings import FONT


def _pixel_resistor_icon() -> pygame.Surface:
    surf = pygame.Surface((32, 20), pygame.SRCALPHA)
    # terminals
    pygame.draw.rect(surf, (176, 178, 186), (0, 9, 6, 2))
    pygame.draw.rect(surf, (176, 178, 186), (26, 9, 6, 2))
    # body
    pygame.draw.rect(surf, (84, 62, 48), (6, 5, 20, 10))
    pygame.draw.rect(surf, (168, 124, 88), (6, 5, 20, 10), 2)
    # bands
    pygame.draw.rect(surf, (190, 55, 50), (10, 6, 2, 8))
    pygame.draw.rect(surf, (240, 210, 60), (14, 6, 2, 8))
    pygame.draw.rect(surf, (70, 70, 70), (18, 6, 2, 8))
    return surf


class ResistorItem(Item):
    def __init__(self, x, y, active,props):
        super().__init__(x, y, active,props)
        self.value = props['valor']
        self.area_id =  int(props['area'])
        self.img = _pixel_resistor_icon()
        self.em =  EventManager.get()
        self.area_trigger = Rect(0,0,self.img.get_width(),self.img.get_height())
        self.add(
            Position(x,y),
            AreaTrigger(self.area_trigger,active=active,on_entered=self.on_collect),
            Sprite(self.img),
            LabelComponent(
                "",
                self.value,
                FONT,
                font_size=10,
                offset_y=12,
                value_color=(244, 230, 170),
                use_outline=True,
            ),
            AlwaysOnTop(),
            LightComponent(radius=22)
        )
    def on_active(self):
        area_trigger:AreaTrigger =  self.get(AreaTrigger)
        area_trigger.active = True
    
    def on_collect(self, entity):
        if not isinstance(entity,Player):
            return
        pos: Position = self.get(Position)
        self.em.post(
            events={
                'type': 'resistor_collected',
                'value': self.value,
                'area_id': self.area_id,
                'spawn_x': pos.x,
                'spawn_y': pos.y,
            }
        )
        self.em.post(events={'type':'kill_entity','id':self.id})
        
        
    
