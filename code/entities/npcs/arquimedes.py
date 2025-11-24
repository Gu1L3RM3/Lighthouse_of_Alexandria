from core.ecs import Entity
from core.components.position import Position
from core.components.collider import Collider
from core.components.sprite import Sprite
from core.components.dialogue import Dialogue
from core.components.light_component import LightComponent
from core.components.animation_sprite import AnimateSprite
from core.settings import *
from core.managers.resource_manager import ResourceManager

class Arquimedes(Entity):
    def __init__(self,x,y,props = None):
        super().__init__()
        self.rm =  ResourceManager.get()
        self.props =  props
        animations =  self.rm.load_sprite_sheet("arquimedes",trim_transparent=False,size=(24,24))
        self.anim = AnimateSprite(animations)
        self.add(
            Position(x,y),
            Collider(24,24),
            Sprite(animations["idle"][0]),
            self.anim,
            Dialogue(['A vida é como a água que sai da nascente'],size_dialogue=(48,48)),
            LightComponent()
        )
        self.anim.play('idle')
