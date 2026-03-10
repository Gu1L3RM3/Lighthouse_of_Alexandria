from pygame import Rect
from entities.itens.item import Item
from core.components.area_trigger import AreaTrigger
from core.components.animation_sprite import AnimateSprite
from core.components.sprite import Sprite
from core.components.position import Position
from core.components.always_on_top import AlwaysOnTop
from core.managers.resource_manager import ResourceManager
from core.managers.event_manager import EventManager
from core.managers.audio_manager import AudioManager
from entities.player import Player

class Key(Item):
    def __init__(self, x, y, active,props):
        super().__init__(x, y, active,props)
        self.animations =  ResourceManager.get().load_sprite_sheet('itens/key',(16,16),trim_transparent=False)
        self.em =  EventManager.get()
        self.animate_sprite =  AnimateSprite(self.animations,fps=10)
        self.area_trigger = Rect(0,0,16,16)
        self.hidden_surface = self._build_hidden_surface()
        self.add(
            Position(x,y),
            AreaTrigger(self.area_trigger,active=active,on_entered=self.on_collect),
            Sprite(self.animations['idle'][0]),
            AlwaysOnTop(),
            self.animate_sprite,
        )
        self.animate_sprite.play('idle')

    def _build_hidden_surface(self):
        surf = self.animations['idle'][0].copy()
        surf.fill((255, 255, 255, 0))
        return surf

    def on_active(self):
        area_trigger:AreaTrigger =  self.get(AreaTrigger)
        area_trigger.active = True
        sprite: Sprite = self.get(Sprite)
        sprite.image = self.animations['idle'][0]
        self.animate_sprite.play('idle', reset=True)

    def on_deactive(self):
        area_trigger: AreaTrigger = self.get(AreaTrigger)
        area_trigger.active = False
        self.animate_sprite.stop()
        self.animate_sprite.current_animation = None
        sprite: Sprite = self.get(Sprite)
        sprite.image = self.hidden_surface
    def after_collected(self):
        AudioManager.get().play_sfx("sfx/key_pickup.wav", volume=0.9)
        self.em.post(events={'type':'get_key'})
        self.em.post(events={'type':'kill_entity','id':self.id})
    def on_collect(self, entity):
        if not isinstance(entity,Player):
            return
        self.animate_sprite.play("collected",
                                 loop=False,
                                 on_finish=self.after_collected,)
        
    
