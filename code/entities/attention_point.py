from core.ecs import Entity
from core.components.position import Position
from core.components.animation_sprite import AnimateSprite
from core.components.always_on_top import AlwaysOnTop
from core.managers.resource_manager import ResourceManager
from core.components.sprite import Sprite
class AttentionPoint(Entity):
    def __init__(self,x:int,y:int,list_points:list[tuple]):
        super().__init__()
        self.resource_mn=ResourceManager.get()
        self.list_points=list_points
        animations = self.resource_mn.load_sprite_sheet("exclamation",
                                                        (48,48),
                                                        scale=1.0,
                                                        trim_transparent=False)
        anim = AnimateSprite(animations,8,True)
        self.add(
            Position((x-24,y-48)),
            Sprite(animations['idle'][0]),
            anim
        )
        anim.play("idle")
    
