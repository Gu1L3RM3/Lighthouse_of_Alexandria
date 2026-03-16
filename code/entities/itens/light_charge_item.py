import pygame
from pygame import Rect

from core.components.always_on_top import AlwaysOnTop
from core.components.animation_sprite import AnimateSprite
from core.components.area_trigger import AreaTrigger
from core.components.light_component import LightComponent
from core.components.position import Position
from core.components.sprite import Sprite
from core.managers.event_manager import EventManager
from core.managers.resource_manager import ResourceManager
from entities.itens.item import Item
from entities.player import Player


class LightChargeItem(Item):
    def __init__(self, x, y, active, props):
        super().__init__(x, y, active, props)
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
            LightComponent(radius=18),
            self.animate_sprite,
        )
        self.animate_sprite.play("idle")

    def _load_animations(self) -> dict[str, list[pygame.Surface]]:
        rm = ResourceManager.get()
        sheet = rm.load_image("itens/light_charge/coin_pickup.png")
        frames = self._slice_strip(sheet, 11)
        return {
            "idle": frames[:7],
            "collected": self._build_collected_frames(frames[7:]),
        }

    def _slice_strip(self, surface: pygame.Surface, frames: int) -> list[pygame.Surface]:
        frame_w = surface.get_width() // frames
        frame_h = surface.get_height()
        result = []
        for i in range(frames):
            rect = pygame.Rect(i * frame_w, 0, frame_w, frame_h)
            result.append(surface.subsurface(rect).copy())
        return result

    def _build_collected_frames(self, base_frames: list[pygame.Surface]) -> list[pygame.Surface]:
        result = []
        frame_count = len(base_frames)
        for i, source in enumerate(base_frames):
            progress = i / max(1, frame_count - 1)
            scale = 1.0 + progress * 0.25
            alpha = max(0, int(255 * (1.0 - progress * 0.2)))
            scaled = pygame.transform.scale(
                source,
                (
                    max(1, int(source.get_width() * scale)),
                    max(1, int(source.get_height() * scale)),
                ),
            )
            scaled.set_alpha(alpha)

            canvas_size = max(scaled.get_width(), scaled.get_height(), 18)
            canvas = pygame.Surface((canvas_size, canvas_size), pygame.SRCALPHA)
            rect = scaled.get_rect(center=(canvas_size // 2, canvas_size // 2))
            canvas.blit(scaled, rect)
            result.append(canvas)
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
        self.em.post({"type": "temporary_light_collected"})
        self.em.post({"type": "kill_entity", "id": self.id})
