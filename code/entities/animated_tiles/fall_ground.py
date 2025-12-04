from pygame import Rect
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
    def __init__(self, x, y):
        super().__init__()
        self.rm = ResourceManager.get()
        self.animations = self.rm.load_sprite_sheet('fall_ground', (16, 16), trim_transparent=False)
        self.animate = AnimateSprite(self.animations, loop=False, fps=20)
        self.area = Rect(x, y, 16, 16)
        self.add(
            Position(x, y),
            Sprite(self.animations['broken'][0]),
            self.animate,
            AreaTrigger(self.area, once=True, on_entered=self.on_entered)
        )

    def _fall_player(self):
        EventManager.get().post({'type': 'fall_player'})

    def on_entered(self, entity: Entity):
        if not isinstance(entity, Player):
            return

        col = entity.get(Collider)
        pos = entity.get(Position)

        if col is None or pos is None:
            return

        rect = col.get_rect(pos.x, pos.y)
        if rect.width <= 0 or rect.height <= 0:
            return

        intersection = self.area.clip(rect)
        if intersection.width <= 0 or intersection.height <= 0:
            return

        player_area = rect.width * rect.height
        intersect_area = intersection.width * intersection.height
        if player_area <= 0:
            return

        percent_inside = (intersect_area / player_area) * 100

        REQUIRED_PERCENT_INSIDE = 10

        if percent_inside >= REQUIRED_PERCENT_INSIDE:
            EventManager.get().post({'type': 'request_freeze', 'type_request': 'player fall'})
            self._fall_player()
            self.animate.play('broken')
