import pygame
from pygame import Surface
from core.components.animation_sprite import AnimateSprite
from core.components.area_trigger import AreaTrigger
from core.components.label_component import LabelComponent
from core.components.dialogue import Dialogue
from core.components.collider import Collider
from core.settings import *
from scenes.base_scene import BaseScene
from entities.dialogue_area import DialogueArea
from entities.animated_tiles.iron_gate import IronGate
from entities.itens.resistor_item import ResistorItem
from entities.itens.old_paper import OldPaper
from entities.animated_tiles.door import Door
from entities.itens.control_pannel import ControlPannel
from entities.npcs.arquimedes import Arquimedes
from core.components.position import Position
from core.components.velocity import Velocity
from core.components.freeze import Freeze
from core.components.phantom_ai import PhantomAI
from core.ui.widgets.fps_widget import FPSWidget
from core.ui.widgets.lives_widget import LivesWidget
from core.ui.widgets.alert_dialog import AlertDialog
from core.ui.widgets.interaction_key_widget import InteractionKeyWidget
from core.ui.widgets.temporary_light_bar_widget import TemporaryLightBarWidget
from core.map.tile_map_loader import TileMapLoader
from core.map.map_entity_spawner import MapEntitySpawner
from core.map.map_renderer import MapRenderer
from core.managers.scene_manager import SceneManager
from core.managers.death_flow_manager import DeathFlowManager
from core.managers.audio_manager import AudioManager
from core.circuit_tools.storage_circuit_manager import StorageCircuitManager
from core.managers.circuit_manager import CircuitManager
from core.ui.dialogue_interaction_hud_controller import DialogueInteractionHUDController
from core.ui.widgets.button import Button
from core.ui.widgets.gesture_detector import ClickType

class BaseGenericLevel(BaseScene):
    TEMPORARY_LIGHT_DURATION_SECONDS = 8.0

    def __init__(self, screen: Surface, level_path: str):
        self.loader = TileMapLoader()
        self.level_path = level_path
        self.tile_map = self.loader.load(f"fases/{self.level_path}.tmx")
        self.scale = 2

        super().__init__(screen, self.tile_map.map_width * self.scale, self.tile_map.map_height * self.scale)
        self.camera.scale = self.scale
        self.map_renderer = MapRenderer(self.tile_map, self.camera, self.screen, self.scale)
        
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
            
    def set_ui(self):
        fps = FPSWidget()
        lives = LivesWidget(pos=(10, 42))
        self.ui_manager.add(fps)
        self.ui_manager.add(lives)
        idle = pygame.transform.scale(self.resources.load_image("buttons/short.png"), (142, 78))
        pressed = pygame.transform.scale(self.resources.load_image("buttons/short_pressed.png"), (142, 78))
        self.menu_button = Button(
            init_surface=idle,
            surface_pressed=pressed,
            pos_center=(self.screen.get_width() - 92, 44),
            click_type=ClickType.AFTER_RELEASED,
            action=lambda: SceneManager.get().open_menu(0.35),
            text="MENU",
            font_size=11,
            color_text=(245, 230, 170),
        )
        self.ui_manager.add(self.menu_button)
        self.interaction_key_widget = InteractionKeyWidget(self.screen.get_size(), label="ENTRAR")
        self.ui_manager.add(self.interaction_key_widget)
        self.temporary_light_bar_widget = TemporaryLightBarWidget(self.screen.get_size(), self)
        self.ui_manager.add(self.temporary_light_bar_widget)

    def set_map(self):
        spawner = MapEntitySpawner()
        spawner.spawn_entities(self.tile_map, self.entity_mn)
        self.player = self.entity_mn.get_player()
        self.physics_system.cache_static_colliders(self.entity_mn)

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
            if "luz" in action_type:
                self.event_manager.subscribe(action_type, self._activate_permanent_light)
            elif "door" in action_type and self.door:
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
        self.entity_mn.remove_entity_by_id(event['id'])
        
    def process_input(self, events):
        for event in events:
            self.ui_manager.handle_event(event)
        self._handle_panel_interaction(events)
        self._handle_old_paper_interaction(events)
        self.player.input(events)

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
        self._update_temporary_light(dt)
        self.dialog_system.update(self.entity_mn, self.player,dt)
        self.update_systems(dt)
        self.ui_manager.update(dt)
       
    def render(self):
        self.screen.fill(BLACK)
        self.map_renderer.draw()
        self.render_system.draw(scale=self.scale) 
        if self.debug_interaction_areas:
            self._draw_debug_areas()
        if hasattr(self, 'light_system'):
            self.light_system.update(self.entity_mn,0)
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
        self._temporary_light_timer = 0.0
        self._temporary_light_restore_enabled = None
        if hasattr(self, "light_system"):
            self.light_system.set_enabled(self.light_system.initial_enabled)
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
        self.event_manager.subscribe("temporary_light_collected", self._on_temporary_light_collected)
        self.event_manager.subscribe("temporary_light_collected", lambda e: self.audio_manager.play_sfx("sfx/light_on.wav", volume=0.95))
        self.event_manager.subscribe("panel_solved", lambda e: self.audio_manager.play_sfx("sfx/panel_solved.wav", volume=0.9))
        self.event_manager.subscribe("panel_light_on", lambda e: self.audio_manager.play_sfx("sfx/light_on.wav", volume=0.95))
        self.event_manager.subscribe("open_old_paper",self.open_old_paper)
        self.event_manager.subscribe("close_old_paper",self.after_close_old_paper)
        self.subscribe_panels()
        self.subscribe_iron_gates()

    def _on_temporary_light_collected(self, event):
        _ = event
        if not hasattr(self, "light_system"):
            return
        self._activate_temporary_light(self.TEMPORARY_LIGHT_DURATION_SECONDS)

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

    def _update_temporary_light(self, dt: float):
        if self._temporary_light_timer <= 0:
            return
        self._temporary_light_timer = max(0.0, self._temporary_light_timer - dt)
        if self._temporary_light_timer > 0:
            return
        if hasattr(self, "light_system") and self._temporary_light_restore_enabled is not None:
            self.light_system.set_enabled(self._temporary_light_restore_enabled)
        self._temporary_light_restore_enabled = None

    def get_temporary_light_ratio(self) -> float:
        duration = float(self.TEMPORARY_LIGHT_DURATION_SECONDS)
        if duration <= 0:
            return 0.0
        return max(0.0, min(1.0, self._temporary_light_timer / duration))






