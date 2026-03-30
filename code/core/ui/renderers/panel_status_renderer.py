import math
import pygame
from pygame import Rect
from functools import lru_cache

from core.components.panel_status import PanelStatus


class PanelStatusRenderer:
    def __init__(self):
        self._font_name = "consolas"

    @lru_cache(maxsize=96)
    def _build_label_surfaces(self, label_text: str, scale_key: int):
        scale = max(0.5, scale_key / 100.0)
        font_size = max(8, int(8 * scale))
        font = pygame.font.SysFont(self._font_name, font_size, bold=True)

        text_surface = font.render(label_text, True, (235, 219, 167))
        plate_pad_x = max(4, int(5 * scale))
        plate_pad_y = max(2, int(2 * scale))
        plate_w = text_surface.get_width() + plate_pad_x * 2
        plate_h = text_surface.get_height() + plate_pad_y * 2

        plate_surface = pygame.Surface((plate_w, plate_h), pygame.SRCALPHA)
        # Placa em tom bronze para combinar com a identidade visual do painel.
        pygame.draw.rect(plate_surface, (35, 28, 21, 232), plate_surface.get_rect(), border_radius=4)
        pygame.draw.rect(plate_surface, (141, 110, 64, 255), plate_surface.get_rect(), width=1, border_radius=4)
        plate_surface.blit(text_surface, (plate_pad_x, plate_pad_y))

        return plate_surface

    def _draw_panel_id_label(self, surface: pygame.Surface, draw_rect: Rect, panel_id: int | None, scale: float):
        if panel_id is None:
            return
        label_text = f"PAINEL {int(panel_id):02d}"
        scale_key = int(max(50, min(300, scale * 100)))
        plate_surface = self._build_label_surfaces(label_text, scale_key)
        plate_rect = plate_surface.get_rect(
            center=(
                draw_rect.centerx,
                draw_rect.top - max(8, int(10 * scale)),
            )
        )
        surface.blit(plate_surface, plate_rect)

    def draw(self, surface: pygame.Surface, draw_rect: Rect, status: PanelStatus, scale: float, panel_id: int | None = None):
        self._draw_panel_id_label(surface, draw_rect, panel_id, scale)

        led_radius = max(2, int(2 * scale))
        led_center = (
            draw_rect.right - max(4, int(6 * scale)),
            draw_rect.top + max(4, int(6 * scale)),
        )

        border_color = (28, 22, 12)
        glow_surface = pygame.Surface((led_radius * 6, led_radius * 6), pygame.SRCALPHA)
        glow_rect = glow_surface.get_rect(center=led_center)

        if status.state == "inactive":
            led_color = (80, 80, 84)
            glow_color = (110, 110, 120, 40)
            glow_strength = 1.0
        elif status.state == "done":
            led_color = (108, 220, 126)
            glow_color = (110, 230, 140, 95)
            glow_strength = 1.0
        else:
            pulse = (math.sin(pygame.time.get_ticks() * 0.006) + 1.0) * 0.5
            glow_strength = 0.45 + pulse * 0.55
            led_color = (224, 178, 84)
            glow_color = (236, 196, 102, int(100 * glow_strength))

        pygame.draw.circle(
            glow_surface,
            glow_color,
            (glow_surface.get_width() // 2, glow_surface.get_height() // 2),
            int(led_radius * 2.5 * glow_strength),
        )
        surface.blit(glow_surface, glow_rect.topleft)
        pygame.draw.circle(surface, border_color, led_center, led_radius + 1)
        pygame.draw.circle(surface, led_color, led_center, led_radius)
