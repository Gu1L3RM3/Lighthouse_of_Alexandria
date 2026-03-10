import pygame

from core.components.position import Position
from core.components.velocity import Velocity
from core.components.sprite import Sprite
from core.components.collider import Collider
from core.components.freeze import Freeze
from core.components.animation_sprite import AnimateSprite
from core.components.team import Team
from core.components.render_layer import RenderLayer
from core.components.depth_anchor import DepthAnchor
from core.settings import *
from core.ecs import Entity
from core.components.light_component import LightComponent
from pygame import Vector2, Event
from core.managers.resource_manager import ResourceManager
from core.managers.audio_manager import AudioManager
from pygame.key import get_pressed
class Player(Entity):
    def __init__(self, x: float = 100, y: float = 100):
        super().__init__()
        self.rm = ResourceManager.get()
        self._direction = Vector2(0, 0)
        self._old_direction = Vector2(0, 1)
        self._speed = 100
        self._current_animation_state = "" 
        self.attack=False
        self.audio_manager = AudioManager.get()
        self._step_interval = 0.24
        self._step_timer = 0.0

        self._key_to_direction = {
            PLAYER_RIGHT: Vector2(1, 0),
            PLAYER_LEFT: Vector2(-1, 0),
            PLAYER_DOWN: Vector2(0, 1),
            PLAYER_UP: Vector2(0, -1),
        }

        pos = Position(x, y)
        vel = Velocity(0, 0)
        col = Collider(8, 6,offset_x=4,offset_y=10)

        self.animations = self.rm.load_sprite_sheet("player copy",size=(16,16),trim_transparent=False)
        self._inject_death_animations()
        spr = Sprite(self.animations["idle_front"][0])
        anim = AnimateSprite(self.animations, fps=8, loop=True)

        self.add(pos, vel, spr, col,
                 anim,
                 Freeze(),
                 LightComponent(radius=20),
                 Team("player"),
                 RenderLayer(RenderLayer.ACTOR),
                 DepthAnchor(offset_y=16),
                 )

        self._set_animation("idle_front")

    @property
    def old_direction(self):
        return self._old_direction
    def stay_idle(self):
        self._direction.xy = 0, 0
        vel: Velocity = self.get(Velocity)
        vel.vxy = 0, 0
        dir_name = self._get_dir_name(self._old_direction)
        self._set_animation(f"idle_{dir_name}")

    def _set_animation(self, new_state: str):
        if self._current_animation_state != new_state:
            anim: AnimateSprite = self.get(AnimateSprite)
            anim.play(new_state)
            self._current_animation_state = new_state

    def input(self, events: list[Event]):
        freeze:Freeze = self.get(Freeze)
        if freeze.active:
             self._step_timer = 0.0
             return

        vel: Velocity = self.get(Velocity)
        keys = get_pressed()

        self._direction.update(0, 0)
        for key, vector in self._key_to_direction.items():
            if keys[key]:
                self._direction += vector

        if self._direction.length_squared() > 0:
            self._direction.normalize_ip()
            vel.vxy = (self._direction.x * self._speed, self._direction.y * self._speed)
            self._old_direction = self._direction.copy()
            dir_name = self._get_dir_name(self._direction)
            self._set_animation(f"walk_{dir_name}")
            self._play_footstep()
        else:
            vel.vxy = (0, 0)
            dir_name = self._get_dir_name(self._old_direction)
            self._set_animation(f"idle_{dir_name}")
            self._step_timer = 0.0

    def _play_footstep(self):
        now = pygame.time.get_ticks() / 1000.0
        if now - self._step_timer < self._step_interval:
            return
        self._step_timer = now
        self.audio_manager.play_sfx("sfx/footstep_1.wav", volume=0.42)

    def _get_dir_name(self, direction: Vector2) -> str:
        if direction.y != 0:
            return "back" if direction.y < 0 else "front"
        if direction.x != 0:
            return "right" if direction.x > 0 else "left"
        return "front"

    def _inject_death_animations(self):
        # Usa o strip de morte e disponibiliza para qualquer direcao.
        base_size = self.animations["idle_front"][0].get_size()
        base = "Top_Down_Adventure_Pack_v.1.0/Char_Sprites"
        strip = self.rm.load_image(f"{base}/char_death_all_dir_anim_strip_10.png")
        frames = self._slice_strip(strip, 10)
        resized = [pygame.transform.scale(frame, base_size) for frame in frames]
        for direction in ("front", "back", "left", "right"):
            self.animations[f"death_{direction}"] = resized

    def _slice_strip(self, strip: pygame.Surface, frame_count: int) -> list[pygame.Surface]:
        frame_w = strip.get_width() // frame_count
        frame_h = strip.get_height()
        frames = []
        for i in range(frame_count):
            rect = pygame.Rect(i * frame_w, 0, frame_w, frame_h)
            frame = strip.subsurface(rect).copy()
            bbox = frame.get_bounding_rect()
            if bbox.width > 0 and bbox.height > 0:
                frame = frame.subsurface(bbox).copy()
            frames.append(frame)
        return frames
