from pygame import Rect
from entities.itens.item import Item
from core.components.area_trigger import AreaTrigger
from core.components.animation_sprite import AnimateSprite
from core.components.sprite import Sprite
from core.components.position import Position
from core.components.always_on_top import AlwaysOnTop
from core.managers.resource_manager import ResourceManager
from core.managers.event_manager import EventManager
from entities.player import Player

class Key(Item):
    def __init__(self, x, y, active,props):
        super().__init__(x, y, active,props)
        self.animations =  ResourceManager.get().load_sprite_sheet('itens/key',(16,16),trim_transparent=False)
        self.em =  EventManager.get()
        self.animate_sprite =  AnimateSprite(self.animations,fps=10)
        self.area_trigger = Rect(x,y,16,16)
        self.add(
            Position(x,y),
            AreaTrigger(self.area_trigger,active=active,on_entered=self.on_collect),
            Sprite(self.animations['idle'][0]),
            AlwaysOnTop(),
            self.animate_sprite,
        )
        self.animate_sprite.play('idle')
    def on_active(self):
        area_trigger:AreaTrigger =  self.get(AreaTrigger)
        area_trigger.active = True
    def after_collected(self):
        self.em.post(events={'type':'get_key'})
        self.em.post(events={'type':'kill_entity','id':self.id})
    def on_collect(self, entity):
        if not isinstance(entity,Player):
            return
        self.animate_sprite.play("collected",
                                 loop=False,
                                 on_finish=self.after_collected,)
        
    