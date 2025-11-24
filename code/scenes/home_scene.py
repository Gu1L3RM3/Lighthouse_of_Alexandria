from pygame import Surface
from core.settings import *
from scenes.base_scene import BaseScene
from entities.dialogue_area import DialogueArea
from entities.itens.old_paper import OldPaper
from core.ui.widgets.fps_widget import FPSWidget
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

class HomeScene(BaseScene):
    def __init__(self, screen:Surface):
        loader = TileMapLoader()
        self.tile_map=loader.load("house.tmx")
        self.scale = 2
        super().__init__(screen, self.tile_map.map_width*self.scale, self.tile_map.map_height*self.scale)

        
        
        self.map_renderer=MapRenderer(self.tile_map,self.camera,self.screen,self.scale)
        fps=FPSWidget()
        self.ui_manager.add(fps)
        self.set_map()

        self.animation_system =  AnimationSystem()
        self.area_trigger_system = AreaTriggerSystem()
        self.freeze_system = FreezeSystem()
        
        self.camera.scale =  self.scale
        self.camera.follow = self.player
        self.index_dialog_for_old_paper = '2'
    

        self.systems.update(
            [self.freeze_system,
            self.physics_system,
            self.animation_system,
            self.area_trigger_system,
            self.render_system]
            )
        self.attention_manager = AttentionManager(self.entity_mn)
        self.scene_manager     = SceneManager.get() 

    def start(self):
        self.set_subscribes()
       


    def set_subscribes(self):
        self.event_manager.subscribe("request_freeze", self.freeze_system.request_freeze)
        self.event_manager.subscribe("release_freeze", self.freeze_system.release_freeze)

        self.event_manager.subscribe("dialogue_end",self.attention_manager.set_attention_position_after_event)
        self.event_manager.subscribe("dialogue_end",self.attention_manager.set_dialogue_area_after_event)
        self.event_manager.subscribe("dialogue_end",self.set_old_paper)
        self.event_manager.subscribe("open_old_paper",self.open_old_paper)
        self.event_manager.subscribe("close_old_paper",self.after_close_old_paper)
    def after_close_old_paper(self,event):
        self.event_manager.post({'type':'release_freeze'})
        self.scene_manager.start_fade('level_1')
    def set_old_paper(self,event):
        dialogue :DialogueArea= event['entity']
        if not isinstance(dialogue,DialogueArea):
            return
        if not self.index_dialog_for_old_paper in dialogue.name:
            return
         
        self.old_paper :OldPaper= self.entity_mn.get_entities_by_class(OldPaper)[0]
        self.old_paper.on_active()


    def open_old_paper(self,event):
        self.event_manager.post({'type':'request_freeze','type_request':'teste'})
        def close_old_paper(widget):
            self.ui_manager.remove(widget)
            self.event_manager.post({'type':'close_old_paper'})

        paper :Surface= self.resources.load_image('letters/letter_1.png')
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

    def process_input(self, events):
        self.player.input(events)

    def update(self, dt):
        self.dialog_system.update(self.entity_mn, self.player,dt)

        self.update_systems(dt)
        self.ui_manager.update(dt)
    
    def render(self):
    
        self.screen.fill(BLACK)
        self.map_renderer.draw()
        self.render_system.draw(scale=self.scale) 
        self.ui_manager.draw(self.screen)
