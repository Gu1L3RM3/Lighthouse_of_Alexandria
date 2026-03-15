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
            AreaTrigger(self.area_trigger,active=active,on_entered=self.on_player_enter, on_exit=self.on_player_exit),
            AlwaysOnTop(),
            Sprite(surf),
            LightComponent(),
            self.animate_sprite
            )
        self.player_inside = False
        
   

    def on_player_enter(self, entity):
        if isinstance(entity, Player):
            self.player_inside = True

    def on_player_exit(self, entity):
        if isinstance(entity, Player):
            self.player_inside = False

    # Mantém a interface abstrata de Item satisfeita; a abertura agora é acionada via tecla E, não pelo trigger.
    def on_collect(self, entity):
        _ = entity
        return
    def on_active(self):
        
        area_trigger :AreaTrigger=self.get(AreaTrigger)
        area_trigger.active=True
        self.animate_sprite.play('fade_in')
