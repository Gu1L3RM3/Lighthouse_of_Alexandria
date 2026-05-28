import pygame
from pygame import Rect
from core.ecs import Entity
from entities.player import Player
from core.components.sprite import Sprite
from core.components.position import Position
from core.components.area_trigger import AreaTrigger
from core.components.animation_sprite import AnimateSprite
from core.managers.resource_manager import ResourceManager
from core.managers.event_manager import EventManager
from core.managers.audio_manager import AudioManager
from core.components.collider import Collider
from core.components.render_layer import RenderLayer
from core.settings import (
    FALL_GROUND_ARM_DELAY_MS,
    FALL_GROUND_REQUIRED_PERCENT_INSIDE,
    FALL_GROUND_WARNING_SFX,
    FALL_GROUND_WARNING_VOLUME,
)

class FallGround(Entity):
    _fall_cooldown_ms = 250
    _last_fall_ms = -10_000

    def __init__(self, x, y):
        super().__init__()
        self.rm = ResourceManager.get()
        self.audio_manager = AudioManager.get()
        self.animations = self.rm.load_sprite_sheet('fall_ground', (16, 16), trim_transparent=False)
        self.animate = AnimateSprite(self.animations, loop=False, fps=20)
        self.area = Rect(0, 0, 16, 16)
        self._armed_player_id: int | None = None
        self._armed_since_ms: int | None = None
        self.add(
            Position(x, y),
            Sprite(self.animations['broken'][0]),
            self.animate,
            RenderLayer(RenderLayer.WORLD),
            AreaTrigger(
                self.area,
                once=False,
                on_entered=self.on_entered,
                on_stayed=self.on_stayed,
                on_exit=self.on_exit,
            )
        )

    def _fall_player(self):
        now_ms = pygame.time.get_ticks()
        if now_ms - FallGround._last_fall_ms < FallGround._fall_cooldown_ms:
            return
        FallGround._last_fall_ms = now_ms
        EventManager.get().post({'type': 'fall_player'})

    def _clear_armed_player(self):
        self._armed_player_id = None
        self._armed_since_ms = None

    def _compute_player_overlap_percent(self, entity: Entity) -> float:
        col = entity.get(Collider)
        pos = entity.get(Position)
        rect = col.get_rect(pos.x, pos.y)
        if rect.width <= 0 or rect.height <= 0:
            return 0.0

        ground_pos = self.get(Position)
        ground_area = self.area.move(ground_pos.x, ground_pos.y)
        intersection = ground_area.clip(rect)
        if intersection.width <= 0 or intersection.height <= 0:
            return 0.0

        player_area = rect.width * rect.height
        if player_area <= 0:
            return 0.0
        intersect_area = intersection.width * intersection.height
        return (intersect_area / player_area) * 100

    def _arm_or_trigger_fall(self, entity: Entity):
        if not isinstance(entity, Player):
            return
        if not entity.has(Collider) or not entity.has(Position):
            return

        percent_inside = self._compute_player_overlap_percent(entity)
        if percent_inside < FALL_GROUND_REQUIRED_PERCENT_INSIDE:
            if self._armed_player_id == entity.id:
                self._clear_armed_player()
            return

        now_ms = pygame.time.get_ticks()
        if self._armed_player_id != entity.id:
            self._armed_player_id = entity.id
            self._armed_since_ms = now_ms
            self.audio_manager.play_sfx(FALL_GROUND_WARNING_SFX, volume=FALL_GROUND_WARNING_VOLUME)
            return

        armed_since_ms = self._armed_since_ms if self._armed_since_ms is not None else now_ms
        if now_ms - armed_since_ms < FALL_GROUND_ARM_DELAY_MS:
            return

        if now_ms - FallGround._last_fall_ms >= FallGround._fall_cooldown_ms:
            EventManager.get().post({'type': 'request_freeze', 'type_request': 'player fall'})
            self._fall_player()
        self.animate.play('broken')
        self.get(AreaTrigger).active = False
        self._clear_armed_player()

    def on_entered(self, entity: Entity):
        self._arm_or_trigger_fall(entity)

    def on_stayed(self, entity: Entity):
        self._arm_or_trigger_fall(entity)

    def on_exit(self, entity: Entity):
        if self._armed_player_id == getattr(entity, "id", None):
            self._clear_armed_player()
