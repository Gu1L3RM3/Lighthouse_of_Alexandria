import pygame
from pygame import Rect

from core.components.area_trigger import AreaTrigger
from core.components.animation_sprite import AnimateSprite
from core.components.position import Position
from core.components.sprite import Sprite
from core.components.always_on_top import AlwaysOnTop
from core.components.light_component import LightComponent
from core.managers.event_manager import EventManager
from core.managers.resource_manager import ResourceManager
from entities.itens.item import Item
from entities.player import Player


class CrystalInvisibilityItem(Item):
    def __init__(self, x, y, active, props):
        super().__init__(x, y, active, props)
        self.duration = float(props.get("duration", 6.0))
        self.respawn_delay = float(props.get("respawn_delay", 20.0))
        self.em = EventManager.get()
        self.animations = self._load_animations()
        self.animate_sprite = AnimateSprite(self.animations, fps=8, loop=True)
        self.area_trigger = Rect(0, 0, 16, 16)
        self._collected = False

        self.add(
            Position(x, y),
            AreaTrigger(self.area_trigger, active=active, on_entered=self.on_collect),
            Sprite(self.animations["idle"][0]),
            AlwaysOnTop(),
            LightComponent(radius=24),
            self.animate_sprite,
        )
        self.animate_sprite.play("idle")

    def _load_animations(self) -> dict[str, list[pygame.Surface]]:
        rm = ResourceManager.get()
        base = "Top_Down_Adventure_Pack_v.1.0/Props_Items_(animated)"
        idle_strip = rm.load_image(f"{base}/crystal_item_anim_strip_6.png")
        collected_strip = rm.load_image(f"{base}/crystal_item_anim_collected_strip_5.png")
        return {
            "idle": self._slice_strip(idle_strip, 6),
            "collected": self._slice_strip(collected_strip, 5),
        }

    def _slice_strip(self, surface: pygame.Surface, frames: int) -> list[pygame.Surface]:
        frame_w = surface.get_width() // frames
        frame_h = surface.get_height()
        result = []
        for i in range(frames):
            rect = pygame.Rect(i * frame_w, 0, frame_w, frame_h)
            result.append(surface.subsurface(rect).copy())
        return result

    def on_collect(self, entity):
        if self._collected or not isinstance(entity, Player):
            return
        self._collected = True
        trigger: AreaTrigger = self.get(AreaTrigger)
        trigger.active = False
        self.animate_sprite.play(
            "collected",
            reset=True,
            loop=False,
            on_finish=self._after_collected,
        )

    def _after_collected(self):
        pos: Position = self.get(Position)
        self.em.post({"type": "player_invisible_to_enemies_started", "duration": self.duration})
        self.em.post(
            {
                "type": "crystal_invisibility_collected",
                "spawn_x": pos.x,
                "spawn_y": pos.y,
                "duration": self.duration,
                "respawn_delay": self.respawn_delay,
            }
        )
        self.em.post({"type": "kill_entity", "id": self.id})
