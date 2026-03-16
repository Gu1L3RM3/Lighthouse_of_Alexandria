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


def _pixel_voltage_icon() -> pygame.Surface:
    surf = pygame.Surface((32, 32), pygame.SRCALPHA)

    body = pygame.Rect(6, 6, 20, 20)
    pygame.draw.rect(surf, (52, 45, 34), body)
    pygame.draw.rect(surf, (206, 176, 112), body, 2)

    mark = (246, 228, 170)

    # minus (left) 
    pygame.draw.rect(surf, mark, (11, 16, 5, 1))

    # plus (right)
    pygame.draw.rect(surf, mark, (18, 16, 5, 1))  
    pygame.draw.rect(surf, mark, (20, 14, 1, 5))  

    # terminals
    pygame.draw.rect(surf, (176, 178, 186), (0, 15, 6, 2))
    pygame.draw.rect(surf, (176, 178, 186), (26, 15, 6, 2))

    return surf

class VoutageSourceItem(Item):
    def __init__(self, x, y, active,props):
        super().__init__(x, y, active,props)
        self.value = props['valor']
        self.area_id =  int(props.get('area', -1))
        self.img = _pixel_voltage_icon()
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
                offset_y=16,
                value_color=(244, 230, 170),
                use_outline=True,
            ),
            AlwaysOnTop(),
            LightComponent(radius=30)
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
                'type': 'voltage_source_collected',
                'value': self.value,
                'area_id': self.area_id,
                'spawn_x': pos.x,
                'spawn_y': pos.y,
            }
        )
        self.em.post(events={'type':'kill_entity','id':self.id})
