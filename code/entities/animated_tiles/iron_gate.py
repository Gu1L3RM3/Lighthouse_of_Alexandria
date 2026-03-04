from pygame import  Rect
from core.ecs import Entity
from core.components.sprite import Sprite
from core.components.position import Position
from core.components.animation_sprite import AnimateSprite
from core.managers.resource_manager import ResourceManager
from core.components.collider import Collider
from core.managers.event_manager import EventManager
from core.components.render_layer import RenderLayer
from core.components.depth_anchor import DepthAnchor
class IronGate(Entity):
    def __init__(self,x,y,props):
        super().__init__()
        self.rm = ResourceManager.get()
        self.animations =  self.rm.load_sprite_sheet('iron_gate',(16,32),trim_transparent=False)
        self.animate    = AnimateSprite(self.animations,loop=False,fps=20)
        self.area       = Rect(x,y,16,16)
        col:Collider    = Collider(32,10,offset_y=26)
        self.pannel_id = int(props['pannel_id'])
        self.add(
            Position(x,y),
            Sprite(self.animations['open'][0]),
            col,
            self.animate,
            RenderLayer(RenderLayer.ACTOR),
            DepthAnchor(offset_y=36),

        )
        
        
    def _after_open(self):
        self.remove(Collider)
        EventManager().get().post({'type':'set_cache_colliders'})
    def open(self,event):
        self.animate.play('open',on_finish=self._after_open)


    
