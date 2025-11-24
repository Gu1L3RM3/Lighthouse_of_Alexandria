from pygame import  Rect
from core.ecs import Entity
from entities.player import Player
from core.components.sprite import Sprite
from core.components.position import Position
from core.components.area_trigger import AreaTrigger
from core.components.animation_sprite import AnimateSprite
from core.managers.resource_manager import ResourceManager
from core.managers.event_manager import EventManager
from core.components.collider import Collider
class FallGround(Entity):
    def __init__(self,x,y):
        super().__init__()
        self.rm = ResourceManager.get()
        self.animations =  self.rm.load_sprite_sheet('fall_ground',(16,16),trim_transparent=False)
        self.animate = AnimateSprite(self.animations,loop=False,fps=20)
        self.area = Rect(x,y,16,16)
        self.add(
            Position(x,y),
            Sprite(self.animations['broken'][0]),
            self.animate,
            AreaTrigger(self.area,once=True,on_entered=self.on_entered)

        )
    def _fall_player(self):
        EventManager.get().post({'type':'fall_player'})
    def on_entered(self, entity: Entity):
        if isinstance(entity, Player):
            col: Collider = entity.get(Collider)
            pos: Position = entity.get(Position)
            rect = col.get_rect(pos.x, pos.y)

            

            intersection = self.area.clip(rect)
            
            player_area = rect.width * rect.height
            intersect_area = intersection.width * intersection.height
            percent_inside = (intersect_area / player_area) * 100 if player_area > 0 else 0


            REQUIRED_PERCENT_INSIDE = 12  

            if percent_inside >= REQUIRED_PERCENT_INSIDE:
                EventManager.get().post({'type':'request_freeze', 'type_request':'player fall'})
                self._fall_player()
                self.animate.play('broken')
            