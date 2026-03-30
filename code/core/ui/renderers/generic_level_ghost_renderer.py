import pygame

from core.settings import GENERIC_LEVEL_GHOST_REBIRTH_ANIM_SECONDS


class GenericLevelGhostRenderer:
    @staticmethod
    def draw_rebirth_effects(scene):
        if not scene.ghost_rebirth_effects:
            return

        off_x, off_y = scene.camera.render_offset
        for effect in scene.ghost_rebirth_effects:
            duration = max(0.001, float(effect.get("duration", GENERIC_LEVEL_GHOST_REBIRTH_ANIM_SECONDS)))
            ratio = max(0.0, min(1.0, float(effect.get("elapsed", 0.0)) / duration))
            x = float(effect.get("x", 0.0))
            y = float(effect.get("y", 0.0))

            center = (
                int(x * scene.scale - scene.camera.viewport.x + off_x),
                int(y * scene.scale - scene.camera.viewport.y + off_y),
            )
            base_r = max(8, int(8 * scene.scale))
            pulse_r = int(base_r + ratio * (20 * scene.scale))
            core_r = max(2, int(base_r * (0.32 + ratio * 0.55)))
            alpha = int(170 * (1.0 - ratio))
            core_alpha = int(220 * (0.3 + 0.7 * ratio))

            overlay = pygame.Surface((pulse_r * 2 + 12, pulse_r * 2 + 12), pygame.SRCALPHA)
            local_center = (overlay.get_width() // 2, overlay.get_height() // 2)
            pygame.draw.circle(overlay, (96, 180, 255, alpha), local_center, pulse_r, width=max(1, int(2 * scene.scale)))
            pygame.draw.circle(overlay, (160, 230, 255, int(alpha * 0.6)), local_center, max(1, int(pulse_r * 0.62)))
            pygame.draw.circle(overlay, (220, 245, 255, core_alpha), local_center, core_r)
            scene.screen.blit(
                overlay,
                (center[0] - overlay.get_width() // 2, center[1] - overlay.get_height() // 2),
            )

