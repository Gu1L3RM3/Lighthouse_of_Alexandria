import pygame
import shutil
from pathlib import Path
from pygame import Surface
from core.components.animation_sprite import AnimateSprite
from core.components.area_trigger import AreaTrigger
from core.components.label_component import LabelComponent
from core.components.dialogue import Dialogue
from core.components.collider import Collider
from core.components.health import Health
from core.components.team import Team
from core.settings import *
from scenes.base_scene import BaseScene
from scenes.circuit_editor import CircuitEditor
from entities.dialogue_area import DialogueArea
from entities.animated_tiles.iron_gate import IronGate
from entities.enemies.enemy_factory import EnemyFactory
from entities.enemies.phantom_enemy import PhantomEnemy
from entities.itens.resistor_item import ResistorItem
from entities.itens.old_paper import OldPaper
from entities.animated_tiles.door import Door
from entities.itens.control_pannel import ControlPannel
from entities.itens.crystal_invisibility_item import CrystalInvisibilityItem
from entities.npcs.arquimedes import Arquimedes
from core.components.position import Position
from core.components.velocity import Velocity
from core.components.freeze import Freeze
from core.components.phantom_ai import PhantomAI
from core.components.path_follower import PathFollower
from core.ui.widgets.fps_widget import FPSWidget
from core.ui.widgets.lives_widget import LivesWidget
from core.ui.widgets.alert_dialog import AlertDialog
from core.ui.widgets.interaction_key_widget import InteractionKeyWidget
from core.map.tile_map_loader import TileMapLoader
from core.map.map_entity_spawner import MapEntitySpawner
from core.map.map_renderer import MapRenderer
from core.managers.scene_manager import SceneManager
from core.managers.death_flow_manager import DeathFlowManager
from core.managers.audio_manager import AudioManager
from core.managers.bomb_manager import BombManager
from core.circuit_tools.storage_circuit_manager import StorageCircuitManager
from core.managers.circuit_manager import CircuitManager
from core.ui.dialogue_interaction_hud_controller import DialogueInteractionHUDController
from core.ui.widgets.button import Button
from core.ui.widgets.bomb_status_widget import BombStatusWidget
from core.ui.widgets.gesture_detector import ClickType

class BaseGenericLevel(BaseScene):
    def __init__(self, screen: Surface, level_path: str):
        self.loader = TileMapLoader()
        self.level_path = level_path
        self.tile_map = self.loader.load(f"fases/{self.level_path}.tmx")
        self.scale = 2

        super().__init__(screen, self.tile_map.map_width * self.scale, self.tile_map.map_height * self.scale)
        self.camera.scale = self.scale
        self.map_renderer = MapRenderer(self.tile_map, self.camera, self.screen, self.scale)
        self.bomb_manager = BombManager(
            bombs_per_level=GENERIC_LEVEL_BOMB_COUNT_PER_LEVEL,
            default_netlist_path=path_in_ltspice(GENERIC_LEVEL_BOMB_DEFAULT_NETLIST),
        )
        self._configure_bomb_balance_profile()
        self.pending_bombs: list[dict] = []
        self.active_explosions: list[dict] = []
        self.crystal_respawn_queue: list[dict] = []
        self.ghost_respawn_queue: list[dict] = []
        self.ghost_rebirth_effects: list[dict] = []
        self._ghost_spawn_templates: dict[str, dict] = {}
        self._ghost_entity_to_spawn_key: dict[int, str] = {}
        self._last_frame_dt = 0.0
        self.bomb_world_sprite = None
        self.bomb_prefuze_frames: list[pygame.Surface] = []
        self.bomb_boom_frames: list[pygame.Surface] = []
        
        self.set_ui()
        self.set_map()
        self._configure_persistent_area_dialogues()
        self._disable_default_arquimedes_dialogue()

        self.can_set_resistors = True
        self.player = self.entity_mn.get_player()
        self.camera.follow = self.player
        self.index_dialog_for_old_paper = '5'
        
        self.storage_circuit = StorageCircuitManager()
        self.scene_manager = SceneManager.get()
        self.audio_manager = AudioManager.get()
        self.death_flow_manager = DeathFlowManager.get()
        self.circuit_manager = CircuitManager.get()
        self.dialogue_hud = DialogueInteractionHUDController(
            self.entity_mn,
            self.dialog_system,
            self.interaction_key_widget,
        )
        # Mantem o recurso de debug no codigo, mas desativado por padrao.
        self.debug_interaction_areas = False
        self._temporary_light_timer = 0.0
        self._temporary_light_restore_enabled = None
        
        # Subclasses will override this
        self.set_systems() 
        
        self.door = self.entity_mn.get_entities_by_class(Door)
        if self.door:
            self.door = self.door[0]
        self._set_bomb_visuals()

    def _configure_bomb_balance_profile(self):
        level_name = Path(self.level_path).stem.lower()
        if level_name in {"fase_8", "final_level"}:
            self.bomb_manager.set_balance_profile("final")
            return
        if level_name in {"fase_6", "fase_7"}:
            self.bomb_manager.set_balance_profile("challenging")
            return
        self.bomb_manager.set_balance_profile("standard")
            
    def set_ui(self):
        fps = FPSWidget()
        lives = LivesWidget(pos=(10, 42))
        self.ui_manager.add(fps)
        self.ui_manager.add(lives)
        top_button_gap = 20
        top_button_step = 142 + top_button_gap
        nucleo_x = self.screen.get_width() - 92
        help_x = nucleo_x - top_button_step
        menu_x = help_x - top_button_step
        idle = pygame.transform.scale(self.resources.load_image("buttons/short.png"), (142, 78))
        pressed = pygame.transform.scale(self.resources.load_image("buttons/short_pressed.png"), (142, 78))
        self.menu_button = Button(
            init_surface=idle,
            surface_pressed=pressed,
            pos_center=(menu_x, 44),
            click_type=ClickType.AFTER_RELEASED,
            action=lambda: SceneManager.get().open_menu(0.35),
            text="MENU",
            font_size=11,
            color_text=(245, 230, 170),
        )
        self.help_button = Button(
            init_surface=idle.copy(),
            surface_pressed=pressed.copy(),
            pos_center=(help_x, 44),
            click_type=ClickType.AFTER_RELEASED,
            action=lambda: SceneManager.get().open_help(0.35),
            text="HELP",
            font_size=11,
            color_text=(245, 230, 170),
        )
        self.edit_bomb_button = Button(
            init_surface=idle.copy(),
            surface_pressed=pressed.copy(),
            pos_center=(nucleo_x, 44),
            click_type=ClickType.AFTER_RELEASED,
            action=self.open_bomb_editor,
            text="NUCLEO",
            font_size=10,
            color_text=(245, 230, 170),
        )
        self.bomb_status_widget = BombStatusWidget(self.bomb_manager, pos=(10, 86))
        self.ui_manager.add(self.menu_button, self.help_button, self.edit_bomb_button, self.bomb_status_widget)
        self.interaction_key_widget = InteractionKeyWidget(self.screen.get_size(), label="ENTRAR")
        self.ui_manager.add(self.interaction_key_widget)

    def _set_bomb_visuals(self):
        try:
            icon = self.resources.load_image("circuit_components/eletron.png")
            self.bomb_world_sprite = pygame.transform.scale(icon, (18, 18))
        except Exception:
            self.bomb_world_sprite = None
        self.bomb_prefuze_frames = []
        self.bomb_boom_frames = []

    def _slice_strip(self, strip: pygame.Surface, frame_count: int) -> list[pygame.Surface]:
        if frame_count <= 0:
            return []
        frame_w = strip.get_width() // frame_count
        frame_h = strip.get_height()
        frames = []
        for i in range(frame_count):
            rect = pygame.Rect(i * frame_w, 0, frame_w, frame_h)
            frames.append(strip.subsurface(rect).copy())
        return frames

    def set_map(self):
        spawner = MapEntitySpawner()
        spawner.spawn_entities(self.tile_map, self.entity_mn)
        self.player = self.entity_mn.get_player()
        self.physics_system.cache_static_colliders(self.entity_mn)
        self._capture_initial_ghost_spawn_templates()

    def _capture_initial_ghost_spawn_templates(self):
        self._ghost_spawn_templates.clear()
        self._ghost_entity_to_spawn_key.clear()
        routes = self._extract_enemy_routes_from_map()

        enemy_layer = None
        for layer in self.tile_map.tmx_data.objectgroups:
            if (layer.name or "").lower() == "enemies":
                enemy_layer = layer
                break
        if enemy_layer is None:
            return

        spawn_index = 0
        for obj in enemy_layer:
            props = {k.lower(): v for k, v in (obj.properties or {}).items()}
            enemy_type = (obj.type or props.get("enemy_type") or obj.name or "spider").lower()
            if enemy_type != "phantom":
                continue

            route_id = str(props.get("route_id", "")).lower().strip()
            route = routes.get(route_id) if route_id else None
            if route:
                start_tile = (
                    int(obj.x // self.tile_map.tile_width),
                    int(obj.y // self.tile_map.tile_height),
                )
                if route[0] != start_tile:
                    route = [start_tile, *route]

            spawn_key = f"phantom_spawn_{spawn_index}"
            spawn_index += 1
            self._ghost_spawn_templates[spawn_key] = {
                "enemy_type": enemy_type,
                "x": float(obj.x),
                "y": float(obj.y),
                "props": dict(props),
                "route": [tuple(tile) for tile in (route or [])],
                "pending_respawn": False,
                "active_entity_id": None,
            }

        self._bind_existing_ghost_entities_to_templates()

    def _extract_enemy_routes_from_map(self) -> dict[str, list[tuple[int, int]]]:
        routes: dict[str, list[tuple[int, tuple[int, int]]]] = {}
        for layer in self.tile_map.tmx_data.objectgroups:
            if (layer.name or "").lower() != "enemy_routes":
                continue
            for obj in layer:
                properties = {k.lower(): v for k, v in (obj.properties or {}).items()}
                route_id = str(properties.get("route_id") or obj.name or "").lower().strip()
                if not route_id:
                    continue
                order = int(properties.get("order", 0))
                tile_point = (
                    int(obj.x // self.tile_map.tile_width),
                    int(obj.y // self.tile_map.tile_height),
                )
                routes.setdefault(route_id, []).append((order, tile_point))

        normalized_routes: dict[str, list[tuple[int, int]]] = {}
        for route_id, points in routes.items():
            ordered_points = sorted(points, key=lambda p: p[0])
            normalized_routes[route_id] = [tile for _, tile in ordered_points]
        return normalized_routes

    def _bind_existing_ghost_entities_to_templates(self):
        self._ghost_entity_to_spawn_key.clear()
        for template in self._ghost_spawn_templates.values():
            template["pending_respawn"] = False
            template["active_entity_id"] = None

        ghosts: list[PhantomEnemy] = self.entity_mn.get_entities_by_class(PhantomEnemy)
        unmatched_ghosts = list(ghosts)

        for spawn_key, template in self._ghost_spawn_templates.items():
            target_x = float(template["x"])
            target_y = float(template["y"])
            chosen = None
            chosen_dist = None
            for ghost in unmatched_ghosts:
                if not ghost.has(Position):
                    continue
                pos: Position = ghost.get(Position)
                dist_sq = ((float(pos.x) - target_x) ** 2) + ((float(pos.y) - target_y) ** 2)
                if chosen is None or dist_sq < chosen_dist:
                    chosen = ghost
                    chosen_dist = dist_sq
            if chosen is None:
                continue
            template["active_entity_id"] = chosen.id
            self._ghost_entity_to_spawn_key[chosen.id] = spawn_key
            unmatched_ghosts.remove(chosen)

    def _queue_ghost_respawn_by_entity_id(self, entity_id: int, death_x: float | None = None, death_y: float | None = None):
        spawn_key = self._ghost_entity_to_spawn_key.pop(entity_id, None)
        if spawn_key is None:
            return
        template = self._ghost_spawn_templates.get(spawn_key)
        if not template:
            return
        if template.get("pending_respawn", False):
            return
        template["active_entity_id"] = None
        template["pending_respawn"] = True
        self.ghost_respawn_queue.append(
            {
                "spawn_key": spawn_key,
                "remaining": float(GENERIC_LEVEL_GHOST_RESPAWN_SECONDS),
                "respawn_x": death_x,
                "respawn_y": death_y,
            }
        )

    def _spawn_ghost_from_template(self, spawn_key: str, respawn_x: float | None = None, respawn_y: float | None = None):
        template = self._ghost_spawn_templates.get(spawn_key)
        if not template:
            return
        props = dict(template.get("props", {}))
        route = [tuple(tile) for tile in template.get("route", [])]
        spawn_x = float(template.get("x", 0.0)) if respawn_x is None else float(respawn_x)
        spawn_y = float(template.get("y", 0.0)) if respawn_y is None else float(respawn_y)
        enemy = EnemyFactory.create(
            enemy_type=str(template.get("enemy_type", "phantom")),
            x=spawn_x,
            y=spawn_y,
            props=props,
            route=route,
        )
        self.entity_mn.add_entity(enemy)
        template["pending_respawn"] = False
        template["active_entity_id"] = enemy.id
        self._ghost_entity_to_spawn_key[enemy.id] = spawn_key

    def _start_ghost_rebirth_effect(self, spawn_key: str, respawn_x: float | None = None, respawn_y: float | None = None):
        template = self._ghost_spawn_templates.get(spawn_key)
        if not template:
            return
        spawn_x = float(template.get("x", 0.0)) if respawn_x is None else float(respawn_x)
        spawn_y = float(template.get("y", 0.0)) if respawn_y is None else float(respawn_y)
        self.ghost_rebirth_effects.append(
            {
                "spawn_key": spawn_key,
                "x": spawn_x,
                "y": spawn_y,
                "elapsed": 0.0,
                "duration": float(GENERIC_LEVEL_GHOST_REBIRTH_ANIM_SECONDS),
            }
        )

    def _update_ghost_respawns(self, dt: float):
        if not self.ghost_respawn_queue:
            return
        still_waiting = []
        for entry in self.ghost_respawn_queue:
            entry["remaining"] -= dt
            if entry["remaining"] > 0:
                still_waiting.append(entry)
                continue
            self._start_ghost_rebirth_effect(
                str(entry.get("spawn_key", "")),
                respawn_x=entry.get("respawn_x"),
                respawn_y=entry.get("respawn_y"),
            )
        self.ghost_respawn_queue = still_waiting

    def _update_ghost_rebirth_effects(self, dt: float):
        if not self.ghost_rebirth_effects:
            return
        still_animating = []
        for effect in self.ghost_rebirth_effects:
            effect["elapsed"] += dt
            duration = max(0.001, float(effect.get("duration", GENERIC_LEVEL_GHOST_REBIRTH_ANIM_SECONDS)))
            if effect["elapsed"] < duration:
                still_animating.append(effect)
                continue
            self._spawn_ghost_from_template(
                str(effect.get("spawn_key", "")),
                respawn_x=effect.get("x"),
                respawn_y=effect.get("y"),
            )
            self.audio_manager.play_sfx("sfx/light_on.wav", volume=0.82)
        self.ghost_rebirth_effects = still_animating

    def _draw_ghost_rebirth_effects(self):
        if not self.ghost_rebirth_effects:
            return

        off_x, off_y = self.camera.render_offset
        for effect in self.ghost_rebirth_effects:
            duration = max(0.001, float(effect.get("duration", GENERIC_LEVEL_GHOST_REBIRTH_ANIM_SECONDS)))
            ratio = max(0.0, min(1.0, float(effect.get("elapsed", 0.0)) / duration))
            x = float(effect.get("x", 0.0))
            y = float(effect.get("y", 0.0))

            center = (
                int(x * self.scale - self.camera.viewport.x + off_x),
                int(y * self.scale - self.camera.viewport.y + off_y),
            )
            base_r = max(8, int(8 * self.scale))
            pulse_r = int(base_r + ratio * (20 * self.scale))
            core_r = max(2, int(base_r * (0.32 + ratio * 0.55)))
            alpha = int(170 * (1.0 - ratio))
            core_alpha = int(220 * (0.3 + 0.7 * ratio))

            overlay = pygame.Surface((pulse_r * 2 + 12, pulse_r * 2 + 12), pygame.SRCALPHA)
            local_center = (overlay.get_width() // 2, overlay.get_height() // 2)
            pygame.draw.circle(overlay, (96, 180, 255, alpha), local_center, pulse_r, width=max(1, int(2 * self.scale)))
            pygame.draw.circle(overlay, (160, 230, 255, int(alpha * 0.6)), local_center, max(1, int(pulse_r * 0.62)))
            pygame.draw.circle(overlay, (220, 245, 255, core_alpha), local_center, core_r)
            self.screen.blit(
                overlay,
                (center[0] - overlay.get_width() // 2, center[1] - overlay.get_height() // 2),
            )

    def _configure_persistent_area_dialogues(self):
        dialogue_areas: list[DialogueArea] = self.entity_mn.get_entities_by_class(DialogueArea)
        for area in dialogue_areas:
            dialogue: Dialogue = area.get(Dialogue)
            dialogue.active_status = True
            dialogue.auto_start = False
            dialogue.triggered = False

    def _disable_default_arquimedes_dialogue(self):
        arquimedes_list: list[Arquimedes] = self.entity_mn.get_entities_by_class(Arquimedes)
        for arquimedes in arquimedes_list:
            if not arquimedes.has(Dialogue):
                continue
            dialogue: Dialogue = arquimedes.get(Dialogue)
            dialogue.active_status = False
        
    def set_resistors(self):
        if not self.can_set_resistors:
            return
        
        self.can_set_resistors = False
        self.storage_circuit.remove_all_components()

        resistors_itens :list[ResistorItem] = self.entity_mn.get_entities_by_class(ResistorItem)
        amount = len(resistors_itens)
        resistor_values = self.circuit_manager.random_list_resistors(amount)

        resistors_per_area:dict[int,list[str]] = {}

        for index, resistor_item in enumerate(resistors_itens):
            new_value = resistor_values[index]
            label: LabelComponent = resistor_item.get(LabelComponent)
            if label:
                label.value = new_value
            resistor_item.value = new_value

            area_id = resistor_item.area_id
            if area_id not in resistors_per_area:
                resistors_per_area[area_id] = []
            resistors_per_area[area_id].append(new_value)

        self.event_manager.post({'type':'set_solutions','components':resistors_per_area})

    def subscribe_panels(self):
        pannels: list[ControlPannel] = self.entity_mn.get_entities_by_class(ControlPannel)
        for pannel in pannels:
            action_type = pannel.action_type
            if "door" in action_type and self.door:
                self.event_manager.subscribe(action_type, self.door.open)
                
    def subscribe_iron_gates(self):
        irons_gates :list[IronGate]= self.entity_mn.get_entities_by_class(IronGate)
        for iron_gate in irons_gates:
            self.event_manager.subscribe(f'pannel_iron_gate{iron_gate.pannel_id}', iron_gate.open)
            
    def set_old_paper(self,event):
        dialogue :DialogueArea= event['entity']
        if not isinstance(dialogue,DialogueArea):
            return
        if not self.index_dialog_for_old_paper in dialogue.name:
            return
        old_paper_list = self.entity_mn.get_entities_by_class(OldPaper)
        if old_paper_list:
            self.old_paper :OldPaper= old_paper_list[0]
            self.old_paper.on_active()
            
    def after_close_old_paper(self,event):
        self.event_manager.post({'type':'release_freeze'})
        self.audio_manager.play_sfx("sfx/paper_close.wav", volume=0.85)
        
    def open_old_paper(self,event):
        self.event_manager.post({'type':'request_freeze','type_request':'open paper'})
        self.audio_manager.play_sfx("sfx/paper_open.wav", volume=0.9)
        def close_old_paper(widget):
            self.ui_manager.remove(widget)
            self.event_manager.post({'type':'close_old_paper'})

        paper :Surface= self.resources.load_image('letters/letter_3.png')
        alert_dialog = AlertDialog(
            title='',
            surface=paper,
            on_close= close_old_paper
        )
        self.ui_manager.add(alert_dialog)
        
    def fall_player(self, event):
        self.can_set_resistors = True
        self.audio_manager.play_sfx("sfx/player_fall.wav", volume=0.95)
        # Freeze immediately so next process_input cannot override the fall animation.
        if self.player and self.player.has(Freeze):
            self.player.get(Freeze).active = True
        if self.player and self.player.has(Velocity):
            self.player.get(Velocity).vxy = (0, 0)
        anim:AnimateSprite = self.player.get(AnimateSprite)
        anim.play('fall', reset=True, loop=False, on_finish=self.death_flow_manager.handle_player_death)

    def update_storage_circuit(self,event):
        value = event['value']
        self.audio_manager.play_sfx("sfx/electric_pickup.wav", volume=0.84)
        self.storage_circuit.reload_storage()
        self.storage_circuit.add_component(type='Resistor',value=value)
        self.storage_circuit.save_eletric_storage()

    def update_storage_circuit_generic(self, event, component_type):
        value = event["value"]
        self.audio_manager.play_sfx("sfx/electric_pickup.wav", volume=0.84)
        self.storage_circuit.reload_storage()
        self.storage_circuit.add_component(type=component_type, value=value)
        self.storage_circuit.save_eletric_storage()
        
    def kill_entity_event(self,event):
        entity_id = event['id']
        entity = self.entity_mn.get_entity_by_id(entity_id)
        if isinstance(entity, PhantomEnemy):
            death_x = None
            death_y = None
            if entity.has(Position):
                pos: Position = entity.get(Position)
                death_x = float(pos.x)
                death_y = float(pos.y)
            self._queue_ghost_respawn_by_entity_id(entity_id, death_x=death_x, death_y=death_y)
        self.entity_mn.remove_entity_by_id(entity_id)

    def open_bomb_editor(self):
        self.audio_manager.play_sfx("sfx/interact_confirm.wav", volume=0.9)
        SceneManager.get().active_scene = CircuitEditor(
            pygame.display.get_surface(),
            file=GENERIC_LEVEL_BOMB_EDITOR_FILE,
            debug_mode=False,
        )

    def place_bomb(self):
        if not self.bomb_manager.consume_bomb():
            self.audio_manager.play_ui("sfx/ui_back.wav", volume=0.9)
            return

        self._sync_bomb_runtime()
        if not self.player or not self.player.has(Position):
            return

        player_pos: Position = self.player.get(Position)
        center = player_pos.center_pos()
        params = self.bomb_manager.current_params
        self.pending_bombs.append(
            {
                "center": center,
                "total_delay": float(params.explosion_delay),
                "delay": float(params.explosion_delay),
                "radius": float(params.explosion_radius),
                "damage": float(params.damage),
            }
        )
        self.audio_manager.play_sfx("sfx/lighthouse_ignite.wav", volume=0.58)

    def _sync_bomb_runtime(self):
        bomb_results = self.circuit_manager.get_circuit_values(GENERIC_LEVEL_BOMB_EDITOR_FILE)
        self.bomb_manager.update_from_resistor_results(bomb_results, target_resistor=GENERIC_LEVEL_BOMB_TARGET_RESISTOR)

    def _update_bombs(self, dt: float):
        self._sync_bomb_runtime()
        if not self.pending_bombs:
            return

        still_pending = []
        for bomb in self.pending_bombs:
            bomb["delay"] -= dt
            if bomb["delay"] > 0:
                still_pending.append(bomb)
                continue
            self._explode_bomb(bomb)
        self.pending_bombs = still_pending

    def _explode_bomb(self, bomb_data: dict):
        center: pygame.Vector2 = bomb_data["center"]
        radius = float(bomb_data["radius"])
        damage = float(bomb_data["damage"])
        radius_sq = radius * radius
        enemy_radius_sq = (radius + float(GENERIC_LEVEL_BOMB_ENEMY_HIT_MARGIN)) ** 2

        self.active_explosions.append(
            {
                "center": center,
                "radius": radius,
                "elapsed": 0.0,
                "duration": 0.36,
            }
        )
        shake_intensity = max(3.0, min(9.0, radius / 22.0))
        self.camera.start_shake(duration=0.22, intensity=shake_intensity)
        self.audio_manager.play_sfx("sfx/bombs/explosion_01.ogg", volume=0.45)

        # Dano aos inimigos por area.
        enemies = self.entity_mn.get_entities_with(Position, Collider, Team, Health)
        for enemy in enemies:
            team: Team = enemy.get(Team)
            if team.name != "enemy":
                continue
            enemy_pos: Position = enemy.get(Position)
            if (enemy_pos.center_pos() - center).length_squared() > enemy_radius_sq:
                continue
            self._damage_enemy(enemy, damage)

        # Bomba tambem limpa teias de aranha no raio da explosao.
        if hasattr(self, "spider_web_system"):
            try:
                self.spider_web_system.destroy_traps_in_radius(self.entity_mn, center, radius)
            except Exception:
                pass

        # Friendly fire no jogador.
        if self.player and self.player.has(Position):
            if (self.player.get(Position).center_pos() - center).length_squared() <= radius_sq:
                self._trigger_player_death()

    def _damage_enemy(self, enemy, damage: float):
        health: Health = enemy.get(Health)
        died = health.take_damage(damage)
        if not died:
            self._play_enemy_hit_feedback(enemy)
            return
        was_phantom = enemy.has(PhantomAI)

        # Impede sistemas de movimento/IA de sobrescrever a animacao de morte.
        if enemy.has(PathFollower):
            enemy.remove(PathFollower)
        if enemy.has(PhantomAI):
            enemy.remove(PhantomAI)

        # Fantasma: congela no momento da morte para reforcar feedback visual.
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
                    on_finish=lambda eid=enemy.id: self.event_manager.post({"type": "kill_entity", "id": eid}),
                )
                return
        self.event_manager.post({"type": "kill_entity", "id": enemy.id})

    def _play_enemy_hit_feedback(self, enemy):
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

    def _trigger_player_death(self):
        if getattr(self, "player_dead_by_enemy", False):
            return
        if hasattr(self, "player_dead_by_enemy"):
            self.player_dead_by_enemy = True

        player = self.entity_mn.get_player()
        if not player:
            self.death_flow_manager.handle_player_death()
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
                on_finish=lambda: self.death_flow_manager.handle_player_death(),
            )
            return
        self.death_flow_manager.handle_player_death()

    def _draw_active_explosions(self, dt: float):
        if not self.active_explosions:
            return

        alive_effects = []
        for effect in self.active_explosions:
            effect["elapsed"] += dt
            ratio = effect["elapsed"] / effect["duration"]
            if ratio >= 1.0:
                continue

            center = effect["center"]
            base_radius = float(effect["radius"])
            draw_radius = int(max(1, base_radius * ratio * self.scale))
            off_x, off_y = self.camera.render_offset
            center_scaled = (
                int(center.x * self.scale - self.camera.viewport.x + off_x),
                int(center.y * self.scale - self.camera.viewport.y + off_y),
            )
            if self.bomb_boom_frames:
                frame_index = min(len(self.bomb_boom_frames) - 1, int(ratio * len(self.bomb_boom_frames)))
                frame = self.bomb_boom_frames[frame_index]
                sprite = pygame.transform.scale(
                    frame,
                    (
                        max(20, int(draw_radius * 2.0)),
                        max(20, int(draw_radius * 2.0)),
                    ),
                )
                rect = sprite.get_rect(center=center_scaled)
                self.screen.blit(sprite, rect)
            else:
                alpha = int(max(0, 185 * (1.0 - ratio)))
                core_alpha = int(max(0, 230 * (1.0 - ratio * 1.15)))
                overlay = pygame.Surface((draw_radius * 2 + 12, draw_radius * 2 + 12), pygame.SRCALPHA)
                center_overlay = (overlay.get_width() // 2, overlay.get_height() // 2)
                pygame.draw.circle(overlay, (80, 200, 255, alpha), center_overlay, draw_radius)
                pygame.draw.circle(overlay, (190, 245, 255, core_alpha), center_overlay, max(2, int(draw_radius * 0.35)))
                ring_radius = max(2, int(draw_radius * 0.78))
                ring_width = max(1, int(2 * self.scale))
                pygame.draw.circle(overlay, (120, 230, 255, alpha), center_overlay, ring_radius, ring_width)
                self.screen.blit(
                    overlay,
                    (center_scaled[0] - overlay.get_width() // 2, center_scaled[1] - overlay.get_height() // 2),
                )
            alive_effects.append(effect)

        self.active_explosions = alive_effects

    def _draw_pending_bombs(self):
        if not self.pending_bombs:
            return
        for bomb in self.pending_bombs:
            center = bomb["center"]
            delay = max(0.001, float(bomb["delay"]))
            total = max(0.001, float(bomb.get("total_delay", delay)))
            ratio = max(0.0, min(1.0, delay / total))

            off_x, off_y = self.camera.render_offset
            world_center = (
                int(center.x * self.scale - self.camera.viewport.x + off_x),
                int(center.y * self.scale - self.camera.viewport.y + off_y),
            )
            radius_world = max(1, int(float(bomb["radius"]) * self.scale))
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
                width=max(1, int(2 * self.scale)),
            )
            self.screen.blit(
                preview_overlay,
                (world_center[0] - preview_overlay.get_width() // 2, world_center[1] - preview_overlay.get_height() // 2),
            )

            blink = int((pygame.time.get_ticks() / 120) % 2)
            pulse_scale = 1.0 + (0.1 * (1.0 - ratio)) + (0.08 if blink == 0 else 0.0)

            if self.bomb_prefuze_frames:
                speed_up = 1.0 + (1.4 * (1.0 - ratio))
                ticks = pygame.time.get_ticks() / 170.0
                frame_index = int(ticks * speed_up) % len(self.bomb_prefuze_frames)
                frame = self.bomb_prefuze_frames[frame_index]
                sprite = pygame.transform.scale(
                    frame,
                    (
                        max(10, int(frame.get_width() * self.scale * pulse_scale * GENERIC_LEVEL_BOMB_VISUAL_SCALE)),
                        max(10, int(frame.get_height() * self.scale * pulse_scale * GENERIC_LEVEL_BOMB_VISUAL_SCALE)),
                    ),
                )
                rect = sprite.get_rect(center=world_center)
                self.screen.blit(sprite, rect)
            elif self.bomb_world_sprite is not None:
                sprite = pygame.transform.scale(
                    self.bomb_world_sprite,
                    (
                        max(10, int(self.bomb_world_sprite.get_width() * self.scale * pulse_scale * 0.75)),
                        max(10, int(self.bomb_world_sprite.get_height() * self.scale * pulse_scale * 0.75)),
                    ),
                )
                rect = sprite.get_rect(center=world_center)
                self.screen.blit(sprite, rect)
            else:
                radius = max(4, int(7 * self.scale * pulse_scale))
                color = (20, 90, 120) if blink else (90, 230, 255)
                pygame.draw.circle(self.screen, color, world_center, radius)

            # Barra visual curta de "tempo pra explodir".
            bar_w = max(18, int(24 * self.scale))
            bar_h = max(3, int(3 * self.scale))
            bx = world_center[0] - bar_w // 2
            by = world_center[1] - max(14, int(16 * self.scale))
            pygame.draw.rect(self.screen, (20, 20, 20), pygame.Rect(bx, by, bar_w, bar_h))
            pygame.draw.rect(self.screen, (255, 196, 96), pygame.Rect(bx, by, int(bar_w * ratio), bar_h))
        
    def process_input(self, events):
        modal = self._get_modal_alert_dialog()
        if modal is not None:
            for event in events:
                modal.handle_events(event)
            return

        for event in events:
            self.ui_manager.handle_event(event)
            if event.type == pygame.KEYDOWN:
                if event.key == KEY_PLACE_BOMB:
                    self.place_bomb()
        self._handle_panel_interaction(events)
        self._handle_old_paper_interaction(events)
        self.player.input(events)

    def _get_modal_alert_dialog(self):
        for widget in self.ui_manager.widgets:
            if isinstance(widget, AlertDialog):
                return widget
        return None

    def _handle_panel_interaction(self, events):
        player = self.entity_mn.get_player()
        if not player:
            self.interaction_key_widget.set_visible(False)
            return

        target_panel = None
        for panel in self.entity_mn.get_entities_by_class(ControlPannel):
            if panel.can_player_interact(player):
                target_panel = panel
                break

        target_door = self.door if self.door and self.door.can_player_interact(player) else None
        self.dialogue_hud.update(player, extra_interaction=(target_panel is not None or target_door is not None))
        if not target_panel and not target_door:
            return

        for event in events:
            if event.type == pygame.KEYDOWN and event.key == KEY_DIALOG:
                if target_panel:
                    self.audio_manager.play_sfx("sfx/interact_confirm.wav", volume=0.9)
                    target_panel.open_circuit_editor()
                elif target_door:
                    target_door.try_enter(player)
                self.interaction_key_widget.set_visible(False)
                break

    def _can_old_paper_interact(self) -> bool:
        old_papers = self.entity_mn.get_entities_by_class(OldPaper)
        if not old_papers:
            return False
        paper = old_papers[0]
        if not paper.has(AreaTrigger) or not paper.has(Position):
            return False
        if not self.player or not self.player.has(Position) or not self.player.has(Collider):
            return False

        trigger: AreaTrigger = paper.get(AreaTrigger)
        pos: Position = paper.get(Position)
        if not trigger or not pos:
            return False

        rect = trigger.get_rect(pos.x, pos.y)
        player_rect = self.player.get(Collider).get_rect(*self.player.get(Position).pos)
        return rect.colliderect(player_rect)

    def _handle_old_paper_interaction(self, events):
        can_interact = self._can_old_paper_interact()
        if can_interact:
            self.dialogue_hud.update(self.player, extra_interaction=True)
        for event in events:
            if (
                can_interact
                and event.type == pygame.KEYDOWN
                and event.key == KEY_DIALOG
            ):
                self.event_manager.post({"type": "open_old_paper"})
                break

    def update(self, dt):
        self._last_frame_dt = dt
        self._update_bombs(dt)
        self._update_crystal_respawn_queue(dt)
        self._update_temporary_light(dt)
        self._update_ghost_respawns(dt)
        self._update_ghost_rebirth_effects(dt)
        self.dialog_system.update(self.entity_mn, self.player,dt)
        self.update_systems(dt)
        self.ui_manager.update(dt)
       
    def render(self):
        self.screen.fill(BLACK)
        self.map_renderer.draw()
        self.render_system.draw(scale=self.scale) 
        self._draw_pending_bombs()
        self._draw_active_explosions(self._last_frame_dt)
        self._draw_ghost_rebirth_effects()
        if self.debug_interaction_areas:
            self._draw_debug_areas()
        if hasattr(self, 'light_system'):
            # Usa o dt real para permitir transicoes de luz (fade in/out) fluirem.
            self.light_system.update(self.entity_mn, self._last_frame_dt)
        self.ui_manager.draw(self.screen)

    def _draw_debug_areas(self):
        # Debug do painel de controle (área de interação para tecla E).
        for panel in self.entity_mn.get_entities_by_class(ControlPannel):
            world_rect = panel.get_interaction_rect()
            scaled_rect = pygame.Rect(
                int(world_rect.x * self.scale),
                int(world_rect.y * self.scale),
                int(world_rect.width * self.scale),
                int(world_rect.height * self.scale),
            )
            draw_rect = self.camera.apply(scaled_rect)
            pygame.draw.rect(self.screen, (255, 210, 80), draw_rect, 2)

        # Debug da área de atuação do inimigo (raio de detecção do fantasma).
        for enemy in self.entity_mn.get_entities_with(PhantomAI, Position):
            ai: PhantomAI = enemy.get(PhantomAI)
            pos: Position = enemy.get(Position)
            center = pos.center_pos()
            center_scaled = (
                int(center.x * self.scale - self.camera.viewport.x),
                int(center.y * self.scale - self.camera.viewport.y),
            )
            radius_scaled = max(1, int(ai.detection_radius * self.scale))
            pygame.draw.circle(self.screen, (90, 210, 255), center_scaled, radius_scaled, 1)

    def common_subscribes(self):
        self.pending_bombs.clear()
        self.active_explosions.clear()
        self.crystal_respawn_queue.clear()
        self.ghost_respawn_queue.clear()
        self.ghost_rebirth_effects.clear()
        self._bind_existing_ghost_entities_to_templates()
        self.bomb_manager.reset_bombs(GENERIC_LEVEL_BOMB_COUNT_PER_LEVEL)
        self._sync_bomb_runtime()
        self._temporary_light_timer = 0.0
        self._temporary_light_restore_enabled = None
        self.event_manager.subscribe('fall_player',self.fall_player)
        self.event_manager.subscribe('request_freeze',self.freeze_system.request_freeze)
        self.event_manager.subscribe('release_freeze',self.freeze_system.release_freeze)
        self.event_manager.subscribe('set_cache_colliders',lambda event:self.physics_system.cache_static_colliders(self.entity_mn))
        self.event_manager.subscribe("kill_entity",self.kill_entity_event)
        self.event_manager.subscribe("resistor_collected",self.update_storage_circuit)
        self.event_manager.subscribe("current_source_collected", lambda e: self.update_storage_circuit_generic(e, "CurrentSource"))
        self.event_manager.subscribe("voltage_source_collected", lambda e: self.update_storage_circuit_generic(e, "VoutageSource"))
        self.event_manager.subscribe("voutage_source_collected", lambda e: self.update_storage_circuit_generic(e, "VoutageSource"))
        self.event_manager.subscribe("crystal_invisibility_collected", lambda e: self.audio_manager.play_sfx("sfx/crystal_pickup.wav", volume=0.88))
        if not self._uses_custom_crystal_respawn():
            self.event_manager.subscribe("crystal_invisibility_collected", self._on_crystal_invisibility_collected)
        self.event_manager.subscribe("panel_solved", lambda e: self.audio_manager.play_sfx("sfx/panel_solved.wav", volume=0.9))
        self.event_manager.subscribe("panel_bomb_reward", self._on_panel_bomb_reward)
        self.event_manager.subscribe("open_old_paper",self.open_old_paper)
        self.event_manager.subscribe("close_old_paper",self.after_close_old_paper)
        self.subscribe_panels()
        self.subscribe_iron_gates()

    def _on_panel_bomb_reward(self, event):
        amount_raw = event.get("amount", 0)
        try:
            amount = int(float(amount_raw))
        except (TypeError, ValueError):
            amount = 0
        if amount <= 0:
            return
        self.bomb_manager.max_bombs += amount
        self.bomb_manager.remaining_bombs += amount
        self.audio_manager.play_sfx("sfx/electric_pickup.wav", volume=0.84)

    def reset_bomb_circuit_to_default(self):
        default_json = path_in_circuitos("bombs", "default_bomb.json")
        editor_json = path_in_circuitos("bombs", "bomb_editor.json")
        try:
            editor_json.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(default_json, editor_json)
        except Exception:
            pass
        self.circuit_manager.clear_circuit(GENERIC_LEVEL_BOMB_EDITOR_FILE)
        self.bomb_manager.current_params = self.bomb_manager.default_params

    def on_scene_will_change(self, target_scene_name: str):
        if target_scene_name in {"main_menu", "help"}:
            return
        self.reset_bomb_circuit_to_default()

    def _on_temporary_light_collected(self, event):
        _ = event
        if not hasattr(self, "light_system"):
            return
        self._activate_temporary_light(GENERIC_LEVEL_TEMPORARY_LIGHT_DURATION_SECONDS)

    def _activate_temporary_light(self, duration: float):
        if not hasattr(self, "light_system"):
            return
        if self._temporary_light_timer <= 0:
            self._temporary_light_restore_enabled = self.light_system.enabled
        self.light_system.turn_on()
        self._temporary_light_timer = max(0.0, float(duration))

    def _activate_permanent_light(self, event):
        _ = event
        if not hasattr(self, "light_system"):
            return
        self.light_system.turn_on()
        if self._temporary_light_timer > 0:
            self._temporary_light_restore_enabled = self.light_system.enabled

    def _toggle_permanent_light(self, event):
        _ = event
        if not hasattr(self, "light_system"):
            return

        if self.light_system.enabled:
            self.light_system.turn_on()
        else:
            self.light_system.turn_off()

        if self._temporary_light_timer > 0:
            # Respeita a escolha manual atual quando o boost temporario expirar.
            self._temporary_light_restore_enabled = self.light_system.enabled

    def _update_temporary_light(self, dt: float):
        if self._temporary_light_timer <= 0:
            return
        self._temporary_light_timer = max(0.0, self._temporary_light_timer - dt)
        if self._temporary_light_timer > 0:
            return
        if hasattr(self, "light_system") and self._temporary_light_restore_enabled is not None:
            self.light_system.set_enabled(
                self._temporary_light_restore_enabled,
                transition_seconds=GENERIC_LEVEL_TEMPORARY_LIGHT_FADE_OUT_SECONDS,
            )
        self._temporary_light_restore_enabled = None

    def get_temporary_light_ratio(self) -> float:
        duration = float(GENERIC_LEVEL_TEMPORARY_LIGHT_DURATION_SECONDS)
        if duration <= 0:
            return 0.0
        return max(0.0, min(1.0, self._temporary_light_timer / duration))

    def _uses_custom_crystal_respawn(self) -> bool:
        level_name = Path(self.level_path).stem.lower()
        return level_name in {"fase_8", "final_level"}

    def _on_crystal_invisibility_collected(self, event: dict):
        self.crystal_respawn_queue.append(
            {
                "remaining": float(event.get("respawn_delay", 20.0)),
                "x": float(event.get("spawn_x", 0.0)),
                "y": float(event.get("spawn_y", 0.0)),
                "duration": float(event.get("duration", 6.0)),
                "respawn_delay": float(event.get("respawn_delay", 20.0)),
            }
        )

    def _update_crystal_respawn_queue(self, dt: float):
        if self._uses_custom_crystal_respawn() or not self.crystal_respawn_queue:
            return

        still_waiting: list[dict] = []
        for entry in self.crystal_respawn_queue:
            entry["remaining"] -= dt
            if entry["remaining"] > 0:
                still_waiting.append(entry)
                continue

            props = {
                "duration": entry["duration"],
                "respawn_delay": entry["respawn_delay"],
                "tmx_file": self.tile_map.tmx_file,
            }
            crystal = CrystalInvisibilityItem(entry["x"], entry["y"], True, props)
            self.entity_mn.add_entity(crystal)

        self.crystal_respawn_queue = still_waiting
