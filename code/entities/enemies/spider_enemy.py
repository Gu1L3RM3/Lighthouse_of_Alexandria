import pygame

from core.components.collider import Collider
from core.managers.resource_manager import ResourceManager
from entities.enemies.base_enemy import EnemyBase


class SpiderEnemy(EnemyBase):
    def __init__(
        self,
        x: float,
        y: float,
        speed: float = 42.0,
        route: list[tuple[int, int]] | None = None,
        max_hp: float = 130.0,
    ):
        animations = self._load_animations()
        super().__init__(
            x=x,
            y=y,
            animations=animations,
            collider=Collider(10, 8, offset_x=3, offset_y=4),
            route=route,
            speed=speed,
            max_hp=max_hp,
        )

    def _load_animations(self) -> dict[str, list[pygame.Surface]]:
        rm = ResourceManager.get()
        base = "Top_Down_Adventure_Pack_v.1.0/Enemies_Sprites/Spider_Sprites"

        idle_strip = rm.load_image(f"{base}/spider_idle_anim_all_dir_strip_4.png")
        run_strip = rm.load_image(f"{base}/spider_run_anim_all_dir_strip_4.png")
        hit_strip = rm.load_image(f"{base}/spider_hit_anim_all_dir_strip_4.png")
        death_strip = rm.load_image(f"{base}/spider_death_anim_all_dir_strip_8.png")

        idle_frames = self._slice_strip(idle_strip, 4)
        run_frames = self._slice_strip(run_strip, 4)
        hit_frames = self._slice_strip(hit_strip, 4)
        death_frames = self._slice_strip(death_strip, 8)

        return {
            "idle_front": idle_frames,
            "idle_back": idle_frames,
            "idle_left": idle_frames,
            "idle_right": idle_frames,
            "walk_front": run_frames,
            "walk_back": run_frames,
            "walk_left": run_frames,
            "walk_right": run_frames,
            "hit_front": hit_frames,
            "hit_back": hit_frames,
            "hit_left": hit_frames,
            "hit_right": hit_frames,
            "death_front": death_frames,
            "death_back": death_frames,
            "death_left": death_frames,
            "death_right": death_frames,
        }

    def _slice_strip(self, surface: pygame.Surface, frames: int) -> list[pygame.Surface]:
        frame_w = surface.get_width() // frames
        frame_h = surface.get_height()
        result = []
        for i in range(frames):
            rect = pygame.Rect(i * frame_w, 0, frame_w, frame_h)
            frame = surface.subsurface(rect).copy()
            result.append(frame)
        return result
