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
from entities.enemies.phantom_enemy import PhantomEnemy
from entities.itens.current_source_item import CurrentSourceItem
from entities.itens.voltage_source_item import VoutageSourceItem
from entities.itens.resistor_item import ResistorItem
from entities.itens.old_paper import OldPaper
from entities.animated_tiles.door import Door
from entities.itens.control_pannel import ControlPannel
from entities.npcs.arquimedes import Arquimedes
from core.components.position import Position
from core.components.velocity import Velocity
from core.components.freeze import Freeze
from core.components.phantom_ai import PhantomAI
from core.ui.widgets.lives_widget import LivesWidget
from core.ui.widgets.alert_dialog import AlertDialog
from core.ui.widgets.interaction_key_widget import InteractionKeyWidget
from core.map.tile_map_loader import TileMapLoader
from core.map.map_entity_spawner import MapEntitySpawner
from core.map.map_renderer import MapRenderer
from core.managers.scene_manager import SceneManager
from core.managers.death_flow_manager import DeathFlowManager
from core.managers.audio_manager import AudioManager
from core.managers.language_service import LanguageService
from core.managers.bomb_manager import BombManager
from core.circuit_tools.storage_circuit_manager import StorageCircuitManager
from core.managers.circuit_manager import CircuitManager
from core.localization.letter_asset_resolver import LetterAssetResolver
from core.ui.dialogue_interaction_hud_controller import DialogueInteractionHUDController
from core.ui.widgets.button import Button
from core.ui.widgets.bomb_status_widget import BombStatusWidget
from core.ui.widgets.component_overload_widget import ComponentOverloadWidget
from core.ui.widgets.gesture_detector import ClickType
from core.systems.generic_level_interaction_system import GenericLevelInteractionSystem
from core.systems.generic_level_ghost_system import GenericLevelGhostSystem
from core.systems.generic_level_bomb_system import GenericLevelBombSystem
from core.systems.generic_level_environment_system import GenericLevelEnvironmentSystem
from core.ui.renderers.generic_level_bomb_renderer import GenericLevelBombRenderer
from core.ui.renderers.generic_level_ghost_renderer import GenericLevelGhostRenderer
from core.managers.input_manager import InputManager
from core.ui.prompt_ui import draw_prompt_hint_row
from scenes.fases.component_overload_service import ComponentOverloadService

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
        self._restore_bombs_after_editor = False
        self._saved_bomb_counts: tuple[int, int] | None = None
        self._ghost_spawn_templates: dict[str, dict] = {}
        self._ghost_entity_to_spawn_key: dict[int, str] = {}
        self._last_frame_dt = 0.0
        self.bomb_world_sprite = None
        self.bomb_prefuze_frames: list[pygame.Surface] = []
        self.bomb_boom_frames: list[pygame.Surface] = []
        self.component_overload = ComponentOverloadService(
            speed_multiplier_applier=self._apply_player_speed_multiplier,
            total_components_provider=self._total_map_components,
            total_areas_provider=self._total_component_areas,
        )
        # Sistemas de suporte precisam existir antes de set_map(),
        # porque o fluxo do mapa já prepara templates de fantasmas.
        self.ghost_system = GenericLevelGhostSystem(self)
        self.bomb_system = GenericLevelBombSystem(self)
        self.environment_system = GenericLevelEnvironmentSystem(self)
        self.bomb_renderer = GenericLevelBombRenderer()
        self.ghost_renderer = GenericLevelGhostRenderer()
        
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
        self.input_manager = InputManager.get()
        self.language_service = LanguageService.get()
        self.death_flow_manager = DeathFlowManager.get()
        self.circuit_manager = CircuitManager.get()
        self.dialogue_hud = DialogueInteractionHUDController(
            self.entity_mn,
            self.dialog_system,
            self.interaction_key_widget,
        )
        self.interaction_system = GenericLevelInteractionSystem(self)
        # Mantem o recurso de debug no codigo, mas desativado por padrao.
        self.debug_interaction_areas = False
        self._temporary_light_timer = 0.0
        self._temporary_light_restore_enabled = None
        self._scene_change_target_name: str | None = None
        self._preserve_runtime_state_on_next_start = False
        self._preserve_component_overload_on_next_start = False
        self._startup_player_lock_frames = 0
        
        # Subclasses will override this
        self.set_systems() 
        
        self.door = self.entity_mn.get_entities_by_class(Door)
        if self.door:
            self.door = self.door[0]
        self._set_bomb_visuals()

    def _configure_bomb_balance_profile(self):
        self.bomb_manager.set_balance_profile("standard")
            
    def set_ui(self):
        lives = LivesWidget(pos=(10, 42))
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
        bomb_x, bomb_y = self.bomb_status_widget.pos
        overload_y = bomb_y + 68 + 8
        self.component_overload_widget = ComponentOverloadWidget(
            self.screen.get_size(),
            self,
            anchor_pos=(bomb_x + 2, overload_y),
        )
        self.ui_manager.add(
            self.menu_button,
            self.help_button,
            self.edit_bomb_button,
            self.bomb_status_widget,
            self.component_overload_widget,
        )
        self.interaction_key_widget = InteractionKeyWidget(self.screen.get_size(), label="ENTRAR")
        self.ui_manager.add(self.interaction_key_widget)
        self.prompt_chip_font = self.resources.load_font("PressStart2P-Regular.ttf", 8)
        self.prompt_text_font = self.resources.load_font("PressStart2P-Regular.ttf", 8)

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
        spawner = MapEntitySpawner(spawn_tile_layer_entities=False)
        spawner.spawn_entities(self.tile_map, self.entity_mn)
        self.player = self.entity_mn.get_player()
        self.physics_system.set_external_static_colliders(self.tile_map.solid_colliders)
        self.physics_system.cache_static_colliders(self.entity_mn)
        self._capture_initial_ghost_spawn_templates()

    def _capture_initial_ghost_spawn_templates(self):
        self.ghost_system.capture_initial_ghost_spawn_templates()

    def _extract_enemy_routes_from_map(self) -> dict[str, list[tuple[int, int]]]:
        return self.ghost_system.extract_enemy_routes_from_map()

    def _bind_existing_ghost_entities_to_templates(self):
        self.ghost_system.bind_existing_ghost_entities_to_templates()

    def _queue_ghost_respawn_by_entity_id(self, entity_id: int, death_x: float | None = None, death_y: float | None = None):
        self.ghost_system.queue_ghost_respawn_by_entity_id(entity_id, death_x=death_x, death_y=death_y)

    def _spawn_ghost_from_template(self, spawn_key: str, respawn_x: float | None = None, respawn_y: float | None = None):
        self.ghost_system.spawn_ghost_from_template(spawn_key, respawn_x=respawn_x, respawn_y=respawn_y)

    def _start_ghost_rebirth_effect(self, spawn_key: str, respawn_x: float | None = None, respawn_y: float | None = None):
        self.ghost_system.start_ghost_rebirth_effect(spawn_key, respawn_x=respawn_x, respawn_y=respawn_y)

    def _update_ghost_respawns(self, dt: float):
        self.ghost_system.update_ghost_respawns(dt)

    def _update_ghost_rebirth_effects(self, dt: float):
        self.ghost_system.update_ghost_rebirth_effects(dt)

    def _draw_ghost_rebirth_effects(self):
        self.ghost_renderer.draw_rebirth_effects(self)

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

        paper_path = LetterAssetResolver(
            language=self.language_service.get_current_language()
        ).resolve("letter_3")
        paper :Surface= self.resources.load_image(paper_path)
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
        self._register_collected_component(event, "resistor")

    def update_storage_circuit_generic(self, event, component_type):
        value = event["value"]
        self.audio_manager.play_sfx("sfx/electric_pickup.wav", volume=0.84)
        self.storage_circuit.reload_storage()
        self.storage_circuit.add_component(type=component_type, value=value)
        self.storage_circuit.save_eletric_storage()
        normalized = component_type.lower()
        if "current" in normalized:
            kind = "current_source"
        elif "voutage" in normalized or "voltage" in normalized:
            kind = "voltage_source"
        else:
            kind = "resistor"
        self._register_collected_component(event, kind)
        
    def kill_entity_event(self,event):
        entity_id = event['id']
        entity = self.entity_mn.get_entity_by_id(entity_id)
        is_phantom = bool(
            entity
            and (
                entity.has(PhantomAI)
                or isinstance(entity, PhantomEnemy)
            )
        )
        if is_phantom:
            death_x = None
            death_y = None
            if entity.has(Position):
                pos: Position = entity.get(Position)
                death_x = float(pos.x)
                death_y = float(pos.y)
            self.ghost_system.queue_ghost_respawn_by_entity_id(entity_id, death_x=death_x, death_y=death_y)
        self.entity_mn.remove_entity_by_id(entity_id)

    def open_bomb_editor(self):
        self.audio_manager.play_sfx("sfx/interact_confirm.wav", volume=0.9)
        # Ao voltar do editor, manter filas de runtime (ex.: respawn de fantasma).
        self._preserve_runtime_state_on_next_start = True
        # Preserva contagem de nucleos ao abrir/fechar o editor durante a mesma fase.
        self._saved_bomb_counts = (
            int(self.bomb_manager.max_bombs),
            int(self.bomb_manager.remaining_bombs),
        )
        self._restore_bombs_after_editor = True
        SceneManager.get().active_scene = CircuitEditor(
            pygame.display.get_surface(),
            file=GENERIC_LEVEL_BOMB_EDITOR_FILE,
            debug_mode=False,
        )

    def place_bomb(self):
        self.bomb_system.place_bomb()

    def _sync_bomb_runtime(self):
        self.bomb_system.sync_bomb_runtime()

    def _update_bombs(self, dt: float):
        self.bomb_system.update_bombs(dt)

    def _explode_bomb(self, bomb_data: dict):
        self.bomb_system.explode_bomb(bomb_data)

    def _damage_enemy(self, enemy, damage: float):
        self.bomb_system.damage_enemy(enemy, damage)

    def _play_enemy_hit_feedback(self, enemy):
        self.bomb_system.play_enemy_hit_feedback(enemy)

    def _trigger_player_death(self):
        self.bomb_system.trigger_player_death()

    def _draw_active_explosions(self, dt: float):
        self.bomb_renderer.draw_active_explosions(self, dt)

    def _draw_pending_bombs(self):
        self.bomb_renderer.draw_pending_bombs(self)
        
    def process_input(self, events):
        modal = self._get_modal_alert_dialog()
        if modal is not None:
            for event in events:
                modal.handle_events(event)
            return

        if self.input_manager.is_action_just_pressed("help"):
            SceneManager.get().open_help(0.35)
            return

        if self.input_manager.is_action_just_pressed("pause"):
            SceneManager.get().open_menu(0.35)
            return

        if self.input_manager.is_action_just_pressed("open_editor"):
            self.open_bomb_editor()
            return

        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F1:
                SceneManager.get().open_help(0.35)
                return
            self.ui_manager.handle_event(event)
            if event.type == pygame.KEYDOWN and event.key == KEY_PLACE_BOMB:
                self.place_bomb()
        self._handle_panel_interaction(events)
        self._handle_old_paper_interaction(events)
        if self.player:
            self.player.input(events)

    def _get_modal_alert_dialog(self):
        return self.interaction_system.get_modal_alert_dialog()

    def _handle_panel_interaction(self, events):
        self.interaction_system.handle_panel_interaction(events)

    def _can_old_paper_interact(self) -> bool:
        return self.interaction_system.can_old_paper_interact()

    def _handle_old_paper_interaction(self, events):
        self.interaction_system.handle_old_paper_interaction(events)

    def update(self, dt):
        if self._startup_player_lock_frames > 0:
            self._halt_player_motion()
            self._startup_player_lock_frames = max(0, self._startup_player_lock_frames - 1)
        self._last_frame_dt = dt
        self.bomb_system.update_bombs(dt)
        self.environment_system.update(self.entity_mn, dt)
        self.ghost_system.update(self.entity_mn, dt)
        prompt_label = self.interaction_system.resolve_interaction_prompt(self.player)
        self.dialogue_hud.update(
            self.player,
            extra_interaction=prompt_label is not None,
            extra_prompt_label=prompt_label or "INTERAGIR",
        )
        self.dialog_system.update(self.entity_mn, self.player,dt)
        self.update_systems(dt)
        self.ui_manager.update(dt)
       
    def render(self):
        self.screen.fill(BLACK)
        self.map_renderer.draw()
        self.render_system.draw(scale=self.scale) 
        self.map_renderer.draw_foreground()
        self.bomb_renderer.draw_pending_bombs(self)
        self.bomb_renderer.draw_active_explosions(self, self._last_frame_dt)
        self.ghost_renderer.draw_rebirth_effects(self)
        if self.debug_interaction_areas:
            self._draw_debug_areas()
        if hasattr(self, 'light_system'):
            # Usa o dt real para permitir transicoes de luz (fade in/out) fluirem.
            self.light_system.update(self.entity_mn, self._last_frame_dt)
        self.ui_manager.draw(self.screen)
        self._draw_gameplay_prompt_bar()

    def _draw_gameplay_prompt_bar(self):
        if not self.should_draw_bottom_prompt_bar():
            return
        items = self.input_manager.get_prompt_items("generic_level")
        if not items:
            return
        draw_prompt_hint_row(
            self.screen,
            self.prompt_chip_font,
            self.prompt_text_font,
            items,
            anchor=(18, self.screen.get_height() - 24),
            align="left",
        )

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
        preserve_runtime = bool(getattr(self, "_preserve_runtime_state_on_next_start", False))
        self._preserve_runtime_state_on_next_start = False
        if not preserve_runtime:
            self.pending_bombs.clear()
            self.active_explosions.clear()
            self.crystal_respawn_queue.clear()
            self.ghost_respawn_queue.clear()
            self.ghost_rebirth_effects.clear()
        preserve_overload = bool(getattr(self, "_preserve_component_overload_on_next_start", False)) or preserve_runtime
        if preserve_overload:
            self._apply_player_speed_multiplier(self.component_overload.multiplier)
            self._preserve_component_overload_on_next_start = False
        else:
            self.component_overload.reset()
        if not preserve_runtime:
            self.ghost_system.bind_existing_ghost_entities_to_templates()
        if self._restore_bombs_after_editor and self._saved_bomb_counts is not None:
            max_bombs, remaining_bombs = self._saved_bomb_counts
            self.bomb_manager.max_bombs = max(0, int(max_bombs))
            self.bomb_manager.remaining_bombs = max(
                0,
                min(int(remaining_bombs), self.bomb_manager.max_bombs),
            )
            self._saved_bomb_counts = None
            self._restore_bombs_after_editor = False
        else:
            self.bomb_manager.reset_bombs(GENERIC_LEVEL_BOMB_COUNT_PER_LEVEL)
        self.bomb_system.sync_bomb_runtime()
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
        if not self.environment_system.uses_custom_crystal_respawn():
            self.event_manager.subscribe("crystal_invisibility_collected", self.environment_system.on_crystal_invisibility_collected)
        self.event_manager.subscribe("panel_solved", lambda e: self.audio_manager.play_sfx("sfx/panel_solved.wav", volume=0.9))
        self.event_manager.subscribe("panel_solved", self._on_panel_solved_overload)
        self.event_manager.subscribe("panel_bomb_reward", self._on_panel_bomb_reward)
        self.event_manager.subscribe("open_old_paper",self.open_old_paper)
        self.event_manager.subscribe("close_old_paper",self.after_close_old_paper)
        self.subscribe_panels()
        self.subscribe_iron_gates()
        # Evita atravessar parede se o player estiver segurando movimento
        # durante os frames iniciais de carga/rebind da fase.
        self._startup_player_lock_frames = max(self._startup_player_lock_frames, 2)
        self._halt_player_motion()

    def _halt_player_motion(self):
        player = self.entity_mn.get_player()
        if not player or not player.has(Velocity):
            return
        player.get(Velocity).vxy = (0, 0)

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

    def _should_skip_progress_reset_on_end(self) -> bool:
        target = (self._scene_change_target_name or "").strip().lower()
        return target in {"main_menu", "help"}

    def _reset_panels_runtime_state(self):
        for panel in self.entity_mn.get_entities_by_class(ControlPannel):
            panel.done = False
            if hasattr(panel, "solution_value"):
                panel.solution_value = None
            if hasattr(panel, "panel_status"):
                try:
                    panel.panel_status.set_done(False)
                    panel.panel_status.set_active(bool(getattr(panel, "active", True)))
                except Exception:
                    pass

    def reset_bomb_circuit_to_default(self):
        default_json = path_in_circuitos("bombs", "default_bomb.json")
        editor_json = path_in_circuitos("bombs", "bomb_editor.json")
        default_net = path_in_ltspice("bombs", "default_bomb.net")
        editor_net = path_in_ltspice("bombs", "bomb_editor.net")
        default_asc = path_in_ltspice("bombs", "default_bomb.asc")
        editor_asc = path_in_ltspice("bombs", "bomb_editor.asc")
        try:
            editor_json.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(default_json, editor_json)
            editor_net.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(default_net, editor_net)
            if default_asc.exists():
                shutil.copyfile(default_asc, editor_asc)
        except Exception:
            pass
        self.circuit_manager.clear_circuit(GENERIC_LEVEL_BOMB_EDITOR_FILE)
        self.bomb_manager.current_params = self.bomb_manager.default_params

    def on_scene_will_change(self, target_scene_name: str):
        self._scene_change_target_name = target_scene_name
        if target_scene_name in {"main_menu", "help"}:
            self._preserve_runtime_state_on_next_start = True
            self._preserve_component_overload_on_next_start = True
        self.component_overload.clear_speed_penalty()
        if target_scene_name in {"main_menu", "help"}:
            return
        self.reset_bomb_circuit_to_default()

    def _on_temporary_light_collected(self, event):
        _ = event
        if not hasattr(self, "light_system"):
            return
        self._activate_temporary_light(GENERIC_LEVEL_TEMPORARY_LIGHT_DURATION_SECONDS)

    def _activate_temporary_light(self, duration: float):
        self.environment_system.activate_temporary_light(duration)

    def _activate_permanent_light(self, event):
        _ = event
        self.environment_system.activate_permanent_light()

    def _toggle_permanent_light(self, event):
        _ = event
        self.environment_system.toggle_permanent_light()

    def _update_temporary_light(self, dt: float):
        self.environment_system.update_temporary_light(dt)

    def get_temporary_light_ratio(self) -> float:
        return self.environment_system.get_temporary_light_ratio()

    def _uses_custom_crystal_respawn(self) -> bool:
        return self.environment_system.uses_custom_crystal_respawn()

    def _on_crystal_invisibility_collected(self, event: dict):
        self.environment_system.on_crystal_invisibility_collected(event)

    def _update_crystal_respawn_queue(self, dt: float):
        self.environment_system.update_crystal_respawn_queue(dt)

    def _register_collected_component(self, event: dict, kind: str):
        self.component_overload.register_component(event, kind)

    def _on_panel_solved_overload(self, event: dict):
        payload = dict(event or {})
        if "area_id" not in payload:
            panel_id = payload.get("pannel_id")
            pannels: list[ControlPannel] = self.entity_mn.get_entities_by_class(ControlPannel)
            for panel in pannels:
                if getattr(panel, "pannel_id", None) == panel_id:
                    try:
                        payload["area_id"] = int(panel.component_for_area)
                    except (TypeError, ValueError):
                        payload["area_id"] = -1
                    break
        self.component_overload.on_panel_solved(payload)

    def get_component_overload_snapshot(self) -> dict:
        return self.component_overload.get_snapshot()

    def _apply_player_speed_multiplier(self, multiplier: float):
        if self.player and hasattr(self.player, "set_external_speed_multiplier"):
            self.player.set_external_speed_multiplier(multiplier)

    def _active_component_areas(self) -> set[int]:
        areas: set[int] = set()
        pannels: list[ControlPannel] = self.entity_mn.get_entities_by_class(ControlPannel)
        for panel in pannels:
            if bool(getattr(panel, "done", False)):
                continue
            try:
                areas.add(int(panel.component_for_area))
            except (TypeError, ValueError):
                continue
        return areas

    def _total_map_components(self) -> int:
        total = 0
        total += len(self.entity_mn.get_entities_by_class(ResistorItem))
        total += len(self.entity_mn.get_entities_by_class(CurrentSourceItem))
        total += len(self.entity_mn.get_entities_by_class(VoutageSourceItem))
        return max(1, total)

    def _total_component_areas(self) -> int:
        areas: set[int] = set()
        pannels: list[ControlPannel] = self.entity_mn.get_entities_by_class(ControlPannel)
        for panel in pannels:
            try:
                areas.add(int(panel.component_for_area))
            except (TypeError, ValueError):
                continue
        return max(1, len(areas))
