import pygame

from core.circuit_tools.circuit_file_service import CircuitFileService
from core.components.animation_sprite import AnimateSprite
from core.components.freeze import Freeze
from core.components.health import Health
from core.components.path_follower import PathFollower
from core.components.phantom_ai import PhantomAI
from core.components.position import Position
from core.components.team import Team
from core.components.velocity import Velocity
from core.ecs import System
from core.settings import (
    GENERIC_LEVEL_BOMB_EDITOR_FILE,
    GENERIC_LEVEL_BOMB_ENEMY_HIT_MARGIN,
    GENERIC_LEVEL_BOMB_TARGET_RESISTOR,
    CELL_SIZE,
    path_in_circuitos,
)


class GenericLevelBombSystem(System):
    def __init__(self, scene):
        self.scene = scene
        self.circuits = CircuitFileService(CELL_SIZE)

    def update(self, entity_manager, dt: float):
        _ = entity_manager
        self.update_bombs(dt)

    def place_bomb(self):
        if not self.scene.bomb_manager.consume_bomb():
            self.scene.audio_manager.play_ui("sfx/ui_back.wav", volume=0.9)
            return

        self.sync_bomb_runtime()
        if not self.scene.player or not self.scene.player.has(Position):
            return

        player_pos: Position = self.scene.player.get(Position)
        center = player_pos.center_pos()
        params = self.scene.bomb_manager.current_params
        self.scene.pending_bombs.append(
            {
                "center": center,
                "total_delay": float(params.explosion_delay),
                "delay": float(params.explosion_delay),
                "radius": float(params.explosion_radius),
                "damage": float(params.damage),
            }
        )
        self.scene.audio_manager.play_sfx("sfx/lighthouse_ignite.wav", volume=0.58)

    def sync_bomb_runtime(self):
        bomb_results = self.scene.circuit_manager.get_circuit_values(GENERIC_LEVEL_BOMB_EDITOR_FILE)
        if not bomb_results:
            solver = self.circuits.solve(path_in_circuitos(f"{GENERIC_LEVEL_BOMB_EDITOR_FILE}.json"))
            if solver.is_solved:
                bomb_results = solver.get_resistor_results()
                total_values = solver.get_total_values()
                self.scene.circuit_manager.add_circuit_values(GENERIC_LEVEL_BOMB_EDITOR_FILE, bomb_results)
                self.scene.circuit_manager.add_total_values(GENERIC_LEVEL_BOMB_EDITOR_FILE, total_values)
        self.scene.bomb_manager.update_from_resistor_results(
            bomb_results,
            target_resistor=GENERIC_LEVEL_BOMB_TARGET_RESISTOR,
        )

    def update_bombs(self, dt: float):
        self.sync_bomb_runtime()
        if not self.scene.pending_bombs:
            return

        still_pending = []
        for bomb in self.scene.pending_bombs:
            bomb["delay"] -= dt
            if bomb["delay"] > 0:
                still_pending.append(bomb)
                continue
            self.explode_bomb(bomb)
        self.scene.pending_bombs = still_pending

    def explode_bomb(self, bomb_data: dict):
        center: pygame.Vector2 = bomb_data["center"]
        radius = float(bomb_data["radius"])
        damage = float(bomb_data["damage"])
        radius_sq = radius * radius
        enemy_radius_sq = (radius + float(GENERIC_LEVEL_BOMB_ENEMY_HIT_MARGIN)) ** 2

        self.scene.active_explosions.append(
            {
                "center": center,
                "radius": radius,
                "elapsed": 0.0,
                "duration": 0.36,
            }
        )
        shake_intensity = max(3.0, min(9.0, radius / 22.0))
        self.scene.camera.start_shake(duration=0.22, intensity=shake_intensity)
        self.scene.audio_manager.play_sfx("sfx/bombs/explosion_01.ogg", volume=0.45)

        enemies = self.scene.entity_mn.get_entities_with(Position, Team, Health)
        for enemy in enemies:
            team: Team = enemy.get(Team)
            if team.name != "enemy":
                continue
            enemy_pos: Position = enemy.get(Position)
            if (enemy_pos.center_pos() - center).length_squared() > enemy_radius_sq:
                continue
            self.damage_enemy(enemy, damage)

        if hasattr(self.scene, "spider_web_system"):
            try:
                self.scene.spider_web_system.destroy_traps_in_radius(self.scene.entity_mn, center, radius)
            except Exception:
                pass

        if self.scene.player and self.scene.player.has(Position):
            if (self.scene.player.get(Position).center_pos() - center).length_squared() <= radius_sq:
                self.trigger_player_death()

    def damage_enemy(self, enemy, damage: float):
        health: Health = enemy.get(Health)
        died = health.take_damage(damage)
        if not died:
            self.play_enemy_hit_feedback(enemy)
            return
        was_phantom = enemy.has(PhantomAI)

        if enemy.has(PathFollower):
            enemy.remove(PathFollower)
        if enemy.has(PhantomAI):
            enemy.remove(PhantomAI)

        if was_phantom and enemy.has(Freeze):
            enemy.get(Freeze).active = True

        if enemy.has(Velocity):
            enemy.get(Velocity).vxy = (0, 0)

        if enemy.has(AnimateSprite):
            anim: AnimateSprite = enemy.get(AnimateSprite)
            facing = "front"
            if hasattr(enemy, "get_facing_name"):
                facing = enemy.get_facing_name()
            death_state = f"death_{facing}"
            if death_state in anim.animations:
                anim.play(
                    death_state,
                    reset=True,
                    loop=False,
                    on_finish=lambda eid=enemy.id: self.scene.event_manager.post({"type": "kill_entity", "id": eid}),
                )
                return
        self.scene.event_manager.post({"type": "kill_entity", "id": enemy.id})

    def play_enemy_hit_feedback(self, enemy):
        if not enemy.has(AnimateSprite):
            return

        anim: AnimateSprite = enemy.get(AnimateSprite)
        facing = "front"
        if hasattr(enemy, "get_facing_name"):
            facing = enemy.get_facing_name()
        hit_state = f"hit_{facing}"
        if hit_state not in anim.animations:
            return

        def _resume_after_hit():
            if enemy.has(Velocity):
                vel: Velocity = enemy.get(Velocity)
                moving = vel.vel.length_squared() > 1e-6
            else:
                moving = False

            next_state = f"walk_{facing}" if moving else f"idle_{facing}"
            if next_state in anim.animations:
                anim.play(next_state, reset=True, loop=True)
                if hasattr(enemy, "_current_animation_state"):
                    enemy._current_animation_state = next_state

        anim.play(
            hit_state,
            reset=True,
            loop=False,
            on_finish=_resume_after_hit,
        )

    def trigger_player_death(self):
        if getattr(self.scene, "player_dead_by_enemy", False):
            return
        if hasattr(self.scene, "player_dead_by_enemy"):
            self.scene.player_dead_by_enemy = True

        player = self.scene.entity_mn.get_player()
        if not player:
            self.scene.death_flow_manager.handle_player_death()
            return

        if player.has(Freeze):
            player.get(Freeze).active = True
        if player.has(Velocity):
            player.get(Velocity).vxy = (0, 0)
        if player.has(AnimateSprite):
            anim: AnimateSprite = player.get(AnimateSprite)
            dir_name = "front"
            if hasattr(player, "_get_dir_name") and hasattr(player, "old_direction"):
                dir_name = player._get_dir_name(player.old_direction)
            anim.play(
                f"death_{dir_name}",
                reset=True,
                loop=False,
                on_finish=lambda: self.scene.death_flow_manager.handle_player_death(),
            )
            return
        self.scene.death_flow_manager.handle_player_death()
