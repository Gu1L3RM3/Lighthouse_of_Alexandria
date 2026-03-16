import pygame

from core.components.collider import Collider
from core.components.phantom_ai import PhantomAI
from core.components.light_component import LightComponent
from core.managers.resource_manager import ResourceManager
from entities.enemies.base_enemy import EnemyBase


class PhantomEnemy(EnemyBase):
    def __init__(
        self,
        x: float,
        y: float,
        speed: float = 42.0,
        route: list[tuple[int, int]] | None = None,
        detection_radius: float = 90.0,
        touch_radius: float = 10.0,
        chase_speed: float = 58.0,
        max_hp: float = 130.0,
    ):
        animations = self._load_animations()
        super().__init__(
            x=x,
            y=y,
            animations=animations,
            collider=Collider(0, 0),
            route=route,
            speed=speed,
            max_hp=max_hp,
        )
        self.add(

            PhantomAI(
                detection_radius=detection_radius,
                touch_radius=touch_radius,
                chase_speed=chase_speed,
                patrol_speed=speed,
                route=route,
            ),
            LightComponent()
        )

    def _load_animations(self) -> dict[str, list[pygame.Surface]]:
        rm = ResourceManager.get()
        base = "Top_Down_Adventure_Pack_v.1.0/Enemies_Sprites/Phantom_Sprites"

        idle_left = rm.load_image(f"{base}/phantom_idle_anim_left_strip_4.png")
        idle_right = rm.load_image(f"{base}/phantom_idle_anim_right_strip_4.png")
        run_left = rm.load_image(f"{base}/phantom_run_anim_left_strip_6.png")
        run_right = rm.load_image(f"{base}/phantom_run_anim_right_strip_6.png")
        hit_left = rm.load_image(f"{base}/phantom_hit_anim_left_strip_4.png")
        hit_right = rm.load_image(f"{base}/phantom_hit_anim_right_strip_4.png")
        death_left = rm.load_image(f"{base}/phantom_death_anim_left_strip_8.png")
        death_right = rm.load_image(f"{base}/phantom_death_anim_right_strip_8.png")

        idle_left_frames = self._slice_strip(idle_left, 4)
        idle_right_frames = self._slice_strip(idle_right, 4)
        run_left_frames = self._slice_strip(run_left, 6)
        run_right_frames = self._slice_strip(run_right, 6)
        hit_left_frames = self._slice_strip(hit_left, 4)
        hit_right_frames = self._slice_strip(hit_right, 4)
        death_left_frames = self._slice_strip(death_left, 8)
        death_right_frames = self._slice_strip(death_right, 8)

        return {
            "idle_left": idle_left_frames,
            "idle_right": idle_right_frames,
            "idle_front": idle_right_frames,
            "idle_back": idle_left_frames,
            "walk_left": run_left_frames,
            "walk_right": run_right_frames,
            "walk_front": run_right_frames,
            "walk_back": run_left_frames,
            "hit_left": hit_left_frames,
            "hit_right": hit_right_frames,
            "hit_front": hit_right_frames,
            "hit_back": hit_left_frames,
            "death_left": death_left_frames,
            "death_right": death_right_frames,
            "death_front": death_right_frames,
            "death_back": death_left_frames,
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
