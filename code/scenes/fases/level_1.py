import pygame
from pygame import Surface
from core.settings import *
from scenes.base_scene import BaseScene
from entities.dialogue_area import DialogueArea
from entities.itens.old_paper import OldPaper
from entities.itens.key import Key
from entities.animated_tiles.door import Door
from core.components.area_trigger import AreaTrigger
from core.components.position import Position
from core.components.collider import Collider
from core.ui.widgets.lives_widget import LivesWidget
from core.ui.widgets.alert_dialog import AlertDialog
from core.map.tile_map_loader import TileMapLoader
from core.map.map_entity_spawner import MapEntitySpawner
from core.map.map_renderer import MapRenderer
from core.map.map_entity_spawner import MapEntitySpawner
from core.systems.animation_system import AnimationSystem
from core.systems.area_trigger_system import AreaTriggerSystem
from core.systems.freeze_system import FreezeSystem
from core.managers.attention_manager import AttentionManager
from core.managers.scene_manager import SceneManager
from core.ui.dialogue_interaction_hud_controller import DialogueInteractionHUDController
from core.ui.widgets.interaction_key_widget import InteractionKeyWidget
from core.ui.widgets.button import Button
from core.ui.widgets.gesture_detector import ClickType

class Level1(BaseScene):
    def __init__(self, screen:Surface):
        loader = TileMapLoader()
        self.tile_map=loader.load("fases/fase_1.tmx")
        self.scale = 2
        super().__init__(screen, self.tile_map.map_width*self.scale, self.tile_map.map_height*self.scale)

        
        
        self.map_renderer=MapRenderer(self.tile_map,self.camera,self.screen,self.scale)

        self.set_ui()
        self.set_map()
        self.set_systems()

        self.camera.scale = self.scale
        self.player =  self.entity_mn.get_player()
        self.camera.follow = self.player

        

        self.attention_manager       = AttentionManager(self.entity_mn)
        self.dialogue_hud = DialogueInteractionHUDController(
            self.entity_mn,
            self.dialog_system,
            self.interaction_key_widget,
        )
        
        self.scene_manager           = SceneManager.get() 
    def set_systems(self):
        self.animation_system        =  AnimationSystem()
        self.area_trigger_system     = AreaTriggerSystem()
        self.freeze_system           = FreezeSystem()
        self.systems.update(
            [self.freeze_system,
            self.physics_system,
            self.animation_system,
            self.area_trigger_system,
            self.render_system]
            )
        self.index_dialog_for_old_paper = '1'
        self.key:Key= self.entity_mn.get_entities_by_class(Key)[0]
        self.old_paper:OldPaper =  self.entity_mn.get_entities_by_class(OldPaper)[0]
        self.door:Door = self.entity_mn.get_entities_by_class(Door)[0]
        self.door.next_scene = 'level_2'
    def set_ui(self):
        lives = LivesWidget(pos=(10, 42))
        self.ui_manager.add(lives)
        top_button_gap = 20
        top_button_step = 142 + top_button_gap
        menu_x = self.screen.get_width() - 92
        help_x = menu_x - top_button_step
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
        self.ui_manager.add(self.menu_button, self.help_button)
        self.interaction_key_widget = InteractionKeyWidget(self.screen.get_size(), label="ENTRAR")
        self.ui_manager.add(self.interaction_key_widget)

        
    def start(self):
        self.event_manager.post({'type':'release_freeze'})
        self.set_subscribes()

    def set_subscribes(self):
        self.event_manager.subscribe("request_freeze", self.freeze_system.request_freeze)
        self.event_manager.subscribe("release_freeze", self.freeze_system.release_freeze)
        self.event_manager.subscribe("dialogue_end",self.attention_manager.set_attention_position_after_event)
        self.event_manager.subscribe("dialogue_end",self.attention_manager.set_dialogue_area_after_event)
        self.event_manager.subscribe("dialogue_end",self.set_old_paper)
        self.event_manager.subscribe("kill_entity",self.kill_entity_event)
        self.event_manager.subscribe("open_old_paper",self.open_old_paper)
        self.event_manager.subscribe("close_old_paper",self.after_close_old_paper)
        self.event_manager.subscribe('get_key',self.door.open)
    
    def set_old_paper(self,event):
        dialogue :DialogueArea= event['entity']
        if not isinstance(dialogue,DialogueArea):
            return
        if not self.index_dialog_for_old_paper in dialogue.name:
            return
         
        self.old_paper :OldPaper= self.entity_mn.get_entities_by_class(OldPaper)[0]
        self.old_paper.on_active()
    def after_close_old_paper(self,event):
        self.event_manager.post({'type':'release_freeze'})
        self.key.on_active()
    def open_old_paper(self,event):
        self.event_manager.post({'type':'request_freeze','type_request':'open paper'})

        def close_old_paper(widget):
            self.ui_manager.remove(widget)
            self.event_manager.post({'type':'close_old_paper'})

        paper :Surface= self.resources.load_image('letters/letter_2.png')
        alert_dialog = AlertDialog(
            title='',
            surface=paper,
            on_close= close_old_paper
        )
        self.ui_manager.add(alert_dialog)

    def set_map(self):
        spawner = MapEntitySpawner()
        spawner.spawn_entities(self.tile_map, self.entity_mn)

        self.player = self.entity_mn.get_player()
        

        self.physics_system.cache_static_colliders(self.entity_mn)
    def kill_entity_event(self,event):
        self.entity_mn.remove_entity_by_id(event['id'])

    def process_input(self, events):
        modal = self._get_modal_alert_dialog()
        if modal is not None:
            for event in events:
                modal.handle_events(event)
            return

        for event in events:
            self.ui_manager.handle_event(event)
        self._handle_door_interaction(events)
        self._handle_old_paper_interaction(events)
        self.player.input(events)

    def _get_modal_alert_dialog(self):
        for widget in self.ui_manager.widgets:
            if isinstance(widget, AlertDialog):
                return widget
        return None

    def _handle_door_interaction(self, events):
        if not self.door or not self.player:
            return
        if not self.door.can_player_interact(self.player):
            return
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == KEY_DIALOG:
                self.door.try_enter(self.player)
                self.interaction_key_widget.set_visible(False)
                break

    def _can_old_paper_interact(self) -> bool:
        if not hasattr(self, "old_paper") or not self.old_paper:
            return False
        if not self.player or not self.player.has(Position) or not self.player.has(Collider):
            return False
        if not self.old_paper.has(AreaTrigger) or not self.old_paper.has(Position):
            return False

        trigger: AreaTrigger = self.old_paper.get(AreaTrigger)
        if not trigger.active:
            return False

        paper_pos: Position = self.old_paper.get(Position)
        paper_rect = trigger.get_rect(paper_pos.x, paper_pos.y)
        player_pos: Position = self.player.get(Position)
        player_rect = self.player.get(Collider).get_rect(player_pos.x, player_pos.y)
        return player_rect.colliderect(paper_rect)

    def _handle_old_paper_interaction(self, events):
        if not self._can_old_paper_interact():
            return
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == KEY_DIALOG:
                self.interaction_key_widget.set_visible(False)
                self.event_manager.post({"type": "open_old_paper"})
                break

    def update(self, dt):
        can_door_interact = self.door.can_player_interact(self.player) if self.door and self.player else False
        can_paper_interact = self._can_old_paper_interact()
        self.dialogue_hud.update(self.player, extra_interaction=(can_door_interact or can_paper_interact))
        self.dialog_system.update(self.entity_mn, self.player,dt)

        self.update_systems(dt)
        self.ui_manager.update(dt)
       
    def render(self):
    
        self.screen.fill(BLACK)
        self.map_renderer.draw()
        self.render_system.draw(scale=self.scale) 
        self.ui_manager.draw(self.screen)
