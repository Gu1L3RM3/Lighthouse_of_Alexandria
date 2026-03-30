import pygame

from core.settings import GENERIC_LEVEL_BOMB_VISUAL_SCALE


class GenericLevelBombRenderer:
    @staticmethod
    def draw_active_explosions(scene, dt: float):
        if not scene.active_explosions:
            return

        alive_effects = []
        for effect in scene.active_explosions:
            effect["elapsed"] += dt
            ratio = effect["elapsed"] / effect["duration"]
            if ratio >= 1.0:
                continue

            center = effect["center"]
            base_radius = float(effect["radius"])
            draw_radius = int(max(1, base_radius * ratio * scene.scale))
            off_x, off_y = scene.camera.render_offset
            center_scaled = (
                int(center.x * scene.scale - scene.camera.viewport.x + off_x),
                int(center.y * scene.scale - scene.camera.viewport.y + off_y),
            )
            if scene.bomb_boom_frames:
                frame_index = min(len(scene.bomb_boom_frames) - 1, int(ratio * len(scene.bomb_boom_frames)))
                frame = scene.bomb_boom_frames[frame_index]
                sprite = pygame.transform.scale(
                    frame,
                    (
                        max(20, int(draw_radius * 2.0)),
                        max(20, int(draw_radius * 2.0)),
                    ),
                )
                rect = sprite.get_rect(center=center_scaled)
                scene.screen.blit(sprite, rect)
            else:
                alpha = int(max(0, 185 * (1.0 - ratio)))
                core_alpha = int(max(0, 230 * (1.0 - ratio * 1.15)))
                overlay = pygame.Surface((draw_radius * 2 + 12, draw_radius * 2 + 12), pygame.SRCALPHA)
                center_overlay = (overlay.get_width() // 2, overlay.get_height() // 2)
                pygame.draw.circle(overlay, (80, 200, 255, alpha), center_overlay, draw_radius)
                pygame.draw.circle(overlay, (190, 245, 255, core_alpha), center_overlay, max(2, int(draw_radius * 0.35)))
                ring_radius = max(2, int(draw_radius * 0.78))
                ring_width = max(1, int(2 * scene.scale))
                pygame.draw.circle(overlay, (120, 230, 255, alpha), center_overlay, ring_radius, ring_width)
                scene.screen.blit(
                    overlay,
                    (center_scaled[0] - overlay.get_width() // 2, center_scaled[1] - overlay.get_height() // 2),
                )
            alive_effects.append(effect)

        scene.active_explosions = alive_effects

    @staticmethod
    def draw_pending_bombs(scene):
        if not scene.pending_bombs:
            return
        for bomb in scene.pending_bombs:
            center = bomb["center"]
            delay = max(0.001, float(bomb["delay"]))
            total = max(0.001, float(bomb.get("total_delay", delay)))
            ratio = max(0.0, min(1.0, delay / total))

            off_x, off_y = scene.camera.render_offset
            world_center = (
                int(center.x * scene.scale - scene.camera.viewport.x + off_x),
                int(center.y * scene.scale - scene.camera.viewport.y + off_y),
            )
            radius_world = max(1, int(float(bomb["radius"]) * scene.scale))
            preview_overlay = pygame.Surface((radius_world * 2 + 6, radius_world * 2 + 6), pygame.SRCALPHA)
            pc = (preview_overlay.get_width() // 2, preview_overlay.get_height() // 2)
            preview_alpha = int(42 + (26 * (1.0 - ratio)))
            ring_alpha = int(128 + (44 * (1.0 - ratio)))
            pygame.draw.circle(preview_overlay, (100, 215, 255, preview_alpha), pc, radius_world)
            pygame.draw.circle(
                preview_overlay,
                (168, 238, 255, ring_alpha),
                pc,
                radius_world,
                width=max(1, int(2 * scene.scale)),
            )
            scene.screen.blit(
                preview_overlay,
                (world_center[0] - preview_overlay.get_width() // 2, world_center[1] - preview_overlay.get_height() // 2),
            )

            blink = int((pygame.time.get_ticks() / 120) % 2)
            pulse_scale = 1.0 + (0.1 * (1.0 - ratio)) + (0.08 if blink == 0 else 0.0)

            if scene.bomb_prefuze_frames:
                speed_up = 1.0 + (1.4 * (1.0 - ratio))
                ticks = pygame.time.get_ticks() / 170.0
                frame_index = int(ticks * speed_up) % len(scene.bomb_prefuze_frames)
                frame = scene.bomb_prefuze_frames[frame_index]
                sprite = pygame.transform.scale(
                    frame,
                    (
                        max(10, int(frame.get_width() * scene.scale * pulse_scale * GENERIC_LEVEL_BOMB_VISUAL_SCALE)),
                        max(10, int(frame.get_height() * scene.scale * pulse_scale * GENERIC_LEVEL_BOMB_VISUAL_SCALE)),
                    ),
                )
                rect = sprite.get_rect(center=world_center)
                scene.screen.blit(sprite, rect)
            elif scene.bomb_world_sprite is not None:
                sprite = pygame.transform.scale(
                    scene.bomb_world_sprite,
                    (
                        max(10, int(scene.bomb_world_sprite.get_width() * scene.scale * pulse_scale * 0.75)),
                        max(10, int(scene.bomb_world_sprite.get_height() * scene.scale * pulse_scale * 0.75)),
                    ),
                )
                rect = sprite.get_rect(center=world_center)
                scene.screen.blit(sprite, rect)
            else:
                radius = max(4, int(7 * scene.scale * pulse_scale))
                color = (20, 90, 120) if blink else (90, 230, 255)
                pygame.draw.circle(scene.screen, color, world_center, radius)

            bar_w = max(18, int(24 * scene.scale))
            bar_h = max(3, int(3 * scene.scale))
            bx = world_center[0] - bar_w // 2
            by = world_center[1] - max(14, int(16 * scene.scale))
            pygame.draw.rect(scene.screen, (20, 20, 20), pygame.Rect(bx, by, bar_w, bar_h))
            pygame.draw.rect(scene.screen, (255, 196, 96), pygame.Rect(bx, by, int(bar_w * ratio), bar_h))

