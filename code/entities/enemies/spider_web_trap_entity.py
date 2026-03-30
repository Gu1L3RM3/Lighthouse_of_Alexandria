import pygame

from core.ecs import Entity
from core.components.position import Position
from core.components.sprite import Sprite
from core.components.render_layer import RenderLayer
from core.components.spider_web_trap import SpiderWebTrap


class SpiderWebTrapEntity(Entity):
    def __init__(
        self,
        owner_id: int,
        center_x: float,
        center_y: float,
        radius: float,
        lifetime: float,
        slow_multiplier: float,
        slow_duration: float,
        arm_delay: float = 0.1,
    ):
        super().__init__()
        diameter = max(8, int(radius * 2))
        image = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        center = (diameter // 2, diameter // 2)
        pygame.draw.circle(image, (160, 188, 205, 120), center, diameter // 2)
        pygame.draw.circle(image, (226, 240, 248, 165), center, max(2, int(diameter * 0.42)), width=1)
        pygame.draw.circle(image, (244, 250, 255, 90), center, max(1, int(diameter * 0.18)))

        self.add(
            Position(center_x - (diameter / 2), center_y - (diameter / 2)),
            Sprite(image),
            RenderLayer(RenderLayer.WORLD),
            SpiderWebTrap(
                owner_id=owner_id,
                center_x=center_x,
                center_y=center_y,
                radius=radius,
                lifetime=lifetime,
                slow_multiplier=slow_multiplier,
                slow_duration=slow_duration,
                arm_delay=arm_delay,
            ),
        )
