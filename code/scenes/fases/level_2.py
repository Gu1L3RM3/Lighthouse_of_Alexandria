import pygame
from pygame import Surface
from core.components.position import Position
from core.components.dialogue import Dialogue
from core.settings import *
from scenes.base_scene import BaseScene
from entities.dialogue_area import DialogueArea
from entities.itens.old_paper import OldPaper
from entities.itens.key import Key
from entities.animated_tiles.door import Door
from core.ui.widgets.fps_widget import FPSWidget
from core.ui.widgets.lives_widget import LivesWidget
from core.ui.widgets.alert_dialog import AlertDialog
from core.map.tile_map_loader import TileMapLoader
from core.map.map_entity_spawner import MapEntitySpawner
from core.map.map_renderer import MapRenderer
from core.map.map_entity_spawner import MapEntitySpawner
from core.systems.animation_system import AnimationSystem
from core.systems.area_trigger_system import AreaTriggerSystem
from core.systems.freeze_system import FreezeSystem
from core.systems.eletrons_system import EletronSystem
from core.systems.path_following_system import PathFollowingSystem
from core.systems.light_system import LightSystem
from core.managers.attention_manager import AttentionManager
from core.managers.scene_manager import SceneManager
from core.ui.dialogue_interaction_hud_controller import DialogueInteractionHUDController
from core.ui.widgets.interaction_key_widget import InteractionKeyWidget
from core.ui.widgets.button import Button
from core.ui.widgets.gesture_detector import ClickType

class Level2(BaseScene):
    def __init__(self, screen:Surface):
        loader = TileMapLoader()
        self.tile_map=loader.load("fases/fase_2.tmx")
        self.scale = 2


        super().__init__(screen, self.tile_map.map_width*self.scale, self.tile_map.map_height*self.scale)

        
        self.camera.scale=self.scale
        
        self.map_renderer=MapRenderer(self.tile_map,self.camera,self.screen,self.scale,(32,32))

        self.set_ui()
        self.set_map()
        self.set_systems()

      
        self.player =  self.entity_mn.get_player()
        self.camera.follow = self.player

        self.set_door()

        self.index_dialog_for_old_paper = '5'
        self.key:Key= self.entity_mn.get_entities_by_class(Key)[0]
        self.key.on_deactive()
        self.old_paper:OldPaper =  self.entity_mn.get_entities_by_class(OldPaper)[0]


        self.attention_manager = AttentionManager(self.entity_mn)
        self.dialogue_hud = DialogueInteractionHUDController(
            self.entity_mn,
            self.dialog_system,
            self.interaction_key_widget,
        )
        
        self.scene_manager     = SceneManager.get()
        self._events_bound = False
        self._current_dialog_step = 1
        self._normalize_dialogue_sequence()

    def _normalize_dialogue_sequence(self):
        expected_name = f"dialog_{self._current_dialog_step}"
        for area in self.entity_mn.get_entities_by_class(DialogueArea):
            if not area.has(Dialogue):
                continue
            dialogue: Dialogue = area.get(Dialogue)
            dialogue.active_status = (area.name == expected_name)
    def set_door(self):
        self.door:Door = self.entity_mn.get_entities_by_class(Door)[0]
        pos :Position= self.door.get(Position)
        pos.x +=16
        pos.y +=16


        self.door.next_scene = 'exp_fase_3'
    def set_systems(self):
        self.animation_system  =  AnimationSystem()
        self.area_trigger_system  = AreaTriggerSystem()
        self.freeze_system     = FreezeSystem()
        self.eletron_system = EletronSystem(self.tile_map)
        self.light_system   = LightSystem(self.screen,self.camera,debug=True)
        self.path_following_system =  PathFollowingSystem()
        self.systems.update(

            [self.freeze_system,
            self.eletron_system,
            self.path_following_system,
            self.physics_system,
            self.animation_system,
            self.area_trigger_system,
            self.render_system,
            
            ]
            )

    def set_ui(self):
        fps=FPSWidget()
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

        
    def start(self):
        self.event_manager.post({'type':'release_freeze'})
        self.set_subscribes()

    def set_subscribes(self):
        if self._events_bound:
            return
        self._events_bound = True

        self.event_manager.subscribe("request_freeze", self.freeze_system.request_freeze)
        self.event_manager.subscribe("release_freeze", self.freeze_system.release_freeze)
        self.event_manager.subscribe("dialogue_end", self._on_dialogue_end)
        self.event_manager.subscribe("kill_entity",self.kill_entity_event)
        self.event_manager.subscribe("open_old_paper",self.open_old_paper)
        self.event_manager.subscribe("close_old_paper",self.after_close_old_paper)
        self.event_manager.subscribe('get_key',self.door.open)

    def _on_dialogue_end(self, event):
        entity = event.get("entity")
        if not isinstance(entity, DialogueArea):
            return

        expected_name = f"dialog_{self._current_dialog_step}"
        if entity.name != expected_name:
            return

        self.attention_manager.set_attention_position_after_event(event)
        self._advance_dialogue_sequence(event)
        self.set_old_paper(event)

    def _advance_dialogue_sequence(self, event):
        entity = event.get("entity")
        if not isinstance(entity, DialogueArea):
            return

        expected_name = f"dialog_{self._current_dialog_step}"
        if entity.name != expected_name:
            return

        current_dialogue: Dialogue = entity.get(Dialogue)
        current_dialogue.active_status = False

        self._current_dialog_step += 1
        next_name = f"dialog_{self._current_dialog_step}"
        next_area = None
        for area in self.entity_mn.get_entities_by_class(DialogueArea):
            dialogue: Dialogue = area.get(Dialogue)
            if area.name == next_name:
                dialogue.active_status = True
                next_area = area
            else:
                dialogue.active_status = False

        if next_area is None:
            self.key.on_active()
    
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
        for event in events:
            self.ui_manager.handle_event(event)
        self._handle_door_interaction(events)
        self.player.input(events)

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

    def update(self, dt):
        can_door_interact = self.door.can_player_interact(self.player) if self.door and self.player else False
        self.dialogue_hud.update(self.player, extra_interaction=can_door_interact)
        self.dialog_system.update(self.entity_mn, self.player,dt)

        self.update_systems(dt)
        self.ui_manager.update(dt)
       
    def render(self):
    
        self.screen.fill(BLACK)
        self.map_renderer.draw()
        self.render_system.draw(scale=self.scale) 
        #self.light_system.update(self.entity_mn,0)
        self.ui_manager.draw(self.screen)
