from pygame import Surface
from entities.itens.item import Item
from entities.player import Player
from core.components.area_trigger import AreaTrigger
from core.components.animation_sprite import AnimateSprite
from core.components.sprite import Sprite
from core.components.position import Position
from core.components.light_component import LightComponent
from core.managers.resource_manager import ResourceManager
from core.components.always_on_top import AlwaysOnTop
from core.managers.event_manager import EventManager

class OldPaper(Item):
    def __init__(self, x, y,active,props):
        super().__init__(x,y,active,props)
        
        self.rm =  ResourceManager.get()
        self.em =  EventManager.get()
        self.animations = self.rm.load_sprite_sheet("itens/paper_item")
        self.animate_sprite= AnimateSprite(self.animations,fps=6,loop=False)

        surf = Surface((48,48))
        surf.set_alpha(0)
        self.add(
            Position(x,y),
            AreaTrigger(self.area_trigger,active=active,on_entered=self.on_collect),
            AlwaysOnTop(),
            Sprite(surf),
            LightComponent(),
            self.animate_sprite
            )
        
   

    def on_collect(self,entity):
        if not isinstance(entity,Player):
            return
        self.em.post(events={'type':'open_old_paper'})
    def on_active(self):
        
        area_trigger :AreaTrigger=self.get(AreaTrigger)
        area_trigger.active=True
        self.animate_sprite.play('fade_in')
