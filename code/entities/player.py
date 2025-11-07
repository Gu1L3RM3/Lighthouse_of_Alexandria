from core.components.position import Position
from core.components.velocity import Velocity
from core.components.sprite import Sprite
from core.components.collider import Collider
from core.components.freeze import Freeze
from core.components.animation_sprite import AnimateSprite
from core.settings import *
from core.ecs import Entity
from core.components.weapon_slot import WeaponSlot
from entities.weapons.sword import Sword   
from pygame import Vector2, Event
from core.managers.resource_manager import ResourceManager
from pygame.key import get_pressed
from core.components.always_on_top import AlwaysOnTop
class Player(Entity):
    def __init__(self, x: float = 100, y: float = 100):
        super().__init__()
        self.rm = ResourceManager.get()
        self._direction = Vector2(0, 0)
        self._old_direction = Vector2(0, 1)
        self._speed = 100
        self._current_animation_state = "" 
        self.attack=False

        self._key_to_direction = {
            PLAYER_RIGHT: Vector2(1, 0),
            PLAYER_LEFT: Vector2(-1, 0),
            PLAYER_DOWN: Vector2(0, 1),
            PLAYER_UP: Vector2(0, -1),
        }

        pos = Position(x, y)
        vel = Velocity(0, 0)
        col = Collider(10, 6, offset_x=20, offset_y=36)

        self.animations = self.rm.load_sprite_sheet("player",trim_transparent=False)
        spr = Sprite(self.animations["idle_front"][0])
        anim = AnimateSprite(self.animations, fps=8, loop=True)

        weapon_slot = WeaponSlot(weapon=Sword())  
        self.add(pos, vel, spr, col,
                 anim, weapon_slot,
                 Freeze(),AlwaysOnTop(),
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
        else:
            vel.vxy = (0, 0)
            dir_name = self._get_dir_name(self._old_direction)
            self._set_animation(f"idle_{dir_name}")

    def _get_dir_name(self, direction: Vector2) -> str:
        if direction.y != 0:
            return "back" if direction.y < 0 else "front"
        if direction.x != 0:
            return "right" if direction.x > 0 else "left"
        return "front"
    
