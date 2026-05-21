from pygame import Vector2

from core.components.animation_sprite import AnimateSprite
from core.components.collider import Collider
from core.components.dialogue import Dialogue
from core.components.freeze import Freeze
from core.components.position import Position
from core.components.sprite import Sprite
from core.components.velocity import Velocity
from core.ecs import Entity
from core.localization.story_dialogue_catalog import StoryDialogueCatalog
from core.managers.language_service import LanguageService
from core.managers.resource_manager import ResourceManager


class ProfessorNPC(Entity):
    def __init__(self, x, y, props=None):
        super().__init__()
        self.rm = ResourceManager.get()
        animations = self.rm.load_sprite_sheet("player")

        spr = Sprite(animations["idle_front"][0])
        anim = AnimateSprite(animations, fps=6, loop=True)

        self.add(
            Position(x, y),
            Collider(10, 6, offset_x=2, offset_y=13),
            spr,
            anim,
            Freeze(active=False),
            Dialogue(
                StoryDialogueCatalog(
                    LanguageService.get().get_current_language()
                ).get_npc_dialogue("professor"),
                (20, 16),
            ),
            Velocity(),
        )
        self.props = props or {}
        self._direction = Vector2(0, 1)
        self._current_animation_state = "idle_front"

    def set_direction(self, direction: Vector2):
        anim: AnimateSprite = self.get(AnimateSprite)
        dir_name = self._get_dir_name(direction)
        state = f"walk_{dir_name}" if direction.length_squared() > 0 else f"idle_{dir_name}"
        if self._current_animation_state != state:
            anim.play(state)
            self._current_animation_state = state
        if direction.length_squared() > 0:
            self._direction = direction.copy()

    def _get_dir_name(self, direction: Vector2) -> str:
        if direction.y != 0:
            return "back" if direction.y < 0 else "front"
        if direction.x != 0:
            return "right" if direction.x > 0 else "left"
        return "front"
