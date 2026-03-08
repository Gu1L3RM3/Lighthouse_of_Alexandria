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


def _pixel_current_icon() -> pygame.Surface:
    surf = pygame.Surface((32, 32), pygame.SRCALPHA)

    body = pygame.Rect(6, 6, 20, 20)
    pygame.draw.rect(surf, (44, 50, 58), body)
    pygame.draw.rect(surf, (110, 198, 222), body, 2)



    arrow = (188, 238, 246)
    shade = (140, 196, 208)  

    pygame.draw.rect(surf, arrow, (11, 15, 8, 2))  # x, y, w, h

    pygame.draw.rect(surf, arrow, (22, 16, 1, 1))          # 1
    pygame.draw.rect(surf, arrow, (21, 15, 1, 3))          # 3
    pygame.draw.rect(surf, arrow, (20, 14, 1, 5))          # 5
    pygame.draw.rect(surf, arrow, (19, 15, 1, 3))          # 3
    pygame.draw.rect(surf, arrow, (18, 16, 1, 1))          # 1

    pygame.draw.rect(surf, shade, (20, 16, 1, 1))          # center notch
    pygame.draw.rect(surf, shade, (19, 16, 1, 1))          # tiny blend with shaft

    # terminals
    pygame.draw.rect(surf, (176, 178, 186), (0, 15, 6, 2))
    pygame.draw.rect(surf, (176, 178, 186), (26, 15, 6, 2))

    return surf


class CurrentSourceItem(Item):
    def __init__(self, x, y, active,props):
        super().__init__(x, y, active,props)
        self.value = props['valor']
        self.area_id =  int(props.get('area', -1))
        self.img = _pixel_current_icon()
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
            LightComponent(radius=26)
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
                'type': 'current_source_collected',
                'value': self.value,
                'area_id': self.area_id,
                'spawn_x': pos.x,
                'spawn_y': pos.y,
            }
        )
        self.em.post(events={'type':'kill_entity','id':self.id})
