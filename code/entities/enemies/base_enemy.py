from pygame import Vector2

from core.ecs import Entity
from core.components.position import Position
from core.components.velocity import Velocity
from core.components.sprite import Sprite
from core.components.collider import Collider
from core.components.animation_sprite import AnimateSprite
from core.components.team import Team
from core.components.path_follower import PathFollower
from core.components.freeze import Freeze
from core.components.render_layer import RenderLayer
from core.components.depth_anchor import DepthAnchor
from core.components.health import Health


class EnemyBase(Entity):
    def __init__(
        self,
        x: float,
        y: float,
        animations: dict,
        collider: Collider,
        route: list[tuple[int, int]] | None = None,
        speed: float = 42.0,
        max_hp: float = 100.0,
    ):
        super().__init__()
        self._facing = Vector2(0, 1)
        self._current_animation_state = "idle_front"
        self.speed = speed

        first_frame = animations["idle_front"][0]
        self.add(
            Position(x, y),
            Velocity(0, 0),
            collider,
            Sprite(first_frame),
            AnimateSprite(animations, fps=8, loop=True),
            Team("enemy"),
            Health(max_hp=max_hp),
            Freeze(),
            RenderLayer(RenderLayer.ACTOR),
            DepthAnchor(offset_y=12),
        )
        if route and len(route) > 1:
            self.add(PathFollower(route, speed=speed, loop=True))

    def set_direction(self, direction: Vector2):
        if direction.length_squared() > 0:
            self._facing = direction.copy()
        dir_name = self._get_dir_name(self._facing)
        state = f"walk_{dir_name}" if direction.length_squared() > 0 else f"idle_{dir_name}"
        if state == self._current_animation_state:
            return
        anim: AnimateSprite = self.get(AnimateSprite)
        if state in anim.animations:
            anim.play(state)
            self._current_animation_state = state

    def get_facing_name(self) -> str:
        return self._get_dir_name(self._facing)

    def _get_dir_name(self, direction: Vector2) -> str:
        if abs(direction.y) >= abs(direction.x):
            return "back" if direction.y < 0 else "front"
        return "right" if direction.x > 0 else "left"
